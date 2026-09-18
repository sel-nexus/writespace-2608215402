"""File-backed SQLite integration tests for WriteSpace authentication."""

from pathlib import Path

import bcrypt
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.main import create_app
from app.models import User


def make_client(tmp_path: Path) -> TestClient:
    """Create a client backed by an isolated file-based SQLite database.

    Args:
        tmp_path: Pytest-provided temporary directory.

    Returns:
        An application test client.
    """
    settings = Settings(
        DATABASE_URL=f"sqlite:///{(tmp_path / 'auth.db').as_posix()}",
        SEED_ON_STARTUP=True,
        CORS_ORIGINS="http://testserver",
        JWT_SECRET="test-signing-secret-with-sufficient-length",
        JWT_EXPIRATION_MINUTES=60,
    )
    return TestClient(create_app(settings))


def registration_payload(username: str = "newreader") -> dict[str, str]:
    """Build a valid public registration request.

    Args:
        username: Username to include.

    Returns:
        A strict registration payload.
    """
    return {"display_name": "New Reader", "username": username, "password": "reader-pass-123", "confirm_password": "reader-pass-123"}


def test_registration_hashes_password_and_projects_only_safe_user_fields(tmp_path: Path) -> None:
    """Registering persists bcrypt credentials while response excludes them."""
    client = make_client(tmp_path)
    with client:
        response = client.post("/api/auth/register", json=registration_payload())
        session = client.app.state.session_factory()
        try:
            user = session.scalar(select(User).where(User.username == "newreader"))
        finally:
            session.close()
    assert response.status_code == 201
    assert set(response.json()["user"]) == {"id", "display_name", "username", "role", "created_at"}
    assert "password" not in response.text and "password_hash" not in response.text
    assert user is not None and user.password_hash.startswith("$2")
    assert bcrypt.checkpw(b"reader-pass-123", user.password_hash.encode("utf-8"))


def test_registration_normalizes_and_rejects_case_insensitive_duplicate(tmp_path: Path) -> None:
    """A normalized username cannot be registered twice with different case."""
    client = make_client(tmp_path)
    with client:
        first = client.post("/api/auth/register", json=registration_payload("ReaderName"))
        second = client.post("/api/auth/register", json=registration_payload("readername"))
    assert first.status_code == 201
    assert first.json()["user"]["username"] == "readername"
    assert second.status_code == 409
    assert second.json()["code"] == "username_conflict"


def test_registration_rejects_reserved_admin_and_elevated_role_input(tmp_path: Path) -> None:
    """Seeded admin conflicts and undeclared role input receives native validation."""
    client = make_client(tmp_path)
    with client:
        reserved = client.post("/api/auth/register", json=registration_payload("admin"))
        elevated = client.post("/api/auth/register", json={**registration_payload("ordinary"), "role": "admin"})
    assert reserved.status_code == 409
    assert elevated.status_code == 422


def test_login_always_returns_exact_safe_invalid_credentials_envelope(tmp_path: Path) -> None:
    """Unknown and wrong credentials produce the same safe 401 payload."""
    client = make_client(tmp_path)
    with client:
        unknown = client.post("/api/auth/login", json={"username": "nobody", "password": "wrong-pass"})
        wrong = client.post("/api/auth/login", json={"username": "admin", "password": "wrong-pass"})
    for response in (unknown, wrong):
        body = response.json()
        assert response.status_code == 401
        assert body["code"] == "invalid_credentials"
        assert body["message"] == "Invalid username or password."
        assert isinstance(body["request_id"], str)


def test_successful_login_and_me_return_safe_projection(tmp_path: Path) -> None:
    """A seeded account receives a usable token and safe current-user projection."""
    client = make_client(tmp_path)
    with client:
        login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        token = login.json()["access_token"]
        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert set(me.json()) == {"id", "display_name", "username", "role", "created_at"}


def test_missing_and_invalid_bearers_receive_401(tmp_path: Path) -> None:
    """Protected profile denies absent and malformed bearer tokens."""
    client = make_client(tmp_path)
    with client:
        missing = client.get("/api/auth/me")
        invalid = client.get("/api/auth/me", headers={"Authorization": "Bearer not.a.token"})
    assert missing.status_code == 401
    assert invalid.status_code == 401


def test_inactive_account_cannot_login_or_use_existing_token(tmp_path: Path) -> None:
    """Inactive users are denied at both credential and token checks."""
    client = make_client(tmp_path)
    with client:
        login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        token = login.json()["access_token"]
        session = client.app.state.session_factory()
        try:
            admin = session.scalar(select(User).where(User.username == "admin"))
            assert admin is not None
            admin.is_active = False
            session.commit()
        finally:
            session.close()
        rejected_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        rejected_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert rejected_login.status_code == 401
    assert rejected_login.json()["code"] == "invalid_credentials"
    assert rejected_me.status_code == 401

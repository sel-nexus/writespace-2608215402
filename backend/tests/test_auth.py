"""File-backed SQLite authentication and strict-input tests."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'auth.db'}", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver", JWT_SECRET="test-auth-secret")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def register_payload() -> dict[str, str]:
    return {"display_name": "New Reader", "username": "newreader", "password": "reader-pass-123", "confirm_password": "reader-pass-123"}


def test_registration_and_login_return_uuid_safe_user(client: TestClient) -> None:
    registered = client.post("/api/auth/register", json=register_payload())
    assert registered.status_code == 201
    assert len(registered.json()["user"]["id"]) == 36
    login = client.post("/api/auth/login", json={"username": "newreader", "password": "reader-pass-123"})
    assert login.status_code == 200 and "password" not in login.text


@pytest.mark.parametrize("path,payload", [
    ("/api/auth/register", {"username": "only"}),
    ("/api/auth/register", {"display_name": 3, "username": "reader", "password": "password8", "confirm_password": "password8"}),
    ("/api/auth/login", {"username": "admin"}),
    ("/api/auth/login", {"username": ["admin"], "password": "admin"}),
])
def test_registration_and_login_reject_missing_or_wrong_typed_fields(client: TestClient, path: str, payload: dict[str, object]) -> None:
    response = client.post(path, json=payload)
    assert response.status_code == 422
    assert response.status_code < 500 and "traceback" not in response.text.lower()


def test_invalid_credentials_and_me_bearers_are_safe(client: TestClient) -> None:
    for response in (client.post("/api/auth/login", json={"username": "nobody", "password": "password8"}), client.get("/api/auth/me"), client.get("/api/auth/me", headers={"Authorization": "Bearer malformed"})):
        assert response.status_code == 401
        assert "traceback" not in response.text.lower()

"""Real file-backed SQLite TestClient coverage for backend endpoint contracts."""

import sqlite3
from pathlib import Path
from uuid import uuid4

import bcrypt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.config import Settings
from app.main import create_app


def make_client(tmp_path: Path, name: str = "contract.db") -> TestClient:
    """Create an application client backed by a dedicated SQLite file."""
    settings = Settings(
        DATABASE_URL=f"sqlite:///{tmp_path / name}",
        CORS_ORIGINS="http://testserver",
        JWT_SECRET="contract-secret",
        SEED_ON_STARTUP=True,
    )
    return TestClient(create_app(settings))


def auth_headers(client: TestClient, username: str, password: str) -> dict[str, str]:
    """Log in and return a bearer header for the supplied active account."""
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def register(client: TestClient, username: str, display_name: str | None = None) -> tuple[dict[str, str], str]:
    """Register a standard writer and return its token header and UUID."""
    response = client.post(
        "/api/auth/register",
        json={
            "display_name": display_name or username.title(),
            "username": username,
            "password": "password8",
            "confirm_password": "password8",
        },
    )
    assert response.status_code == 201
    return {"Authorization": f"Bearer {response.json()['access_token']}"}, response.json()["user"]["id"]


@pytest.mark.parametrize("path", ["/api/health", "/api/public/posts"])
def test_public_and_health_statuses_are_explicit(tmp_path: Path, path: str) -> None:
    """Return successful explicit statuses for unauthenticated operational routes."""
    with make_client(tmp_path) as client:
        response = client.get(path)
    assert response.status_code == 200


@pytest.mark.parametrize(
    "path,payload",
    [
        ("/api/auth/register", {}),
        ("/api/auth/register", {"display_name": "Name", "username": "valid", "password": "password8"}),
        ("/api/auth/register", {"display_name": 1, "username": "valid", "password": "password8", "confirm_password": "password8"}),
        ("/api/auth/register", {"display_name": " ", "username": "valid", "password": "password8", "confirm_password": "password8"}),
        ("/api/auth/register", {"display_name": "Name", "username": "ab", "password": "password8", "confirm_password": "password8"}),
        ("/api/auth/register", {"display_name": "Name", "username": "u" * 51, "password": "password8", "confirm_password": "password8"}),
        ("/api/auth/register", {"display_name": "Name", "username": "valid", "password": "short", "confirm_password": "short"}),
        ("/api/auth/register", {"display_name": "Name", "username": "valid", "password": "p" * 129, "confirm_password": "p" * 129}),
        ("/api/auth/login", {}),
        ("/api/auth/login", {"username": ["admin"], "password": "admin"}),
        ("/api/auth/login", {"username": "   ", "password": "admin"}),
        ("/api/auth/login", {"username": "admin", "password": " "}),
        ("/api/auth/login", {"username": "u" * 51, "password": "admin"}),
        ("/api/auth/login", {"username": "admin", "password": "p" * 129}),
    ],
)
def test_auth_strict_fields_missing_types_blank_and_boundaries(tmp_path: Path, path: str, payload: dict[str, object]) -> None:
    """Reject malformed authentication request fields before domain processing."""
    with make_client(tmp_path) as client:
        response = client.post(path, json=payload)
    assert response.status_code == 422


def test_registration_rejects_case_variant_and_preserves_boundary_values(tmp_path: Path) -> None:
    """Enforce case-insensitive usernames while accepting documented maximum fields."""
    with make_client(tmp_path) as client:
        payload = {"display_name": "D" * 120, "username": "u" * 50, "password": "p" * 128, "confirm_password": "p" * 128}
        assert client.post("/api/auth/register", json=payload).status_code == 201
        duplicate = client.post("/api/auth/register", json={**payload, "username": ("U" * 50)})
    assert duplicate.status_code == 409


def test_post_crud_owner_nonowner_admin_and_missing_contract(tmp_path: Path) -> None:
    """Enforce owner-or-admin mutations while preserving normal CRUD behavior."""
    with make_client(tmp_path) as client:
        owner_headers, _ = register(client, "owner")
        other_headers, _ = register(client, "other")
        admin = auth_headers(client, "admin", "admin")
        created = client.post("/api/posts", headers=owner_headers, json={"title": "Original", "content": "Original content"})
        assert created.status_code == 201
        post_id = created.json()["id"]
        listing = client.get("/api/posts?limit=1", headers=owner_headers)
        assert listing.status_code == 200 and listing.json()[0]["id"] == post_id
        detail = client.get(f"/api/posts/{post_id}", headers=other_headers)
        assert detail.status_code == 200 and detail.json()["content"] == "Original content"
        assert client.put(f"/api/posts/{post_id}", headers=other_headers, json={"title": "No", "content": "No"}).status_code == 403
        assert client.delete(f"/api/posts/{post_id}", headers=other_headers).status_code == 403
        owner_update = client.put(f"/api/posts/{post_id}", headers=owner_headers, json={"title": "Owner edit", "content": "Owner content"})
        assert owner_update.status_code == 200 and owner_update.json()["title"] == "Owner edit"
        admin_update = client.put(f"/api/posts/{post_id}", headers=admin, json={"title": "Admin edit", "content": "Admin content"})
        assert admin_update.status_code == 200 and admin_update.json()["title"] == "Admin edit"
        assert client.get(f"/api/posts/{uuid4()}", headers=owner_headers).status_code == 404
        assert client.put(f"/api/posts/{uuid4()}", headers=owner_headers, json={"title": "x", "content": "y"}).status_code == 404
        assert client.delete(f"/api/posts/{uuid4()}", headers=owner_headers).status_code == 404
        assert client.delete(f"/api/posts/{post_id}", headers=admin).status_code == 204
        assert client.get(f"/api/posts/{post_id}", headers=owner_headers).status_code == 404


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": "x"},
        {"content": "x"},
        {"title": 1, "content": "x"},
        {"title": "x", "content": 1},
        {"title": " ", "content": "x"},
        {"title": "x", "content": " \n"},
        {"title": "x" * 201, "content": "x"},
        {"title": "x", "content": "x" * 50001},
        {"title": "x", "content": "x", "author_id": str(uuid4())},
    ],
)
def test_post_write_strict_fields_missing_type_blank_and_boundaries(tmp_path: Path, payload: dict[str, object]) -> None:
    """Reject every invalid post field shape while accepting exact maximum boundaries."""
    with make_client(tmp_path) as client:
        headers = auth_headers(client, "admin", "admin")
        assert client.post("/api/posts", headers=headers, json=payload).status_code == 422
        exact = client.post("/api/posts", headers=headers, json={"title": "t" * 200, "content": "c" * 50000})
    assert exact.status_code == 201


def test_admin_users_stats_lifecycle_authorization_and_stale_token(tmp_path: Path) -> None:
    """Persist deactivation and ensure stale credentials fail downstream safely."""
    with make_client(tmp_path) as client:
        admin = auth_headers(client, "admin", "admin")
        writer_headers, writer_id = register(client, "writer", "Writer Snapshot")
        created_post = client.post("/api/posts", headers=writer_headers, json={"title": "Snapshot", "content": "Retained body"})
        assert created_post.status_code == 201
        assert client.get("/api/admin/stats", headers={}).status_code == 401
        assert client.get("/api/admin/stats", headers=writer_headers).status_code == 403
        stats = client.get("/api/admin/stats", headers=admin)
        assert stats.status_code == 200 and stats.json()["post_count"] == 1
        assert client.get("/api/users", headers=admin).status_code == 200
        assert client.get("/api/users", headers=writer_headers).status_code == 403
        created = client.post("/api/users", headers=admin, json={"display_name": "Managed", "username": "managed", "password": "password8", "role": "user"})
        assert created.status_code == 201 and created.json()["is_active"] is True
        assert client.post("/api/users", headers=admin, json={"display_name": "Other", "username": "MANAGED", "password": "password8", "role": "user"}).status_code == 409
        assert client.patch(f"/api/users/{uuid4()}/deactivate", headers=admin).status_code == 404
        assert client.delete(f"/api/users/{uuid4()}", headers=admin).status_code == 404
        deactivated = client.patch(f"/api/users/{writer_id}/deactivate", headers=admin)
        assert deactivated.status_code == 200 and deactivated.json()["is_active"] is False
        with client.app.state.session_factory() as session:
            stored = session.execute(text("SELECT is_active FROM users WHERE id = :id"), {"id": writer_id}).scalar_one()
            assert stored == 0
        assert client.post("/api/auth/login", json={"username": "writer", "password": "password8"}).status_code == 401
        stale_response = client.post("/api/posts", headers=writer_headers, json={"title": "Must not persist", "content": "stale downstream"})
        assert stale_response.status_code == 401
        retained = client.get(f"/api/posts/{created_post.json()['id']}", headers=admin)
        assert retained.status_code == 200
        assert retained.json()["author"] == {"id": writer_id, "display_name": "Writer Snapshot", "role": "user"}
        assert client.delete(f"/api/users/{writer_id}", headers=admin).status_code == 204
        retained_after_delete = client.get(f"/api/posts/{created_post.json()['id']}", headers=admin)
    assert retained_after_delete.status_code == 200
    assert retained_after_delete.json()["author"] == {"id": None, "display_name": "Writer Snapshot", "role": "user"}


@pytest.mark.parametrize("method,path", [
    ("get", "/api/users"),
    ("post", "/api/users"),
    ("patch", f"/api/users/{uuid4()}/deactivate"),
    ("delete", f"/api/users/{uuid4()}"),
])
def test_user_endpoints_reject_missing_and_malformed_bearers(tmp_path: Path, method: str, path: str) -> None:
    """Fail closed for each user-management method before route work begins."""
    payload = {"display_name": "Valid", "username": "valid", "password": "password8", "role": "user"}
    with make_client(tmp_path) as client:
        for headers in ({}, {"Authorization": "Bearer malformed"}):
            response = client.request(method.upper(), path, headers=headers, json=payload if method == "post" else None)
            assert response.status_code == 401


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"display_name": "Name", "username": "valid", "password": "password8"},
        {"display_name": 1, "username": "valid", "password": "password8", "role": "user"},
        {"display_name": "Name", "username": 1, "password": "password8", "role": "user"},
        {"display_name": "Name", "username": "valid", "password": 1, "role": "user"},
        {"display_name": " ", "username": "valid", "password": "password8", "role": "user"},
        {"display_name": "Name", "username": "   ", "password": "password8", "role": "user"},
        {"display_name": "N" * 121, "username": "valid", "password": "password8", "role": "user"},
        {"display_name": "Name", "username": "u" * 51, "password": "password8", "role": "user"},
        {"display_name": "Name", "username": "valid", "password": "p" * 129, "role": "user"},
    ],
)
def test_admin_user_create_strict_fields_missing_type_blank_and_bounds(tmp_path: Path, payload: dict[str, object]) -> None:
    """Reject invalid administrative account bodies at the HTTP boundary."""
    with make_client(tmp_path) as client:
        response = client.post("/api/users", headers=auth_headers(client, "admin", "admin"), json=payload)
    assert response.status_code == 422


def test_legacy_integer_schema_migration_retains_accounts_posts_mappings_and_backups(tmp_path: Path) -> None:
    """Migrate a manually-created legacy SQLite database without destructive data loss."""
    database = tmp_path / "legacy.db"
    password_hash = bcrypt.hashpw(b"password8", bcrypt.gensalt()).decode("utf-8")
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT, role TEXT, active INTEGER, created TEXT)")
        connection.execute("CREATE TABLE posts (id INTEGER PRIMARY KEY, title TEXT, body TEXT, user_id INTEGER, author TEXT, created TEXT)")
        connection.execute("INSERT INTO users VALUES (7, 'legacywriter', ?, 'user', 1, '2020-01-01T00:00:00+00:00')", (password_hash,))
        connection.execute("INSERT INTO posts VALUES (9, 'Legacy retained', 'Legacy body retained', 7, 'Legacy Writer', '2020-01-02T00:00:00+00:00')")
    settings = Settings(DATABASE_URL=f"sqlite:///{database}", CORS_ORIGINS="http://testserver", JWT_SECRET="legacy-secret", SEED_ON_STARTUP=False)
    with TestClient(create_app(settings)) as client:
        login = client.post("/api/auth/login", json={"username": "legacywriter", "password": "password8"})
        assert login.status_code == 200
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        posts = client.get("/api/posts", headers=headers)
        assert posts.status_code == 200
        assert posts.json()[0]["title"] == "Legacy retained"
        assert posts.json()[0]["content"] == "Legacy body retained"
        assert posts.json()[0]["author"] == {"id": login.json()["user"]["id"], "display_name": "Legacy Writer", "role": "user"}
        assert posts.json()[0]["author"]["id"] != "7"
        with client.app.state.engine.connect() as connection:
            assert connection.execute(text("SELECT user_id FROM legacy_user_id_map WHERE legacy_id = '7'")).scalar_one() == login.json()["user"]["id"]
            assert connection.execute(text("SELECT COUNT(*) FROM users__legacy_backup")).scalar_one() == 1
            assert connection.execute(text("SELECT COUNT(*) FROM posts__legacy_backup")).scalar_one() == 1
            assert connection.execute(text("SELECT title FROM posts__legacy_backup WHERE id = 9")).scalar_one() == "Legacy retained"
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get("/api/health").status_code == 200
        with restarted.app.state.engine.connect() as connection:
            assert connection.execute(text("SELECT COUNT(*) FROM users")).scalar_one() == 1
            assert connection.execute(text("SELECT COUNT(*) FROM posts")).scalar_one() == 1

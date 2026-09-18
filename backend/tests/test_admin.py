"""File-backed SQLite API coverage for WriteSpace administration."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.auth.jwt import create_access_token
from app.config import Settings, get_settings
from app.main import create_app
from app.models import Post, User


@pytest.fixture
def client(tmp_path: Path):
    """Yield a client backed by a fresh temporary SQLite file."""
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'admin.db'}", JWT_SECRET="test-admin-secret", SEED_ON_STARTUP=False, CORS_ORIGINS="http://testserver")
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client, settings


def add_user(client: TestClient, settings: Settings, username: str, role: str = "user", is_default: bool = False) -> tuple[User, str]:
    """Persist an active account and return its signed bearer token."""
    with client.app.state.session_factory() as session:
        account = User(username=username, display_name=username.title(), password_hash="unused", role=role, is_active=True, is_default=is_default)
        session.add(account)
        session.commit()
        session.refresh(account)
        return account, create_access_token(account.id, account.role, settings)


def auth(token: str) -> dict[str, str]:
    """Build bearer authorization headers."""
    return {"Authorization": f"Bearer {token}"}


def test_admin_endpoints_require_valid_active_administrator(client) -> None:
    """Guests and standard users are denied while an administrator succeeds."""
    test_client, settings = client
    _, user_token = add_user(test_client, settings, "reader")
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    assert test_client.get("/api/admin/stats").status_code == 401
    assert test_client.get("/api/users").status_code == 401
    forbidden = test_client.get("/api/admin/stats", headers=auth(user_token))
    assert forbidden.status_code == 403 and forbidden.json()["code"] == "admin_forbidden"
    assert test_client.get("/api/users", headers=auth(admin_token)).status_code == 200


def test_stats_uses_counts_and_newest_five_safe_post_projections(client) -> None:
    """Stats counts persisted rows and orders only the five latest safe posts."""
    test_client, settings = client
    writer, _ = add_user(test_client, settings, "writer")
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    with test_client.app.state.session_factory() as session:
        for number in range(6):
            session.add(Post(title=f"Note {number}", body=f"Body {number}", author_id=writer.id, author_display_name="Writer", author_role="user", created_at=datetime.now(timezone.utc) + timedelta(minutes=number), updated_at=datetime.now(timezone.utc)))
        inactive = User(username="inactive", display_name="Inactive", password_hash="unused", role="user", is_active=False)
        session.add(inactive)
        session.commit()
    response = test_client.get("/api/admin/stats", headers=auth(admin_token))
    assert response.status_code == 200
    body = response.json()
    assert body["user_count"] == 3 and body["active_user_count"] == 2 and body["post_count"] == 6
    assert [post["title"] for post in body["recent_posts"]] == ["Note 5", "Note 4", "Note 3", "Note 2", "Note 1"]
    assert "body" not in body["recent_posts"][0] and body["recent_posts"][0]["author"]["display_name"] == "Writer"


def test_admin_can_create_strict_user_and_conflict_is_safe(client) -> None:
    """Creation allows only explicit fields and reports case-insensitive conflicts."""
    test_client, settings = client
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    payload = {"display_name": "Created User", "username": "Created", "password": "password8", "role": "user"}
    created = test_client.post("/api/users", headers=auth(admin_token), json=payload)
    conflict = test_client.post("/api/users", headers=auth(admin_token), json={**payload, "username": "created"})
    forged = test_client.post("/api/users", headers=auth(admin_token), json={**payload, "is_active": False})
    assert created.status_code == 201 and set(created.json()) == {"id", "display_name", "username", "role", "created_at"}
    assert conflict.status_code == 409 and conflict.json()["code"] == "username_conflict"
    assert forged.status_code == 422


def test_deactivate_updates_eligible_account_and_missing_returns_404(client) -> None:
    """Deactivation persists inactive state and handles an absent account safely."""
    test_client, settings = client
    target, _ = add_user(test_client, settings, "target")
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    response = test_client.patch(f"/api/users/{target.id}/deactivate", headers=auth(admin_token))
    missing = test_client.patch("/api/users/99999/deactivate", headers=auth(admin_token))
    assert response.status_code == 200 and response.json()["username"] == "target"
    assert missing.status_code == 404
    with test_client.app.state.session_factory() as session:
        assert session.get(User, target.id).is_active is False


def test_self_and_default_administrator_are_protected(client) -> None:
    """Administrators cannot deactivate themselves or delete the default admin."""
    test_client, settings = client
    default, _ = add_user(test_client, settings, "default", role="admin", is_default=True)
    manager, manager_token = add_user(test_client, settings, "manager", role="admin")
    self_deactivate = test_client.patch(f"/api/users/{manager.id}/deactivate", headers=auth(manager_token))
    default_delete = test_client.delete(f"/api/users/{default.id}", headers=auth(manager_token))
    assert self_deactivate.status_code == 403 and self_deactivate.json()["code"] == "user_protected"
    assert default_delete.status_code == 403 and default_delete.json()["code"] == "user_protected"


def test_deleting_eligible_user_nulls_foreign_key_and_keeps_snapshot_attribution(client) -> None:
    """Deletion preserves readable author identity while breaking the account link."""
    test_client, settings = client
    author, _ = add_user(test_client, settings, "author")
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    with test_client.app.state.session_factory() as session:
        post = Post(title="Historical", body="Retained", author_id=author.id, author_display_name="Author", author_role="user")
        session.add(post); session.commit(); session.refresh(post); post_id = post.id
    deleted = test_client.delete(f"/api/users/{author.id}", headers=auth(admin_token))
    read = test_client.get(f"/api/posts/{post_id}", headers=auth(admin_token))
    assert deleted.status_code == 204 and read.status_code == 200
    assert read.json()["author"] == {"id": None, "display_name": "Author", "role": "user"}
    with test_client.app.state.session_factory() as session:
        preserved = session.scalar(select(Post).where(Post.id == post_id))
        assert preserved is not None and preserved.author_id is None and preserved.author_display_name == "Author"


def test_admin_override_remains_available_for_another_authors_post(client) -> None:
    """An administrator retains the established override for post revisions."""
    test_client, settings = client
    _, writer_token = add_user(test_client, settings, "writer")
    _, admin_token = add_user(test_client, settings, "manager", role="admin")
    created = test_client.post("/api/posts", headers=auth(writer_token), json={"title": "Original", "content": "Body"}).json()
    updated = test_client.put(f"/api/posts/{created['id']}", headers=auth(admin_token), json={"title": "Revision", "content": "Admin body"})
    assert updated.status_code == 200 and updated.json()["title"] == "Revision"

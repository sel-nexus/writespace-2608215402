"""API coverage for author-controlled post creation, changes, and deletion."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.config import Settings, get_settings
from app.main import create_app
from app.models import Post, User


@pytest.fixture
def client(tmp_path: Path):
    """Create an application using a fresh file-backed SQLite database."""
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'writer.db'}", JWT_SECRET="test-writer-secret", SEED_ON_STARTUP=False, CORS_ORIGINS="http://testserver")
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client, settings


def make_user(client: TestClient, settings: Settings, username: str, role: str = "user") -> tuple[User, str]:
    """Persist one active account and issue its real bearer token."""
    with client.app.state.session_factory() as session:
        user = User(username=username, display_name=username.title(), password_hash="unused", role=role, is_active=True)
        session.add(user)
        session.commit()
        session.refresh(user)
        return user, create_access_token(user.id, user.role, settings)


def headers(token: str) -> dict[str, str]:
    """Build authenticated request headers."""
    return {"Authorization": f"Bearer {token}"}


def test_create_rejects_forged_or_invalid_write_fields(client) -> None:
    """Writer input accepts only bounded title and content fields."""
    test_client, settings = client
    _, token = make_user(test_client, settings, "writer")

    forged = test_client.post("/api/posts", headers=headers(token), json={"title": "Valid", "content": "Body", "author_id": 999})
    empty = test_client.post("/api/posts", headers=headers(token), json={"title": "", "content": ""})
    oversized = test_client.post("/api/posts", headers=headers(token), json={"title": "x" * 201, "content": "Body"})

    assert forged.status_code == 422
    assert empty.status_code == 422
    assert oversized.status_code == 422


def test_create_derives_author_snapshot_and_server_timestamps(client) -> None:
    """A create response exposes only server-derived ownership and audit data."""
    test_client, settings = client
    writer, token = make_user(test_client, settings, "writer")

    response = test_client.post("/api/posts", headers=headers(token), json={"title": "Server-owned", "content": "Written here."})

    assert response.status_code == 201
    payload = response.json()
    assert payload["author"] == {"id": writer.id, "display_name": "Writer", "role": "user"}
    assert payload["created_at"] == payload["updated_at"]
    with test_client.app.state.session_factory() as session:
        post = session.get(Post, payload["id"])
        assert post is not None
        assert post.author_id == writer.id
        assert post.author_display_name == "Writer"
        assert post.author_role == "user"


def test_nonowner_mutations_return_403_and_leave_post_unchanged(client) -> None:
    """A different standard account cannot alter or remove an existing post."""
    test_client, settings = client
    owner, owner_token = make_user(test_client, settings, "owner")
    _, other_token = make_user(test_client, settings, "other")
    created = test_client.post("/api/posts", headers=headers(owner_token), json={"title": "Original", "content": "Original body"}).json()

    update = test_client.put(f"/api/posts/{created['id']}", headers=headers(other_token), json={"title": "Stolen", "content": "Changed"})
    delete = test_client.delete(f"/api/posts/{created['id']}", headers=headers(other_token))

    assert update.status_code == 403
    assert delete.status_code == 403
    with test_client.app.state.session_factory() as session:
        post = session.get(Post, created["id"])
        assert post is not None
        assert post.author_id == owner.id
        assert post.title == "Original"
        assert post.body == "Original body"


def test_admin_can_override_owner_and_missing_posts_return_404(client) -> None:
    """Administrators can update another user's post while absent records remain hidden."""
    test_client, settings = client
    _, owner_token = make_user(test_client, settings, "owner")
    _, admin_token = make_user(test_client, settings, "admin2", role="admin")
    created = test_client.post("/api/posts", headers=headers(owner_token), json={"title": "Original", "content": "Original body"}).json()

    updated = test_client.put(f"/api/posts/{created['id']}", headers=headers(admin_token), json={"title": "Admin revision", "content": "Changed by an admin"})
    missing_update = test_client.put("/api/posts/99999", headers=headers(admin_token), json={"title": "None", "content": "None"})
    missing_delete = test_client.delete("/api/posts/99999", headers=headers(admin_token))

    assert updated.status_code == 200
    assert updated.json()["title"] == "Admin revision"
    assert updated.json()["author"] == created["author"]
    assert missing_update.status_code == 404
    assert missing_delete.status_code == 404


def test_delete_persists_across_a_new_application_instance(client) -> None:
    """A successful 204 deletion remains absent after reopening the file database."""
    test_client, settings = client
    _, token = make_user(test_client, settings, "writer")
    created = test_client.post("/api/posts", headers=headers(token), json={"title": "Disposable", "content": "Remove me"}).json()

    response = test_client.delete(f"/api/posts/{created['id']}", headers=headers(token))
    assert response.status_code == 204
    assert response.content == b""

    restarted = create_app(settings)
    restarted.dependency_overrides[get_settings] = lambda: settings
    with TestClient(restarted) as reopened:
        missing = reopened.get(f"/api/posts/{created['id']}", headers=headers(token))
    assert missing.status_code == 404

"""API coverage for authenticated post-library reading."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from app.auth.jwt import create_access_token
from app.config import Settings, get_settings
from app.main import create_app
from app.models import Post, User


@pytest.fixture
def client(tmp_path):
    """Create an app backed by a fresh file-based SQLite database."""
    settings = Settings(
        DATABASE_URL=f"sqlite:///{tmp_path / 'reading.db'}",
        JWT_SECRET="test-reading-secret",
        SEED_ON_STARTUP=False,
        CORS_ORIGINS="http://testserver",
    )
    app = create_app(settings)
    app.dependency_overrides[get_settings] = lambda: settings
    with TestClient(app) as test_client:
        yield test_client, settings


def create_reader(client: TestClient, settings: Settings) -> tuple[User, str]:
    """Persist an active reader and return their real signed token."""
    session = client.app.state.session_factory
    with session() as database_session:
        reader = User(
            username="reader",
            display_name="Reading User",
            password_hash="not-exposed",
            role="user",
            is_active=True,
        )
        database_session.add(reader)
        database_session.commit()
        database_session.refresh(reader)
        token = create_access_token(reader.id, reader.role, settings)
        return reader, token


def auth_headers(token: str) -> dict[str, str]:
    """Return bearer authorization headers for a signed reader token."""
    return {"Authorization": f"Bearer {token}"}


def test_list_posts_orders_newest_then_id_and_honors_limit(client) -> None:
    """The library uses deterministic newest-first ordering and server bounds."""
    test_client, settings = client
    author, token = create_reader(test_client, settings)
    session_factory = test_client.app.state.session_factory
    shared_time = datetime(2026, 1, 2, tzinfo=UTC)
    with session_factory() as session:
        session.add_all([
            Post(title="Older", body="older content", author_id=author.id, created_at=datetime(2026, 1, 1, tzinfo=UTC)),
            Post(title="Tie first", body="first tied content", author_id=author.id, created_at=shared_time),
            Post(title="Tie second", body="second tied content", author_id=author.id, created_at=shared_time),
        ])
        session.commit()

    response = test_client.get("/api/posts?limit=2", headers=auth_headers(token))

    assert response.status_code == 200
    assert [post["title"] for post in response.json()] == ["Tie second", "Tie first"]
    assert len(response.json()) == 2


def test_list_posts_rejects_anonymous_requests_with_safe_401(client) -> None:
    """Missing bearer credentials never expose internals."""
    test_client, _ = client

    response = test_client.get("/api/posts")

    assert response.status_code == 401
    assert response.json()["code"] == "invalid_token"
    assert "request_id" in response.json()


def test_get_post_returns_full_safe_projection(client) -> None:
    """A reader receives full text and a safe stored-author projection only."""
    test_client, settings = client
    author, token = create_reader(test_client, settings)
    session_factory = test_client.app.state.session_factory
    with session_factory() as session:
        post = Post(title="A full note", body="First line.\nSecond line.", author_id=author.id)
        session.add(post)
        session.commit()
        session.refresh(post)

    response = test_client.get(f"/api/posts/{post.id}", headers=auth_headers(token))

    assert response.status_code == 200
    assert response.json() == {
        "id": post.id,
        "title": "A full note",
        "content": "First line.\nSecond line.",
        "excerpt": "First line. Second line.",
        "author": {"id": author.id, "display_name": "Reading User", "role": "user"},
        "created_at": response.json()["created_at"],
        "updated_at": response.json()["updated_at"],
    }
    assert "password_hash" not in response.text
    assert "is_default" not in response.text


def test_get_post_returns_safe_404_when_missing(client) -> None:
    """A valid but absent identifier receives the standard safe envelope."""
    test_client, settings = client
    _, token = create_reader(test_client, settings)

    response = test_client.get("/api/posts/9999", headers=auth_headers(token))

    assert response.status_code == 404
    assert response.json()["code"] == "post_not_found"
    assert "request_id" in response.json()


def test_list_posts_rejects_invalid_limit_with_native_422(client) -> None:
    """FastAPI validates the public list bound before querying the database."""
    test_client, settings = client
    _, token = create_reader(test_client, settings)

    response = test_client.get("/api/posts?limit=101", headers=auth_headers(token))

    assert response.status_code == 422

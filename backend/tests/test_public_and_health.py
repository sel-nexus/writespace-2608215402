"""Integration tests for public previews, health, and restart-safe seeding."""

from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.database import create_session_factory
from app.main import create_app
from app.models import Post, User


def make_client(tmp_path: Path) -> tuple[TestClient, Settings]:
    """Create a TestClient backed by a fresh file-based SQLite database."""
    database_path = tmp_path / "writespace-test.db"
    settings = Settings(
        DATABASE_URL=f"sqlite:///{database_path.as_posix()}",
        SEED_ON_STARTUP=True,
        CORS_ORIGINS="http://testserver",
    )
    return TestClient(create_app(settings)), settings


def add_post(client: TestClient, title: str, body: str, created_at: datetime) -> None:
    """Insert a post directly into the real test database for public-read setup."""
    session = client.app.state.session_factory()
    try:
        session.add(Post(title=title, body=body, created_at=created_at))
        session.commit()
    finally:
        session.close()


def test_public_posts_clamps_to_three_and_projects_safe_fields(tmp_path: Path) -> None:
    """Public previews return newest-first safe fields and normalized excerpts."""
    client, _ = make_client(tmp_path)
    with client:
        base_time = datetime(2025, 1, 1, tzinfo=timezone.utc)
        for index in range(4):
            add_post(
                client,
                f"Post {index}",
                "  Opening\n\nnotes    with  deliberate\tspace. " + ("x" * 260),
                base_time + timedelta(minutes=index),
            )
        response = client.get("/api/public/posts?limit=3")

    assert response.status_code == 200
    payload = response.json()
    assert [item["title"] for item in payload] == ["Post 3", "Post 2", "Post 1"]
    assert len(payload) == 3
    assert set(payload[0]) == {"id", "title", "excerpt", "created_at"}
    assert len(payload[0]["excerpt"]) == 240
    assert "  " not in payload[0]["excerpt"]


def test_public_posts_rejects_invalid_limit(tmp_path: Path) -> None:
    """The public endpoint rejects limits outside its strict one-to-three range."""
    client, _ = make_client(tmp_path)
    with client:
        too_high = client.get("/api/public/posts?limit=4")
        too_low = client.get("/api/public/posts?limit=0")

    assert too_high.status_code == 422
    assert too_low.status_code == 422


def test_health_reports_reachable_database_after_select_probe(tmp_path: Path) -> None:
    """Health returns only the safe reachable status after using real SQLite."""
    client, _ = make_client(tmp_path)
    with client:
        response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "reachable"}


def test_restart_safe_seed_creates_one_bcrypt_admin(tmp_path: Path) -> None:
    """Starting two app instances against one file creates the default admin once."""
    client, settings = make_client(tmp_path)
    with client:
        pass
    second_client = TestClient(create_app(settings))
    with second_client:
        session_factory = create_session_factory(second_client.app.state.engine)
        session = session_factory()
        try:
            admins = list(session.scalars(select(User).where(User.username == "admin")))
        finally:
            session.close()

    assert len(admins) == 1
    assert admins[0].password_hash.startswith("$2")
    assert "admin" not in admins[0].password_hash

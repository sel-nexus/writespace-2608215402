"""File-backed SQLite health and public-read API tests."""
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.config import Settings
from app.main import create_app
from app.models import Post


def make_client(tmp_path: Path) -> TestClient:
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'health.db'}", SEED_ON_STARTUP=False, CORS_ORIGINS="http://testserver")
    return TestClient(create_app(settings))


def test_health_reports_reachable_and_select_failure_is_safe_503(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    with client:
        assert client.get("/api/health").json() == {"status": "ok", "database": "reachable"}
        original = client.app.state.engine.connect
        client.app.state.engine.connect = Mock(side_effect=OperationalError("SELECT 1", {}, RuntimeError("secret database detail")))
        failed = client.get("/api/health")
        client.app.state.engine.connect = original
    assert failed.status_code == 503
    assert failed.json() == {"status": "unavailable", "database": "unreachable"}
    assert "secret database detail" not in failed.text


def test_public_preview_reads_uuid_post_without_internal_fields(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    with client:
        with client.app.state.session_factory() as session:
            post = Post(title="Public", content="  plain\ntext content  ", author_name="Snapshot", author_role="user", created_at=datetime(2026, 1, 1, tzinfo=UTC))
            session.add(post); session.commit()
        response = client.get("/api/public/posts?limit=1")
    assert response.status_code == 200
    assert len(response.json()[0]["id"]) == 36
    assert response.json()[0]["excerpt"] == "plain text content"
    assert "author" not in response.text

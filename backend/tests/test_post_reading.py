"""File-backed SQLite post reading tests."""
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_post_reading_uses_uuid_paths_and_safe_404(tmp_path: Path) -> None:
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'read.db'}", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver", JWT_SECRET="read-secret")
    with TestClient(create_app(settings)) as client:
        token = client.post("/api/auth/login", json={"username": "admin", "password": "admin"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        created = client.post("/api/posts", headers=headers, json={"title": "A note", "content": "Readable content"})
        assert created.status_code == 201 and len(created.json()["id"]) == 36
        assert client.get(f"/api/posts/{created.json()['id']}", headers=headers).json()["content"] == "Readable content"
        assert client.get("/api/posts/not-a-uuid", headers=headers).status_code == 422
        missing = client.get("/api/posts/00000000-0000-0000-0000-000000000000", headers=headers)
    assert missing.status_code == 404 and "traceback" not in missing.text.lower()

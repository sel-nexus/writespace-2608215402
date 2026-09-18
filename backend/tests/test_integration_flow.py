"""Cross-router file-backed SQLite integration coverage for WriteSpace."""

from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


def test_registration_authoring_and_administration_lifecycle_stay_consistent(tmp_path: Path) -> None:
    """Chain registration, posts, stats, lifecycle, and ownership error across routes."""
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'flow.db'}", JWT_SECRET="integration-secret", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver")
    with TestClient(create_app(settings)) as client:
        registration = client.post("/api/auth/register", json={"display_name": "Flow Writer", "username": "flowwriter", "password": "password8", "confirm_password": "password8"})
        assert registration.status_code == 201
        writer_token = registration.json()["access_token"]
        writer_headers = {"Authorization": f"Bearer {writer_token}"}
        created = client.post("/api/posts", headers=writer_headers, json={"title": "Integrated note", "content": "Created by the registered writer."})
        assert created.status_code == 201
        post_id = created.json()["id"]

        admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        assert admin_login.status_code == 200
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        stats = client.get("/api/admin/stats", headers=admin_headers)
        users = client.get("/api/users", headers=admin_headers)
        assert stats.status_code == 200 and stats.json()["post_count"] == 1
        assert stats.json()["recent_posts"][0]["author"]["display_name"] == "Flow Writer"
        writer_id = next(account["id"] for account in users.json() if account["username"] == "flowwriter")

        other_registration = client.post("/api/auth/register", json={"display_name": "Other Writer", "username": "otherwriter", "password": "password8", "confirm_password": "password8"})
        assert other_registration.status_code == 201
        other_headers = {"Authorization": f"Bearer {other_registration.json()['access_token']}"}
        ownership_error = client.delete(f"/api/posts/{post_id}", headers=other_headers)
        assert ownership_error.status_code == 403
        recreated = client.post("/api/posts", headers=writer_headers, json={"title": "Historical note", "content": "Preserve my author."})
        assert recreated.status_code == 201
        deactivated = client.patch(f"/api/users/{writer_id}/deactivate", headers=admin_headers)
        assert deactivated.status_code == 200
        inactive_access = client.get("/api/posts", headers=writer_headers)
        assert inactive_access.status_code == 401
        deleted = client.delete(f"/api/users/{writer_id}", headers=admin_headers)
        assert deleted.status_code == 204
        retained = client.get(f"/api/posts/{recreated.json()['id']}", headers=admin_headers)
        assert retained.status_code == 200 and retained.json()["author"] == {"id": None, "display_name": "Flow Writer", "role": "user"}

"""Cross-router file-backed SQLite lifecycle persistence coverage."""
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.config import Settings
from app.main import create_app
from app.models import Post, User


def test_account_deletion_nulls_actual_sqlite_fk_and_retains_snapshots(tmp_path: Path) -> None:
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'flow.db'}", JWT_SECRET="integration-secret", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver")
    with TestClient(create_app(settings)) as client:
        registered = client.post("/api/auth/register", json={"display_name": "Flow Writer", "username": "flowwriter", "password": "password8", "confirm_password": "password8"})
        assert registered.status_code == 201
        writer_id = registered.json()["user"]["id"]
        writer_headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
        created = client.post("/api/posts", headers=writer_headers, json={"title": "Historical", "content": "Keep literal attribution."})
        assert created.status_code == 201
        post_id = created.json()["id"]
        admin_login = client.post("/api/auth/login", json={"username": "admin", "password": "admin"})
        admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
        deleted = client.delete(f"/api/users/{writer_id}", headers=admin_headers)
        assert deleted.status_code == 204
        with client.app.state.session_factory() as session:
            assert session.get(User, writer_id) is None
            post = session.scalar(select(Post).where(Post.id == post_id))
            assert post is not None
            assert post.author_id is None
            assert post.author_name == "Flow Writer" and post.author_role == "user"
            assert post.content == "Keep literal attribution."
        retained = client.get(f"/api/posts/{post_id}", headers=admin_headers)
    assert retained.status_code == 200
    assert retained.json()["author"] == {"id": None, "display_name": "Flow Writer", "role": "user"}

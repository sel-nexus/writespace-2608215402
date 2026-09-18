"""File-backed SQLite post mutation security and hostile-input tests."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'posts.db'}", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver", JWT_SECRET="posts-secret")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def admin_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": f"Bearer {client.post('/api/auth/login', json={'username': 'admin', 'password': 'admin'}).json()['access_token']}"}


@pytest.mark.parametrize("method,path,payload", [
    ("post", "/api/posts", {"title": "x", "content": "y"}),
    ("put", "/api/posts/00000000-0000-0000-0000-000000000000", {"title": "x", "content": "y"}),
    ("delete", "/api/posts/00000000-0000-0000-0000-000000000000", None),
])
def test_post_mutations_reject_missing_and_malformed_tokens_safely(client: TestClient, method: str, path: str, payload: dict[str, str] | None) -> None:
    for headers in ({}, {"Authorization": "Bearer malformed"}):
        response = client.request(method.upper(), path, headers=headers, json=payload)
        assert response.status_code == 401
        assert "traceback" not in response.text.lower()


def test_post_write_rejects_missing_or_wrong_types_and_safely_persists_hostile_plain_text(client: TestClient) -> None:
    headers = admin_headers(client)
    for payload in ({"title": "missing content"}, {"title": ["wrong"], "content": "text"}, {"title": "ok", "content": {"wrong": "type"}}):
        assert client.post("/api/posts", headers=headers, json=payload).status_code == 422
    title = "<script>alert('title')</script>"
    content = "<img src=x onerror=alert(1)>\nPlain text remains literal."
    created = client.post("/api/posts", headers=headers, json={"title": title, "content": content})
    assert created.status_code == 201
    assert created.json()["title"] == title and created.json()["content"] == content
    fetched = client.get(f"/api/posts/{created.json()['id']}", headers=headers)
    assert fetched.status_code == 200 and fetched.json()["content"] == content
    assert all(response.status_code < 500 for response in (created, fetched))

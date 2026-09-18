"""File-backed SQLite administrator input and mutation authorization tests."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import create_app


@pytest.fixture
def client(tmp_path: Path):
    settings = Settings(DATABASE_URL=f"sqlite:///{tmp_path / 'admin.db'}", SEED_ON_STARTUP=True, CORS_ORIGINS="http://testserver", JWT_SECRET="admin-secret")
    with TestClient(create_app(settings)) as test_client:
        yield test_client


def admin_headers(client: TestClient) -> dict[str, str]:
    token = client.post("/api/auth/login", json={"username": "admin", "password": "admin"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.parametrize("method,path,payload", [
    ("post", "/api/users", {"display_name": "User", "username": "created", "password": "password8", "role": "user"}),
    ("patch", "/api/users/00000000-0000-0000-0000-000000000000/deactivate", None),
    ("delete", "/api/users/00000000-0000-0000-0000-000000000000", None),
])
def test_user_mutations_reject_missing_and_malformed_tokens_safely(client: TestClient, method: str, path: str, payload: dict[str, str] | None) -> None:
    for headers in ({}, {"Authorization": "Bearer malformed"}):
        response = client.request(method.upper(), path, headers=headers, json=payload)
        assert response.status_code == 401
        assert "traceback" not in response.text.lower()


def test_admin_user_input_is_strict_and_creates_uuid_user(client: TestClient) -> None:
    headers = admin_headers(client)
    for payload in ({"username": "missing"}, {"display_name": "User", "username": "created", "password": "password8", "role": 4}, {"display_name": "User", "username": "created", "password": "password8", "role": "user", "is_active": True}):
        assert client.post("/api/users", headers=headers, json=payload).status_code == 422
    created = client.post("/api/users", headers=headers, json={"display_name": "User", "username": "created", "password": "password8", "role": "user"})
    assert created.status_code == 201 and len(created.json()["id"]) == 36
    assert client.patch(f"/api/users/{created.json()['id']}/deactivate", headers=headers).status_code == 200

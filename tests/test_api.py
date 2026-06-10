from types import SimpleNamespace

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.app import app
from src.context import worker_env


class EnvClient:
    def __init__(self):
        self.env = SimpleNamespace(
            ADMIN_TOKEN="secret",
            ALLOWED_ORIGINS="https://frontend.pages.dev,http://localhost:3000",
            DB=None,
        )

    def __enter__(self):
        self.token = worker_env.set(self.env)
        self.client = TestClient(app)
        return self.client

    def __exit__(self, *_args):
        worker_env.reset(self.token)


def test_health_is_public():
    with EnvClient() as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["code"] == "ok"


def test_api_rejects_invalid_token_with_cors_headers():
    with EnvClient() as client:
        response = client.get(
            "/api/bookmarks",
            headers={
                "Authorization": "Bearer wrong",
                "Origin": "https://frontend.pages.dev",
            },
        )

    assert response.status_code == 401
    assert response.json()["code"] == "auth_invalid"
    assert (
        response.headers["access-control-allow-origin"]
        == "https://frontend.pages.dev"
    )


def test_preflight_rejects_unknown_origin():
    with EnvClient() as client:
        response = client.options(
            "/api/bookmarks", headers={"Origin": "https://untrusted.example"}
        )

    assert response.status_code == 403
    assert response.json()["code"] == "origin_not_allowed"

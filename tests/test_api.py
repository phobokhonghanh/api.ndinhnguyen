from types import SimpleNamespace

import pytest

pytest.importorskip("httpx")

from fastapi.testclient import TestClient

from src.app import app
from src.context import worker_env


class FakeR2Object:
    def __init__(self, content):
        self.content = content

    async def text(self):
        if isinstance(self.content, bytes):
            return self.content.decode("utf-8")
        return self.content


class FakeR2Bucket:
    def __init__(self, fail_put=False):
        self.fail_put = fail_put
        self.objects = {}

    async def get(self, key):
        if key not in self.objects:
            return None
        return FakeR2Object(self.objects[key])

    async def put(self, key, body):
        if self.fail_put:
            raise RuntimeError("storage failed")
        self.objects[key] = body


class EnvClient:
    def __init__(self, bucket=None):
        self.bucket = bucket or FakeR2Bucket()
        self.env = SimpleNamespace(
            ADMIN_TOKEN="secret",
            ALLOWED_ORIGINS="https://frontend.pages.dev,http://localhost:3000",
            DB=None,
            STATS_BUCKET=self.bucket,
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


def test_stats_snapshot_is_public_without_token():
    bucket = FakeR2Bucket()
    with EnvClient(bucket) as client:
        response = client.post(
            "/api/stats",
            params={
                "product": "autohdr",
                "machine_id": "machine-1",
                "snapshot": "true",
                "user": "nguyen",
                "snapshot_event_id": "event-1",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "snapshot": True, "runtime": False}
    assert len(bucket.objects) == 1


def test_stats_runtime_upload_writes_object():
    bucket = FakeR2Bucket()
    with EnvClient(bucket) as client:
        response = client.post(
            "/api/stats",
            params={
                "product": "autohdr",
                "machine_id": "machine-1",
                "runtime": "true",
                "batch_id": "batch-1",
            },
            files={"file": ("runtime.jsonl", b'{"id":"runtime-1"}\n')},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "snapshot": False, "runtime": True}
    key = next(iter(bucket.objects))
    assert key.endswith("/machine-1_batch-1.jsonl")
    assert bucket.objects[key] == b'{"id":"runtime-1"}\n'


def test_stats_combined_request_stores_snapshot_and_runtime():
    bucket = FakeR2Bucket()
    with EnvClient(bucket) as client:
        response = client.post(
            "/api/stats",
            params={
                "product": "autohdr",
                "machine_id": "machine-1",
                "snapshot": "true",
                "runtime": "true",
                "user": "nguyen",
                "snapshot_event_id": "event-1",
                "batch_id": "batch-1",
            },
            files={"file": ("runtime.jsonl", b'{"id":"runtime-1"}\n')},
        )

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "snapshot": True, "runtime": True}
    assert len(bucket.objects) == 2


@pytest.mark.parametrize(
    ("params", "files", "code"),
    [
        (
            {
                "product": "autohdr",
                "machine_id": "machine-1",
                "runtime": "true",
                "batch_id": "batch-1",
            },
            None,
            "stats_file_required",
        ),
        (
            {
                "product": "autohdr",
                "machine_id": "machine-1",
                "runtime": "true",
                "batch_id": "bad/id",
            },
            {"file": ("runtime.jsonl", b'{"id":"runtime-1"}\n')},
            "stats_batch_id_invalid",
        ),
        (
            {
                "product": "unknown",
                "machine_id": "machine-1",
                "snapshot": "true",
                "user": "nguyen",
                "snapshot_event_id": "event-1",
            },
            None,
            "stats_product_invalid",
        ),
        (
            {
                "product": "autohdr",
                "machine_id": "bad/id",
                "snapshot": "true",
                "user": "nguyen",
                "snapshot_event_id": "event-1",
            },
            None,
            "stats_machine_id_invalid",
        ),
        (
            {
                "product": "autohdr",
                "machine_id": "machine-1",
            },
            None,
            "stats_no_operation",
        ),
    ],
)
def test_stats_validation_errors_return_400(params, files, code):
    with EnvClient() as client:
        response = client.post("/api/stats", params=params, files=files)

    assert response.status_code == 400
    assert response.json() == {"ok": False, "code": code}


@pytest.mark.parametrize(
    ("content", "code"),
    [
        (b"x" * (256 * 1024 + 1), "stats_file_too_large"),
        (b"\xff", "stats_file_invalid_utf8"),
        (("\n" * 10_000 + "x").encode(), "stats_file_too_many_lines"),
    ],
)
def test_stats_runtime_file_validation_errors_return_400(content, code):
    with EnvClient() as client:
        response = client.post(
            "/api/stats",
            params={
                "product": "autohdr",
                "machine_id": "machine-1",
                "runtime": "true",
                "batch_id": "batch-1",
            },
            files={"file": ("runtime.jsonl", content)},
        )

    assert response.status_code == 400
    assert response.json() == {"ok": False, "code": code}


def test_stats_storage_exception_returns_500():
    with EnvClient(FakeR2Bucket(fail_put=True)) as client:
        response = client.post(
            "/api/stats",
            params={
                "product": "autohdr",
                "machine_id": "machine-1",
                "snapshot": "true",
                "user": "nguyen",
                "snapshot_event_id": "event-1",
            },
        )

    assert response.status_code == 500
    assert response.json() == {"ok": False, "code": "stats_storage_error"}

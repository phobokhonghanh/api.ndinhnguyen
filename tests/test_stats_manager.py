import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from src.features.stats import constants
from src.features.stats.errors import StatsStorageError, StatsValidationError
from src.features.stats.path_builder import PathTemplateBuilder
from src.features.stats.service import handle_stats


class FakeUpload:
    def __init__(self, content: bytes):
        self.content = content

    async def read(self):
        return self.content


class FakeR2Object:
    def __init__(self, content: bytes | str):
        self.content = content

    async def text(self):
        if isinstance(self.content, bytes):
            return self.content.decode("utf-8")
        return self.content


class FakeR2Bucket:
    def __init__(self):
        self.objects = {}

    async def get(self, key):
        if key not in self.objects:
            return None
        return FakeR2Object(self.objects[key])

    async def put(self, key, body):
        self.objects[key] = body


def env(bucket=None, **overrides):
    return SimpleNamespace(STATS_BUCKET=bucket or FakeR2Bucket(), **overrides)


def run(coro):
    return asyncio.run(coro)


def test_default_templates_build_expected_keys():
    values = {
        "product": "autohdr",
        "yyyymmdd": "20260616",
        "machine_id": "machine-1",
        "batch_id": "batch-1",
    }

    assert (
        PathTemplateBuilder().build(
            constants.DEFAULT_SNAPSHOT_PATH_TEMPLATE,
            {"product", "yyyymmdd", "machine_id"},
            values,
        )
        == "lakehouse-raw/autohdr/snapshot/loaddate=20260616/machine-1.csv"
    )
    assert (
        PathTemplateBuilder().build(
            constants.DEFAULT_RUNTIME_PATH_TEMPLATE,
            {"product", "yyyymmdd", "machine_id", "batch_id"},
            values,
        )
        == "lakehouse-raw/autohdr/runtime/loaddate=20260616/machine-1_batch-1.jsonl"
    )


def test_custom_template_builds_expected_key():
    path = PathTemplateBuilder().build(
        "custom/{product}/{yyyymmdd}/{machine_id}/{batch_id}.jsonl",
        {"product", "yyyymmdd", "machine_id", "batch_id"},
        {
            "product": "autohdr",
            "yyyymmdd": "20260616",
            "machine_id": "machine-1",
            "batch_id": "batch-1",
        },
    )

    assert path == "custom/autohdr/20260616/machine-1/batch-1.jsonl"


def test_template_rejects_unknown_placeholder():
    try:
        PathTemplateBuilder().build(
            "{product}/{unknown}",
            {"product"},
            {"product": "autohdr", "unknown": "value"},
        )
    except StatsStorageError:
        return

    raise AssertionError("expected StatsStorageError")


def test_snapshot_creates_appends_and_skips_duplicate_event():
    bucket = FakeR2Bucket()
    now = datetime(2026, 6, 16, 1, 2, 3, tzinfo=UTC)
    key = "lakehouse-raw/autohdr/snapshot/loaddate=20260616/machine-1.csv"

    run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=True,
            runtime=False,
            user="nguyen",
            snapshot_event_id="event-1",
            batch_id=None,
            file=None,
            now=now,
        )
    )
    run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=True,
            runtime=False,
            user="nguyen",
            snapshot_event_id="event-2",
            batch_id=None,
            file=None,
            now=now,
        )
    )
    before_duplicate = bucket.objects[key]
    run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=True,
            runtime=False,
            user="nguyen",
            snapshot_event_id="event-2",
            batch_id=None,
            file=None,
            now=now,
        )
    )

    assert bucket.objects[key] == before_duplicate
    assert bucket.objects[key].splitlines() == [
        "snapshot_event_id,user,machine_id,created_at_utc",
        "event-1,nguyen,machine-1,2026-06-16T01:02:03Z",
        "event-2,nguyen,machine-1,2026-06-16T01:02:03Z",
    ]


def test_runtime_writes_jsonl_and_overwrites_same_batch_id():
    bucket = FakeR2Bucket()
    now = datetime(2026, 6, 16, tzinfo=UTC)
    key = "lakehouse-raw/autohdr/runtime/loaddate=20260616/machine-1_batch-1.jsonl"

    run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=False,
            runtime=True,
            user=None,
            snapshot_event_id=None,
            batch_id="batch-1",
            file=FakeUpload(b'{"id":"runtime-1"}\n'),
            now=now,
        )
    )
    run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=False,
            runtime=True,
            user=None,
            snapshot_event_id=None,
            batch_id="batch-1",
            file=FakeUpload(b'{"id":"runtime-2"}\n'),
            now=now,
        )
    )

    assert bucket.objects[key] == b'{"id":"runtime-2"}\n'


def test_combined_snapshot_and_runtime_request_stores_both():
    bucket = FakeR2Bucket()
    now = datetime(2026, 6, 16, tzinfo=UTC)

    result = run(
        handle_stats(
            env(bucket),
            product="autohdr",
            machine_id="machine-1",
            snapshot=True,
            runtime=True,
            user="nguyen",
            snapshot_event_id="event-1",
            batch_id="batch-1",
            file=FakeUpload(b'{"id":"runtime-1"}\n'),
            now=now,
        )
    )

    assert result == {"status": "ok", "snapshot": True, "runtime": True}
    assert set(bucket.objects) == {
        "lakehouse-raw/autohdr/snapshot/loaddate=20260616/machine-1.csv",
        "lakehouse-raw/autohdr/runtime/loaddate=20260616/machine-1_batch-1.jsonl",
    }


def test_runtime_rejects_invalid_uploads_and_ids():
    cases = [
        {"file": None, "batch_id": "batch-1", "code": "stats_file_required"},
        {
            "file": FakeUpload(b"x" * (constants.MAX_RUNTIME_FILE_SIZE + 1)),
            "batch_id": "batch-1",
            "code": "stats_file_too_large",
        },
        {
            "file": FakeUpload(b"\xff"),
            "batch_id": "batch-1",
            "code": "stats_file_invalid_utf8",
        },
        {
            "file": FakeUpload(("\n" * constants.MAX_RUNTIME_LINES + "x").encode()),
            "batch_id": "batch-1",
            "code": "stats_file_too_many_lines",
        },
        {
            "file": FakeUpload(b'{"id":"runtime-1"}\n'),
            "batch_id": "bad/id",
            "code": "stats_batch_id_invalid",
        },
    ]

    for case in cases:
        try:
            run(
                handle_stats(
                    env(),
                    product="autohdr",
                    machine_id="machine-1",
                    snapshot=False,
                    runtime=True,
                    user=None,
                    snapshot_event_id=None,
                    batch_id=case["batch_id"],
                    file=case["file"],
                    now=datetime(2026, 6, 16, tzinfo=UTC),
                )
            )
        except StatsValidationError as exc:
            assert exc.code == case["code"]
        else:
            raise AssertionError(f"expected {case['code']}")


def test_invalid_product_and_machine_id_return_validation_codes():
    invalid_product = {
        "product": "unknown",
        "machine_id": "machine-1",
        "code": "stats_product_invalid",
    }
    invalid_machine = {
        "product": "autohdr",
        "machine_id": "bad/id",
        "code": "stats_machine_id_invalid",
    }

    for case in [invalid_product, invalid_machine]:
        try:
            run(
                handle_stats(
                    env(),
                    product=case["product"],
                    machine_id=case["machine_id"],
                    snapshot=True,
                    runtime=False,
                    user="nguyen",
                    snapshot_event_id="event-1",
                    batch_id=None,
                    file=None,
                    now=datetime(2026, 6, 16, tzinfo=UTC),
                )
            )
        except StatsValidationError as exc:
            assert exc.code == case["code"]
        else:
            raise AssertionError(f"expected {case['code']}")

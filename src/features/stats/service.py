import asyncio
from typing import Any

from core.settings import env_value
from infra.object_store import R2ObjectStore
from features.stats.constants import DEFAULT_RUNTIME_PATH_TEMPLATE, DEFAULT_SNAPSHOT_PATH_TEMPLATE
from features.stats.errors import StatsStorageError, StatsValidationError
from features.stats.path_builder import PathTemplateBuilder
from features.stats.runtime import RuntimeHandler
from features.stats.schemas import StatsCommand
from features.stats.snapshot import SnapshotHandler
from features.stats.validators import validate_product, validate_safe_id


class StatsService:
    def __init__(
        self,
        *,
        path_builder: PathTemplateBuilder | None = None,
        snapshot_handler: SnapshotHandler | None = None,
        runtime_handler: RuntimeHandler | None = None,
    ):
        self.path_builder = path_builder or PathTemplateBuilder()
        self.snapshot_handler = snapshot_handler or SnapshotHandler()
        self.runtime_handler = runtime_handler or RuntimeHandler()

    async def handle(self, env: Any, command: StatsCommand) -> dict[str, bool | str]:
        if not command.snapshot and not command.runtime:
            raise StatsValidationError("stats_no_operation")

        product = validate_product(command.product)
        machine_id = validate_safe_id(command.machine_id, "stats_machine_id_invalid")
        current_time = command.current_time
        yyyymmdd = current_time.strftime("%Y%m%d")
        bucket = getattr(env, "STATS_BUCKET", None)
        if bucket is None:
            raise StatsStorageError
        store = R2ObjectStore(bucket)

        tasks = []
        try:
            if command.snapshot:
                tasks.append(
                    self._handle_snapshot(
                        env,
                        store,
                        product=product,
                        machine_id=machine_id,
                        yyyymmdd=yyyymmdd,
                        command=command,
                    )
                )

            if command.runtime:
                tasks.append(
                    self._handle_runtime(
                        env,
                        store,
                        product=product,
                        machine_id=machine_id,
                        yyyymmdd=yyyymmdd,
                        command=command,
                    )
                )

            if tasks:
                await asyncio.gather(*tasks)
        except StatsValidationError:
            raise
        except Exception as exc:
            raise StatsStorageError from exc

        return {"status": "ok", "snapshot": command.snapshot, "runtime": command.runtime}

    async def _handle_snapshot(
        self,
        env: Any,
        store: R2ObjectStore,
        *,
        product: str,
        machine_id: str,
        yyyymmdd: str,
        command: StatsCommand,
    ) -> None:
        if not command.user or not command.user.strip():
            raise StatsValidationError("stats_user_required")
        if not command.snapshot_event_id:
            raise StatsValidationError("stats_snapshot_event_id_required")
        snapshot_event_id = validate_safe_id(
            command.snapshot_event_id, "stats_snapshot_event_id_invalid"
        )
        snapshot_template = env_value(
            env,
            "STATS_SNAPSHOT_PATH_TEMPLATE",
            DEFAULT_SNAPSHOT_PATH_TEMPLATE,
        )
        snapshot_key = self.path_builder.build(
            snapshot_template,
            {"product", "yyyymmdd", "machine_id"},
            {
                "product": product,
                "yyyymmdd": yyyymmdd,
                "machine_id": machine_id,
            },
        )
        await self.snapshot_handler.write_once(
            store,
            snapshot_key,
            snapshot_event_id=snapshot_event_id,
            user=command.user.strip(),
            machine_id=machine_id,
            now=command.current_time,
        )

    async def _handle_runtime(
        self,
        env: Any,
        store: R2ObjectStore,
        *,
        product: str,
        machine_id: str,
        yyyymmdd: str,
        command: StatsCommand,
    ) -> None:
        if not command.batch_id:
            raise StatsValidationError("stats_batch_id_required")
        batch_id = validate_safe_id(command.batch_id, "stats_batch_id_invalid")
        if command.file is None:
            raise StatsValidationError("stats_file_required")
        runtime_template = env_value(
            env,
            "STATS_RUNTIME_PATH_TEMPLATE",
            DEFAULT_RUNTIME_PATH_TEMPLATE,
        )
        runtime_key = self.path_builder.build(
            runtime_template,
            {"product", "yyyymmdd", "machine_id", "batch_id"},
            {
                "product": product,
                "yyyymmdd": yyyymmdd,
                "machine_id": machine_id,
                "batch_id": batch_id,
            },
        )
        await self.runtime_handler.write(store, runtime_key, command.file, machine_id)


async def handle_stats(
    env: Any,
    *,
    product: str,
    machine_id: str,
    snapshot: bool,
    runtime: bool,
    user: str | None,
    snapshot_event_id: str | None,
    batch_id: str | None,
    file: Any | None,
    now=None,
) -> dict[str, bool | str]:
    command = StatsCommand(
        product=product,
        machine_id=machine_id,
        snapshot=snapshot,
        runtime=runtime,
        user=user,
        snapshot_event_id=snapshot_event_id,
        batch_id=batch_id,
        file=file,
        now=now,
    )
    return await StatsService().handle(env, command)

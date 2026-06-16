from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from ...core.context import worker_env
from ...core.responses import json_response, response
from ...features.stats.errors import StatsStorageError, StatsValidationError
from ...features.stats.schemas import StatsCommand
from ...features.stats.service import StatsService


router = APIRouter()


@router.post("/api/stats")
async def create_stats(
    product: str,
    machine_id: str,
    snapshot: bool = False,
    runtime: bool = False,
    user: str | None = None,
    snapshot_event_id: str | None = None,
    batch_id: str | None = None,
    file: UploadFile | None = File(None),
) -> JSONResponse:
    command = StatsCommand(
        product=product,
        machine_id=machine_id,
        snapshot=snapshot,
        runtime=runtime,
        user=user,
        snapshot_event_id=snapshot_event_id,
        batch_id=batch_id,
        file=file,
    )
    try:
        result = await StatsService().handle(worker_env.get(None), command)
        return json_response(result)
    except StatsValidationError as exc:
        return json_response(response(False, exc.code), 400)
    except StatsStorageError:
        return json_response(response(False, "stats_storage_error"), 500)

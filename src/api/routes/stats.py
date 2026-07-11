from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from api.helpers import get_env
from core.responses import json_response, Response
from features.stats.errors import StatsStorageError, StatsValidationError
from features.stats.schemas import StatsCommand, StatsResponse
from features.stats.service import StatsService


router = APIRouter()


@router.post("/api/stats", response_model=StatsResponse)
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
    """
    Handles stats collection upload (snapshots and/or runtime logs) for various product versions and machines.
    """

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
        result = await StatsService().handle(get_env(), command)
        return json_response(StatsResponse(**result))
    except StatsValidationError as exc:
        return json_response(ok=False, code=exc.code, status_code=400)
    except StatsStorageError as e:
        print(f"Stats storage error: {e}")
        return json_response(ok=False, code="stats_storage_error", status_code=500)


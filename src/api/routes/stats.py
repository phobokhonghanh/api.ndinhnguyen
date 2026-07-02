from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, response
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
        result = await StatsService().handle(worker_env.get(None), command)
        return json_response(result)
    except StatsValidationError as exc:
        return json_response(response(False, exc.code), 400)
    except StatsStorageError as e:
        print(f"Stats storage error: {e}")
        return json_response(response(False, "stats_storage_error"), 500)
    except Exception as e:
        print(f"Exception in stats operation: {e}")
        return json_response(response(False, "unknown_error"), 500)

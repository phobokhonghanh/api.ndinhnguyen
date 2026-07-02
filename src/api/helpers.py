from typing import Any
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, response


def get_db() -> Any:
    """
    Retrieves the D1 database connection from the current worker environment.
    """
    env = worker_env.get(None)
    return getattr(env, "DB", None)


def get_model_data(model: Any, by_alias: bool = False) -> dict[str, Any]:
    """
    Safely serializes a Pydantic model to dictionary across Pydantic v1 & v2.
    """
    if hasattr(model, "model_dump"):
        return model.model_dump(by_alias=by_alias)
    return model.dict(by_alias=by_alias)


async def run_db_operation(
    operation: Any, operation_name: str = "database"
) -> JSONResponse:
    """
    Runs a database operation with standard error handling and response formatting.
    """
    db = get_db()
    if db is None:
        return json_response(response(False, "db_unavailable"), 503)
    try:
        result = await operation(db)
        return json_response(result, 200 if result["ok"] else 400)
    except Exception as e:
        print(f"Exception in {operation_name} operation: {e}")
        return json_response(response(False, "unknown_error"), 500)

from functools import wraps
from typing import Any
from fastapi import HTTPException
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, Response
from core.settings import AppSettings


def require_value(detail: str, status_code: int = 500):
    """
    Decorator that raises an HTTPException if the decorated function returns a falsy value.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            val = func(*args, **kwargs)
            try:
                is_falsy = not val
            except TypeError:
                is_falsy = False
            if is_falsy:
                raise HTTPException(status_code=status_code, detail=detail)
            return val
        return wrapper
    return decorator


def get_env() -> Any:
    """
    Retrieves the current worker environment context.
    """
    return worker_env.get(None)


def get_settings() -> AppSettings:
    """
    Retrieves AppSettings parsed from the current worker environment.
    """
    return AppSettings.from_env(get_env())


@require_value(detail="db_unavailable", status_code=503)
def get_db() -> Any:
    """
    Retrieves the D1 database connection from the current worker environment.
    """
    return getattr(get_env(), "DB", None)


@require_value(detail="shopee_cookie_not_found", status_code=500)
def get_shopee_cookie() -> str:
    """
    Retrieves the Shopee cookie from settings, raising an HTTPException if not set.
    """
    return get_settings().shopee_cookie


@require_value(detail="commission_rate_not_found", status_code=500)
def get_commission_rate() -> float:
    """
    Retrieves the commission rate from settings, raising an HTTPException if not set.
    """
    return get_settings().commission_rate


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
    result = await operation(db)
    if isinstance(result, dict):
        result_obj = Response(
            ok=result.get("ok", True),
            code=result.get("code", "ok"),
            data=result.get("data"),
            pagination=result.get("pagination")
        )
        return json_response(result_obj, 200 if result_obj.ok else 400)
    return json_response(result, 200 if result.ok else 400)

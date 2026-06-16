from typing import Any

from fastapi.responses import JSONResponse


def response(ok: bool, code: str, data: Any | None = None) -> dict[str, Any]:
    result: dict[str, Any] = {"ok": ok, "code": code}
    if data is not None:
        result["data"] = data
    return result


def json_response(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(payload, status_code=status_code)

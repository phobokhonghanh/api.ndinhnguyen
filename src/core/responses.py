from typing import Generic, TypeVar

from fastapi.responses import JSONResponse
from pydantic import BaseModel

T = TypeVar("T")


class Pagination(BaseModel):
    total: int
    page: int
    pageSize: int
    totalPages: int


class Response(BaseModel, Generic[T]):
    ok: bool
    code: str
    data: T | None = None
    pagination: Pagination | None = None


def json_response(
    payload: BaseModel | None = None,
    status_code: int = 200,
    *,
    ok: bool = True,
    code: str = "ok",
    data: object = None,
    pagination: Pagination | None = None,
) -> JSONResponse:
    if payload is None:
        payload = Response(ok=ok, code=code, data=data, pagination=pagination)
    return JSONResponse(payload.model_dump(by_alias=True, exclude_none=True), status_code=status_code)
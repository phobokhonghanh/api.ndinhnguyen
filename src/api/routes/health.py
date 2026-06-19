from typing import Any

from fastapi import APIRouter, Response
from pydantic import BaseModel

from core.responses import response


class HealthData(BaseModel):
    service: str


class HealthResponse(BaseModel):
    ok: bool
    code: str
    data: HealthData


router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health() -> dict[str, Any]:
    return response(True, "ok", {"service": "api.ndinhnguyen"})


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)

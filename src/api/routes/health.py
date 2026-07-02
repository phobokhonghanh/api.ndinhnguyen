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
    """
    Returns the health status of the service.
    """
    return response(True, "ok", {"service": "api.ndinhnguyen"})


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    """
    Handles favicon requests by returning a 204 No Content response.
    """
    return Response(status_code=204)


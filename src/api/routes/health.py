from fastapi import APIRouter
import fastapi
from pydantic import BaseModel

from core.responses import Response


class HealthData(BaseModel):
    service: str


router = APIRouter()


@router.get("/health", response_model=Response[HealthData])
async def health() -> Response[HealthData]:
    """
    Returns the health status of the service.
    """
    return Response(ok=True, code="ok", data=HealthData(service="api.ndinhnguyen"))


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> fastapi.Response:
    """
    Handles favicon requests by returning a 204 No Content response.
    """
    return fastapi.Response(status_code=204)


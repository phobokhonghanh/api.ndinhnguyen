from typing import Any

from fastapi import APIRouter, Response

from core.responses import response


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    return response(True, "ok", {"service": "api.ndinhnguyen"})


@router.get("/favicon.ico", include_in_schema=False)
async def favicon() -> Response:
    return Response(status_code=204)

from typing import Any

from fastapi import APIRouter

from core.responses import response


router = APIRouter()


@router.get("/health")
async def health() -> dict[str, Any]:
    return response(True, "ok", {"service": "api-ndinhnguyen"})

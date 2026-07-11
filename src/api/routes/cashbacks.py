from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from api.helpers import get_db
from core.responses import Response, json_response
from features.cashbacks import service
from features.cashbacks.schemas import CashbackRecord

router = APIRouter()


@router.get("/api/cashbacks", response_model=Response[list[CashbackRecord]])
async def get_cashbacks(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """
    Retrieves the logged-in user's cashback history.
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    user_id = user.get("sub")
    db = get_db()
    records, pagination = await service.get_cashbacks(db, page=page, page_size=pageSize, user_id=user_id)
    return json_response(data=records, pagination=pagination)


@router.get("/api/admin/cashbacks", response_model=Response[list[CashbackRecord]])
async def get_admin_cashbacks(
    request: Request,
    page: int = Query(1, ge=1),
    pageSize: int = Query(20, ge=1, le=100),
    userId: str | None = Query(None),
) -> JSONResponse:
    """
    Retrieves all cashback records or filtered by userId (Admin only).
    """
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    records, pagination = await service.get_cashbacks(db, page=page, page_size=pageSize, user_id=userId)
    return json_response(data=records, pagination=pagination)

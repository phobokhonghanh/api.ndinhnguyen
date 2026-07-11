from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.helpers import get_db, get_settings
from core.responses import Response, json_response
from features.users import service as user_service
from features.users.schemas import GoogleLoginRequest, LoginResponseData

router = APIRouter()


@router.post("/api/auth/google/login", response_model=Response[LoginResponseData])
async def google_login(payload: GoogleLoginRequest) -> JSONResponse:
    """
    Handles Google OAuth login by validating the ID token, saving/updating the user in the database,
    and issuing a session JWT.
    """
    db = get_db()
    settings = get_settings()
    
    if not settings.jwt_secret or not settings.google_client_id:
        return json_response(ok=False, code="authentication unavailable", status_code=500)

    result = await user_service.google_login(db, settings, payload.id_token)
    if result.ok:
        return json_response(data=result.data)
    return json_response(ok=False, code=result.code, status_code=400)


@router.post("/api/auth/google/logout")
async def google_logout() -> JSONResponse:
    """
    Handles Google OAuth logout by clearing client-side session.
    """
    return json_response()


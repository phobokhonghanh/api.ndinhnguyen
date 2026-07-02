from fastapi import APIRouter, Response

from core.context import worker_env
from core.responses import json_response, response
from core.settings import AppSettings
from features.users import service as user_service
from features.users.schemas import GoogleLoginRequest, LoginResponse

router = APIRouter()


@router.post("/api/auth/google/login", response_model=LoginResponse)
async def google_login(payload: GoogleLoginRequest) -> Response:

    """
    Handles Google OAuth login by validating the ID token, saving/updating the user in the database,
    and issuing a session JWT.
    """
    env = worker_env.get(None)
    db = getattr(env, "DB", None)
    if db is None:
        return json_response(response(False, "db_unavailable"), 503)

    settings = AppSettings.from_env(env)
    if not settings.jwt_secret or not settings.google_client_id:
        return json_response(response(False, "auth_missing_config"), 500)

    result = await user_service.google_login(db, settings, payload.id_token)
    return json_response(result, 200 if result["ok"] else 400)


@router.post("/api/auth/google/logout")
async def google_logout() -> Response:
    """
    Handles Google OAuth logout by clearing client-side session.
    """
    return json_response(response(True, "ok"))


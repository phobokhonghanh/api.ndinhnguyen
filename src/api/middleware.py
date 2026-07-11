import hmac
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from api.helpers import get_settings
from core.responses import json_response, Response


PUBLIC_API_PATHS = {
    "/api/stats",
    "/api/shopee/affiliate",
    "/api/shopee/conversions",
    "/api/auth/google/login",
    "/api/auth/google/logout",
    "/api/cashbacks",
}


async def security_middleware(request: Request, call_next: Any) -> JSONResponse:
    settings = get_settings()
    origin = request.headers.get("origin")
    path = request.url.path
    if origin and settings.environment != "development" and origin not in settings.allowed_origins:
        return json_response(Response(ok=False, code="origin_not_allowed"), 403)
    if settings.environment == "production" and (
        path in {"/openapi.json", "/redoc", "/docs"} or path.startswith("/docs/")
    ):
        return json_response(Response(ok=False, code="not_found"), 404)

    # 1. Extract and verify user context
    authorization = request.headers.get("authorization", "")
    supplied = authorization.removeprefix("Bearer ").strip()

    user_context = None
    if supplied:
        if settings.admin_token and hmac.compare_digest(supplied, settings.admin_token):
            user_context = {"role": "admin", "sub": "admin"}
        elif settings.jwt_secret:
            from core.auth import verify_jwt

            payload = verify_jwt(supplied, settings.jwt_secret)
            if payload:
                user_context = payload

    request.state.user = user_context

    # 2. CORS or method checks
    if request.method == "OPTIONS":
        api_response = json_response(Response(ok=True, code="ok"))
    elif (
        request.url.path.startswith("/api/")
        and request.url.path not in PUBLIC_API_PATHS
    ):
        if not request.state.user:
            api_response = json_response(Response(ok=False, code="auth_invalid"), 401)
        elif request.state.user.get("role") != "admin":
            api_response = json_response(Response(ok=False, code="auth_forbidden"), 403)
        else:
            api_response = await call_next(request)
    else:
        api_response = await call_next(request)


    if origin and (settings.environment == "development" or origin in settings.allowed_origins):
        api_response.headers["Access-Control-Allow-Origin"] = origin
        api_response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        api_response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        api_response.headers["Access-Control-Max-Age"] = "86400"
        api_response.headers["Vary"] = "Origin"
    return api_response

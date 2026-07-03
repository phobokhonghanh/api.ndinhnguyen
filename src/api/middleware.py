import hmac
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, response
from core.settings import AppSettings


PUBLIC_API_PATHS = {
    "/api/stats",
    "/api/shopee/affiliate",
    "/api/shopee/conversions",
    "/api/auth/google/login",
    "/api/auth/google/logout",
}


async def security_middleware(request: Request, call_next: Any) -> JSONResponse:
    env = worker_env.get(None)
    settings = AppSettings.from_env(env)
    origin = request.headers.get("origin")

    if origin and origin not in settings.allowed_origins:
        return json_response(response(False, "origin_not_allowed"), 403)

    path = request.url.path
    if settings.environment == "production" and (
        path in {"/openapi.json", "/redoc", "/docs"} or path.startswith("/docs/")
    ):
        return json_response(response(False, "not_found"), 404)

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
        api_response = json_response(response(True, "ok"))
    elif (
        request.url.path.startswith("/api/")
        and request.url.path not in PUBLIC_API_PATHS
    ):
        if not request.state.user:
            api_response = json_response(response(False, "auth_invalid"), 401)
        elif request.state.user.get("role") != "admin":
            api_response = json_response(response(False, "auth_forbidden"), 403)
        else:
            api_response = await call_next(request)
    else:
        api_response = await call_next(request)


    if origin and origin in settings.allowed_origins:
        api_response.headers["Access-Control-Allow-Origin"] = origin
        api_response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        api_response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        api_response.headers["Access-Control-Max-Age"] = "86400"
        api_response.headers["Vary"] = "Origin"
    return api_response

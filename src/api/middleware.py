import hmac
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse

from api.helpers import get_settings
from core.responses import json_response, Response


PUBLIC_API_PREFIXES = (
    "/api/stats",
    "/api/shopee/affiliate",
    "/api/shopee/conversions",
    "/api/auth/google/login",
    "/api/auth/google/logout",
    "/api/cashbacks",
    "/api/user/payment-info",
    "/api/user/dashboard",
    "/api/payments",
    "/api/banks",
)

PUBLIC_API_PATHS = set(PUBLIC_API_PREFIXES)



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
                user_context = dict(payload)
                if "sub" in user_context and isinstance(user_context["sub"], str):
                    user_context["sub"] = user_context["sub"].replace("-", "")

    request.state.user = user_context


    # 2. CORS or method checks
    if request.method == "OPTIONS":
        api_response = json_response(Response(ok=True, code="ok"))
    elif path.startswith("/api/admin/"):
        if not request.state.user:
            api_response = json_response(Response(ok=False, code="auth_invalid"), 401)
        elif request.state.user.get("role") != "admin":
            api_response = json_response(Response(ok=False, code="auth_forbidden"), 403)
        else:
            api_response = await call_next(request)
    elif path.startswith("/api/") and not any(path.startswith(prefix) for prefix in PUBLIC_API_PREFIXES):
        if not request.state.user:
            api_response = json_response(Response(ok=False, code="auth_invalid"), 401)
        elif request.state.user.get("role") != "admin":
            api_response = json_response(Response(ok=False, code="auth_forbidden"), 403)
        else:
            api_response = await call_next(request)
    else:
        api_response = await call_next(request)



    # 3. Telegram error notifications for sync endpoints != 200 and 500 status codes
    SHOPEE_SYNC_PATHS = {
        "/api/admin/shopee/conversions/sync",
        "/api/shopee/conversions",
        "/api/admin/shopee/conversions",
    }
    from infra.telegram import dispatch_telegram_error, telegram_error_notified

    if not getattr(request.state, "telegram_notified", False) and not telegram_error_notified.get():
        if path in SHOPEE_SYNC_PATHS and api_response.status_code != 200:
            request.state.telegram_notified = True
            body_content = getattr(api_response, "body", None)
            content_val: Any = body_content
            if isinstance(body_content, bytes):
                import json
                try:
                    content_val = json.loads(body_content.decode("utf-8"))
                except Exception:
                    content_val = body_content.decode("utf-8")
            await dispatch_telegram_error(
                feature="Shopee Sync",
                code=api_response.status_code,
                content=content_val,
                is_external=True,
            )
        elif api_response.status_code == 500:
            request.state.telegram_notified = True
            feature = "Product" if ("product" in path or "shopee" in path) else "System"
            body_content = getattr(api_response, "body", None)
            content_val = body_content
            if isinstance(body_content, bytes):
                import json
                try:
                    content_val = json.loads(body_content.decode("utf-8"))
                except Exception:
                    content_val = body_content.decode("utf-8")
            await dispatch_telegram_error(
                feature=feature,
                code=500,
                content=content_val,
                is_external=False,
            )

    if origin and (settings.environment == "development" or origin in settings.allowed_origins):
        api_response.headers["Access-Control-Allow-Origin"] = origin
        api_response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        api_response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS"
        api_response.headers["Access-Control-Max-Age"] = "86400"
        api_response.headers["Vary"] = "Origin"
    return api_response

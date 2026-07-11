import logging
from fastapi import FastAPI, HTTPException, Request
from core.responses import json_response, Response

from api.middleware import security_middleware
from api.routes import bookmarks, categories, health, stats, shopee, auth, cashbacks

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api")


def create_app() -> FastAPI:
    app = FastAPI(
        title="api.ndinhnguyen",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.middleware("http")(security_middleware)

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return json_response(ok=False, code=exc.detail, status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.error("Unhandled exception occurred", exc_info=exc)
        return json_response(ok=False, code="unknown_error", status_code=500)

    app.include_router(health.router)
    app.include_router(stats.router)
    app.include_router(bookmarks.router)
    app.include_router(categories.router)
    app.include_router(shopee.router)
    app.include_router(auth.router)
    app.include_router(cashbacks.router)

    from fastapi.openapi.utils import get_openapi
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version="1.0.0",
            routes=app.routes,
        )
        openapi_schema["components"] = openapi_schema.get("components", {})
        openapi_schema["components"]["securitySchemes"] = {
            "BearerAuth": {
                "type": "http",
                "scheme": "bearer",
                "bearerFormat": "JWT",
                "description": "Enter your static admin token or JWT user token."
            }
        }
        # Apply security globally (padlock icon will show next to endpoints)
        openapi_schema["security"] = [{"BearerAuth": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    return app

app = create_app()

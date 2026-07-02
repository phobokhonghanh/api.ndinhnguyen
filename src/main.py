from fastapi import FastAPI

from api.middleware import security_middleware
from api.routes import bookmarks, categories, health, stats, shopee, auth


def create_app() -> FastAPI:
    app = FastAPI(
        title="api.ndinhnguyen",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )
    app.middleware("http")(security_middleware)
    app.include_router(health.router)
    app.include_router(stats.router)
    app.include_router(bookmarks.router)
    app.include_router(categories.router)
    app.include_router(shopee.router)
    app.include_router(auth.router)
    return app

app = create_app()

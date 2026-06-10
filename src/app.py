import hmac
from typing import Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from .context import worker_env
from .models import BookmarkInput, CategoryInput
from . import service


app = FastAPI(title="Simple Skill API", docs_url=None, redoc_url=None)


def _env_value(env: Any, key: str, default: str = "") -> str:
    value = getattr(env, key, default)
    return str(value) if value is not None else default


def _json(payload: dict[str, Any], status_code: int = 200) -> JSONResponse:
    return JSONResponse(payload, status_code=status_code)


@app.middleware("http")
async def security_middleware(request: Request, call_next: Any) -> JSONResponse:
    env = worker_env.get(None)
    origin = request.headers.get("origin")
    allowed = {
        item.strip()
        for item in _env_value(env, "ALLOWED_ORIGINS").split(",")
        if item.strip()
    }

    if origin and origin not in allowed:
        return _json(service.response(False, "origin_not_allowed"), 403)

    if request.method == "OPTIONS":
        response = _json(service.response(True, "ok"))
    elif request.url.path.startswith("/api/"):
        configured = _env_value(env, "ADMIN_TOKEN")
        authorization = request.headers.get("authorization", "")
        supplied = authorization.removeprefix("Bearer ").strip()
        if not configured:
            response = _json(service.response(False, "auth_missing_config"), 500)
        elif not supplied or not hmac.compare_digest(supplied, configured):
            response = _json(service.response(False, "auth_invalid"), 401)
        else:
            response = await call_next(request)
    else:
        response = await call_next(request)

    if origin and origin in allowed:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Vary"] = "Origin"
    return response


def _db() -> Any:
    env = worker_env.get(None)
    return getattr(env, "BOOKMARKS_DB", None)


def _model_data(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def _run(operation: Any) -> JSONResponse:
    db = _db()
    if db is None:
        return _json(service.response(False, "db_unavailable"), 503)
    try:
        result = await operation(db)
        return _json(result, 200 if result["ok"] else 400)
    except Exception:
        return _json(service.response(False, "unknown_error"), 500)


@app.get("/health")
async def health() -> dict[str, Any]:
    return service.response(True, "ok", {"service": "simple-skill-api"})


@app.get("/api/bookmarks")
async def get_bookmarks(q: str = "", categoryId: str = "") -> JSONResponse:
    return await _run(lambda db: service.dashboard(db, q, categoryId))


@app.post("/api/bookmarks")
async def create_bookmark(payload: BookmarkInput) -> JSONResponse:
    return await _run(lambda db: service.save_bookmark(db, _model_data(payload)))


@app.put("/api/bookmarks/{bookmark_id}")
async def update_bookmark(
    bookmark_id: str, payload: BookmarkInput
) -> JSONResponse:
    return await _run(
        lambda db: service.save_bookmark(db, _model_data(payload), bookmark_id)
    )


@app.delete("/api/bookmarks/{bookmark_id}")
async def delete_bookmark(bookmark_id: str) -> JSONResponse:
    return await _run(lambda db: service.remove_bookmark(db, bookmark_id))


@app.post("/api/categories")
async def create_category(payload: CategoryInput) -> JSONResponse:
    return await _run(lambda db: service.save_category(db, _model_data(payload)))


@app.put("/api/categories/{category_id}")
async def update_category(
    category_id: str, payload: CategoryInput
) -> JSONResponse:
    return await _run(
        lambda db: service.save_category(db, _model_data(payload), category_id)
    )


@app.delete("/api/categories/{category_id}")
async def delete_category(category_id: str) -> JSONResponse:
    return await _run(lambda db: service.remove_category(db, category_id))

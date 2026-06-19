from typing import Any, Literal

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, response
from features.bookmarks import service
from features.bookmarks.schemas import BookmarkInput, PaginatedBookmarksResponse, ApiResponse


router = APIRouter()


def _db() -> Any:
    env = worker_env.get(None)
    return getattr(env, "DB", None)


def _model_data(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    return model.dict()


async def _run(operation: Any) -> JSONResponse:
    db = _db()
    if db is None:
        return json_response(response(False, "db_unavailable"), 503)
    try:
        result = await operation(db)
        return json_response(result, 200 if result["ok"] else 400)
    except Exception as e:
        print(f"Exception in bookmarks operation: {e}")
        return json_response(response(False, "unknown_error"), 500)


@router.get("/api/bookmarks", response_model=PaginatedBookmarksResponse)
async def get_bookmarks(
    categoryId: str = Query("", description="Filter bookmarks by category ID (includes sub-categories)"),
    q: str = Query("", description="Search term matching title, URL, or description"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    pageSize: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sortBy: Literal["createdAt", "title", "url"] = Query("createdAt", description="Field to sort bookmarks by"),
    sortOrder: Literal["asc", "desc"] = Query("desc", description="Sort order direction"),
) -> JSONResponse:
    return await _run(
        lambda db: service.get_bookmarks_dashboard(
            db, q, categoryId, page, pageSize, sortBy, sortOrder
        )
    )


@router.post("/api/bookmarks", response_model=ApiResponse)
async def create_bookmark(payload: BookmarkInput) -> JSONResponse:
    return await _run(lambda db: service.save_bookmark(db, _model_data(payload)))


@router.put("/api/bookmarks/{bookmark_id}", response_model=ApiResponse)
async def update_bookmark(
    bookmark_id: str, payload: BookmarkInput
) -> JSONResponse:
    return await _run(
        lambda db: service.save_bookmark(db, _model_data(payload), bookmark_id)
    )


@router.delete("/api/bookmarks/{bookmark_id}", response_model=ApiResponse)
async def delete_bookmark(bookmark_id: str) -> JSONResponse:
    return await _run(lambda db: service.remove_bookmark(db, bookmark_id))

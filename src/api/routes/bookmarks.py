from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.helpers import get_model_data, run_db_operation
from core.responses import Response, json_response
from features.bookmarks import service
from features.bookmarks.schemas import BookmarkInput, BookmarkSchema
from typing import Any


router = APIRouter()


@router.get("/api/bookmarks", response_model=Response[list[BookmarkSchema]])
async def get_bookmarks(
    categoryId: str = Query("", description="Filter bookmarks by category ID (includes sub-categories)"),
    q: str = Query("", description="Search term matching title, URL, or description"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    pageSize: int = Query(20, ge=1, le=100, description="Number of items per page"),
    sortBy: Literal["createdAt", "title", "url"] = Query("createdAt", description="Field to sort bookmarks by"),
    sortOrder: Literal["asc", "desc"] = Query("desc", description="Sort order direction"),
) -> JSONResponse:
    """
    Retrieves a paginated list of bookmarks, optionally filtered by category and search query.
    """
    return await run_db_operation(
        lambda db: service.get_bookmarks_dashboard(
            db, q, categoryId, page, pageSize, sortBy, sortOrder
        ),
        "bookmarks"
    )


@router.post("/api/bookmarks", response_model=Response[Any])
async def create_bookmark(payload: BookmarkInput) -> JSONResponse:
    """
    Creates a new bookmark.
    """
    return await run_db_operation(
        lambda db: service.save_bookmark(db, get_model_data(payload)),
        "bookmarks"
    )


@router.put("/api/bookmarks/{bookmark_id}", response_model=Response[Any])
async def update_bookmark(
    bookmark_id: str, payload: BookmarkInput
) -> JSONResponse:
    """
    Updates an existing bookmark by ID.
    """
    return await run_db_operation(
        lambda db: service.save_bookmark(db, get_model_data(payload), bookmark_id),
        "bookmarks"
    )


@router.delete("/api/bookmarks/{bookmark_id}", response_model=Response[Any])
async def delete_bookmark(bookmark_id: str) -> JSONResponse:
    """
    Deletes a bookmark by ID.
    """
    return await run_db_operation(
        lambda db: service.remove_bookmark(db, bookmark_id),
        "bookmarks"
    )


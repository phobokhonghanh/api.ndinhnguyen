from typing import Any, Literal

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from core.context import worker_env
from core.responses import json_response, response
from features.bookmarks import service
from features.bookmarks.schemas import CategoryInput, ApiResponse, PaginatedCategoriesResponse


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
        print(f"Exception in categories operation: {e}")
        return json_response(response(False, "unknown_error"), 500)


@router.get("/api/categories", response_model=PaginatedCategoriesResponse)
async def get_categories(
    q: str = Query("", description="Search term for category name"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of items per page"),
    sortBy: Literal["name", "createdAt"] = Query("name", description="Field to sort categories by"),
    sortOrder: Literal["asc", "desc"] = Query("asc", description="Sort order direction"),
) -> JSONResponse:
    return await _run(
        lambda db: service.get_categories_dashboard(
            db, q, page, pageSize, sortBy, sortOrder
        )
    )


@router.post("/api/categories", response_model=ApiResponse)
async def create_category(payload: CategoryInput) -> JSONResponse:
    return await _run(lambda db: service.save_category(db, _model_data(payload)))


@router.put("/api/categories/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: str, payload: CategoryInput
) -> JSONResponse:
    return await _run(
        lambda db: service.save_category(db, _model_data(payload), category_id)
    )


@router.delete("/api/categories/{category_id}", response_model=ApiResponse)
async def delete_category(category_id: str) -> JSONResponse:
    return await _run(lambda db: service.remove_category(db, category_id))

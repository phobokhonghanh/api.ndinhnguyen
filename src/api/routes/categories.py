from typing import Literal

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from api.helpers import get_model_data, run_db_operation
from features.bookmarks import service
from features.bookmarks.schemas import CategoryInput, ApiResponse, PaginatedCategoriesResponse


router = APIRouter()


@router.get("/api/categories", response_model=PaginatedCategoriesResponse)
async def get_categories(
    q: str = Query("", description="Search term for category name"),
    page: int = Query(1, ge=1, description="Page number (starts from 1)"),
    pageSize: int = Query(10, ge=1, le=100, description="Number of items per page"),
    sortBy: Literal["name", "createdAt"] = Query("name", description="Field to sort categories by"),
    sortOrder: Literal["asc", "desc"] = Query("asc", description="Sort order direction"),
) -> JSONResponse:
    """
    Retrieves a paginated list of categories.
    """
    return await run_db_operation(
        lambda db: service.get_categories_dashboard(
            db, q, page, pageSize, sortBy, sortOrder
        ),
        "categories"
    )


@router.post("/api/categories", response_model=ApiResponse)
async def create_category(payload: CategoryInput) -> JSONResponse:
    """
    Creates a new category.
    """
    return await run_db_operation(
        lambda db: service.save_category(db, get_model_data(payload)),
        "categories"
    )


@router.put("/api/categories/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: str, payload: CategoryInput
) -> JSONResponse:
    """
    Updates an existing category by ID.
    """
    return await run_db_operation(
        lambda db: service.save_category(db, get_model_data(payload), category_id),
        "categories"
    )


@router.delete("/api/categories/{category_id}", response_model=ApiResponse)
async def delete_category(category_id: str) -> JSONResponse:
    """
    Deletes a category by ID.
    """
    return await run_db_operation(
        lambda db: service.remove_category(db, category_id),
        "categories"
    )


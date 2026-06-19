from typing import Any

from pydantic import BaseModel


class BookmarkInput(BaseModel):
    title: str = ""
    url: str = ""
    description: str | None = None
    categoryId: str = ""


class CategoryInput(BaseModel):
    name: str = ""
    color: str = "blue"
    parentId: str | None = None


class ApiResponse(BaseModel):
    ok: bool
    code: str
    data: Any | None = None


class BookmarkSchema(BaseModel):
    id: str
    title: str
    url: str
    description: str | None = None
    categoryId: str
    categoryName: str
    categorySlug: str
    categoryColor: str
    createdAt: str
    updatedAt: str


class CategoryTreeNode(BaseModel):
    id: str
    name: str
    slug: str
    color: str
    parentId: str | None = None
    createdAt: str
    children: list["CategoryTreeNode"] = []


CategoryTreeNode.model_rebuild()


class PaginationMetadata(BaseModel):
    total: int
    page: int
    pageSize: int
    totalPages: int


class PaginatedCategoriesData(BaseModel):
    categoryTree: list[CategoryTreeNode]
    pagination: PaginationMetadata


class PaginatedCategoriesResponse(BaseModel):
    ok: bool
    code: str
    data: PaginatedCategoriesData


class PaginatedBookmarksData(BaseModel):
    bookmarks: list[BookmarkSchema]
    pagination: PaginationMetadata


class PaginatedBookmarksResponse(BaseModel):
    ok: bool
    code: str
    data: PaginatedBookmarksData



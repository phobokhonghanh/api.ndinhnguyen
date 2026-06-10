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

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







import asyncio
import re
import unicodedata
from typing import Any
from urllib.parse import urlparse
from uuid import uuid4

from core.responses import response
from features.bookmarks import repository


COLORS = {"blue", "emerald", "amber", "rose", "violet", "cyan"}


def slugify(name: str) -> str:
    normalized = unicodedata.normalize("NFD", name)
    ascii_name = "".join(char for char in normalized if not unicodedata.combining(char))
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_name.lower()).strip("-")
    return slug or str(uuid4())[:8]


def build_tree(categories: list[dict[str, Any]], bookmarks: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    bookmarks = bookmarks or []
    bookmarks_by_category: dict[str, list[dict[str, Any]]] = {}
    for bookmark in bookmarks:
        cat_id = bookmark["categoryId"]
        bookmarks_by_category.setdefault(cat_id, []).append(bookmark)

    nodes = {
        item["id"]: {
            **item,
            "bookmarks": bookmarks_by_category.get(item["id"], []),
            "children": []
        }
        for item in categories
    }
    roots: list[dict[str, Any]] = []
    for node in nodes.values():
        parent_id = node["parentId"]
        if parent_id and parent_id in nodes:
            nodes[parent_id]["children"].append(node)
        else:
            roots.append(node)
    return roots


def descendant_ids(categories: list[dict[str, Any]], category_id: str) -> list[str]:
    children: dict[str, list[str]] = {}
    for category in categories:
        parent_id = category["parentId"]
        if parent_id:
            children.setdefault(parent_id, []).append(category["id"])
    found = {category_id}
    stack = [category_id]
    while stack:
        current = stack.pop()
        for child_id in children.get(current, []):
            if child_id not in found:
                found.add(child_id)
                stack.append(child_id)
    return list(found)


def validate_bookmark(data: dict[str, Any]) -> str | None:
    if not data["title"]:
        return "title_required"
    parsed = urlparse(data["url"])
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return "url_invalid"
    if not data["categoryId"]:
        return "category_required"
    return None


def normalize_bookmark(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": data["title"].strip(),
        "url": data["url"].strip(),
        "description": (data.get("description") or "").strip() or None,
        "categoryId": data["categoryId"].strip(),
    }


def normalize_category(data: dict[str, Any]) -> dict[str, Any]:
    color = (data.get("color") or "blue").strip()
    return {
        "name": data["name"].strip(),
        "color": color if color in COLORS else "blue",
        "parentId": (data.get("parentId") or "").strip() or None,
    }


async def dashboard(db: Any, query: str, category_id: str) -> dict[str, Any]:
    if category_id:
        categories, all_bookmarks = await asyncio.gather(
            repository.list_categories(db),
            repository.list_bookmarks(db, query.strip(), [])
        )
        selected_ids = descendant_ids(categories, category_id)
        selected_set = set(selected_ids)
        bookmarks = [b for b in all_bookmarks if b["categoryId"] in selected_set]
    else:
        categories, bookmarks = await asyncio.gather(
            repository.list_categories(db),
            repository.list_bookmarks(db, query.strip(), [])
        )
        selected_ids = []

    return response(
        True,
        "ok",
        {
            "categoryTree": build_tree(categories, bookmarks),
            "selectedCategoryIds": selected_ids,
            "dbReady": True,
        },
    )


async def save_bookmark(
    db: Any, raw: dict[str, Any], bookmark_id: str | None = None
) -> dict[str, Any]:
    data = normalize_bookmark(raw)
    error = validate_bookmark(data)
    if error:
        return response(False, error)
    if not await repository.category_exists(db, data["categoryId"]):
        return response(False, "category_not_found")
    if bookmark_id and not await repository.bookmark_exists(db, bookmark_id):
        return response(False, "bookmark_not_found")
    if bookmark_id:
        await repository.update_bookmark(db, bookmark_id, data)
    else:
        await repository.create_bookmark(db, data)
    return response(True, "ok")


async def save_category(
    db: Any, raw: dict[str, Any], category_id: str | None = None
) -> dict[str, Any]:
    data = normalize_category(raw)
    if not data["name"]:
        return response(False, "title_required")
    if category_id and not await repository.category_exists(db, category_id):
        return response(False, "category_not_found")
    if data["parentId"]:
        if data["parentId"] == category_id:
            return response(False, "category_required")
        if not await repository.category_exists(db, data["parentId"]):
            return response(False, "category_not_found")
        if category_id:
            categories = await repository.list_categories(db)
            if data["parentId"] in descendant_ids(categories, category_id):
                return response(False, "category_required")
    slug = await repository.unique_slug(db, slugify(data["name"]), category_id)
    if category_id:
        await repository.update_category(db, category_id, data, slug)
    else:
        await repository.create_category(db, data, slug)
    return response(True, "ok")


async def remove_bookmark(db: Any, bookmark_id: str) -> dict[str, Any]:
    if not await repository.bookmark_exists(db, bookmark_id):
        return response(False, "bookmark_not_found")
    await repository.delete_bookmark(db, bookmark_id)
    return response(True, "ok")


async def remove_category(db: Any, category_id: str) -> dict[str, Any]:
    if not await repository.category_exists(db, category_id):
        return response(False, "category_not_found")
    state = await repository.category_delete_state(db, category_id)
    if state == "has_children":
        return response(False, "category_has_children")
    if state == "in_use":
        return response(False, "category_in_use")
    await repository.delete_category(db, category_id)
    return response(True, "ok")

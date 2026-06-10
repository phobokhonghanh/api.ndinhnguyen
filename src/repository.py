from typing import Any
from uuid import uuid4


def _row_value(row: Any, key: str) -> Any:
    if isinstance(row, dict):
        return row.get(key)
    return getattr(row, key, None)


async def _rows(statement: Any) -> list[Any]:
    result = await statement.all()
    return list(result.results or [])


async def _first(statement: Any) -> Any | None:
    return await statement.first()


def _category(row: Any) -> dict[str, Any]:
    return {
        "id": _row_value(row, "id"),
        "name": _row_value(row, "name"),
        "slug": _row_value(row, "slug"),
        "color": _row_value(row, "color") or "blue",
        "parentId": _row_value(row, "parent_id"),
        "createdAt": _row_value(row, "created_at"),
    }


def _bookmark(row: Any) -> dict[str, Any]:
    return {
        "id": _row_value(row, "id"),
        "title": _row_value(row, "title"),
        "url": _row_value(row, "url"),
        "description": _row_value(row, "description"),
        "categoryId": _row_value(row, "category_id"),
        "categoryName": _row_value(row, "category_name"),
        "categorySlug": _row_value(row, "category_slug"),
        "categoryColor": _row_value(row, "category_color") or "blue",
        "createdAt": _row_value(row, "created_at"),
        "updatedAt": _row_value(row, "updated_at"),
    }


async def list_categories(db: Any) -> list[dict[str, Any]]:
    rows = await _rows(
        db.prepare(
            """SELECT id, name, slug, color, parent_id, created_at
               FROM categories
               ORDER BY parent_id IS NOT NULL, name COLLATE NOCASE ASC"""
        )
    )
    return [_category(row) for row in rows]


async def list_bookmarks(
    db: Any, query: str, category_ids: list[str]
) -> list[dict[str, Any]]:
    conditions: list[str] = []
    values: list[str] = []
    if query:
        conditions.append(
            "(bookmarks.title LIKE ? OR bookmarks.url LIKE ? "
            "OR bookmarks.description LIKE ?)"
        )
        pattern = f"%{query}%"
        values.extend([pattern, pattern, pattern])
    if category_ids:
        placeholders = ", ".join("?" for _ in category_ids)
        conditions.append(f"bookmarks.category_id IN ({placeholders})")
        values.extend(category_ids)

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    statement = db.prepare(
        f"""SELECT bookmarks.id, bookmarks.title, bookmarks.url,
                   bookmarks.description, bookmarks.category_id,
                   bookmarks.created_at, bookmarks.updated_at,
                   categories.name AS category_name,
                   categories.slug AS category_slug,
                   categories.color AS category_color
            FROM bookmarks
            INNER JOIN categories ON categories.id = bookmarks.category_id
            {where}
            ORDER BY bookmarks.updated_at DESC, bookmarks.created_at DESC"""
    )
    if values:
        statement = statement.bind(*values)
    return [_bookmark(row) for row in await _rows(statement)]


async def category_exists(db: Any, category_id: str) -> bool:
    row = await _first(
        db.prepare("SELECT id FROM categories WHERE id = ? LIMIT 1").bind(category_id)
    )
    return row is not None


async def bookmark_exists(db: Any, bookmark_id: str) -> bool:
    row = await _first(
        db.prepare("SELECT id FROM bookmarks WHERE id = ? LIMIT 1").bind(bookmark_id)
    )
    return row is not None


async def unique_slug(
    db: Any, base_slug: str, category_id: str | None = None
) -> str:
    slug = base_slug
    suffix = 1
    while True:
        row = await _first(
            db.prepare("SELECT id FROM categories WHERE slug = ? LIMIT 1").bind(slug)
        )
        if row is None or _row_value(row, "id") == category_id:
            return slug
        suffix += 1
        slug = f"{base_slug}-{suffix}"


async def create_category(db: Any, data: dict[str, Any], slug: str) -> None:
    await db.prepare(
        """INSERT INTO categories (id, name, slug, color, parent_id)
           VALUES (?, ?, ?, ?, ?)"""
    ).bind(
        str(uuid4()), data["name"], slug, data["color"], data["parentId"]
    ).run()


async def update_category(
    db: Any, category_id: str, data: dict[str, Any], slug: str
) -> None:
    await db.prepare(
        """UPDATE categories
           SET name = ?, slug = ?, color = ?, parent_id = ?
           WHERE id = ?"""
    ).bind(
        data["name"], slug, data["color"], data["parentId"], category_id
    ).run()


async def category_delete_state(db: Any, category_id: str) -> str:
    child = await _first(
        db.prepare("SELECT id FROM categories WHERE parent_id = ? LIMIT 1").bind(
            category_id
        )
    )
    if child is not None:
        return "has_children"
    bookmark = await _first(
        db.prepare("SELECT id FROM bookmarks WHERE category_id = ? LIMIT 1").bind(
            category_id
        )
    )
    return "in_use" if bookmark is not None else "ready"


async def delete_category(db: Any, category_id: str) -> None:
    await db.prepare("DELETE FROM categories WHERE id = ?").bind(category_id).run()


async def create_bookmark(db: Any, data: dict[str, Any]) -> None:
    await db.prepare(
        """INSERT INTO bookmarks (id, title, url, description, category_id)
           VALUES (?, ?, ?, ?, ?)"""
    ).bind(
        str(uuid4()),
        data["title"],
        data["url"],
        data["description"],
        data["categoryId"],
    ).run()


async def update_bookmark(
    db: Any, bookmark_id: str, data: dict[str, Any]
) -> None:
    await db.prepare(
        """UPDATE bookmarks
           SET title = ?, url = ?, description = ?, category_id = ?,
               updated_at = CURRENT_TIMESTAMP
           WHERE id = ?"""
    ).bind(
        data["title"],
        data["url"],
        data["description"],
        data["categoryId"],
        bookmark_id,
    ).run()


async def delete_bookmark(db: Any, bookmark_id: str) -> None:
    await db.prepare("DELETE FROM bookmarks WHERE id = ?").bind(bookmark_id).run()

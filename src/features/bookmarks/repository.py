from typing import Any
from uuid import uuid4

from infra.d1 import first, row_value, rows


def _category(row: Any) -> dict[str, Any]:
    return {
        "id": row_value(row, "id"),
        "name": row_value(row, "name"),
        "slug": row_value(row, "slug"),
        "color": row_value(row, "color") or "blue",
        "parentId": row_value(row, "parent_id"),
        "createdAt": row_value(row, "created_at"),
    }


def _bookmark(row: Any) -> dict[str, Any]:
    return {
        "id": row_value(row, "id"),
        "title": row_value(row, "title"),
        "url": row_value(row, "url"),
        "description": row_value(row, "description"),
        "categoryId": row_value(row, "category_id"),
        "categoryName": row_value(row, "category_name"),
        "categorySlug": row_value(row, "category_slug"),
        "categoryColor": row_value(row, "category_color") or "blue",
        "createdAt": row_value(row, "created_at"),
        "updatedAt": row_value(row, "updated_at"),
    }


async def list_categories(db: Any) -> list[dict[str, Any]]:
    result_rows = await rows(
        db.prepare(
            """SELECT id, name, slug, color, parent_id, created_at
               FROM categories
               ORDER BY parent_id IS NOT NULL, name COLLATE NOCASE ASC"""
        )
    )
    return [_category(row) for row in result_rows]


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
    return [_bookmark(row) for row in await rows(statement)]


async def category_exists(db: Any, category_id: str) -> bool:
    row = await first(
        db.prepare("SELECT id FROM categories WHERE id = ? LIMIT 1").bind(category_id)
    )
    return row is not None


async def bookmark_exists(db: Any, bookmark_id: str) -> bool:
    row = await first(
        db.prepare("SELECT id FROM bookmarks WHERE id = ? LIMIT 1").bind(bookmark_id)
    )
    return row is not None


async def unique_slug(
    db: Any, base_slug: str, category_id: str | None = None
) -> str:
    slug = base_slug
    suffix = 1
    while True:
        row = await first(
            db.prepare("SELECT id FROM categories WHERE slug = ? LIMIT 1").bind(slug)
        )
        if row is None or row_value(row, "id") == category_id:
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
    child = await first(
        db.prepare("SELECT id FROM categories WHERE parent_id = ? LIMIT 1").bind(
            category_id
        )
    )
    if child is not None:
        return "has_children"
    bookmark = await first(
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


async def count_categories(db: Any, query: str) -> int:
    conditions: list[str] = []
    values: list[Any] = []
    if query:
        conditions.append("name LIKE ?")
        values.append(f"%{query}%")
    else:
        conditions.append("parent_id IS NULL")

    where = f"WHERE {' AND '.join(conditions)}"
    row = await first(
        db.prepare(f"SELECT COUNT(*) AS total FROM categories {where}").bind(*values)
    )
    return row_value(row, "total") or 0


async def list_categories_paginated(
    db: Any,
    query: str,
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
) -> list[dict[str, Any]]:
    sort_column = "created_at" if sort_by == "createdAt" else "name"
    collate = " COLLATE NOCASE" if sort_column == "name" else ""
    order = "DESC" if sort_order.upper() == "DESC" else "ASC"

    conditions: list[str] = []
    values: list[Any] = []
    if query:
        conditions.append("name LIKE ?")
        values.append(f"%{query}%")
    else:
        conditions.append("parent_id IS NULL")

    where = f"WHERE {' AND '.join(conditions)}"
    offset = (page - 1) * page_size

    id_rows = await rows(
        db.prepare(
            f"SELECT id FROM categories {where} ORDER BY {sort_column}{collate} {order} LIMIT ? OFFSET ?"
        ).bind(*(values + [page_size, offset]))
    )
    category_ids = [row_value(row, "id") for row in id_rows]
    if not category_ids:
        return []

    placeholders = ", ".join("?" for _ in category_ids)
    result_rows = await rows(
        db.prepare(
            f"""WITH RECURSIVE category_tree(id, name, slug, color, parent_id, created_at) AS (
                SELECT id, name, slug, color, parent_id, created_at
                FROM categories
                WHERE id IN ({placeholders})
                
                UNION ALL
                
                SELECT c.id, c.name, c.slug, c.color, c.parent_id, c.created_at
                FROM categories c
                INNER JOIN category_tree ct ON c.parent_id = ct.id
            )
            SELECT DISTINCT id, name, slug, color, parent_id, created_at FROM category_tree
            ORDER BY parent_id IS NOT NULL, name COLLATE NOCASE ASC"""
        ).bind(*category_ids)
    )

    return [_category(row) for row in result_rows]


async def count_bookmarks(
    db: Any, query: str, category_ids: list[str]
) -> int:
    conditions: list[str] = []
    values: list[Any] = []
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
    row = await first(
        db.prepare(
            f"""SELECT COUNT(*) AS total
               FROM bookmarks
               INNER JOIN categories ON categories.id = bookmarks.category_id
               {where}"""
        ).bind(*values)
    )
    return row_value(row, "total") or 0


async def list_bookmarks_paginated(
    db: Any,
    query: str,
    category_ids: list[str],
    page: int,
    page_size: int,
    sort_by: str,
    sort_order: str,
) -> list[dict[str, Any]]:
    if sort_by == "title":
        sort_column = "bookmarks.title"
    elif sort_by == "url":
        sort_column = "bookmarks.url"
    else:
        sort_column = "bookmarks.created_at"

    collate = " COLLATE NOCASE" if sort_column in {"bookmarks.title", "bookmarks.url"} else ""
    order = "DESC" if sort_order.upper() == "DESC" else "ASC"

    conditions: list[str] = []
    values: list[Any] = []
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
    offset = (page - 1) * page_size

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
            ORDER BY {sort_column}{collate} {order}
            LIMIT ? OFFSET ?"""
    )
    statement = statement.bind(*(values + [page_size, offset]))
    return [_bookmark(row) for row in await rows(statement)]


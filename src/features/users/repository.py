from typing import Any
from uuid import uuid4

from infra.d1 import first, row_value


def _user(row: Any) -> dict[str, Any]:
    return {
        "id": row_value(row, "id"),
        "email": row_value(row, "email"),
        "name": row_value(row, "name"),
        "picture": row_value(row, "picture"),
        "role": row_value(row, "role"),
        "createdAt": row_value(row, "created_at"),
        "updatedAt": row_value(row, "updated_at"),
    }


async def get_user_by_email(db: Any, email: str) -> dict[str, Any] | None:
    row = await first(
        db.prepare(
            """SELECT id, email, name, picture, role, created_at, updated_at
               FROM users
               WHERE email = ?
               LIMIT 1"""
        ).bind(email)
    )
    if row is None:
        return None
    return _user(row)


async def create_or_update_user(
    db: Any, email: str, name: str, picture: str, role: str
) -> dict[str, Any]:
    existing = await get_user_by_email(db, email)
    if existing:
        user_id = existing["id"]
        await db.prepare(
            """UPDATE users
               SET name = ?, picture = ?, role = ?, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?"""
        ).bind(name, picture, role, user_id).run()
    else:
        user_id = str(uuid4())
        await db.prepare(
            """INSERT INTO users (id, email, name, picture, role)
               VALUES (?, ?, ?, ?, ?)"""
        ).bind(user_id, email, name, picture, role).run()

    updated = await get_user_by_email(db, email)
    if not updated:
        raise RuntimeError("Failed to retrieve updated user profile")
    return updated


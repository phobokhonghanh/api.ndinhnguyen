from typing import Any
from uuid import uuid4

from core.banks import get_bank_name_by_code
from infra.d1 import first, row_value


def _user(row: Any) -> dict[str, Any]:
    bank_code = row_value(row, "bank_code")
    bank_name = get_bank_name_by_code(bank_code) if bank_code else None
    return {
        "id": row_value(row, "id"),
        "email": row_value(row, "email"),
        "name": row_value(row, "name"),
        "picture": row_value(row, "picture"),
        "role": row_value(row, "role"),
        "bankCode": bank_code,
        "bankName": bank_name,
        "accountNumber": row_value(row, "account_number"),
        "accountName": row_value(row, "account_name"),
        "createdAt": row_value(row, "created_at"),
        "updatedAt": row_value(row, "updated_at"),
    }


async def get_user_by_email(db: Any, email: str) -> dict[str, Any] | None:
    row = await first(
        db.prepare(
            """SELECT id, email, name, picture, role, bank_code, account_number, account_name, created_at, updated_at
               FROM users
               WHERE email = ?
               LIMIT 1"""
        ).bind(email)
    )
    if row is None:
        return None
    return _user(row)


async def get_user_by_id(db: Any, user_id: str) -> dict[str, Any] | None:
    row = await first(
        db.prepare(
            """SELECT id, email, name, picture, role, bank_code, account_number, account_name, created_at, updated_at
               FROM users
               WHERE id = ?
               LIMIT 1"""
        ).bind(user_id)
    )
    if row is None:
        return None
    return _user(row)


async def update_user_payment_info(
    db: Any,
    user_id: str,
    bank_code: str | None,
    account_number: str | None,
    account_name: str | None,
) -> dict[str, Any] | None:
    await db.prepare(
        """UPDATE users
           SET bank_code = ?, account_number = ?, account_name = ?, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?"""
    ).bind(bank_code, account_number, account_name, user_id).run()
    return await get_user_by_id(db, user_id)


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
        user_id = str(uuid4()).replace("-", "")
        await db.prepare(
            """INSERT INTO users (id, email, name, picture, role)
               VALUES (?, ?, ?, ?, ?)"""
        ).bind(user_id, email, name, picture, role).run()

    updated = await get_user_by_email(db, email)
    if not updated:
        raise RuntimeError("Failed to retrieve updated user profile")
    return updated


async def get_dashboard_stats(db: Any, user_id: str | None = None) -> dict[str, Any]:
    if user_id:
        count_row = await first(
            db.prepare("SELECT COUNT(*) as count FROM cashbacks WHERE user_id = ?").bind(user_id)
        )
        total_cb_row = await first(
            db.prepare("SELECT COALESCE(SUM(cashback_amount), 0) as total FROM cashbacks WHERE user_id = ?").bind(user_id)
        )
        pending_row = await first(
            db.prepare("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE user_id = ? AND status = 'Pending'").bind(user_id)
        )
        completed_row = await first(
            db.prepare("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE user_id = ? AND status = 'Completed'").bind(user_id)
        )
    else:
        count_row = await first(
            db.prepare("SELECT COUNT(*) as count FROM cashbacks")
        )
        total_cb_row = await first(
            db.prepare("SELECT COALESCE(SUM(cashback_amount), 0) as total FROM cashbacks")
        )
        pending_row = await first(
            db.prepare("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'Pending'")
        )
        completed_row = await first(
            db.prepare("SELECT COALESCE(SUM(amount), 0) as total FROM payments WHERE status = 'Completed'")
        )

    return {
        "countOrders": int(row_value(count_row, "count") or 0),
        "totalCashback": float(int(row_value(total_cb_row, "total") or 0)),
        "totalPaymentsPending": float(int(row_value(pending_row, "total") or 0)),
        "totalPaymentsCompleted": float(int(row_value(completed_row, "total") or 0)),
    }


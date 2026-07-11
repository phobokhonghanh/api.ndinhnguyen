import json
from infra.d1 import first, row_value, rows
from core.constants import CASHBACK_STATUS_PENDING
from features.cashbacks.shopee.schemas import Conversion
from features.cashbacks.schemas import CashbackRecord

def _cashback(row) -> CashbackRecord:
    conversion_str = row_value(row, "conversion")
    conversion_dict = {}
    if conversion_str:
        try:
            conversion_dict = json.loads(conversion_str)
        except Exception:
            pass
    return CashbackRecord(
        id=row_value(row, "id"),
        user_id=row_value(row, "user_id"),
        platform=row_value(row, "platform"),
        cashback=row_value(row, "cashback_amount"),
        status=row_value(row, "status"),
        checkout_id=row_value(row, "checkout_id"),
        conversion=conversion_dict,
        created_at=row_value(row, "created_at"),
        updated_at=row_value(row, "updated_at"),
    )

async def get_cashback_by_key(
    db, platform: str, checkout_id: str
) -> CashbackRecord | None:
    row = await first(
        db.prepare(
            """SELECT id, user_id, platform, cashback_amount, status, checkout_id, conversion, created_at, updated_at
               FROM cashbacks
               WHERE platform = ? AND checkout_id = ?
               LIMIT 1"""
        ).bind(platform, checkout_id)
    )
    if row is None:
        return None
    return _cashback(row)

async def insert_cashback(db, data: CashbackRecord) -> None:
    conversion_dict = (
        data.conversion.model_dump(by_alias=True, exclude_none=True)
        if data.conversion else {}
    )
    conversion_str = json.dumps(conversion_dict)
    await db.prepare(
        """INSERT INTO cashbacks (
             id, user_id, platform, cashback_amount, status, checkout_id, conversion
           ) VALUES (?, ?, ?, ?, ?, ?, ?)"""
    ).bind(
        data.id,
        data.user_id,
        data.platform,
        data.cashback,
        data.status or CASHBACK_STATUS_PENDING,
        data.checkout_id,
        conversion_str
    ).run()

async def update_cashback(
    db, platform: str, checkout_id: str, status: str,
    conversion: Conversion | None = None
) -> None:
    if conversion is not None:
        conversion_dict = conversion.model_dump(by_alias=True, exclude_none=True)
        conversion_str = json.dumps(conversion_dict)
        await db.prepare(
            """UPDATE cashbacks
               SET status = ?, conversion = ?, updated_at = CURRENT_TIMESTAMP
               WHERE platform = ? AND checkout_id = ?"""
        ).bind(status, conversion_str, platform, checkout_id).run()
    else:
        await db.prepare(
            """UPDATE cashbacks
               SET status = ?, updated_at = CURRENT_TIMESTAMP
               WHERE platform = ? AND checkout_id = ?"""
        ).bind(status, platform, checkout_id).run()

async def get_cashbacks_by_user(db, user_id: str) -> list[CashbackRecord]:
    result_rows = await rows(
        db.prepare(
            """SELECT id, user_id, platform, cashback_amount, status, checkout_id, conversion, created_at, updated_at
               FROM cashbacks
               WHERE user_id = ?
               ORDER BY created_at DESC"""
        ).bind(user_id)
    )
    return [_cashback(row) for row in result_rows]

async def count_cashbacks(db, user_id: str | None = None) -> int:
    if user_id:
        row = await first(
            db.prepare(
                """SELECT COUNT(*) as count FROM cashbacks WHERE user_id = ?"""
            ).bind(user_id)
        )
    else:
        row = await first(
            db.prepare(
                """SELECT COUNT(*) as count FROM cashbacks"""
            )
        )
    return int(row_value(row, "count") or 0)

async def list_cashbacks_paginated(
    db, page: int, page_size: int, user_id: str | None = None
) -> list[CashbackRecord]:
    offset = (page - 1) * page_size
    if user_id:
        result_rows = await rows(
            db.prepare(
                """SELECT id, user_id, platform, cashback_amount, status, checkout_id, conversion, created_at, updated_at
                   FROM cashbacks
                   WHERE user_id = ?
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?"""
            ).bind(user_id, page_size, offset)
        )
    else:
        result_rows = await rows(
            db.prepare(
                """SELECT id, user_id, platform, cashback_amount, status, checkout_id, conversion, created_at, updated_at
                   FROM cashbacks
                   ORDER BY created_at DESC
                   LIMIT ? OFFSET ?"""
            ).bind(page_size, offset)
        )
    return [_cashback(row) for row in result_rows]

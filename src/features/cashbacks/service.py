from typing import Any
from features.cashbacks import repository
from features.cashbacks.interfaces import PlatformRegistry
from features.cashbacks.shopee.adapter import ShopeePlatformAdapter
from features.cashbacks.schemas import CashbackRecord
from core.constants import CASHBACK_STATUS_PENDING, CASHBACK_STATUSES

from core.responses import Pagination

# Register all adapters at load time
PlatformRegistry.register("shopee", ShopeePlatformAdapter())


async def add_cashback(db: Any, data: CashbackRecord) -> CashbackRecord:
    platform = data.platform
    checkout_id = data.checkout_id
    existing = await repository.get_cashback_by_key(db, platform, checkout_id)

    if existing:
        if (existing.status != data.status or
            existing.conversion != data.conversion):

            await repository.update_cashback(
                db=db,
                platform=platform,
                checkout_id=checkout_id,
                status=data.status,
                conversion=data.conversion
            )
            updated = await repository.get_cashback_by_key(db, platform, checkout_id)
            return updated if updated else existing
        return existing

    await repository.insert_cashback(db, data)
    new_record = await repository.get_cashback_by_key(db, platform, checkout_id)
    if not new_record:
        raise RuntimeError("Failed to retrieve created cashback record")
    return new_record


async def get_cashbacks(
    db: Any, page: int = 1, page_size: int = 20, user_id: str | None = None
) -> tuple[list[CashbackRecord], Pagination]:
    total = await repository.count_cashbacks(db, user_id)
    import math
    total_pages = math.ceil(total / page_size) if total > 0 else 0

    records = await repository.list_cashbacks_paginated(db, page, page_size, user_id)

    pagination = Pagination(
        total=total,
        page=page,
        pageSize=page_size,
        totalPages=total_pages,
    )
    return records, pagination


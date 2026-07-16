from features.cashbacks.shopee.helper import calculate_commission_cashback
from api.helpers import get_commission_rate
from features.cashbacks.schemas import CashbackRecord
from fastapi import HTTPException
from core.responses import Pagination
from features.cashbacks.shopee.schemas import Conversion
from features.cashbacks.shopee.helper import (
    map_raw_to_schema_conversion,
    extract_user_id_from_utm,
    fetch_prod_alt_by_link,
    parse_shopee_link,
    create_affiliate_link,
    safe_cast,
)
from features.cashbacks.shopee.client import ShopeeAffiliateClient
from features.cashbacks.shopee.adapter import ShopeePlatformAdapter
from core.constants import MICRO_UNIT_SCALE

async def fetch_conversion_reports(
    page_size: int = 20,
    page_num: int = 1,
    sub_id: str | None = None,
    purchase_time_s: int | None = None,
    purchase_time_e: int | None = None,
) -> tuple[list[Conversion], Pagination]:
    """
    Fetches conversion reports from Shopee Affiliate API using configured cookie credentials,
    optionally filtering by sub_id, and purchase timestamp ranges.
    """
    client = ShopeeAffiliateClient()
    adapter = ShopeePlatformAdapter()
    res = await client.get_conversion_reports(
        page_size=page_size,
        page_num=page_num,
        sub_id=sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )
    if res.get("code") != 0 or res.get("msg") != "success":
        raise HTTPException(status_code=502, detail=f"shopee_api: {res.get('code')} - msg={res.get('msg', 'error')}")
    
    data = res.get("data", {})
    raw_conversions = data.get("list") or []
    conversions = [map_raw_to_schema_conversion(c) for c in raw_conversions]

    page_num = data.get("page_num", 1)
    page_size = data.get("page_size", 20)
    total_count = data.get("total_count", 0)
    import math
    total_pages = math.ceil(total_count / page_size) if total_count > 0 else 0

    pagination = Pagination(
        total=total_count,
        page=page_num,
        pageSize=page_size,
        totalPages=total_pages,
    )

    return conversions, pagination

async def get_conversion_reports(
    db,
    page_size: int = 20,
    page_num: int = 1,
    sub_id: str | None = None,
    purchase_time_s: int | None = None,
    purchase_time_e: int | None = None,
) -> tuple[list[Conversion], Pagination]:
    """
    Business layer to retrieve Shopee conversion reports, sync them to database.
    """
    # 1. Fetch from Shopee API
    conversions, pagination = await fetch_conversion_reports(
        page_size=page_size,
        page_num=page_num,
        sub_id=sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )

    # 2. Sync fetched conversions to database using raw data
    if conversions:
        await save_conversions_to_db(db, conversions)

    return conversions, pagination

async def save_conversions_to_db(db, records: list[Conversion]) -> int:
    from features.cashbacks import service as cashback_service

    adapter = ShopeePlatformAdapter()
    synced_count = 0

    for record in records:
        user_id = extract_user_id_from_utm(record.utm_content)
        if not user_id:
            user_id = "system"

        affiliate_net_commission = record.affiliate_net_commission or 0.0
        cashback_amount = calculate_commission_cashback(affiliate_net_commission)
        cashback = CashbackRecord(
            userId=user_id,
            platform="shopee",
            cashback=cashback_amount,
            status=adapter.map_status(record.checkout_status),
            checkoutId=record.checkout_id or "",
            conversion=record.model_dump(by_alias=True)
        )
        try:
            await cashback_service.add_cashback(db, cashback)
            synced_count += 1
        except Exception as e:
            checkout_id = record.checkout_id or 'Unknown'
            print(f"Error saving cashback for User ID: {user_id} - Checkout ID: {checkout_id} - Error: {e}")
    return synced_count

async def sync_shopee_cashbacks(
    db,
    purchase_time_s: int | None = None,
    purchase_time_e: int | None = None,
    sub_id: str | None = None,
) -> int:
    """
    Downloads conversion reports from Shopee, parses user ids, updates checkout statuses,
    calculates cashback amounts, and stores records in the generic cashback system.
    """
    page_num = 1
    page_size = 100
    synced_count = 0
    has_more = True

    while has_more:
        mapped_records, pagination = await fetch_conversion_reports(
            page_size=page_size,
            page_num=page_num,
            purchase_time_s=purchase_time_s,
            purchase_time_e=purchase_time_e,
            sub_id=sub_id,
        )

        if not mapped_records:
            break

        synced_count += await save_conversions_to_db(db, mapped_records)

        if len(mapped_records) < page_size:
            has_more = False
        else:
            page_num += 1

    return synced_count

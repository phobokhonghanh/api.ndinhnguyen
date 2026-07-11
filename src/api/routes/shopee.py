from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from api.helpers import get_db
from core.responses import Response, json_response
from features.cashbacks.shopee import service
from features.cashbacks.shopee.helper import safe_cast
from features.cashbacks.shopee.schemas import (
    AffiliateRequest,
    AffiliateResponseData,
    Conversion,
)

router = APIRouter()

@router.post("/api/shopee/affiliate", response_model=Response[AffiliateResponseData])
async def create_shopee_affiliate(payload: AffiliateRequest) -> JSONResponse:
    """
    Parses a Shopee product link, fetches its metadata, and converts it to a formatted affiliate link.
    """
    # 1. Fetch product info
    product = await service.fetch_prod_alt_by_link(payload.link)

    # 2. Determine link to parse
    if product is None or product.link is None:
        return json_response(ok=False, code="product_not_found", status_code=404)

    # 3. Parse link
    parsed_ids = service.parse_shopee_link(product.link)
    if not parsed_ids:
        return json_response(ok=False, code="link_format_invalid", status_code=400)

    item_id = parsed_ids["item_id"]
    shop_id = parsed_ids["shop_id"]

    # 4. Create affiliate link
    affiliate_link = service.create_affiliate_link(
        item_id=item_id,
        shop_id=shop_id,
        affiliate_id=payload.affiliate_id,
        sub_ids=payload.sub_ids,
        deep_and_deferred=payload.deep_and_deferred,
    )

    # 5. Serialize response data
    affiliate_response_data = AffiliateResponseData(affiliate_link=affiliate_link, product=product)

    # 6. Return response
    return json_response(data=affiliate_response_data)

@router.get("/api/shopee/conversions", response_model=Response[list[Conversion]])
async def get_shopee_conversions(
    request: Request,
    page_size: int = Query(20, ge=1, le=100),
    page_num: int = Query(1, ge=1),
    purchase_time_s: int = Query(...),
    purchase_time_e: int = Query(...),
) -> JSONResponse:
    """
    Retrieves conversion reports from Shopee Affiliate API for the logged-in user.
    """
    # 1. Authentication Check
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    # 2. Fetch and sync conversions
    db = get_db()
    sub_id = safe_cast(user.get("sub"), str)

    conversions, pagination = await service.get_conversion_reports(
        db=db,
        page_size=page_size,
        page_num=page_num,
        sub_id=sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )
    return json_response(data=conversions, pagination=pagination)

@router.get("/api/admin/shopee/conversions", response_model=Response[list[Conversion]])
async def get_admin_shopee_conversions(
    request: Request,
    page_size: int = Query(20, ge=1, le=100),
    page_num: int = Query(1, ge=1),
    sub_id: str | None = Query(None),
    purchase_time_s: int = Query(...),
    purchase_time_e: int = Query(...),
) -> JSONResponse:
    """
    Retrieves Shopee conversion reports (Admin only).
    """
    # 1. Authentication and Admin Check
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(ok=False, code="auth_required", status_code=401)

    if user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    # 2. Fetch and sync conversions
    db = get_db()
    conversions, pagination = await service.get_conversion_reports(
        db=db,
        page_size=page_size,
        page_num=page_num,
        sub_id=sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )
    return json_response(data=conversions, pagination=pagination)


@router.post("/api/admin/shopee/conversions/sync")
async def sync_shopee_cashbacks(
    request: Request,
    purchase_time_s: int | None = Query(None),
    purchase_time_e: int | None = Query(None),
    sub_id: str | None = Query(None),
) -> JSONResponse:
    """
    Triggers manual sync of Shopee conversions into the cashback module.
    Only admin users can trigger this.
    """
    user = getattr(request.state, "user", None)
    if not user or user.get("role") != "admin":
        return json_response(ok=False, code="auth_forbidden", status_code=403)

    db = get_db()
    synced_count = await service.sync_shopee_cashbacks(
        db,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
        sub_id=sub_id,
    )
    return json_response(data={"synced_count": synced_count})



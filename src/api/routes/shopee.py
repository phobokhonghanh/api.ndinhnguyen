from fastapi import APIRouter, Request, Query
from fastapi.responses import JSONResponse

from api.helpers import get_model_data
from core.responses import json_response, response
from features.shopee import service
from features.shopee.schemas import (
    AffiliateRequest,
    AffiliateResponseEnvelope,
    AffiliateResponseData,
    ConversionReportEnvelope,
)

router = APIRouter()


@router.post("/api/shopee/affiliate", response_model=AffiliateResponseEnvelope)
async def create_shopee_affiliate(payload: AffiliateRequest) -> JSONResponse:
    """
    Parses a Shopee product link, fetches its metadata, and converts it to a formatted affiliate link.
    """
    # 1. Fetch product info
    product = await service.fetch_prod_alt_by_link(payload.link)

    # 2. Determine link to parse
    link_to_parse = payload.link
    if product is not None and product.productLink:
        link_to_parse = product.productLink

    # 3. Parse link
    try:
        parsed_ids = service.parse_shopee_link(link_to_parse)
        item_id = parsed_ids["item_id"]
        shop_id = parsed_ids["shop_id"]
    except ValueError:
        return json_response(response(False, "shopee_link_invalid"), 400)

    # 4. Create affiliate link
    affiliate_link = service.create_affiliate_link(
        item_id=item_id,
        shop_id=shop_id,
        affiliate_id=payload.affiliate_id,
        sub_ids=payload.sub_ids,
        deep_and_deferred=payload.deep_and_deferred,
    )

    # 5. Serialize response data
    res_data = AffiliateResponseData(affiliate_link=affiliate_link, product=product)

    data_dict = get_model_data(res_data, by_alias=True)

    # 6. Return response
    return json_response(response(True, "ok", data_dict), 200)


@router.get("/api/shopee/conversions", response_model=ConversionReportEnvelope)
async def get_shopee_conversions(
    request: Request,
    page_size: int = Query(20, ge=1, le=100),
    page_num: int = Query(1, ge=1),
    sub_id: str | None = Query(None),
    purchase_time_s: int | None = Query(None),
    purchase_time_e: int | None = Query(None),
) -> JSONResponse:
    """
    Retrieves conversion reports from Shopee Affiliate API.
    Uses request.state.user authenticated by middleware.
    """
    # 1. Authentication Check
    user = getattr(request.state, "user", None)
    if not user:
        return json_response(response(False, "auth_required"), 401)

    # 2. Fetch conversions from service
    result = await service.get_conversion_reports(
        user=user,
        page_size=page_size,
        page_num=page_num,
        sub_id=sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )
    return json_response(result, 200 if result["ok"] else 400)



from fastapi import APIRouter
from fastapi.responses import JSONResponse

from api.helpers import get_model_data
from core.responses import json_response, response
from features.shopee import service
from features.shopee.schemas import AffiliateRequest, AffiliateResponseEnvelope, AffiliateResponseData

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
        deep_and_deferred=payload.deep_and_deferred
    )

    # 5. Serialize response data
    res_data = AffiliateResponseData(
        affiliate_link=affiliate_link,
        product=product
    )

    data_dict = get_model_data(res_data, by_alias=True)

    # 6. Return response
    return json_response(
        response(True, "ok", data_dict),
        200
    )


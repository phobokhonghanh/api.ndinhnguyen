import re
from typing import Any
from core.constants import SHOPEE_AFFILIATE_REDIRECT_TEMPLATE, SHOPEE_PRODUCT_DATA_URL_TEMPLATE, SHOPEE_REPORT_LIST_URL
from core.context import worker_env
from core.settings import AppSettings
from core.responses import response
from infra.http import fetch_json
from features.shopee.schemas import Product, ConversionReportData


def parse_shopee_link(link: str) -> dict[str, str]:
    # Format 1: -i.{item_id}.{shop_id}
    match1 = re.search(r"-i\.(\d+)\.(\d+)", link)
    if match1:
        return {
            "item_id": match1.group(1),
            "shop_id": match1.group(2)
        }

    # Format 2: /product/{item_id}/{shop_id}
    match2 = re.search(r"/product/(\d+)/(\d+)", link)
    if match2:
        return {
            "item_id": match2.group(1),
            "shop_id": match2.group(2)
        }

    raise ValueError("Invalid Shopee link format")


def create_affiliate_link(
    item_id: str,
    shop_id: str,
    affiliate_id: str,
    sub_ids: list[str],
    deep_and_deferred: int = 1
) -> str:
    # limit sub_ids to 5
    sliced_sub_ids = sub_ids[:5]
    joined_sub_ids = "-".join(sliced_sub_ids)
    
    return SHOPEE_AFFILIATE_REDIRECT_TEMPLATE.format(
        item_id=item_id,
        shop_id=shop_id,
        affiliate_id=affiliate_id,
        sub_id=joined_sub_ids,
        deep_and_deferred=deep_and_deferred
    )


async def fetch_prod_alt_by_link(link: str) -> Product | None:
    url = SHOPEE_PRODUCT_DATA_URL_TEMPLATE.format(link=link)
    try:
        data = await fetch_json(url)
        if data.get("status") == "success" and data.get("productInfo") is not None:
            prod_info = data["productInfo"]
            # ProductName and price must be present and not null
            if prod_info.get("productName") and prod_info.get("price") is not None:
                prod_info["dataSource"] = url
                return Product(**prod_info)
    except Exception as e:
        print(f"Error fetching product data: {e}")
    return None


async def fetch_conversion_reports(
    page_size: int = 20,
    page_num: int = 1,
    sub_id: str | None = None,
    purchase_time_s: int | None = None,
    purchase_time_e: int | None = None,
) -> dict[str, Any]:
    """
    Fetches conversion reports from Shopee Affiliate API using configured cookie credentials,
    optionally filtering by sub_id, and purchase timestamp ranges.
    """
    env = worker_env.get(None)
    settings = AppSettings.from_env(env)

    if not settings.shopee_cookie:
        return response(False, "shopee_cookie_missing")

    params = [f"page_size={page_size}", f"page_num={page_num}", "version=1"]
    if sub_id:
        params.append(f"sub_id={sub_id}")
    if purchase_time_s is not None:
        params.append(f"purchase_time_s={purchase_time_s}")
    if purchase_time_e is not None:
        params.append(f"purchase_time_e={purchase_time_e}")

    url = f"{SHOPEE_REPORT_LIST_URL}?{'&'.join(params)}"

    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:152.0) Gecko/20100101 Firefox/152.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://affiliate.shopee.vn/report/conversion_report",
        "Affiliate-Program-Type": "1",
        "Cookie": settings.shopee_cookie,
    }

    try:
        res = await fetch_json(url, headers=headers)
        if res.get("code") != 0 or res.get("msg") != "success":
            return response(False, f"shopee_api_{res.get('msg', 'error')}")

        data = res.get("data", {})
        report_data = ConversionReportData(**data)

        if hasattr(report_data, "model_dump"):
            data_dict = report_data.model_dump()
        else:
            data_dict = report_data.dict()

        return response(True, "ok", data_dict)
    except Exception as e:
        print(f"Error fetching conversion reports: {e}")
        return response(False, "shopee_fetch_failed")


async def get_conversion_reports(
    user: dict[str, Any],
    page_size: int = 20,
    page_num: int = 1,
    sub_id: str | None = None,
    purchase_time_s: int | None = None,
    purchase_time_e: int | None = None,
) -> dict[str, Any]:
    """
    Business layer to retrieve Shopee conversion reports with role-based restrictions.
    Regular users are forced to filter by their own user ID (from JWT 'sub' field).
    """
    is_admin = user.get("role") == "admin"
    if not is_admin:
        query_sub_id = user.get("sub")
    else:
        query_sub_id = sub_id

    return await fetch_conversion_reports(
        page_size=page_size,
        page_num=page_num,
        sub_id=query_sub_id,
        purchase_time_s=purchase_time_s,
        purchase_time_e=purchase_time_e,
    )



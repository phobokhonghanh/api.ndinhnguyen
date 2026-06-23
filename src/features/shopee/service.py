import json
import re
from typing import Any
from features.shopee.schemas import Product


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
    
    return (
        f"https://s.shopee.vn/an_redir"
        f"?origin_link=https://shopee.vn/product/{item_id}/{shop_id}"
        f"&affiliate_id={affiliate_id}"
        f"&sub_id={joined_sub_ids}"
        f"&deep_and_deferred={deep_and_deferred}"
    )


async def fetch_prod_alt_by_link(link: str) -> Product | None:
    url = f"https://data.addlivetag.com/product-data/product-data.php?url={link}"
    try:
        # pyrefly: ignore [missing-import]
        from js import fetch
    except ImportError:
        return None

    try:
        response = await fetch(url)
        if response.status != 200:
            return None
        text = await response.text()
        data = json.loads(text)
        if data.get("status") == "success" and data.get("productInfo") is not None:
            prod_info = data["productInfo"]
            # ProductName and price must be present and not null
            if prod_info.get("productName") and prod_info.get("price") is not None:
                prod_info["dataSource"] = url
                return Product(**prod_info)
    except Exception as e:
        print(f"Error fetching product data: {e}")
    return None

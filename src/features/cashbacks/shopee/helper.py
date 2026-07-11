import re
from typing import TypeVar, Type
from datetime import datetime

from core.constants import (
    SHOPEE_AFFILIATE_REDIRECT_TEMPLATE,
    SHOPEE_PRODUCT_DATA_URL_TEMPLATE,
    SHOPEE_PRODUCT_LINK_TEMPLATE,
    MICRO_UNIT_SCALE,
)
from infra.http import fetch_json
from features.cashbacks.shopee.schemas import Product, Item, Order, Conversion

T = TypeVar('T')

def safe_cast(val: object, target_type: Type[T]) -> T | None:
    if val is None:
        return None
    try:
        return target_type(val)
    except (ValueError, TypeError):
        return None


def convert_micro_to_unit(val: object) -> float | None:
    float_val = safe_cast(val, float)
    if float_val is None:
        return None
    return float_val / MICRO_UNIT_SCALE


def parse_shopee_link(link: str) -> dict[str, str]:
    # Format 1: -i.{shop_id}.{item_id}
    match1 = re.search(r"-i\.(\d+)\.(\d+)", link)
    if match1:
        return {
            "shop_id": match1.group(1),
            "item_id": match1.group(2)
        }

    # Format 2: /product/{shop_id}/{item_id}
    match2 = re.search(r"/product/(\d+)/(\d+)", link)
    if match2:
        return {
            "shop_id": match2.group(1),
            "item_id": match2.group(2)
        }

    raise ValueError("Invalid Shopee link format")

def extract_user_id_from_utm(utm_content: str | None) -> str | None:
    if not utm_content:
        return None
    parts = utm_content.split("-")
    if len(parts) >= 2:
        return parts[1]
    return None


def create_affiliate_link(
    item_id: str,
    shop_id: str,
    affiliate_id: str,
    sub_ids: list[str],
    deep_and_deferred: int = 1
) -> str:
    # limit sub_ids to 5
    joined_sub_ids = "-".join(sub_ids[:5])

    return SHOPEE_AFFILIATE_REDIRECT_TEMPLATE.format(
        item_id=item_id,
        shop_id=shop_id,
        affiliate_id=affiliate_id,
        sub_id=joined_sub_ids,
        deep_and_deferred=deep_and_deferred
    )

def create_product_link(
    shop_id: str,
    item_id: str,
) -> str:
    if not shop_id or not item_id:
        return None
    return SHOPEE_PRODUCT_LINK_TEMPLATE.format(
        shop_id=shop_id,
        item_id=item_id
    )

def format_url_image(url: str | None) -> str | None:
    if not url:
        return url
        
    if url.startswith(('http://', 'https://')):
        return url
        
    return f'https://cf.shopee.vn/file/{url}'

async def fetch_prod_alt_by_link(link: str) -> Product | None:
    url = SHOPEE_PRODUCT_DATA_URL_TEMPLATE.format(link=link)
    try:
        data = await fetch_json(url)
        if data.get("status") == "success" and data.get("productInfo") is not None:
            prod_info = data["productInfo"]
            # ProductName and price must be present and not null
            if prod_info.get("productName") and prod_info.get("price") is not None:
                mapped_info = {
                    "id": safe_cast(prod_info.get("itemId"), str),
                    "name": prod_info.get("productName"),
                    "shop": prod_info.get("shopName"),
                    "price": prod_info.get("price"),
                    "sales": prod_info.get("sales"),
                    "image": format_url_image(prod_info.get("imageUrl")),
                    "link": prod_info.get("productLink"),
                    "rating": float(prod_info["rating"]) if prod_info.get("rating") else None,
                    "commission": float(prod_info["commission"]) if prod_info.get("commission") else None,
                    "lastUpdate": prod_info.get("lastUpdate"),
                    "dataSource": "3rd API",
                }
                return Product(**mapped_info)
    except Exception as e:
        print(f"Error fetching product data: {e}")
    return None



def map_raw_to_schema_conversion(raw: dict[str, object]) -> dict[str, object]:
    # 1. Map orders -> order
    orders_list = []
    raw_orders = raw.get("orders") or []
    for raw_order in raw_orders:
        if not isinstance(raw_order, dict):
            continue
        items_list = []
        raw_items = raw_order.get("items") or []
        for raw_item in raw_items:
            if not isinstance(raw_item, dict):
                continue
                
            product = Product(
                id=safe_cast(raw_item.get("item_id"), str),
                name=safe_cast(raw_item.get("item_name"), str),
                shop=safe_cast(raw_item.get("shop_name"), str),
                price=convert_micro_to_unit(raw_item.get("item_price")),
                sales=safe_cast(raw_item.get("sales"), int),
                image=format_url_image(safe_cast(raw_item.get("img_code"), str)),
                link=create_product_link(
                    shop_id=safe_cast(raw_item.get("shop_id"), str) or "",
                    item_id=safe_cast(raw_item.get("item_id"), str) or ""
                ),
                rating=safe_cast(raw_item.get("rating"), float),
                commission=convert_micro_to_unit(raw_item.get("item_commission")),
                lastUpdate=safe_cast(raw_item.get("lastUpdate"), str) or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                dataSource="Shopee API",
            )
            item = Item(
                product=product,
                qty=safe_cast(raw_item.get("qty"), int),
                actual_amount=convert_micro_to_unit(raw_item.get("actual_amount")),
                is_fraud=safe_cast(raw_item.get("is_fraud"), int),
            )
            items_list.append(item)

        order = Order(
            id=safe_cast(raw_order.get("order_id"), str),
            order_sn=safe_cast(raw_order.get("order_sn"), str),
            items=items_list
        )
        orders_list.append(order)

    conversion = Conversion(
        click_id=safe_cast(raw.get("click_id"), str),
        click_time=safe_cast(raw.get("click_time"), int),
        checkout_id=safe_cast(raw.get("checkout_id"), str),
        purchase_time=safe_cast(raw.get("purchase_time"), int),
        checkout_complete_time=safe_cast(raw.get("checkout_complete_time"), int),
        checkout_status=safe_cast(raw.get("checkout_status"), str),
        affiliate_id=safe_cast(raw.get("affiliate_id"), str),
        affiliate_net_commission=convert_micro_to_unit(raw.get("affiliate_net_commission")),
        utm_content=safe_cast(raw.get("utm_content"), str),
        orders=orders_list
    )
    return conversion.model_dump(by_alias=True)

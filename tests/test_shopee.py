import json
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Create a mock for the "js" module before importing anything that might use it
fake_fetch = AsyncMock()
fake_js = MagicMock()
fake_js.fetch = fake_fetch
sys.modules["js"] = fake_js

from features.cashbacks.shopee import service
from test_api import EnvClient


class MockJSResponse:
    def __init__(self, status, text_data):
        self.status = status
        self._text = text_data

    async def text(self):
        return self._text


def test_parse_shopee_link_format_1():
    # Format 1: -i.{shop_id}.{item_id}
    link = "https://shopee.vn/product-name-i.187103490.12884203570?extraParams=123"
    result = service.parse_shopee_link(link)
    assert result["shop_id"] == "187103490"
    assert result["item_id"] == "12884203570"


def test_parse_shopee_link_format_2():
    # Format 2: /product/{shop_id}/{item_id}
    link = "https://shopee.vn/product/484223682/19785070943"
    result = service.parse_shopee_link(link)
    assert result["shop_id"] == "484223682"
    assert result["item_id"] == "19785070943"


def test_parse_shopee_link_invalid():
    with pytest.raises(ValueError):
        service.parse_shopee_link("https://example.com/not-shopee")


def test_create_affiliate_link():
    # normal
    link = service.create_affiliate_link(
        item_id="12884203570",
        shop_id="187103490",
        affiliate_id="17314780502",
        sub_ids=["localhost01", "tiktok02", "youtube03"]
    )
    assert "https://s.shopee.vn/an_redir" in link
    assert "origin_link=https://shopee.vn/product/187103490/12884203570" in link
    assert "affiliate_id=17314780502" in link
    assert "sub_id=localhost01-tiktok02-youtube03" in link

    # more than 5 sub_ids
    link_capped = service.create_affiliate_link(
        item_id="12884203570",
        shop_id="187103490",
        affiliate_id="17314780502",
        sub_ids=["s1", "s2", "s3", "s4", "s5", "s6"]
    )
    assert "sub_id=s1-s2-s3-s4-s5" in link_capped
    assert "s6" not in link_capped


import asyncio


def test_fetch_prod_alt_by_link_success():
    fake_payload = {
        "status": "success",
        "productInfo": {
            "itemId": 1589295236,
            "productName": "Áo Len Nam Nữ Cổ Lọ",
            "shopName": "DYACI",
            "price": 122200,
            "sales": 990,
            "imageUrl": "https://cf.shopee.vn/file/image",
            "productLink": "https://shopee.vn/product/38003654/1589295236",
            "rating": "4.80",
            "commission": 21996,
            "sellerComFinal": 16497,
            "shopeeComFinal": 5499,
            "isXtra": True,
            "hasSellerCommission": True,
            "hasShopeeCommission": True,
            "isCapped": False,
            "isLimitCap": False,
            "cap": 50000,
            "capRaw": 50000,
            "capAfterRate": 50000,
            "lastUpdate": "2026-03-12 07:39:03",
            "dataSource": "db"
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_payload))

    product = asyncio.run(service.fetch_prod_alt_by_link("https://shopee.vn/product/38003654/1589295236"))
    assert product is not None
    assert product.name == "Áo Len Nam Nữ Cổ Lọ"
    assert product.price == 122200
    assert product.id == "1589295236"


def test_fetch_prod_alt_by_link_failure():
    fake_fetch.return_value = MockJSResponse(404, "Not Found")
    product = asyncio.run(service.fetch_prod_alt_by_link("https://shopee.vn/product/38003654/1589295236"))
    assert product is None


def test_api_shopee_affiliate_success():
    fake_payload = {
        "status": "success",
        "productInfo": {
            "itemId": 1589295236,
            "productName": "Áo Len Nam Nữ Cổ Lọ",
            "price": 122200,
            "productLink": "https://shopee.vn/product/38003654/1589295236"
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_payload))

    with EnvClient() as client:
        response = client.post(
            "/api/shopee/affiliate",
            headers={"Authorization": "Bearer secret"},
            json={
                "link": "https://shopee.vn/product/38003654/1589295236",
                "affiliate_id": "17314780502",
                "sub_ids": ["localhost01", "tiktok02"],
                "deep_and_deferred": 1
            }
        )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["ok"] is True
    assert "affiliate_link" in res_json["data"]
    # Verify the affiliate link got generated with the parsed IDs
    # (Since productLink is "https://shopee.vn/product/38003654/1589295236", it parses 38003654 and 1589295236)
    # Wait, 38003654 -> item_id, 1589295236 -> shop_id
    assert "product/38003654/1589295236" in res_json["data"]["affiliate_link"]
    assert res_json["data"]["product"]["name"] == "Áo Len Nam Nữ Cổ Lọ"


def test_api_shopee_affiliate_invalid_link():
    fake_fetch.return_value = MockJSResponse(404, "Not Found")

    with EnvClient() as client:
        response = client.post(
            "/api/shopee/affiliate",
            headers={"Authorization": "Bearer secret"},
            json={
                "link": "https://example.com/invalid-link",
                "affiliate_id": "17314780502"
            }
        )

    assert response.status_code == 404
    assert response.json()["code"] == "product_not_found"


def test_api_shopee_affiliate_no_auth():
    fake_payload = {
        "status": "success",
        "productInfo": {
            "itemId": 1589295236,
            "productName": "Áo Len Nam Nữ Cổ Lọ",
            "price": 122200,
            "productLink": "https://shopee.vn/product/38003654/1589295236"
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_payload))

    with EnvClient() as client:
        # Request WITHOUT Authorization header
        response = client.post(
            "/api/shopee/affiliate",
            json={
                "link": "https://shopee.vn/product/38003654/1589295236",
                "affiliate_id": "17314780502",
                "sub_ids": ["localhost01", "tiktok02"],
                "deep_and_deferred": 1
            }
        )

    assert response.status_code == 200
    res_json = response.json()
    assert res_json["ok"] is True
    assert "affiliate_link" in res_json["data"]


def test_fetch_conversion_reports_cookie_missing():
    from core.context import worker_env
    from types import SimpleNamespace
    from fastapi import HTTPException
    token = worker_env.set(SimpleNamespace(SHOPEE_COOKIE=""))
    try:
        with pytest.raises(HTTPException) as excinfo:
            asyncio.run(
                service.fetch_conversion_reports()
            )
        assert excinfo.value.status_code == 500
        assert excinfo.value.detail == "shopee_cookie_not_found"
    finally:
        worker_env.reset(token)



def test_fetch_conversion_reports_success():
    from core.context import worker_env
    from types import SimpleNamespace
    token = worker_env.set(SimpleNamespace(SHOPEE_COOKIE="test_cookie"))
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 20,
            "total_count": 1,
            "list": [
                {
                    "purchase_time": 1782402700,
                    "checkout_id": "236101900266795",
                    "checkout_status": "Pending",
                    "checkout_status_app": 0,
                    "checkout_complete_time": 0,
                    "affiliate_id": 17314780502,
                    "affiliate_name": "nguyendeptrai113",
                    "affiliate_net_commission": "3287296000",
                    "utm_content": "ndinhnguyen",
                    "device": "App",
                    "orders": [
                        {
                            "order_id": "236101900261443",
                            "order_status": "PAID",
                            "display_order_status": 1,
                            "complete_time": 0,
                            "fraud_complete_time": 1782434734,
                            "items": [
                                {
                                    "display_item_status": "Pending",
                                    "affiliate_item_status": 1,
                                    "shop_id": 12501250,
                                    "shop_name": "3T Mart",
                                    "item_id": 47500573776,
                                    "item_name": "Bộ vòi xịt",
                                    "item_price": 26900000000,
                                    "item_commission": 3287296000,
                                    "img_code": "img123",
                                    "actual_amount": 82182400000,
                                    "qty": 5,
                                    "is_fraud": 0,
                                    "fraud_reason": "",
                                    "fraud_status": 2,
                                    "platform_commission_rate": 4000,
                                }
                            ],
                        }
                    ],
                }
            ],
        },
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))
    
    try:
        conversions, pagination = asyncio.run(
            service.fetch_conversion_reports(page_size=20, page_num=1)
        )
    finally:
        worker_env.reset(token)
    assert pagination.page == 1
    assert conversions[0].checkout_id == "236101900266795"
    assert conversions[0].orders[0].items[0].product.name == "Bộ vòi xịt"


def test_api_shopee_conversions_unauthenticated():
    from test_cashbacks import CashbackTestClient
    with CashbackTestClient() as client:
        response = client.get("/api/shopee/conversions?purchase_time_s=1782400000&purchase_time_e=1782500000")
    assert response.status_code == 401
    assert response.json()["code"] == "auth_required"


def test_api_shopee_conversions_admin_success():
    from core.auth import generate_jwt
    from test_cashbacks import CashbackTestClient
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 20,
            "total_count": 0,
            "list": [],
        },
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    with CashbackTestClient() as client:
        token = generate_jwt({"sub": "admin_user", "role": "admin"}, "secret_jwt")
        
        response = client.get(
            "/api/admin/shopee/conversions?sub_id=some_user&purchase_time_s=1782400000&purchase_time_e=1782500000",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_api_shopee_conversions_user_success():
    from core.auth import generate_jwt
    from test_cashbacks import CashbackTestClient
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 20,
            "total_count": 0,
            "list": [],
        },
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    with CashbackTestClient() as client:
        token = generate_jwt({"sub": "usr_123", "role": "user"}, "secret_jwt")
        
        response = client.get(
            "/api/shopee/conversions?purchase_time_s=1782400000&purchase_time_e=1782500000",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
        # Try to access admin endpoint -> 403
        response_forbidden = client.get(
            "/api/admin/shopee/conversions?purchase_time_s=1782400000&purchase_time_e=1782500000",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response_forbidden.status_code == 403
    
    call_args = fake_fetch.call_args[0][0]
    assert "sub_id=usr_123" in call_args


def test_api_shopee_conversions_admin_forces_personal_sub_id():
    from core.auth import generate_jwt
    from test_cashbacks import CashbackTestClient
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 20,
            "total_count": 0,
            "list": [],
        },
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    with CashbackTestClient() as client:
        token = generate_jwt({"sub": "admin_user", "role": "admin"}, "secret_jwt")
        
        response = client.get(
            "/api/shopee/conversions?purchase_time_s=1782400000&purchase_time_e=1782500000",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True
        
    call_args = fake_fetch.call_args[0][0]
    assert "sub_id=admin_user" in call_args

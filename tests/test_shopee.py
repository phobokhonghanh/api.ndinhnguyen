import json
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

# Create a mock for the "js" module before importing anything that might use it
fake_fetch = AsyncMock()
fake_js = MagicMock()
fake_js.fetch = fake_fetch
sys.modules["js"] = fake_js

from features.shopee import service
from test_api import EnvClient


class MockJSResponse:
    def __init__(self, status, text_data):
        self.status = status
        self._text = text_data

    async def text(self):
        return self._text


def test_parse_shopee_link_format_1():
    # Format 1: -i.{item_id}.{shop_id}
    link = "https://shopee.vn/product-name-i.187103490.12884203570?extraParams=123"
    result = service.parse_shopee_link(link)
    assert result["item_id"] == "187103490"
    assert result["shop_id"] == "12884203570"


def test_parse_shopee_link_format_2():
    # Format 2: /product/{item_id}/{shop_id}
    link = "https://shopee.vn/product/484223682/19785070943"
    result = service.parse_shopee_link(link)
    assert result["item_id"] == "484223682"
    assert result["shop_id"] == "19785070943"


def test_parse_shopee_link_invalid():
    with pytest.raises(ValueError):
        service.parse_shopee_link("https://example.com/not-shopee")


def test_create_affiliate_link():
    # normal
    link = service.create_affiliate_link(
        item_id="187103490",
        shop_id="12884203570",
        affiliate_id="17314780502",
        sub_ids=["localhost01", "tiktok02", "youtube03"]
    )
    assert "https://s.shopee.vn/an_redir" in link
    assert "origin_link=https://shopee.vn/product/187103490/12884203570" in link
    assert "affiliate_id=17314780502" in link
    assert "sub_id=localhost01-tiktok02-youtube03" in link

    # more than 5 sub_ids
    link_capped = service.create_affiliate_link(
        item_id="187103490",
        shop_id="12884203570",
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
    assert product.productName == "Áo Len Nam Nữ Cổ Lọ"
    assert product.price == 122200
    assert product.itemId == 1589295236


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
    assert res_json["data"]["product"]["productName"] == "Áo Len Nam Nữ Cổ Lọ"


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

    assert response.status_code == 400
    assert response.json()["code"] == "shopee_link_invalid"


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


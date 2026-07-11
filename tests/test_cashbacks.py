import json
import sqlite3
import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from core.context import worker_env
from core.auth import generate_jwt
from test_shopee import fake_fetch, MockJSResponse


class MockD1Result:
    def __init__(self, results):
        self.results = results


class MockD1Statement:
    def __init__(self, db, sql):
        self.db = db
        self.sql = sql
        self.bindings = ()

    def bind(self, *args):
        self.bindings = args
        return self

    async def first(self):
        cursor = self.db.conn.cursor()
        cursor.execute(self.sql, self.bindings)
        row = cursor.fetchone()
        if row is None:
            return None
        col_names = [description[0] for description in cursor.description]
        return dict(zip(col_names, row))

    async def all(self):
        cursor = self.db.conn.cursor()
        cursor.execute(self.sql, self.bindings)
        rows = cursor.fetchall()
        col_names = [description[0] for description in cursor.description]
        results = [dict(zip(col_names, r)) for r in rows]
        return MockD1Result(results)

    async def run(self):
        cursor = self.db.conn.cursor()
        cursor.execute(self.sql, self.bindings)
        self.db.conn.commit()


class MockD1DB:
    def __init__(self):
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL UNIQUE,
            name TEXT,
            picture TEXT,
            role TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS cashbacks (
          id TEXT PRIMARY KEY,
          user_id TEXT NOT NULL,
          platform TEXT NOT NULL,
          cashback_amount REAL NOT NULL,
          status TEXT NOT NULL DEFAULT 'Pending',
          checkout_id TEXT NOT NULL,
          conversion TEXT NOT NULL,
          created_at TEXT DEFAULT CURRENT_TIMESTAMP,
          updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
          FOREIGN KEY(user_id) REFERENCES users(id)
        );
        """)
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_cashbacks_platform_checkout ON cashbacks(platform, checkout_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cashbacks_user_id ON cashbacks(user_id);")
        self.conn.commit()


    def prepare(self, sql):
        return MockD1Statement(self, sql)


class CashbackTestClient:
    def __init__(self):
        self.db = MockD1DB()
        # Seed users to pass foreign key constraint
        cursor = self.db.conn.cursor()
        cursor.execute("INSERT INTO users (id, email, role) VALUES ('usr_123', 'u1@test.com', 'user')")
        cursor.execute("INSERT INTO users (id, email, role) VALUES ('usr_456', 'u2@test.com', 'user')")
        cursor.execute("INSERT INTO users (id, email, role, name) VALUES ('system', 'system@ndinhnguyen.com', 'admin', 'System Account')")
        self.db.conn.commit()

        self.env = SimpleNamespace(
            ADMIN_TOKEN="secret_admin",
            JWT_SECRET="secret_jwt",
            ALLOWED_ORIGINS="https://frontend.pages.dev,http://localhost:3000",
            DB=self.db,
            ENVIRONMENT="production",
            SHOPEE_COOKIE="test_cookie",
            COMMISSION_RATE=0.5
        )

    def __enter__(self):
        self.token = worker_env.set(self.env)
        self.client = TestClient(app)
        return self.client

    def __exit__(self, *_args):
        worker_env.reset(self.token)


def test_get_cashbacks_unauthenticated():
    with CashbackTestClient() as client:
        response = client.get("/api/cashbacks")
    assert response.status_code == 401
    assert response.json()["code"] == "auth_required"


def test_get_cashbacks_authenticated_empty():
    with CashbackTestClient() as client:
        token = generate_jwt({"sub": "usr_123", "email": "u1@test.com", "role": "user"}, "secret_jwt")
        response = client.get(
            "/api/cashbacks",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 200
    res_json = response.json()
    assert res_json["ok"] is True
    assert res_json["data"] == []
    assert res_json["pagination"]["total"] == 0
    assert res_json["pagination"]["page"] == 1


def test_sync_unauthenticated():
    with CashbackTestClient() as client:
        response = client.post("/api/admin/shopee/conversions/sync")
    assert response.status_code == 401
    assert response.json()["code"] == "auth_invalid"


def test_sync_non_admin():
    with CashbackTestClient() as client:
        token = generate_jwt({"sub": "usr_123", "email": "u1@test.com", "role": "user"}, "secret_jwt")
        response = client.post(
            "/api/admin/shopee/conversions/sync",
            headers={"Authorization": f"Bearer {token}"}
        )
    assert response.status_code == 403
    assert response.json()["code"] == "auth_forbidden"


def test_sync_admin_and_verify_cashback_flows():
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 100,
            "total_count": 2,
            "list": [
                {
                    "purchase_time": 1782402700,
                    "checkout_id": "checkout_abc",
                    "checkout_status": "Pending",
                    "affiliate_id": 17314780502,
                    "affiliate_net_commission": 200000,
                    "utm_content": "some-usr_123",
                    "orders": [
                        {
                            "order_id": 111,
                            "order_sn": "order_111",
                            "items": [
                                {
                                     "item_name": "Product A",
                                     "item_commission": 200000,
                                     "actual_amount": 1000000,
                                     "item_price": 1000000,
                                     "is_fraud": 0,
                                     "platform_commission_rate": 2000,
                                }
                            ]
                        }
                    ]
                },
                {
                    "purchase_time": 1782402800,
                    "checkout_id": "checkout_xyz",
                    "checkout_status": "Completed",
                    "affiliate_id": 17314780502,
                    "affiliate_net_commission": 400000,
                    "utm_content": "some-usr_456",
                    "orders": [
                        {
                            "order_id": 222,
                            "order_sn": "order_222",
                            "items": [
                                {
                                     "item_name": "Product B",
                                     "item_commission": 400000,
                                     "actual_amount": 2000000,
                                     "item_price": 2000000,
                                     "is_fraud": 0,
                                     "platform_commission_rate": 4000,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    with CashbackTestClient() as client:
        # 1. Sync cashbacks as admin
        sync_res = client.post(
            "/api/admin/shopee/conversions/sync",
            headers={"Authorization": "Bearer secret_admin"}
        )
        assert sync_res.status_code == 200
        assert sync_res.json()["ok"] is True
        assert sync_res.json()["data"]["synced_count"] == 2

        # 2. Verify usr_123 sees their pending cashback
        u1_token = generate_jwt({"sub": "usr_123", "email": "u1@test.com", "role": "user"}, "secret_jwt")
        res1 = client.get(
            "/api/cashbacks",
            headers={"Authorization": f"Bearer {u1_token}"}
        )
        assert res1.status_code == 200
        data1 = res1.json()["data"]
        assert len(data1) == 1
        assert data1[0]["status"] == "Pending"
        assert data1[0]["conversion"]["orders"][0]["order_sn"] == "order_111"
        assert data1[0]["conversion"]["checkout_status"] == "Pending"
        assert data1[0]["cashback"] == 1.0  # 2.0 * 0.5
        assert data1[0]["conversion"]["orders"][0]["items"][0]["actual_amount"] == 10.0
        assert len(data1[0]["conversion"]["orders"][0]["items"]) == 1
        assert data1[0]["conversion"]["orders"][0]["items"][0]["product"]["name"] == "Product A"
        assert data1[0]["conversion"]["orders"][0]["items"][0]["product"]["commission"] == 2.0
        assert data1[0]["conversion"]["orders"][0]["items"][0]["product"]["price"] == 10.0

        # 3. Verify usr_456 sees their approved cashback
        u2_token = generate_jwt({"sub": "usr_456", "email": "u2@test.com", "role": "user"}, "secret_jwt")
        res2 = client.get(
            "/api/cashbacks",
            headers={"Authorization": f"Bearer {u2_token}"}
        )
        assert res2.status_code == 200
        data2 = res2.json()["data"]
        assert len(data2) == 1
        assert data2[0]["status"] == "Completed"
        assert data2[0]["conversion"]["orders"][0]["order_sn"] == "order_222"
        assert data2[0]["conversion"]["checkout_status"] == "Completed"
        assert data2[0]["cashback"] == 2.0  # 400000 / 100000 * 0.5
        assert len(data2[0]["conversion"]["orders"][0]["items"]) == 1
        assert data2[0]["conversion"]["orders"][0]["items"][0]["product"]["name"] == "Product B"

        # 4. Sync again with updated status for checkout_abc
        fake_report_update = {
            "code": 0,
            "msg": "success",
            "data": {
                "page_num": 1,
                "page_size": 100,
                "total_count": 1,
                "list": [
                    {
                        "purchase_time": 1782402700,
                        "checkout_id": "checkout_abc",
                        "checkout_status": "Completed", # Status changed to Completed
                        "affiliate_id": 17314780502,
                        "affiliate_net_commission": 200000,
                        "utm_content": "some-usr_123",
                        "orders": [
                            {
                                "order_id": 111,
                                "order_sn": "order_111",
                                "items": [
                                    {
                                         "item_name": "Product A",
                                         "item_commission": 200000,
                                         "actual_amount": 1000000,
                                         "item_price": 1000000,
                                         "is_fraud": 0,
                                         "platform_commission_rate": 2000,
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        }
        fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report_update))

        sync_res2 = client.post(
            "/api/admin/shopee/conversions/sync",
            headers={"Authorization": "Bearer secret_admin"}
        )
        assert sync_res2.status_code == 200

        # 5. Verify status updated for usr_123
        res3 = client.get(
            "/api/cashbacks",
            headers={"Authorization": f"Bearer {u1_token}"}
        )
        assert res3.status_code == 200
        data3 = res3.json()["data"]
        assert len(data3) == 1
        assert data3[0]["status"] == "Completed"
        assert data3[0]["conversion"]["orders"][0]["order_sn"] == "order_111"
        assert data3[0]["conversion"]["checkout_status"] == "Completed"



def test_sync_with_sub_id():
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 100,
            "total_count": 0,
            "list": []
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    with CashbackTestClient() as client:
        response = client.post(
            "/api/admin/shopee/conversions/sync?sub_id=usr_123",
            headers={"Authorization": "Bearer secret_admin"}
        )
        assert response.status_code == 200
        assert response.json()["ok"] is True

        # Verify that fetch_json was called with sub_id=usr_123 in the request URL
        call_args = fake_fetch.call_args[0][0]
        assert "sub_id=usr_123" in call_args


def test_get_admin_cashbacks():
    tc = CashbackTestClient()
    with tc as client:
        # Seed cashbacks for usr_123 and usr_456
        cursor = tc.db.conn.cursor()
        cursor.execute("INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion) VALUES ('cb1', 'usr_123', 'shopee', 1.5, 'Pending', 'chk1', '{}')")
        cursor.execute("INSERT INTO cashbacks (id, user_id, platform, cashback_amount, status, checkout_id, conversion) VALUES ('cb2', 'usr_456', 'shopee', 2.5, 'Completed', 'chk2', '{}')")
        tc.db.conn.commit()


        # Admin token
        admin_token = generate_jwt({"sub": "admin_user", "role": "admin"}, "secret_jwt")

        # 1. Admin gets all cashbacks
        res = client.get(
            "/api/admin/cashbacks",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        res_json = res.json()
        assert res_json["ok"] is True
        assert len(res_json["data"]) == 2
        assert res_json["pagination"]["total"] == 2

        # 2. Admin filters by userId=usr_123
        res = client.get(
            "/api/admin/cashbacks?userId=usr_123",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert res.status_code == 200
        res_json = res.json()
        assert len(res_json["data"]) == 1
        assert res_json["data"][0]["id"] == "cb1"
        assert res_json["pagination"]["total"] == 1

        # 3. Regular user is forbidden from admin endpoint
        user_token = generate_jwt({"sub": "usr_123", "email": "u1@test.com", "role": "user"}, "secret_jwt")
        res = client.get(
            "/api/admin/cashbacks",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert res.status_code == 403


def test_sync_with_missing_user_id_fallback():
    fake_report = {
        "code": 0,
        "msg": "success",
        "data": {
            "page_num": 1,
            "page_size": 100,
            "total_count": 1,
            "list": [
                {
                    "purchase_time": 1782402700,
                    "checkout_id": "checkout_fallback_abc",
                    "checkout_status": "Pending",
                    "affiliate_id": 17314780502,
                    "affiliate_net_commission": 200000,
                    "utm_content": "ndinhnguyen",  # No User ID in UTM
                    "orders": [
                        {
                            "order_id": 111,
                            "order_sn": "order_111",
                            "items": [
                                {
                                     "item_name": "Product A",
                                     "item_commission": 200000,
                                     "actual_amount": 1000000,
                                     "item_price": 1000000,
                                     "is_fraud": 0,
                                     "platform_commission_rate": 2000,
                                }
                            ]
                        }
                    ]
                }
            ]
        }
    }
    fake_fetch.return_value = MockJSResponse(200, json.dumps(fake_report))

    tc = CashbackTestClient()
    with tc as client:
        # Sync cashbacks as admin
        sync_res = client.post(
            "/api/admin/shopee/conversions/sync",
            headers={"Authorization": "Bearer secret_admin"}
        )
        assert sync_res.status_code == 200
        assert sync_res.json()["ok"] is True
        assert sync_res.json()["data"]["synced_count"] == 1

        # Verify that "system" user exists in database and owns the synced cashback
        cursor = tc.db.conn.cursor()
        cursor.execute("SELECT user_id, checkout_id FROM cashbacks WHERE checkout_id = 'checkout_fallback_abc'")
        row = cursor.fetchone()
        assert row is not None
        assert row[0] == "system"

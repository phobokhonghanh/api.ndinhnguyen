import asyncio
import time
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from app import app
from core.context import worker_env
from core.auth import generate_jwt, verify_jwt
from features.users import repository as user_repo


# =====================================================================
# 1. JWT Unit Tests
# =====================================================================


def test_jwt_encode_decode():
    secret = "mysecretkey"
    payload = {"sub": "123", "email": "test@test.com", "role": "admin"}
    token = generate_jwt(payload, secret)

    decoded = verify_jwt(token, secret)
    assert decoded is not None
    assert decoded["sub"] == "123"
    assert decoded["email"] == "test@test.com"
    assert decoded["role"] == "admin"


def test_jwt_invalid_secret():
    secret = "mysecretkey"
    payload = {"sub": "123"}
    token = generate_jwt(payload, secret)

    decoded = verify_jwt(token, "wrongsecret")
    assert decoded is None


def test_jwt_expired():
    secret = "mysecretkey"
    payload = {"sub": "123", "exp": time.time() - 10}  # Expired 10 seconds ago
    token = generate_jwt(payload, secret)

    decoded = verify_jwt(token, secret)
    assert decoded is None


def test_jwt_malformed():
    assert verify_jwt("not.a.token", "secret") is None
    assert verify_jwt("not.a.token.with.three.parts", "secret") is None


# =====================================================================
# 2. Database Repository Mock & Unit Tests
# =====================================================================


class MockD1Statement:
    def __init__(self, db, sql):
        self.db = db
        self.sql = sql
        self.bindings = ()

    def bind(self, *args):
        self.bindings = args
        return self

    async def first(self):
        if "FROM users" in self.sql:
            email_param = self.bindings[0] if self.bindings else None
            for row in self.db.tables["users"]:
                if row["email"] == email_param or row["id"] == email_param:
                    return row
        return None

    async def run(self):
        if "INSERT INTO users" in self.sql:
            id_val, email, name, picture, role = self.bindings
            self.db.tables["users"].append(
                {
                    "id": id_val,
                    "email": email,
                    "name": name,
                    "picture": picture,
                    "role": role,
                    "created_at": "2026-07-01",
                    "updated_at": "2026-07-01",
                }
            )
        elif "UPDATE users" in self.sql:
            name, picture, role, id_val = self.bindings
            for row in self.db.tables["users"]:
                if row["id"] == id_val:
                    row["name"] = name
                    row["picture"] = picture
                    row["role"] = role
                    row["updated_at"] = "2026-07-01"


class MockD1DB:
    def __init__(self):
        self.tables = {"users": []}

    def prepare(self, sql):
        return MockD1Statement(self, sql)


def test_user_repository_crud():
    db = MockD1DB()

    # Get non-existing user
    user = asyncio.run(user_repo.get_user_by_email(db, "nonexistent@example.com"))
    assert user is None

    # Create user
    created = asyncio.run(
        user_repo.create_or_update_user(
            db, "admin@test.com", "Admin User", "avatar.png", "admin"
        )
    )
    assert created["email"] == "admin@test.com"
    assert created["role"] == "admin"
    assert created["name"] == "Admin User"
    assert created["picture"] == "avatar.png"
    assert "id" in created

    # Fetch created user
    fetched = asyncio.run(user_repo.get_user_by_email(db, "admin@test.com"))
    assert fetched is not None
    assert fetched["id"] == created["id"]
    assert fetched["role"] == "admin"

    # Update existing user
    updated = asyncio.run(
        user_repo.create_or_update_user(
            db, "admin@test.com", "Updated Admin", "new_avatar.png", "user"
        )
    )
    assert updated["id"] == created["id"]
    assert updated["name"] == "Updated Admin"
    assert updated["role"] == "user"

    # Fetch again to verify updates
    fetched_updated = asyncio.run(user_repo.get_user_by_email(db, "admin@test.com"))
    assert fetched_updated["name"] == "Updated Admin"
    assert fetched_updated["role"] == "user"


# =====================================================================
# 3. API & Middleware Integration Tests
# =====================================================================


class AuthEnvClient:
    def __init__(self):
        self.db = MockD1DB()
        self.env = SimpleNamespace(
            ADMIN_TOKEN="admin-static-token",
            ALLOWED_ORIGINS="https://frontend.pages.dev,http://localhost:3000",
            DB=self.db,
            ENVIRONMENT="production",
            JWT_SECRET="mysecretjwtkeylongerthan32charsfordev",
            GOOGLE_CLIENT_ID="google-client-id",
            ADMIN_EMAIL="admin@test.com",
        )

    def __enter__(self):
        self.token = worker_env.set(self.env)
        self.client = TestClient(app)
        return self.client, self.db, self.env

    def __exit__(self, *_args):
        worker_env.reset(self.token)


@patch("features.users.service.fetch_json", new_callable=AsyncMock)
def test_api_login_admin(mock_fetch):
    mock_fetch.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-id-1",
        "aud": "google-client-id",
        "email": "admin@test.com",
        "email_verified": "true",
        "name": "Admin User",
        "picture": "admin.png",
        "exp": str(time.time() + 3600),
    }

    with AuthEnvClient() as (client, db, _env):
        response = client.post(
            "/api/auth/google/login", json={"id_token": "valid-token"}
        )

        assert response.status_code == 200
        res_json = response.json()
        assert res_json["ok"] is True
        assert "token" in res_json["data"]
        assert res_json["data"]["user"]["role"] == "admin"
        assert res_json["data"]["user"]["email"] == "admin@test.com"

        # Verify user is saved in DB
        db_user = asyncio.run(user_repo.get_user_by_email(db, "admin@test.com"))
        assert db_user is not None
        assert db_user["role"] == "admin"


@patch("features.users.service.fetch_json", new_callable=AsyncMock)
def test_api_login_regular_user(mock_fetch):
    mock_fetch.return_value = {
        "iss": "https://accounts.google.com",
        "sub": "google-id-2",
        "aud": "google-client-id",
        "email": "user@test.com",
        "email_verified": True,
        "name": "Regular User",
        "picture": "user.png",
        "exp": str(time.time() + 3600),
    }

    with AuthEnvClient() as (client, db, _env):
        response = client.post(
            "/api/auth/google/login", json={"id_token": "valid-token"}
        )

        assert response.status_code == 200
        res_json = response.json()
        assert res_json["ok"] is True
        assert res_json["data"]["user"]["role"] == "user"

        # Verify saved user
        db_user = asyncio.run(user_repo.get_user_by_email(db, "user@test.com"))
        assert db_user is not None
        assert db_user["role"] == "user"


@patch("features.users.service.fetch_json", new_callable=AsyncMock)
def test_api_login_failures(mock_fetch):
    with AuthEnvClient() as (client, _db, _env):
        # 1. Invalid token info (unfetchable)
        mock_fetch.side_effect = Exception("failed to fetch")
        response = client.post(
            "/api/auth/google/login", json={"id_token": "invalid-token"}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "auth_invalid_google_token"

        # Reset side_effect for other tests
        mock_fetch.side_effect = None

        # 2. Issuer mismatch
        mock_fetch.return_value = {
            "iss": "wrong-issuer.com",
            "sub": "id",
            "aud": "google-client-id",
            "email": "user@test.com",
            "email_verified": True,
        }
        response = client.post(
            "/api/auth/google/login", json={"id_token": "token"}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "auth_invalid_issuer"

        # 3. Audience mismatch
        mock_fetch.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "id",
            "aud": "wrong-client-id",
            "email": "user@test.com",
            "email_verified": True,
        }
        response = client.post(
            "/api/auth/google/login", json={"id_token": "token"}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "auth_audience_mismatch"

        # 4. Email not verified
        mock_fetch.return_value = {
            "iss": "https://accounts.google.com",
            "sub": "id",
            "aud": "google-client-id",
            "email": "user@test.com",
            "email_verified": "false",
        }
        response = client.post(
            "/api/auth/google/login", json={"id_token": "token"}
        )
        assert response.status_code == 400
        assert response.json()["code"] == "auth_email_not_verified"



def test_secured_routes_middleware_authorizations(monkeypatch):
    # Mock bookmarks service to avoid hitting actual database categories/bookmarks queries
    async def fake_get_bookmarks_dashboard(*_args, **_kwargs):
        return {"ok": True, "code": "ok", "data": []}

    monkeypatch.setattr(
        "api.routes.bookmarks.service.get_bookmarks_dashboard",
        fake_get_bookmarks_dashboard,
    )

    with AuthEnvClient() as (client, _db, env):
        # 1. Access with static admin token -> Succeeds
        response = client.get(
            "/api/bookmarks", headers={"Authorization": "Bearer admin-static-token"}
        )
        assert response.status_code == 200

        # 2. Access with Admin JWT -> Succeeds
        admin_jwt = generate_jwt(
            {
                "sub": "admin-id",
                "email": "admin@test.com",
                "role": "admin",
                "exp": time.time() + 3600,
            },
            env.JWT_SECRET,
        )
        response = client.get(
            "/api/bookmarks", headers={"Authorization": f"Bearer {admin_jwt}"}
        )
        assert response.status_code == 200

        # 3. Access with Regular User JWT -> 403 Forbidden
        user_jwt = generate_jwt(
            {
                "sub": "user-id",
                "email": "user@test.com",
                "role": "user",
                "exp": time.time() + 3600,
            },
            env.JWT_SECRET,
        )
        response = client.get(
            "/api/bookmarks", headers={"Authorization": f"Bearer {user_jwt}"}
        )
        assert response.status_code == 403
        assert response.json()["code"] == "auth_forbidden"

        # 4. Access with Expired JWT -> 401 Unauthorized
        expired_jwt = generate_jwt(
            {
                "sub": "admin-id",
                "email": "admin@test.com",
                "role": "admin",
                "exp": time.time() - 10,
            },
            env.JWT_SECRET,
        )
        response = client.get(
            "/api/bookmarks", headers={"Authorization": f"Bearer {expired_jwt}"}
        )
        assert response.status_code == 401
        assert response.json()["code"] == "auth_invalid"

        # 5. Access with No Authorization -> 401 Unauthorized
        response = client.get("/api/bookmarks")
        assert response.status_code == 401
        assert response.json()["code"] == "auth_invalid"


def test_logout():
    with AuthEnvClient() as (client, _db, _env):
        response = client.post("/api/auth/google/logout")
        assert response.status_code == 200
        assert response.json()["ok"] is True

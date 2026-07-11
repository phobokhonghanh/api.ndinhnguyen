import time
from typing import Any

from core.constants import GOOGLE_TOKENINFO_URL_TEMPLATE
from core.auth import generate_jwt
from core.responses import Response
from core.settings import AppSettings
from infra.http import fetch_json
from features.users import repository as user_repo
from features.users.schemas import User, LoginResponseData


async def google_login(db: Any, settings: AppSettings, id_token: str) -> Response[LoginResponseData]:
    url = GOOGLE_TOKENINFO_URL_TEMPLATE.format(id_token=id_token)
    try:
        token_info = await fetch_json(url)
    except Exception as e:
        print(f"Failed to fetch Google token info: {e}")
        return Response(ok=False, code="auth_invalid_google_token")

    # 1. Verify Issuer
    iss = token_info.get("iss", "")
    if iss not in ("accounts.google.com", "https://accounts.google.com"):
        return Response(ok=False, code="auth_invalid_issuer")

    # 2. Verify Audience (GOOGLE_CLIENT_ID)
    aud = token_info.get("aud", "")
    if settings.environment != "development" and aud != settings.google_client_id:
        return Response(ok=False, code="auth_audience_mismatch")

    # 3. Check Expiry
    exp_str = token_info.get("exp")
    if exp_str:
        try:
            if float(exp_str) < time.time():
                return Response(ok=False, code="auth_token_expired")
        except ValueError:
            pass

    # 4. Verify Email
    email = token_info.get("email", "")
    email_verified = token_info.get("email_verified")
    is_verified = (
        email_verified == "true"
        or email_verified is True
        or token_info.get("email_verified") is True
    )
    if not email or not is_verified:
        return Response(ok=False, code="auth_email_not_verified")

    # Determine role based on ADMIN_EMAIL
    role = "user"
    if settings.admin_email and email == settings.admin_email:
        role = "admin"

    name = token_info.get("name", "")
    picture = token_info.get("picture", "")

    # Save to user database
    try:
        user = await user_repo.create_or_update_user(db, email, name, picture, role)
    except Exception as e:
        print(f"Failed to create/update user in db: {e}")
        return Response(ok=False, code="auth_database_error")

    # Issue Session JWT
    session_payload = {
        "sub": user["id"],
        "email": user["email"],
        "role": user["role"],
        "exp": int(time.time()) + (7 * 24 * 60 * 60),  # 7 days
    }
    session_token = generate_jwt(session_payload, settings.jwt_secret)

    user_schema = User(
        id=user["id"],
        email=user["email"],
        name=user.get("name"),
        picture=user.get("picture"),
        role=user["role"],
        createdAt=user.get("createdAt"),
        updatedAt=user.get("updatedAt"),
    )
    login_data = LoginResponseData(token=session_token, user=user_schema)

    return Response(ok=True, code="ok", data=login_data)



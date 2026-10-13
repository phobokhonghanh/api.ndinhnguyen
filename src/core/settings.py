from dataclasses import dataclass
from typing import Any


def env_value(env: Any, key: str, default: str = "") -> str:
    value = getattr(env, key, default)
    return str(value) if value is not None else default


@dataclass(frozen=True)
class AppSettings:
    admin_token: str = ""
    allowed_origins: frozenset[str] = frozenset()
    environment: str = "production"
    jwt_secret: str = ""
    google_client_id: str = ""
    admin_email: str = ""
    shopee_cookie: str = ""
    commission_rate: float = 0.5
    payment_min_amount: float = 50000.0
    addlivetag_api_key: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    telegram_thread_id: str = ""

    @classmethod
    def from_env(cls, env: Any) -> "AppSettings":
        origins = {
            item.strip()
            for item in env_value(env, "ALLOWED_ORIGINS").split(",")
            if item.strip()
        }
        
        rate_val = getattr(env, "COMMISSION_RATE", None)
        try:
            commission_rate = float(rate_val) if rate_val is not None else 0.5
        except (ValueError, TypeError):
            commission_rate = 0.5

        min_amt_val = getattr(env, "PAYMENT_MIN_AMOUNT", None)
        try:
            payment_min_amount = float(min_amt_val) if min_amt_val is not None else 50000.0
        except (ValueError, TypeError):
            payment_min_amount = 50000.0

        addlivetag_api_key = env_value(env, "ADDLIVETAG_API_KEY")

        return cls(
            admin_token=env_value(env, "ADMIN_TOKEN"),
            allowed_origins=frozenset(origins),
            environment=env_value(env, "ENVIRONMENT", "production"),
            jwt_secret=env_value(env, "JWT_SECRET"),
            google_client_id=env_value(env, "GOOGLE_CLIENT_ID"),
            admin_email=env_value(env, "ADMIN_EMAIL"),
            shopee_cookie=env_value(env, "SHOPEE_COOKIE"),
            commission_rate=commission_rate,
            payment_min_amount=payment_min_amount,
            addlivetag_api_key=addlivetag_api_key,
            telegram_bot_token=env_value(env, "TELEGRAM_BOT_TOKEN"),
            telegram_chat_id=env_value(env, "TELEGRAM_CHAT_ID"),
            telegram_thread_id=env_value(env, "TELEGRAM_THREAD_ID"),
        )


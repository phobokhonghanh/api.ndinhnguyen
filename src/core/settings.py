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

    @classmethod
    def from_env(cls, env: Any) -> "AppSettings":
        origins = {
            item.strip()
            for item in env_value(env, "ALLOWED_ORIGINS").split(",")
            if item.strip()
        }
        return cls(
            admin_token=env_value(env, "ADMIN_TOKEN"),
            allowed_origins=frozenset(origins),
            environment=env_value(env, "ENVIRONMENT", "production"),
        )

from types import SimpleNamespace

from api.middleware import PUBLIC_API_PATHS
from core.settings import AppSettings, env_value


def test_env_value_returns_default_for_missing_or_none():
    env = SimpleNamespace(CONFIGURED="value", EMPTY=None)

    assert env_value(env, "CONFIGURED", "default") == "value"
    assert env_value(env, "EMPTY", "default") == "default"
    assert env_value(env, "MISSING", "default") == "default"


def test_app_settings_parses_allowed_origins():
    settings = AppSettings.from_env(
        SimpleNamespace(
            ADMIN_TOKEN="secret",
            ALLOWED_ORIGINS="https://a.example, https://b.example ,,",
        )
    )

    assert settings.admin_token == "secret"
    assert settings.allowed_origins == frozenset(
        {"https://a.example", "https://b.example"}
    )


def test_stats_is_the_only_public_api_path():
    assert PUBLIC_API_PATHS == {"/api/stats"}

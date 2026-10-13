import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from core.context import worker_env
from infra.telegram import TelegramClient, send_telegram_notification


def test_telegram_client_is_configured():
    # Not configured when tokens are missing
    client_empty = TelegramClient(bot_token="", chat_id="")
    assert not client_empty.is_configured

    # Configured when both are present
    client_ready = TelegramClient(bot_token="bot123", chat_id="chat456")
    assert client_ready.is_configured


def test_telegram_send_message_skipped_if_unconfigured():
    client = TelegramClient(bot_token="", chat_id="")
    res = asyncio.run(client.send_message(text="hello"))
    assert res is None

    client_no_chat = TelegramClient(bot_token="bot123", chat_id="")
    res2 = asyncio.run(client_no_chat.send_message(text="hello"))
    assert res2 is None


def test_telegram_send_message_success():
    client = TelegramClient(bot_token="123456:ABC-DEF", chat_id="-100123456789", thread_id="99")

    fake_response = {"ok": True, "result": {"message_id": 999}}

    with patch("infra.telegram.post_json", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = fake_response

        res = asyncio.run(
            client.send_message(
                text="<b>Test notification</b>",
                parse_mode="HTML",
            )
        )

        assert res == fake_response
        mock_post.assert_called_once_with(
            "https://api.telegram.org/bot123456:ABC-DEF/sendMessage",
            data={
                "chat_id": "-100123456789",
                "message_thread_id": 99,
                "text": "<b>Test notification</b>",
                "disable_web_page_preview": True,
                "parse_mode": "HTML",
            },
        )


def test_telegram_send_message_handles_exception():
    client = TelegramClient(bot_token="123456:ABC-DEF", chat_id="-100123456789")

    with patch("infra.telegram.post_json", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = RuntimeError("Network error")

        res = asyncio.run(client.send_message(text="Fail message"))
        assert res is None


def test_send_telegram_notification_helper():
    token = worker_env.set(
        SimpleNamespace(
            TELEGRAM_BOT_TOKEN="my_token",
            TELEGRAM_CHAT_ID="my_chat_id",
            TELEGRAM_THREAD_ID="123",
        )
    )
    try:
        with patch("infra.telegram.post_json", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"ok": True}
            success = asyncio.run(send_telegram_notification("Alert!"))
            assert success is True
            payload = mock_post.call_args.kwargs["data"]
            assert payload["message_thread_id"] == 123

            mock_post.return_value = {"ok": False, "description": "Bad Request"}
            failure = asyncio.run(send_telegram_notification("Alert!"))
            assert failure is False
    finally:
        worker_env.reset(token)


def test_get_env_telegram():
    from api.helpers import get_env_telegram

    token = worker_env.set(
        SimpleNamespace(
            TELEGRAM_BOT_TOKEN="tok123",
            TELEGRAM_CHAT_ID="chat123",
            TELEGRAM_THREAD_ID="thread456",
        )
    )
    try:
        bot_token, chat_id, thread_id = get_env_telegram()
        assert bot_token == "tok123"
        assert chat_id == "chat123"
        assert thread_id == "thread456"
    finally:
        worker_env.reset(token)


def test_http_error_exception():
    from infra.http import HttpError

    err = HttpError(404, "https://example.com/not-found")
    assert err.status == 404
    assert err.url == "https://example.com/not-found"
    assert "HTTP error 404 for https://example.com/not-found" in str(err)
    assert isinstance(err, RuntimeError)


def test_format_error_content_system_short():
    from infra.telegram import format_error_content

    short_msg = "Database connection error on payment record 123"
    assert format_error_content(short_msg, is_external=False) == short_msg


def test_format_error_content_system_long():
    from infra.telegram import format_error_content

    # 25 words
    long_msg = "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty twentyone twentytwo twentythree twentyfour twentyfive"
    result = format_error_content(long_msg, is_external=False, max_words=20)
    assert result.endswith("...")
    # First 20 words plus ...
    assert len(result.removesuffix("...").split()) == 20
    assert result == "one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty..."


def test_format_error_content_external_json():
    from infra.telegram import format_error_content

    data = {"status": "error", "message": "Invalid cookie", "code": 10001}
    result = format_error_content(data, is_external=True)
    assert json.loads(result) == data


def test_build_error_message_format():
    from infra.telegram import build_error_message

    msg = build_error_message(
        feature="Shopee Sync",
        code=502,
        content={"code": 10001, "msg": "cookie expired"},
        is_external=True,
        timestamp="2026-10-13 15:00:00",
    )
    assert msg.startswith("2026-10-13 15:00:00-Shopee Sync-502-")
    assert '{"code": 10001, "msg": "cookie expired"}' in msg


def test_notify_telegram_error():
    from infra.telegram import notify_telegram_error

    token = worker_env.set(
        SimpleNamespace(
            TELEGRAM_BOT_TOKEN="my_token",
            TELEGRAM_CHAT_ID="my_chat_id",
        )
    )
    try:
        with patch("infra.telegram.post_json", new_callable=AsyncMock) as mock_post:
            mock_post.return_value = {"ok": True}

            success = asyncio.run(
                notify_telegram_error(
                    feature="Product",
                    code=500,
                    content="Crash processing product item",
                    is_external=False,
                )
            )
            assert success is True
            last_call = mock_post.call_args
            payload = last_call.kwargs["data"]
            assert payload["chat_id"] == "my_chat_id"
            assert "-Product-500-Crash processing product item" in payload["text"]
            assert "parse_mode" not in payload  # Sent as plain text
    finally:
        worker_env.reset(token)


def test_dispatch_telegram_error():
    from infra.telegram import dispatch_telegram_error, telegram_error_notified

    token = worker_env.set(
        SimpleNamespace(
            TELEGRAM_BOT_TOKEN="my_token",
            TELEGRAM_CHAT_ID="my_chat_id",
        )
    )
    try:
        telegram_error_notified.set(False)

        async def run_dispatch():
            with patch("infra.telegram.post_json", new_callable=AsyncMock) as mock_post:
                mock_post.return_value = {"ok": True}
                success = await dispatch_telegram_error(
                    feature="Shopee Sync",
                    code=502,
                    content={"error": "sync failed"},
                    is_external=True,
                )
                assert success is True
                assert telegram_error_notified.get() is True
                assert mock_post.called

        asyncio.run(run_dispatch())
    finally:
        worker_env.reset(token)

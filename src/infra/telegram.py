from contextvars import ContextVar
from datetime import datetime, timezone, timedelta
import json
import logging
from typing import Any

from api.helpers import get_env_telegram
from core.constants import TELEGRAM_SEND_MESSAGE_URL_TEMPLATE
from infra.http import post_json

logger = logging.getLogger(__name__)

telegram_error_notified: ContextVar[bool] = ContextVar("telegram_error_notified", default=False)


class TelegramClient:
    """
    Client for interacting with the Telegram Bot API.
    """

    def __init__(
        self,
        bot_token: str | None = None,
        chat_id: str | None = None,
        thread_id: int | str | None = None,
    ):
        env_token, env_chat_id, env_thread_id = get_env_telegram()
        self.bot_token = bot_token or env_token
        self.chat_id = chat_id or env_chat_id
        self.thread_id = thread_id if thread_id is not None else env_thread_id

    @property
    def is_configured(self) -> bool:
        """
        Checks if both the bot token and default chat ID are configured.
        """
        return bool(self.bot_token and self.chat_id)

    async def send_message(
        self,
        text: str,
        chat_id: str | None = None,
        thread_id: int | str | None = None,
        parse_mode: str | None = "HTML",
        disable_web_page_preview: bool = True,
    ) -> dict[str, Any] | None:
        """
        Sends a message to a Telegram chat / topic thread.
        If the bot token or chat ID is not configured, logs a warning and returns None.
        """
        token = self.bot_token
        target_chat_id = chat_id or self.chat_id
        target_thread_id = thread_id if thread_id is not None else self.thread_id

        if not token:
            logger.warning("Telegram notification skipped: TELEGRAM_BOT_TOKEN is not configured.")
            return None

        if not target_chat_id:
            logger.warning("Telegram notification skipped: chat_id is not configured.")
            return None

        url = TELEGRAM_SEND_MESSAGE_URL_TEMPLATE.format(token=token)
        payload: dict[str, Any] = {
            "chat_id": target_chat_id,
            "text": text,
            "disable_web_page_preview": disable_web_page_preview,
        }
        if target_thread_id:
            try:
                payload["message_thread_id"] = int(target_thread_id)
            except (ValueError, TypeError):
                payload["message_thread_id"] = target_thread_id

        if parse_mode:
            payload["parse_mode"] = parse_mode

        try:
            return await post_json(url, data=payload)
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return None


async def send_telegram_notification(
    text: str,
    chat_id: str | None = None,
    thread_id: int | str | None = None,
    parse_mode: str | None = "HTML",
) -> bool:
    """
    Convenience function to send a Telegram notification using default configured settings.
    Returns True if message was sent successfully, False otherwise.
    """
    client = TelegramClient()
    res = await client.send_message(
        text=text,
        chat_id=chat_id,
        thread_id=thread_id,
        parse_mode=parse_mode,
    )
    return bool(res and res.get("ok"))


def format_error_content(content: Any, is_external: bool = False, max_words: int = 20) -> str:
    """
    Formats the error content.
    - If is_external is True (Shopee, Addlivetag): formats as JSON string.
    - Otherwise (System, Product): truncates to max_words words and appends '...' if exceeded.
    """
    if is_external:
        if isinstance(content, (dict, list)):
            return json.dumps(content, ensure_ascii=False)
        return str(content)

    text = str(content).strip()
    words = text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words]) + "..."
    return text


def build_error_message(
    feature: str,
    code: int | str,
    content: Any,
    is_external: bool = False,
    timestamp: str | None = None,
) -> str:
    """
    Builds the standardized error notification message:
    <time>-<chức năng>-<code>-<content>
    Defaults to GMT+7 timestamp if not provided.
    """
    vn_tz = timezone(timedelta(hours=7))
    time_str = timestamp or datetime.now(vn_tz).strftime("%Y-%m-%d %H:%M:%S")
    formatted_content = format_error_content(content, is_external=is_external)
    return f"{time_str}-{feature}-{code}-{formatted_content}"


async def notify_telegram_error(
    feature: str,
    code: int | str,
    content: Any,
    is_external: bool = False,
    chat_id: str | None = None,
    thread_id: int | str | None = None,
) -> bool:
    """
    Formats and sends an error notification to Telegram.
    Uses plain text (parse_mode=None) to prevent formatting errors with arbitrary JSON/code traces.
    """
    message = build_error_message(
        feature=feature,
        code=code,
        content=content,
        is_external=is_external,
    )
    telegram_error_notified.set(True)
    return await send_telegram_notification(
        text=message,
        chat_id=chat_id,
        thread_id=thread_id,
        parse_mode=None,
    )


def dispatch_telegram_error(
    feature: str,
    code: int | str,
    content: Any,
    is_external: bool = False,
    chat_id: str | None = None,
    thread_id: int | str | None = None,
) -> Any:
    """
    Dispatches a Telegram error notification as a non-blocking background task.
    Returns the task if an event loop is available, else None.
    """
    telegram_error_notified.set(True)
    import asyncio
    try:
        loop = asyncio.get_running_loop()
        return loop.create_task(
            notify_telegram_error(
                feature=feature,
                code=code,
                content=content,
                is_external=is_external,
                chat_id=chat_id,
                thread_id=thread_id,
            )
        )
    except RuntimeError:
        return None

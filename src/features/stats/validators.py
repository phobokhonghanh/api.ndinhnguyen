import re

from .constants import (
    ALLOWED_STATS_PRODUCTS,
    MAX_RUNTIME_FILE_SIZE,
    MAX_RUNTIME_ID_LENGTH,
    MAX_RUNTIME_LINES,
)
from .errors import StatsValidationError


SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")


def validate_safe_id(value: str, error_code: str) -> str:
    candidate = value.strip()
    if not candidate or len(candidate) > MAX_RUNTIME_ID_LENGTH:
        raise StatsValidationError(error_code)
    if not SAFE_ID.fullmatch(candidate):
        raise StatsValidationError(error_code)
    return candidate


def validate_product(product: str) -> str:
    candidate = product.strip()
    if candidate not in ALLOWED_STATS_PRODUCTS:
        raise StatsValidationError("stats_product_invalid")
    return candidate


def validate_runtime_bytes(content: bytes) -> None:
    if len(content) > MAX_RUNTIME_FILE_SIZE:
        raise StatsValidationError("stats_file_too_large")
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise StatsValidationError("stats_file_invalid_utf8") from exc
    line_count = text.count("\n") + (1 if text and not text.endswith("\n") else 0)
    if line_count > MAX_RUNTIME_LINES:
        raise StatsValidationError("stats_file_too_many_lines")

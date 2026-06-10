from contextvars import ContextVar
from typing import Any


worker_env: ContextVar[Any] = ContextVar("worker_env")

"""Bounded retry classification for safe read-only API operations."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def is_retryable(error: BaseException) -> bool:
    """Retry only transport/5xx/429 failures, never auth or malformed requests."""
    status = getattr(error, "status_code", None)
    code = str(getattr(error, "code", "")).upper()
    if status in {408, 429} or isinstance(status, int) and status >= 500:
        return True
    if any(token in code for token in ("LOGIN", "AUTH", "PERMISSION", "ENTITLEMENT")):
        return False
    return isinstance(error, (TimeoutError, ConnectionError, OSError))


def call_with_retries(operation: Callable[[], T], retries: int = 2, sleep: Callable[[float], None] | None = None) -> T:
    """Execute an operation with at most ``retries`` bounded retries."""
    if retries < 0:
        raise ValueError("retries cannot be negative")
    sleeper = sleep or __import__("time").sleep
    attempt = 0
    while True:
        try:
            return operation()
        except Exception as error:
            if attempt >= retries or not is_retryable(error):
                raise
            sleeper(0.25 * (2**attempt))
            attempt += 1

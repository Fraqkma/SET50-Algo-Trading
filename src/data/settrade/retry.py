"""Bounded retry classification for safe read-only API operations."""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from .resilience import FailureKind, classify_failure

T = TypeVar("T")


def is_retryable(error: BaseException) -> bool:
    """Retry transport/server/rate-limit failures, never auth or bad requests."""
    response = getattr(error, "response", None)
    status = getattr(error, "status_code", None) or getattr(response, "status_code", None)
    code = str(getattr(error, "code", "")).upper()
    if status in {408, 429} or isinstance(status, int) and status >= 500:
        return True
    if any(token in code for token in ("LOGIN", "AUTH", "PERMISSION", "ENTITLEMENT")) or status in {400, 401, 403, 404}:
        return False
    return classify_failure(error) in {FailureKind.NETWORK_FAILURE, FailureKind.RATE_LIMIT}


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

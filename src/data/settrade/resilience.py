"""Deterministic failure classification, state transitions, and retry timing."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import StrEnum


class FailureKind(StrEnum):
    AUTH_FAILURE = "AUTH_FAILURE"
    NETWORK_FAILURE = "NETWORK_FAILURE"
    RATE_LIMIT = "RATE_LIMIT"
    API_FAILURE = "API_FAILURE"


class CollectorState(StrEnum):
    STARTING = "STARTING"
    LIVE = "LIVE"
    DEGRADED = "DEGRADED"
    OFFLINE = "OFFLINE"
    RECONNECTING = "RECONNECTING"
    RECOVERED = "RECOVERED"
    MARKET_CLOSED = "MARKET_CLOSED"
    STOPPED = "STOPPED"
    ERROR = "ERROR"


def classify_failure(error: BaseException) -> FailureKind:
    """Classify common SDK transport, auth, and rate-limit failures safely."""
    response = getattr(error, "response", None)
    status = getattr(error, "status_code", None) or getattr(response, "status_code", None)
    code = str(getattr(error, "code", "")).upper()
    message = f"{code} {error}".lower()
    if status == 429 or "rate limit" in message or "too many requests" in message:
        return FailureKind.RATE_LIMIT
    if any(token in message for token in ("unauthorized", "authentication", "auth failure", "invalid credential", "token expired", "permission denied", "login failed", "forbidden")) or status in {401, 403}:
        return FailureKind.AUTH_FAILURE
    if isinstance(error, (TimeoutError, ConnectionError, OSError)) or any(token in message for token in ("dns", "name resolution", "connection reset", "connection refused", "network is unreachable", "temporary failure", "websocket")):
        return FailureKind.NETWORK_FAILURE
    return FailureKind.API_FAILURE


def retry_delay_seconds(attempt: int, *, base: float = 5.0, cap: float = 60.0) -> float:
    """Return capped exponential backoff for 1-based retry attempt numbers."""
    if attempt < 1:
        raise ValueError("attempt must be at least 1")
    if base < 0 or cap < 0:
        raise ValueError("backoff values cannot be negative")
    return min(cap, base * 2 ** (attempt - 1))


class CollectorStateTracker:
    """Keep a timestamped local audit trail of collector state changes."""

    def __init__(self) -> None:
        self.state = CollectorState.STARTING
        self.transitions: list[dict[str, str]] = []
        self.transition(CollectorState.STARTING, "RUNNER_STARTED")

    def transition(self, state: CollectorState | str, reason: str) -> dict[str, str]:
        next_state = CollectorState(state)
        event = {"timestamp_utc": datetime.now(timezone.utc).isoformat(), "state": next_state.value, "reason": str(reason)}
        self.state = next_state
        self.transitions.append(event)
        return event

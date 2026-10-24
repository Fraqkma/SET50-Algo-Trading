from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from src.data.settrade.automation import (
    AlreadyRunningError,
    SingleInstanceLock,
    classify_market_window,
    request_stop,
    stop_requested,
)
from src.data.settrade.resilience import (
    CollectorState,
    CollectorStateTracker,
    FailureKind,
    classify_failure,
    retry_delay_seconds,
)
from src.data.settrade.retry import call_with_retries, is_retryable


def test_market_window_handles_weekend_and_api_holiday() -> None:
    saturday = datetime.fromisoformat("2026-09-19T10:00:00+07:00")
    weekday = datetime.fromisoformat("2026-09-21T10:00:00+07:00")
    assert classify_market_window(saturday).reason == "WEEKEND"
    holiday = classify_market_window(weekday, "Close")
    assert holiday.state == "CLOSED"
    assert holiday.reason == "API_CLOSED_OR_HOLIDAY"


def test_stale_preopen_status_cannot_keep_runner_alive_after_session() -> None:
    late = datetime.fromisoformat("2026-09-21T23:28:00+07:00")
    window = classify_market_window(late, "Pre-open")
    assert window.state == "CLOSED"
    assert window.reason == "OUTSIDE_SET_SESSION"


def test_lock_blocks_live_owner_and_recovers_stale(tmp_path: Path) -> None:
    path = tmp_path / "daily.lock"
    first = SingleInstanceLock(path)
    first.acquire()
    try:
        with pytest.raises(AlreadyRunningError, match="ALREADY_RUNNING"):
            SingleInstanceLock(path).acquire()
    finally:
        first.release()

    path.write_text(json.dumps({"pid": 2_147_483_647}), encoding="utf-8")
    recovered = SingleInstanceLock(path)
    recovered.acquire()
    recovered.release()
    assert not path.exists()


def test_stop_request_targets_current_owner(tmp_path: Path) -> None:
    lock = tmp_path / "daily.lock"
    stop = tmp_path / "daily.stop"
    owner = SingleInstanceLock(lock)
    owner.acquire()
    try:
        assert request_stop(lock, stop)
        assert stop_requested(stop, os.getpid())
    finally:
        owner.release()


def test_daily_runner_parses_json_stdout_separately_from_collector_stderr(monkeypatch) -> None:
    import scripts.run_settrade_daily as daily

    class CompletedProcess:
        returncode = 0

        def communicate(self, timeout=None):
            return '{"orders_placed": 0, "status": "SUCCESS", "rows_1m": 1}', "INFO collector diagnostic\n"

    monkeypatch.setattr(daily.subprocess, "Popen", lambda *args, **kwargs: CompletedProcess())
    ok, result = daily._collector_cycle(2)
    assert ok is True
    assert result["status"] == "SUCCESS"
    assert result["orders_placed"] == 0


def test_failure_classifier_separates_auth_network_rate_limit_and_api() -> None:
    class HttpError(RuntimeError):
        def __init__(self, status_code: int, message: str) -> None:
            super().__init__(message)
            self.status_code = status_code

    assert classify_failure(TimeoutError("request timed out")) == FailureKind.NETWORK_FAILURE
    assert classify_failure(HttpError(429, "rate limited")) == FailureKind.RATE_LIMIT
    assert classify_failure(HttpError(401, "unauthorized")) == FailureKind.AUTH_FAILURE
    assert classify_failure(ValueError("invalid response schema")) == FailureKind.API_FAILURE


def test_retry_backoff_is_exponential_and_bounded() -> None:
    assert [retry_delay_seconds(attempt) for attempt in (1, 2, 3, 4, 20)] == [5, 10, 20, 40, 60]


def test_auth_failure_is_never_retried() -> None:
    error = RuntimeError("authentication failed: invalid credentials")
    assert is_retryable(error) is False
    calls = 0

    def operation():
        nonlocal calls
        calls += 1
        raise error

    with pytest.raises(RuntimeError, match="authentication failed"):
        call_with_retries(operation, retries=4, sleep=lambda _seconds: None)
    assert calls == 1


def test_network_failure_retries_then_recovers_without_losing_caller_state() -> None:
    calls = 0
    delays: list[float] = []
    checkpoint = {"last_timestamp": "2026-10-21T03:00:00+00:00"}

    def operation() -> str:
        nonlocal calls
        calls += 1
        if calls < 3:
            raise ConnectionError("connection reset")
        return "reconnected"

    assert call_with_retries(operation, retries=2, sleep=delays.append) == "reconnected"
    assert calls == 3
    assert delays == [0.25, 0.5]
    assert checkpoint["last_timestamp"] == "2026-10-21T03:00:00+00:00"


def test_collector_state_transitions_are_timestamped_and_recovery_aware() -> None:
    tracker = CollectorStateTracker()
    tracker.transition(CollectorState.DEGRADED, "NETWORK_FAILURE")
    tracker.transition(CollectorState.OFFLINE, "transport unavailable")
    tracker.transition(CollectorState.RECONNECTING, "backoff elapsed")
    tracker.transition(CollectorState.RECOVERED, "fresh session and subscriptions restored")
    assert [item["state"] for item in tracker.transitions] == ["STARTING", "DEGRADED", "OFFLINE", "RECONNECTING", "RECOVERED"]
    assert all(item["timestamp_utc"].endswith("+00:00") for item in tracker.transitions)

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

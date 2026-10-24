from __future__ import annotations

import json
import subprocess

import pytest

import scripts.run_settrade_daily as daily


def test_health_accepts_valid_check_that_takes_longer_than_old_timeout(monkeypatch) -> None:
    result = {"source": "settrade", "checkpoints": {"candles": {"status": "OK"}}}

    def slow_health(*_args, timeout: int, **_kwargs):
        # Model the observed 40–45 second health command without making the
        # regression test wait: this command only completes with >=45 seconds.
        if timeout < 45:
            raise subprocess.TimeoutExpired("health", timeout)
        return subprocess.CompletedProcess("health", 0, stdout=json.dumps(result), stderr="")

    monkeypatch.setattr(daily.subprocess, "run", slow_health)

    assert daily._health() == result


def test_health_timeout_can_be_configured_and_is_bounded(monkeypatch) -> None:
    monkeypatch.setenv("SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS", "90")
    assert daily._health_check_timeout_seconds() == 90
    monkeypatch.setenv("SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS", "5")
    assert daily._health_check_timeout_seconds() == 45
    monkeypatch.setenv("SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS", "9999")
    assert daily._health_check_timeout_seconds() == 300
    monkeypatch.setenv("SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS", "bad")
    assert daily._health_check_timeout_seconds() == 60


def test_health_preserves_nonzero_exit_even_with_valid_json(monkeypatch) -> None:
    completed = subprocess.CompletedProcess("health", 1, stdout='{"filesystem_error":"disk"}', stderr="disk check failed")
    monkeypatch.setattr(daily.subprocess, "run", lambda *_args, **_kwargs: completed)

    with pytest.raises(subprocess.CalledProcessError) as error:
        daily._health()

    assert error.value.returncode == 1


def test_health_invalid_json_is_a_failure(monkeypatch) -> None:
    completed = subprocess.CompletedProcess("health", 0, stdout="not-json", stderr="")
    monkeypatch.setattr(daily.subprocess, "run", lambda *_args, **_kwargs: completed)

    with pytest.raises(RuntimeError, match="not valid JSON"):
        daily._health()

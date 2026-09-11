from __future__ import annotations

import pandas as pd
import pytest

from src.strategies.timing import next_trading_session, rebalance_dates


def test_rebalance_schedule_uses_every_three_observed_trading_rows() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05", "2024-01-08", "2024-01-09", "2024-01-10", "2024-01-11"])
    assert list(rebalance_dates(dates)) == list(pd.to_datetime(["2024-01-02", "2024-01-08", "2024-01-11"]))


def test_next_session_is_strictly_after_signal_date() -> None:
    dates = pd.to_datetime(["2024-01-02", "2024-01-03", "2024-01-05"])
    assert next_trading_session("2024-01-03", dates) == pd.Timestamp("2024-01-05")


def test_next_session_requires_a_future_observed_row() -> None:
    with pytest.raises(ValueError, match="No next trading session"):
        next_trading_session("2024-01-05", pd.to_datetime(["2024-01-02", "2024-01-05"]))

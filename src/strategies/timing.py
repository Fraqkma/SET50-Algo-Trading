"""Deterministic schedule and signal/execution timing helpers."""

from __future__ import annotations

from datetime import date, datetime
from typing import Iterable

import pandas as pd


def rebalance_dates(
    trading_dates: Iterable[pd.Timestamp | date | datetime | str],
    *,
    every_n_trading_days: int = 3,
) -> tuple[pd.Timestamp, ...]:
    """Return an anchored schedule using every third observed trading row.

    The first sorted unique date is the anchor; subsequent rebalance dates are
    positions 3, 6, 9, ... in that same observed calendar.  This helper only
    schedules dates and does not infer missing sessions or fill gaps.
    """
    if not isinstance(every_n_trading_days, int) or every_n_trading_days < 1:
        raise ValueError("every_n_trading_days must be a positive integer.")
    dates = pd.DatetimeIndex(pd.to_datetime(list(trading_dates), errors="raise")).sort_values().unique()
    return tuple(dates[::every_n_trading_days])


def next_trading_session(
    signal_date: pd.Timestamp | date | datetime | str,
    trading_dates: Iterable[pd.Timestamp | date | datetime | str],
) -> pd.Timestamp:
    """Resolve the first observed trading row strictly after ``signal_date``."""
    target = pd.Timestamp(signal_date)
    dates = pd.DatetimeIndex(pd.to_datetime(list(trading_dates), errors="raise")).sort_values().unique()
    later = dates[dates > target]
    if len(later) == 0:
        raise ValueError("No next trading session exists after signal_date.")
    return later[0]

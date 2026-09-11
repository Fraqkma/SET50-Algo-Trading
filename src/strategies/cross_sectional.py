"""Small, optional cross-sectional component for the time-series baseline.

This module ranks only rows supplied by callers that loaded data through the
approved research path.  It is a selector, not a portfolio or backtest
engine: execution timing, sizing, and order constraints remain downstream.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Mapping, Protocol

import pandas as pd

from src.data.eligibility import EligibilityDecision, MarketDataEligibilityGate
from .baseline import BaselineStrategy


class _GateLike(Protocol):
    def assess(self, symbol: str, requested_date: date) -> EligibilityDecision: ...


def rank_time_series_candidates(
    feature_frames: Mapping[str, pd.DataFrame],
    as_of: str | date | datetime,
    *,
    top_n: int,
    gate: _GateLike | None = None,
) -> pd.DataFrame:
    """Apply the baseline filter, then rank eligible stocks by momentum.

    ``feature_frames`` must contain features produced from approved daily data.
    The gate is consulted again for ``(symbol, as_of)`` so historical SET50
    membership and exact approved-date boundaries remain enforced.  Only the
    single row at ``as_of`` is inspected; no later row can affect the result.
    Ties are resolved deterministically by normalized symbol.
    """
    if not isinstance(top_n, int) or top_n < 1:
        raise ValueError("top_n must be a positive integer.")
    target = _as_date(as_of)
    eligibility = gate or MarketDataEligibilityGate()
    baseline = BaselineStrategy()
    records: list[dict[str, object]] = []
    for raw_symbol, frame in feature_frames.items():
        symbol = str(raw_symbol).strip().upper()
        decision = eligibility.assess(symbol, target)
        if not decision.eligible:
            continue
        if frame is None or frame.empty:
            continue
        indexed = frame.copy()
        if not isinstance(indexed.index, pd.DatetimeIndex):
            indexed.index = pd.to_datetime(indexed.index, errors="raise")
        row_matches = indexed.loc[indexed.index.date == target]
        if len(row_matches) != 1:
            continue
        row = row_matches.iloc[[0]]
        signal = baseline.generate_signal(row).iloc[0]
        if signal != "BUY":
            continue
        records.append(
            {
                "symbol": symbol,
                "momentum_20": float(row.iloc[0]["momentum_20"]),
                "trend_20_50": _optional_float(row.iloc[0], "trend_20_50"),
                "volatility_20": _optional_float(row.iloc[0], "volatility_20"),
                "signal": signal,
            }
        )
    ranked = pd.DataFrame(records, columns=["symbol", "momentum_20", "trend_20_50", "volatility_20", "signal"])
    if ranked.empty:
        ranked["rank"] = pd.Series(dtype="int64")
        return ranked
    ranked = ranked.sort_values(["momentum_20", "symbol"], ascending=[False, True], kind="mergesort").reset_index(drop=True)
    ranked["rank"] = ranked.index + 1
    return ranked.head(top_n).reset_index(drop=True)


def _optional_float(row: pd.Series, column: str) -> float | None:
    value = row.get(column)
    return None if pd.isna(value) else float(value)


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())

from __future__ import annotations

from datetime import date

import pandas as pd

from src.strategies.research_candidates import select_candidate


class _Eligible:
    def assess(self, symbol: str, requested_date: date):
        from src.data.eligibility import EligibilityDecision
        return EligibilityDecision(symbol, requested_date, True, None)


def test_breakout_uses_prior_high_and_signal_date_only() -> None:
    index = pd.date_range("2025-01-01", periods=22, freq="B")
    frame = pd.DataFrame({
        "high": [10.0] * 21 + [11.0],
        "close": [9.0] * 21 + [10.5],
        "volume_ratio_20": [1.0] * 22,
    }, index=index)
    selected = select_candidate("CANDIDATE_BREAKOUT20", {"AAA": frame}, index[-1], _Eligible(), 10)
    assert selected == ["AAA"]


def test_breakout_does_not_use_future_highs() -> None:
    index = pd.date_range("2025-01-01", periods=23, freq="B")
    frame = pd.DataFrame({"high": [10.0] * 21 + [11.0, 100.0], "close": [9.0] * 21 + [10.5, 100.0], "volume_ratio_20": [1.0] * 23}, index=index)
    selected = select_candidate("CANDIDATE_BREAKOUT20", {"AAA": frame}, index[-2], _Eligible(), 10)
    assert selected == ["AAA"]


def test_mean_reversion_requires_past_sma_and_pullback() -> None:
    index = pd.date_range("2025-01-01", periods=60, freq="B")
    adjusted = [120.0] * 59 + [112.0]
    frame = pd.DataFrame({"adjusted_close": adjusted, "close": [110.0] * 60, "sma_50": [105.0] * 60}, index=index)
    assert select_candidate("CANDIDATE_MEANREV5", {"AAA": frame}, index[-1], _Eligible(), 10) == ["AAA"]

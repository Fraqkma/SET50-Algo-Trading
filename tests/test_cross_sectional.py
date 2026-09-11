from __future__ import annotations

from datetime import date

import pandas as pd

from src.strategies.cross_sectional import rank_time_series_candidates


class _ApprovedGate:
    def assess(self, symbol: str, requested_date: date):
        return type("Decision", (), {"eligible": symbol != "EXCLUDED"})()


class _DateMembershipGate:
    def assess(self, symbol: str, requested_date: date):
        return type("Decision", (), {"eligible": requested_date == date(2024, 1, 10)})()


def _frame(momentum: float, *, future: float | None = None) -> pd.DataFrame:
    index = pd.to_datetime(["2024-01-10", "2024-01-11"])
    rows = pd.DataFrame(
        {
            "close": [110.0, 111.0 if future is None else future],
            "momentum_20": [momentum, momentum],
            "sma_20": [100.0, 100.0],
            "trend_20_50": [0.1, 0.1],
            "volatility_20": [0.02, 0.02],
        },
        index=index,
    )
    return rows


def test_ranker_applies_time_series_filter_then_momentum_rank() -> None:
    result = rank_time_series_candidates(
        {"AAA": _frame(0.10), "BBB": _frame(0.20), "EXCLUDED": _frame(0.90)},
        "2024-01-10",
        top_n=1,
        gate=_ApprovedGate(),
    )
    assert list(result["symbol"]) == ["BBB"]
    assert list(result["rank"]) == [1]


def test_ranker_is_deterministic_for_ties_and_excludes_non_buy_rows() -> None:
    weak = _frame(-0.10)
    result = rank_time_series_candidates(
        {"BBB": _frame(0.20), "AAA": _frame(0.20), "WEAK": weak},
        date(2024, 1, 10),
        top_n=5,
        gate=_ApprovedGate(),
    )
    assert list(result["symbol"]) == ["AAA", "BBB"]
    assert len(result) < 5


def test_ranker_does_not_use_future_rows() -> None:
    original = {"AAA": _frame(0.10)}
    changed_future = {"AAA": _frame(0.10, future=10_000.0)}
    first = rank_time_series_candidates(original, "2024-01-10", top_n=10, gate=_ApprovedGate())
    second = rank_time_series_candidates(changed_future, "2024-01-10", top_n=10, gate=_ApprovedGate())
    pd.testing.assert_frame_equal(first, second)


def test_ranker_respects_date_specific_historical_membership() -> None:
    frames = {"AAA": _frame(0.10)}
    assert not rank_time_series_candidates(frames, "2024-01-11", top_n=10, gate=_DateMembershipGate()).size
    assert rank_time_series_candidates(frames, "2024-01-10", top_n=10, gate=_DateMembershipGate()).iloc[0]["symbol"] == "AAA"

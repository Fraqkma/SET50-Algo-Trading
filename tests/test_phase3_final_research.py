from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.research.phase3_final import (
    holm_adjust,
    g1_promotion_gate,
    prepare_daily_features,
    rolling_benchmark_drawdowns,
    summarize_risk_envelope,
    two_way_pigeonhole_bootstrap,
)


def _bars() -> pd.DataFrame:
    index = pd.bdate_range("2026-01-01", periods=70)
    close = pd.Series(np.linspace(10, 12, len(index)), index=index)
    return pd.DataFrame({
        "open": close - .05, "high": close + .1, "low": close - .1,
        "close": close, "volume": np.arange(len(index)) + 100,
    }, index=index)


def test_daily_features_are_causal_at_each_row() -> None:
    original = _bars()
    changed = original.copy()
    changed.iloc[55:, changed.columns.get_loc("close")] *= 3
    left = prepare_daily_features(original)
    right = prepare_daily_features(changed)
    pd.testing.assert_series_equal(left.loc[:original.index[54], "momentum20"], right.loc[:original.index[54], "momentum20"])
    pd.testing.assert_series_equal(left.loc[:original.index[54], "prior20_high"], right.loc[:original.index[54], "prior20_high"])


def test_rolling_drawdown_and_prior_regime_exclude_window_future() -> None:
    closes = [100, 95, 97, 90, 92, 91, 99, 101]
    frame = pd.DataFrame({"Date": pd.bdate_range("2025-01-01", periods=len(closes)), "Close": closes})
    windows = rolling_benchmark_drawdowns(frame, window_sessions=3, prior_regime_sessions=2)
    assert windows.iloc[0].benchmark_mdd == pytest.approx(0.05)
    assert windows.iloc[0].prior_regime == "UNKNOWN"
    assert windows.iloc[3].prior_regime_return == pytest.approx(97 / 100 - 1)
    envelope = summarize_risk_envelope(windows)
    assert envelope["window_count"] == len(closes) - 2
    assert envelope["mdd_scenarios"][4]["provisional_research_buffer"] == envelope["mdd_scenarios"][4]["benchmark_mdd"] * .75


def test_cluster_bootstrap_is_deterministic_and_holm_is_monotone() -> None:
    values = [0.01, -0.01, 0.02, 0.03, -0.02, 0.04]
    dates = ["d1", "d1", "d2", "d2", "d3", "d3"]
    symbols = ["a", "b", "a", "b", "a", "b"]
    first = two_way_pigeonhole_bootstrap(values, dates, symbols, replications=1000, seed=7)
    second = two_way_pigeonhole_bootstrap(values, dates, symbols, replications=1000, seed=7)
    assert first == second
    adjusted = holm_adjust({"a": .01, "b": .04, "c": None})
    assert adjusted == {"a": .02, "b": .04, "c": None}


def test_g1_gate_rejects_weak_or_inadequate_evidence() -> None:
    adequate = {"matched_events": 100, "symbols": 18, "dates": 100, "holm_adjusted_p": .01}
    assert not g1_promotion_gate(**adequate, ci95=[-.001, .01])
    assert not g1_promotion_gate(**{**adequate, "holm_adjusted_p": 1.0}, ci95=[.001, .01])
    assert not g1_promotion_gate(**{**adequate, "matched_events": 29}, ci95=[.001, .01])
    assert g1_promotion_gate(**adequate, ci95=[.001, .01])

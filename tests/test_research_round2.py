from __future__ import annotations

from decimal import Decimal

import pandas as pd

from scripts.run_research_round2_signal import (
    HORIZONS,
    _regime,
    cost_decomposition,
    persist_selection,
    promotion_gate,
)
from scripts.audit_research_round2_no_lookahead import audit as audit_timing


def test_forward_horizons_start_after_signal_close() -> None:
    assert HORIZONS["next_open_next_close"] == 1
    assert all(offset > 0 for offset in HORIZONS.values())


def test_regime_features_are_causal_to_future_appends() -> None:
    dates = pd.bdate_range("2024-01-01", periods=140)
    benchmark = pd.Series(range(900, 1040), index=dates, dtype=float)
    prices = {f"S{i}": pd.DataFrame({"adj_close": [10 + j * (0.01 + i / 10000) for j in range(140)]}, index=dates) for i in range(12)}
    base = _regime(benchmark, prices)
    changed_benchmark = benchmark.copy()
    changed_benchmark.iloc[-5:] = changed_benchmark.iloc[-5:] * 0.5
    changed_prices = {symbol: frame.copy() for symbol, frame in prices.items()}
    for frame in changed_prices.values():
        frame.iloc[-5:, 0] = frame.iloc[-5:, 0] * 0.4
    changed = _regime(changed_benchmark, changed_prices)
    columns = ["benchmark_sma50", "benchmark_return20", "benchmark_volatility20", "cross_sectional_dispersion", "regime"]
    pd.testing.assert_frame_equal(base.loc[dates[:-5], columns], changed.loc[dates[:-5], columns])


def test_persistence_retains_only_names_with_valid_thesis() -> None:
    assert persist_selection(["A", "B"], ["A"], ["C", "D"], 3) == ["A", "C", "D"]


def test_cost_decomposition_does_not_double_count_slippage() -> None:
    result = cost_decomposition(Decimal("0.02"), Decimal("0.0093"), Decimal("10000"), Decimal("700"), Decimal("25000"), Decimal("1000000"))
    assert result["gross_pnl"] == Decimal("20000")
    assert result["net_reconciliation_difference"] == Decimal("0.0000")
    assert "reflected in gross_return" in result["slippage_treatment"]


def test_failed_stage1_or_missing_oos_blocks_promotion() -> None:
    assert promotion_gate("REJECTED_STAGE_1", "SIGNAL_DIAGNOSTIC_NOT_CLEARLY_POOR", False, False, False) == "NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE"


def test_no_same_bar_execution_and_forward_return_alignment() -> None:
    report = {"run_id": "fixture", "events": [{"signal_date": "2026-01-05", "execution_date": "2026-01-06", "forward_exit_dates": {"next_open_next_close": "2026-01-06", "plus_2": "2026-01-07"}}]}
    assert audit_timing(report)["status"] == "PASS"
    report["events"][0]["execution_date"] = "2026-01-05"
    assert audit_timing(report)["status"] == "FAIL"


def test_round2_registry_preserves_round1_and_failure_records() -> None:
    import json
    from pathlib import Path

    registry = json.loads(Path("reports/experiment_registry.json").read_text(encoding="utf-8"))
    ids = {experiment["experiment_id"] for experiment in registry["experiments"]}
    assert "R2_H6_SIGNAL_DIAGNOSTIC_20261024" in ids
    assert "R2_H6_TOP3_PORTFOLIO_20261024" in ids
    assert any(experiment["experiment_id"].startswith("ROUND1") or "MEANREV" in experiment["experiment_id"] for experiment in registry["experiments"])
    assert "inspected" in registry["multiplicity_warning"] and "not independent" in registry["multiplicity_warning"]

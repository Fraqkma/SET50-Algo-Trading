import json
from pathlib import Path

import pandas as pd
import pytest

from src.research.holding_period import (
    align_directional_return,
    cluster_bootstrap,
    first_passage,
    holm_adjust,
    horizon_index,
    passage_counts,
)
from scripts.analyze_research_holding_distributions import (
    outcome,
    subtract_benchmark_return,
)


def test_horizon_index_counts_observed_sessions_not_calendar_days():
    observed_sessions = ["2026-12-30", "2027-01-04", "2027-01-05"]
    assert observed_sessions[horizon_index(0, 1)] == "2026-12-30"
    assert observed_sessions[horizon_index(0, 2)] == "2027-01-04"
    assert observed_sessions[horizon_index(0, 3)] == "2027-01-05"


def test_first_passage_keeps_never_hit_and_insufficient_paths():
    assert first_passage([0.001, 0.009, 0.011], 0.01) == {
        "status": "HIT", "session": 3, "observed_sessions": 3}
    assert first_passage([0.001, -0.002], 0.01)["status"] == "RIGHT_CENSORED"
    assert first_passage([0.001, None, 0.02], 0.01)["status"] == "INSUFFICIENT_DATA"


def test_adverse_boundary_uses_downside_crossing():
    assert first_passage([0.0, -0.006, -0.012], -0.01)["session"] == 3
    assert first_passage([0.0, 0.01], -0.01)["status"] == "RIGHT_CENSORED"


def test_competing_threshold_hits_keep_both_cohort_members():
    result = passage_counts([
        {"net_path": [0.012, -0.02], "date": "d1", "symbol": "A"},
        {"net_path": [-0.012, None], "date": "d2", "symbol": "B"},
    ], 0.01, (1, 2))
    assert result["cohort_n"] == 2
    assert result["first_hit_count_by_session"] == {"1": 1, "2": 1}
    assert result["status_counts"] == {"HIT": 1, "INSUFFICIENT_DATA": 1}
    assert result["first_hit_fraction_ci95_two_way_cluster"]["2"] is not None
    assert result["first_hit_count_at_each_session"] == {"1": 1, "2": 0}


def test_adverse_boundary_is_a_competing_event_for_objective_hit():
    result = passage_counts([
        {"net_path": [0.0, -0.012, 0.02]},
        {"net_path": [0.006, 0.012]},
    ], 0.01, (1, 2, 3), competing_threshold=-0.01)
    assert result["status_counts"] == {"COMPETING_THRESHOLD_FIRST": 1, "HIT": 1}
    assert result["first_hit_count_by_session"] == {"1": 0, "2": 1, "3": 1}


def test_cluster_bootstrap_is_deterministic_and_marks_overlap_clusters():
    args = ([0.01, -0.005, 0.02, -0.01],
            ["d1", "d1", "d2", "d3"], ["A", "B", "A", "B"])
    first = cluster_bootstrap(*args, replications=500, seed=7)
    second = cluster_bootstrap(*args, replications=500, seed=7)
    assert first == second
    assert first["date_clusters"] == 3
    assert first["symbol_clusters"] == 2


def test_holm_adjustment_handles_family_and_missing_comparisons():
    assert holm_adjust({"a": 0.01, "b": 0.03, "c": None}) == {
        "a": 0.02, "b": 0.03, "c": None}


def test_horizon_return_does_not_read_prices_after_fixed_exit():
    index = pd.date_range("2026-01-01", periods=4, freq="D")
    base = pd.DataFrame({"open": [10, 10, 10, 10], "close": [10, 10.1, 10.2, 10.3],
                         "adjusted_close": [10, 10.1, 10.2, 10.3]}, index=index)
    changed_future = base.copy()
    changed_future.loc[index[3], "close"] = 99
    changed_future.loc[index[3], "adjusted_close"] = 99
    assert outcome(base, 0, 2, "S3-A", stress_tick=False) == outcome(
        changed_future, 0, 2, "S3-A", stress_tick=False)
    assert outcome(base.iloc[:2], 0, 2, "S3-A", stress_tick=False) is None


def test_gap_direction_alignment_keeps_costs_adverse():
    assert align_directional_return(-0.02, -0.023, -1) == pytest.approx((0.02, 0.017))


def test_benchmark_relative_return_uses_only_signal_and_fixed_exit_closes():
    dates = pd.date_range("2026-01-01", periods=3, freq="D")
    frame = pd.DataFrame({"close": [10, 10.2, 10.5]}, index=dates)
    benchmark = pd.Series([100, 110, 1000], index=dates)
    result = subtract_benchmark_return((0.02, 0.017), frame, 0, 1, benchmark)
    assert result == pytest.approx((-0.08, -0.083))


def test_phase4_user_direction_lock_is_recorded_without_changing_phase3_config():
    root = Path(__file__).resolve().parents[1]
    lock = json.loads((root / "config/phase4_research_direction_lock.json").read_text())
    registry = json.loads((root / "reports/experiment_registry.json").read_text())
    assert lock["award_priority"]["primary"] == "Best Alpha"
    assert lock["award_priority"]["secondary"] == "Best Risk Control"
    assert lock["new_data_purchase_budget_thb"] == 0
    assert lock["holding_period_research"]["preferred_starting_sessions"] == [1, 2, 3, 4, 5]
    assert not lock["holding_period_research"]["select_historical_best_exit_day"]
    assert registry["phase4_direction_lock"]["new_data_budget_thb"] == 0

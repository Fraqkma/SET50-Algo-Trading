import json
from pathlib import Path

import pytest

from scripts.build_phase4_data_first_audit import baseline_report, calendar
from src.competition.metrics import competition_metrics_for_period
from src.competition.period import load_competition_period
from src.data.eligibility import MarketDataEligibilityGate

ROOT = Path(__file__).resolve().parents[1]


def test_competition_calendar_has_exact_expected_21_sessions_and_boundary_holidays():
    result = calendar()
    assert result["trading_day_count"] == 21
    assert [x["date"] for x in result["rows"] if x["status"] == "SET_HOLIDAY"] == ["2026-12-31", "2027-01-01"]
    assert result["rows"][0]["date"] == "2026-12-16"
    assert result["rows"][-1]["date"] == "2027-01-15"


def test_period_metric_window_fails_closed_without_complete_date_stamped_rows():
    period = load_competition_period()
    result = competition_metrics_for_period([], [], expected_trading_dates=[d.isoformat() for d in period.trading_dates], starting_nav=10_000_000)
    assert result["period_scope"]["status"] == "NO_COMPETITION_DATES"
    assert result["classification"] == "UNKNOWN_OR_INCOMPLETE"
    assert result["metrics"]["portfolio_total_return"] is None
    assert result["qualification"]["average_exposure"]["status"] == "UNKNOWN"


def test_period_metric_filter_excludes_outside_dates_and_rejects_missing_session():
    period = load_competition_period()
    complete = [{"date": d.isoformat(), "nav_close": 10_000_000, "benchmark_close": 100, "invested_value": 5_000_000} for d in period.trading_dates]
    complete += [{"date": "2026-12-15", "nav_close": 99, "benchmark_close": 99, "invested_value": 99}]
    result = competition_metrics_for_period(complete, [], expected_trading_dates=[d.isoformat() for d in period.trading_dates], starting_nav=10_000_000)
    assert result["period_scope"]["status"] == "COMPLETE_COMPETITION_PERIOD"
    assert len(result["period_scope"]["observed_in_period_dates"]) == 21
    assert "2026-12-15" not in result["period_scope"]["observed_in_period_dates"]
    missing = competition_metrics_for_period(complete[:-2], [], expected_trading_dates=[d.isoformat() for d in period.trading_dates], starting_nav=10_000_000)
    assert missing["metrics"]["portfolio_total_return"] is None


def test_pit_gate_does_not_leak_retired_intuch_identity_or_future_manifest_dates():
    gate = MarketDataEligibilityGate(ROOT)
    assert gate.assess("INTUCH", "2025-04-01").reason == "INTUCH_POST_MERGER_IDENTITY_RETIRED"
    assert gate.assess("GULF", "2025-04-03").eligible is True
    later = gate.assess("BDMS", "2026-12-16")
    assert later.eligible is False
    assert later.reason == "OUTSIDE_APPROVED_DATA_RANGE"


def test_phase4_panels_remain_source_isolated_and_no_unsafe_expansion():
    matrix = json.loads((ROOT / "reports/phase4_pit_universe_eligibility.json").read_text(encoding="utf-8"))
    assert matrix["pipeline_counts"]["phase3_event_panel_symbols"] == 18
    assert matrix["pipeline_counts"]["needs_review"] == 42
    assert "not PIT admissible" in matrix["admissible_panels"]["settrade_production"]
    assert matrix["admissible_panels"]["phase4_expanded_pit_candidate_panel"]["symbol_count"] == 20
    extras = {r["symbol"]: r for r in matrix["symbols"] if r["symbol"] in {"THAI", "MRDIYT"}}
    assert all(not row["phase3_event_panel_member"] and "48 gate-approved rows" in row["phase3_panel_reason"] for row in extras.values())
    assert "not pooled" in matrix["admissible_panels"]["official_tradesim_history"]["status"]


def test_null_cash_baseline_and_deterministic_nonpromotional_scenarios():
    first = baseline_report()
    second = baseline_report()
    assert first == second
    assert first["classification"] == "NON-PROMOTIONAL_DIAGNOSTIC_ONLY"
    assert first["panel_id"] == "expanded_20"
    assert first["cash_only"]["net_return"] == 0
    assert first["cash_only"]["eod_exposure"] == 0
    assert first["equal_weight_buy_hold_scenarios"]["3"]["hypothetical_fifo_roundtrips_if_all_fills_occur"] == 3
    assert first["benchmark_reference"]["observations"] == 747
    assert set(first["symbols"]) >= {"THAI", "MRDIYT"}


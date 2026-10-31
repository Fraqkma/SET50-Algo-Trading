from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _report(name: str) -> dict:
    return json.loads((ROOT / "reports" / name).read_text(encoding="utf-8"))


def test_phase5_fails_closed_on_new_pit_and_independent_oos() -> None:
    pit = _report("phase5_pit_coverage_matrix.json")
    holdout = _report("phase5_data_holdout_audit.json")
    screen = _report("phase5_signal_screen.json")
    assert pit["newly_approved_pit_symbols"] == 0
    assert pit["newly_approved_pit_symbol_date_observations"] == 0
    assert pit["phase4_needs_review"] == 42
    assert holdout["genuinely_independent_oos_exists"] is False
    assert screen["status"] == "NEW_ALPHA_SCREEN_DEFERRED"
    assert screen["candidate_shortlist_for_human_review"] == []


def test_phase5_tick_lane_is_mechanical_and_zero_broker_orders() -> None:
    mechanics = _report("phase5_official_tick_mechanics.json")
    run = mechanics["real_tick_order_run_this_phase"]
    assert mechanics["version"] == "0.2.7"
    assert run["requests"] == 1
    assert run["accepted_orders"] == 0
    assert run["fills"] == 0
    assert mechanics["real_broker_orders_placed"] == 0

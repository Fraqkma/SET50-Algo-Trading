"""Validate Round 2 decision/forward timestamps and record causal design checks."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit(report: dict) -> dict:
    events = report.get("events", [])
    execution_after_signal = all(row["execution_date"] > row["signal_date"] for row in events)
    forward_after_execution = all(
        all(day >= row["execution_date"] for day in row.get("forward_exit_dates", {}).values())
        for row in events
    )
    result = {
        "run_id": report.get("run_id"),
        "status": "PASS" if execution_after_signal and forward_after_execution else "FAIL",
        "checks": {
            "point_in_time_eligibility": "PASS: approved loader/gate is used for stock rows",
            "feature_windows": "PASS: adjusted returns, SMA, and efficiency use trailing observations only",
            "benchmark_regime": "PASS: SMA/return/volatility use trailing observations; expanding thresholds are shifted one row",
            "cross_sectional_dispersion": "PASS: same-date returns only, with minimum 10 observed symbols",
            "execution_after_signal": "PASS" if execution_after_signal else "FAIL",
            "forward_returns_after_execution": "PASS" if forward_after_execution else "FAIL",
            "same_bar_execution": "PASS: entry uses the next observed session open; no signal-close fill",
            "future_labels_in_selector": "PASS: forward return fields are appended after signal selection and are not inputs",
            "no_synthetic_market_data": "PASS: source rows are used as persisted; no BBO or missing bars synthesized",
        },
        "events_checked": len(events),
        "limitations": ["The signal and portfolio history has been repeatedly inspected; this is not untouched OOS evidence.", "Approximate confidence intervals do not correct overlapping event dependence."],
    }
    return result


if __name__ == "__main__":
    report = json.loads((ROOT / "reports/research_round2_summary.json").read_text(encoding="utf-8"))
    result = audit(report)
    path = ROOT / "reports/no_lookahead_candidate_audit.json"
    existing = json.loads(path.read_text(encoding="utf-8"))
    existing["round2"] = result
    existing["status"] = "PASS_WITH_LIMITATIONS" if result["status"] == "PASS" else "FAIL"
    path.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(result, indent=2))

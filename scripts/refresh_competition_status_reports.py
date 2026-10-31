"""Refresh competition-date and Oct 29 evidence summaries from canonical reports."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.competition.period import competition_calendar, load_competition_period


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, value: dict) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    period = load_competition_period(ROOT / "config/competition.yaml")
    calendar = competition_calendar(period)
    competition_config = yaml.safe_load((ROOT / "config/competition.yaml").read_text(encoding="utf-8"))["competition"]
    oct29 = _read(ROOT / "reports/oct29_collection_audit.json")
    scheduler = _read(ROOT / "reports/settrade_scheduler_status.json")
    daily_recovery = _read(ROOT / "reports/settrade_historical_recovery_manifest.json")
    production_readiness = _read(ROOT / "reports/settrade_production_readiness.json")
    probe_path = ROOT / "reports/settrade_backfill_probe.json"
    if probe_path.is_file():
        oct29["gap_probe"] = _read(probe_path)
    oct29["daily_recovery"] = daily_recovery
    oct29["classification"] = "PARTIAL_COLLECTION" if oct29.get("datasets", {}).get("raw_bbo", {}).get("events") and oct29.get("datasets", {}).get("1m", {}).get("rows") else "UNKNOWN"
    oct29["collector_activity_status"] = "COLLECTOR_RAN_AND_DATA_PERSISTED" if oct29["classification"] == "PARTIAL_COLLECTION" else "NO_PERSISTED_MARKET_DATA"
    oct29["scheduled_task_invocation_status"] = "UNVERIFIED_HISTORICAL_TASK_SCHEDULER_EVENT_HISTORY_UNAVAILABLE"
    oct29["task_history_limitations"] = "The runner log begins at 00:21, before the 09:45 scheduled trigger, and shows a later 09:45 login/open-window event. Persisted rows prove collector activity, but neither current last-run metadata (now 2026-10-30) nor available historical Task Scheduler events prove that Task Scheduler itself launched the 2026-10-29 runner."
    oct29["generated_at"] = datetime.now(timezone.utc).isoformat()
    _write(ROOT / "reports/oct29_collection_audit.json", oct29)
    generated = datetime.now(timezone.utc).isoformat()

    readiness = {
        "generated_at": generated,
        "evidence_classification": "NO_OFFICIAL_CONTINUOUS_COMPETITION_SCORE",
        "authoritative_source": "KGI_ALGO26_Performance_TH (1).pdf",
        "source_status": "PRESENT_BUT_TEXT_EXTRACTION_NOT_VALIDATED_IN_THIS_RUN",
        "competition_period": {
            "start": period.start.isoformat(), "end": period.end.isoformat(),
            "timezone": period.timezone,
            "calendar_status": calendar["status"],
            "expected_trading_days": calendar["trading_day_count"],
            "benchmark_window": [period.benchmark["start_date"], period.benchmark["end_date"]],
            "metric_window": [period.start.isoformat(), period.end.isoformat()],
            "exposure_denominator": competition_config["metrics"]["exposure_denominator"],
            "round_trip_boundary_policy": period.round_trip_boundary_policy,
        },
        "official_scored_run": None,
        "scoring_blocker": "Current TradeSim bridge resets portfolio per date; continuous portfolio scoring path not validated.",
        "metrics": {key: None for key in (
            "benchmark_return", "benchmark_max_drawdown", "portfolio_total_return",
            "portfolio_max_drawdown", "excess_return", "calmar_ratio", "fifo_round_trips",
            "average_portfolio_exposure", "win_rate", "expected_payoff")},
        "common_criteria": {
            "drawdown_vs_benchmark": {"status": "UNKNOWN", "threshold": "Portfolio Max DD < 1.5 x Benchmark Max DD"},
            "minimum_roundtrips": {"status": "UNKNOWN", "threshold": ">= 5 completed FIFO Round-Trips"},
            "average_exposure": {"status": "UNKNOWN", "threshold": ">= 50%"},
            "expected_payoff": {"status": "UNKNOWN", "threshold": "> 0"}},
        "awards": {
            "best_alpha": {"eligibility": "UNKNOWN", "requirements": ["Portfolio Total Return >= 0", "Excess Return >= 0"], "ranking": ["Excess Return descending", "Calmar Ratio descending", "Portfolio Total Return descending"]},
            "best_risk_control": {"eligibility": "UNKNOWN", "ranking": ["Calmar Ratio descending", "Excess Return descending", "Maximum Drawdown ascending"]},
            "most_active_trader": {"eligibility": "UNKNOWN", "ranking": ["Round-Trips descending"]},
            "precision_trader": {"eligibility": "UNKNOWN", "ranking": ["Win Rate descending"]}},
        "source_evidence": "Competition dates are user-confirmed. Common Criteria and award definitions are preserved from existing project/task evidence; named PDF is present but its text was not validated during this run.",
        "no_team_rank_fabricated": True,
        "real_orders_placed": 0,
    }
    _write(ROOT / "reports/competition_metric_readiness.json", readiness)

    status_path = ROOT / "reports/current_market_data_status.json"
    status = _read(status_path)
    status["generated_at"] = generated
    status["audit_end"] = "2026-10-29"
    status["oct29_collection_audit"] = {
        "classification": oct29["classification"], "collector_activity_status": oct29["collector_activity_status"],
        "scheduled_task_invocation_status": oct29["scheduled_task_invocation_status"], "report": "reports/oct29_collection_audit.json",
        "raw_bbo_events": oct29["datasets"]["raw_bbo"]["events"],
        "normalized_bbo_rows": oct29["datasets"]["normalized_bbo"]["rows"],
        "candles": {key: {"rows": value["rows"], "symbols": value["symbols"],
                          "first": value["first_local_timestamp"], "latest": value["last_local_timestamp"],
                          "candidate_gap_pairs": value["possible_within_session_gap_pairs"]}
                     for key, value in oct29["datasets"].items() if key in {"1m", "5m", "15m", "daily"}},
        "runner_cycles_exit_0": oct29["runner"]["collector_cycles_exit_0"],
        "runner_finish": oct29["runner"]["finish"][-1]["timestamp"],
        "scheduler_snapshot_date": "2026-10-30",
        "scheduler_last_result": scheduler.get("last_result"),
        "note": "Oct 30 is the current/partial separate snapshot; task metadata at audit time reflects Oct 30, not Oct 29.",
    }
    daily_dataset = status.setdefault("datasets", {}).setdefault("candles_1d", {})
    day_already_recorded = "2026-10-29" in daily_dataset.setdefault("days", {})
    daily_dataset["days"]["2026-10-29"] = {
        "rows": oct29["datasets"]["daily"]["rows"],
        "symbols": oct29["datasets"]["daily"]["symbols"],
        "first": oct29["datasets"]["daily"]["first_local_timestamp"],
        "latest": oct29["datasets"]["daily"]["last_local_timestamp"],
        "adjustment_status": "UNKNOWN",
    }
    if not day_already_recorded:
        daily_dataset["rows"] = int(daily_dataset.get("rows", 0)) + int(oct29["datasets"]["daily"]["rows"])
    daily_dataset["latest"] = oct29["datasets"]["daily"]["last_local_timestamp"]
    daily_dataset["symbols"] = max(int(daily_dataset.get("symbols", 0)), int(oct29["datasets"]["daily"]["symbols"]))
    status["settrade_daily_recovery"] = {
        "interval": "1d", "date": "2026-10-29", "api_status": daily_recovery.get("summary"),
        "manifest": "reports/settrade_historical_recovery_manifest.json",
        "adjustment_status": "UNKNOWN", "orders_placed": 0,
    }
    status["competition_period"] = readiness["competition_period"]
    status["scheduler"] = scheduler
    status["collector"] = {
        "status": "SCHEDULED_READY_LAST_RUN_FAILED" if int(scheduler.get("last_result", 0)) != 0 else "SCHEDULED_READY",
        "logged_out_readiness": "LOGGED_OUT_CONFIGURED_NOT_RUNTIME_VALIDATED" if scheduler.get("logged_out_capable") else "INTERACTIVE_ONLY",
        "unattended_assessment": "Password logon and interactive_only=false permit logged-out execution; a logged-out runtime trial has not been evidenced. Oct 30 last run result 1; consult its runner log for failure details.",
        "oct29_runner_cycles_exit_0": oct29["runner"]["collector_cycles_exit_0"],
        "lock_exists_at_oct29_audit": oct29["process_and_lock_check"]["lock_exists"],
        "live_collector_process_observed_at_oct29_audit": oct29["process_and_lock_check"]["live_collector_process_observed"],
    }
    latest_log = ROOT / "logs/settrade/daily-2026-10-30.log"
    bbo_checkpoint_path = ROOT / "data/pilot/settrade/production/checkpoints/bid_offer.json"
    candle_checkpoint_path = ROOT / "data/pilot/settrade/production/checkpoints/candles.json"
    bbo_checkpoint = _read(bbo_checkpoint_path) if bbo_checkpoint_path.is_file() else {}
    candle_checkpoint = _read(candle_checkpoint_path) if candle_checkpoint_path.is_file() else {}
    latest_log_lines = latest_log.read_text(encoding="utf-8", errors="replace").splitlines() if latest_log.is_file() else []
    status["oct30_partial_snapshot"] = {
        "date": "2026-10-30", "classification": "PARTIAL_CURRENT_DAY_EVIDENCE",
        "runner_log": "logs/settrade/daily-2026-10-30.log",
        "runner_log_first": latest_log_lines[0][:80] if latest_log_lines else None,
        "runner_log_last": latest_log_lines[-1][:160] if latest_log_lines else None,
        "bbo_checkpoint": {key: bbo_checkpoint.get(key) for key in ("status", "events", "symbols_requested", "last_callback_at", "last_error")},
        "candle_checkpoint": {key: candle_checkpoint.get(key) for key in ("status", "expected_session_date", "last_candle_timestamp", "last_error")},
        "readiness_checked_at": production_readiness.get("checked_at"),
        "latest_intraday_candle_bangkok": production_readiness.get("latest_intraday_candle", {}).get("latest_timestamp_bangkok"),
        "readiness_status": production_readiness.get("status"),
        "note": "Separate Oct 30 live/API snapshot; it does not revise Oct 29 coverage counts. The scheduled Oct 30 runner ended FAILED after health-check timeouts.",
    }
    _write(status_path, status)
    print(json.dumps({"readiness": str(ROOT / "reports/competition_metric_readiness.json"),
                      "market_status": str(status_path), "generated_at": generated}, indent=2))


if __name__ == "__main__":
    main()

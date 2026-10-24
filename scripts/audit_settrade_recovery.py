"""Build a read-only report of Settrade freshness, gaps, and file integrity."""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import yaml

from src.data.settrade.health import collect_health
from src.data.settrade.integrity import scan_integrity
from src.data.settrade.paths import resolve_data_root


def build_report(project_root: Path, data_root: Path) -> dict[str, Any]:
    """Assemble evidence without writing into market-data or checkpoint paths."""
    project_root, data_root = project_root.resolve(), data_root.resolve()
    health = collect_health(project_root, data_root)
    audit_path = project_root / "reports" / "settrade_collection_audit.json"
    try:
        collection = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        collection = {}
    daily = collection.get("daily_collection", {})
    artifactless = collection.get("weekday_dates_without_artifacts", [])
    log_dir = project_root / "logs" / "settrade"
    restart_blocked: list[str] = []
    for path in sorted(log_dir.glob("daily-*.log")) if log_dir.exists() else []:
        try:
            if "ALREADY_RUNNING" in path.read_text(encoding="utf-8", errors="replace"):
                day = path.stem.removeprefix("daily-")
                if date.fromisoformat(day).weekday() < 5:
                    restart_blocked.append(day)
        except OSError:
            pass
    checkpoints: dict[str, Any] = {}
    checkpoint_dir = data_root / "checkpoints"
    for path in sorted(checkpoint_dir.glob("*.json")) if checkpoint_dir.exists() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                checkpoints[path.stem] = {key: item for key, item in value.items() if not any(word in key.lower() for word in ("token", "secret", "app_id", "app_secret"))}
        except (OSError, json.JSONDecodeError):
            checkpoints[path.stem] = {"status": "MALFORMED_CHECKPOINT_JSON"}
    candle_days = collection.get("candle_availability", {}).get("days", {})
    upstream_limited = [day for day, item in candle_days.items() if int(item.get("symbols_with_nonempty_response", 0)) < 50]
    candle_rows = {}
    candle_path = data_root / "normalized/bars_1m/data.csv"
    if candle_path.exists():
        import pandas as pd

        frame = pd.read_csv(candle_path, usecols=["symbol", "timestamp"])
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        candle_rows = frame.groupby("symbol")["timestamp"].max().dropna().to_dict()
    checkpoint_consistency: dict[str, Any] = {"checked": 0, "ahead_of_persisted_rows": [], "unparseable": []}
    for name, state in checkpoints.items():
        if not name.startswith("candles") or state.get("status") == "MALFORMED_CHECKPOINT_JSON":
            continue
        stamp = state.get("last_candle_timestamp")
        if not stamp:
            continue
        checkpoint_consistency["checked"] += 1
        symbol = state.get("symbol")
        try:
            checkpoint_stamp = __import__("pandas").Timestamp(stamp)
            persisted_stamp = candle_rows.get(symbol) if symbol else max(candle_rows.values(), default=None)
            if persisted_stamp is None or checkpoint_stamp.tz_convert("UTC") > persisted_stamp:
                checkpoint_consistency["ahead_of_persisted_rows"].append(name)
        except (TypeError, ValueError, AttributeError):
            checkpoint_consistency["unparseable"].append(name)
    return {
        "generated_from": "persisted local rows, runner summaries, collector logs, and checkpoint files",
        "active_repo_path": str(project_root),
        "active_data_root": str(data_root),
        "timezone": "Asia/Bangkok for Settrade timestamps",
        "orders_placed": 0,
        "datasets": health["datasets"],
        "bbo_by_trading_date": collection.get("bbo", {}).get("days", {}),
        "candles_by_timeframe": collection.get("candles", {}).get("timeframes", {}),
        "candle_api_availability": collection.get("candle_availability", {}).get("days", {}),
        "runtime": daily,
        "disk_full_incident": {
            "classification": "UNKNOWN_NOT_CONFIRMED",
            "window_start": None,
            "window_end": None,
            "first_affected_timestamp": None,
            "last_known_good_date": "2026-09-30",
            "first_known_good_after_recovery": None,
            "evidence": [
                "No explicit ENOSPC, disk-full, zero-byte, or disk-guard critical event was found in the retained local evidence.",
                "The 2026-09-30 runtime summary records approximately 6.75 GiB free at start and end: below the 10 GiB warning threshold but above the 5 GiB critical threshold.",
                "The 2026-10-01 collection has genuine morning data but no persisted afternoon callbacks and no runtime summary; the exact stop cause is unknown.",
                "The previous C: checkout and its filesystem history are not available from this research checkout, so the earlier disk-full event cannot be timed from current local evidence.",
            ],
        },
        "date_classification": {
            "confirmed_disk_full": [],
            "likely_disk_full": [],
            "collector_not_running": restart_blocked,
            "weekdays_without_any_artifact_unknown": artifactless,
            "partial_or_abnormal": [day for day, item in daily.items() if str(item.get("quality", "")).startswith(("PARTIAL_SESSION", "ABNORMAL_TERMINATION"))],
            "host_offline": [],
            "upstream_delay_or_no_data_dates": upstream_limited,
        },
        "recovery": {"recovered_intervals": [], "unrecoverable_intervals": ["BBO intervals with no persisted original callbacks; historical public BBO is not available from the retained artifacts."], "recovery_attempted": False},
        "file_integrity_findings": scan_integrity(data_root),
        "checkpoint_directory": str(data_root / "checkpoints"),
        "checkpoint_latest": checkpoints,
        "checkpoint_consistency": checkpoint_consistency,
        "latest_successful_cycle": health.get("latest_successful_cycle"),
        "latest_failed_cycle": health.get("latest_failed_cycle"),
        "filesystem_free_bytes": health.get("filesystem_free_bytes"),
        "known_causes": {"disk_full": "UNKNOWN_NOT_CONFIRMED", "host_offline": "UNKNOWN", "upstream_candle_availability": "EVIDENCED_AS_DELAYED_OR_EMPTY_FOR_SYMBOLS", "stale_lock": "CONFIRMED_STALE_PID_12880_ON_THIS_HOST"},
        "confidence": "HIGH for timestamps and row counts; LOW for historical incident causation because the old drive and earlier logs are unavailable.",
    }


def markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Settrade gap and recovery audit", "",
        "Read-only report from stored rows and local operational artifacts. No market data were created, rewritten, or recovered.", "",
        f"- Research repo: `{report['active_repo_path']}`",
        f"- Active Settrade data root: `{report['active_data_root']}`",
        f"- Current free space on the data filesystem: {report['filesystem_free_bytes']} bytes",
        "- Orders placed: 0", "",
        "## Latest persisted observations", "",
        "| Dataset | Earliest | Latest | Rows | Symbols | Last trading date | Freshness |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for name, item in report["datasets"].items():
        lines.append(f"| {name} | {item.get('earliest')} | {item.get('latest')} | {item.get('rows')} | {item.get('symbols')} | {item.get('last_trading_date')} | {item.get('freshness_status')} |")
    incident = report["disk_full_incident"]
    lines.extend(["", "## Previous disk-full incident", "", f"Classification: **{incident['classification']}**. Exact start, end, and first affected timestamp are not established.", ""])
    lines.extend(f"- {item}" for item in incident["evidence"])
    lines.extend(["", "## Date classification", ""])
    for name, values in report["date_classification"].items():
        lines.append(f"- **{name}:** {', '.join(values) if values else 'none evidenced'}")
    lines.extend(["", "## Trading-date collection coverage", "", "| Date | Runner start/end | Raw BBO | Normalized depth rows | First/last BBO | Morning/afternoon | Candle rows (1m/5m/15m) | Classification |", "|---|---|---:|---:|---|---|---|---|"])
    for day, item in report.get("runtime", {}).items():
        if item.get("quality") == "NON_TRADING_DAY":
            continue
        lines.append(f"| {day} | {item.get('runner_start_local')} - {item.get('runner_end_local')} | {item.get('bbo_events', 0)} | {item.get('normalized_bbo_depth_rows', 0)} | {item.get('morning_first_local') or 'none'} - {item.get('afternoon_last_local') or item.get('morning_last_local') or 'none'} | {item.get('morning_first_local') or 'none'} - {item.get('morning_last_local') or 'none'} / {item.get('afternoon_first_local') or 'none'} - {item.get('afternoon_last_local') or 'none'} | {item.get('candle_rows_by_timeframe', {}).get('1m', 0)}/{item.get('candle_rows_by_timeframe', {}).get('5m', 0)}/{item.get('candle_rows_by_timeframe', {}).get('15m', 0)} | {item.get('quality', 'UNKNOWN')} |")
    lines.extend(["", "## Candle date coverage", "", "API availability counts reflect non-empty raw responses by symbol. The 5m and 15m series are local aggregates of contiguous observed 1m candles; no missing candle is filled.", ""])
    for timeframe, details in report.get("candles_by_timeframe", {}).items():
        lines.extend([f"### {timeframe}", "", "| Date | Rows | First candle | Last candle | Status | API non-empty symbols |", "|---|---:|---|---|---|---:|"])
        for day, day_details in details.get("days", {}).items():
            api_count = report.get("candle_api_availability", {}).get(day, {}).get("symbols_with_nonempty_response", "—")
            lines.append(f"| {day} | {day_details.get('rows', 0)} | {day_details.get('first_local')} | {day_details.get('last_local')} | {day_details.get('status')} | {api_count} |")
        lines.append("")
    lines.extend(["", "## File integrity", ""])
    if report["file_integrity_findings"]:
        for item in report["file_integrity_findings"]:
            lines.append(f"- `{item['path']}`: issues={item['issues']}; rows={item['rows']}; malformed={item['malformed_rows']}; duplicates={item['duplicate_keys']}; timestamp regressions={item['timestamp_regressions']}")
    else:
        lines.append("No zero-byte, malformed, duplicate, regressing, or truncated relevant files were found.")
    lines.extend(["", "## Recovery", "", "No historical BBO was reconstructed. No candle interval was re-downloaded during this audit. The retained evidence shows delayed or empty API responses for some symbol/date combinations, but does not establish that older intervals remain downloadable. Candle recoverability is therefore unverified; BBO intervals without original callbacks are unrecoverable from the retained local artifacts.", "", f"Confidence: {report['confidence']}", ""])
    return "\n".join(lines)


def main() -> int:
    config = yaml.safe_load((ROOT / "config" / "settrade_collection.yaml").read_text(encoding="utf-8")) or {}
    data_root = resolve_data_root(ROOT, config.get("storage_root", "data/pilot/settrade"))
    report = build_report(ROOT, data_root)
    output_dir = ROOT / "reports"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "settrade_gap_recovery_audit.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    (output_dir / "settrade_gap_recovery_audit.md").write_text(markdown(report), encoding="utf-8")
    print(json.dumps({"report": str(output_dir / "settrade_gap_recovery_audit.md"), "active_data_root": str(data_root), "integrity_findings": len(report["file_integrity_findings"]), "orders_placed": 0}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

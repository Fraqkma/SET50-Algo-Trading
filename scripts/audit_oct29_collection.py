"""Reconcile Oct 29, 2026 collector logs with persisted Settrade observations."""
from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
DAY = date(2026, 10, 29)
TZ = ZoneInfo("Asia/Bangkok")
DATA = ROOT / "data/pilot/settrade/production"


def local_time(raw: str | None) -> datetime | None:
    if not raw:
        return None
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(TZ)


def log_audit() -> dict[str, Any]:
    path = ROOT / "logs/settrade/daily-2026-10-29.log"
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    stamp_re = re.compile(r"^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+)")
    stamped = [(datetime.strptime(m.group(1), "%Y-%m-%d %H:%M:%S,%f").replace(tzinfo=TZ), line)
               for line in lines if (m := stamp_re.match(line))]
    cycles = [x for x in stamped if "INFO settrade_daily collector cycle exit=" in x[1]]
    health = [x for x in stamped if "INFO settrade_daily health check completed" in x[1]]
    starts = [x for x in stamped if "INFO settradev2" in x[1] and "login - success" in x[1]]
    finishes = [x for x in stamped if "daily runner finished status=" in x[1]]
    warnings = [x for x in stamped if " WARNING " in x[1]]
    errors = [x for x in stamped if " ERROR " in x[1] or "Traceback" in x[1]]
    market_windows = [x for x in stamped if "market window state=" in x[1]]
    return {
        "path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size,
        "first_log_timestamp": stamped[0][0].isoformat() if stamped else None,
        "last_log_timestamp": stamped[-1][0].isoformat() if stamped else None,
        "successful_login_timestamps": [x[0].isoformat() for x in starts],
        "market_window_events": [{"timestamp": t.isoformat(), "line": line[:250]} for t, line in market_windows],
        "collector_cycles_exit_0": len(cycles),
        "successful_health_snapshots": len(health),
        "warnings": len(warnings), "errors_or_tracebacks": len(errors),
        "warning_lines": [line[:500] for _, line in warnings],
        "error_lines": [line[:500] for _, line in errors],
        "finish": [{"timestamp": t.isoformat(), "line": line} for t, line in finishes],
        "evidence_of_runner_independent_of_ide": "Scheduled-task audit action is cmd.exe -> scripts/start_settrade_daily.bat -> repository Python runner; log shows process lifecycle but does not prove VS Code was closed.",
    }


def _csv_day_stats(path: Path, timeframe: str, *, bbo: bool = False) -> dict[str, Any]:
    malformed = 0
    rows = 0
    symbols: set[str] = set()
    stamps: list[datetime] = []
    per_symbol: dict[str, list[datetime]] = defaultdict(list)
    seen: dict[tuple[str, ...], tuple[str, ...]] = {}
    duplicates = conflicts = invalid = negative_volume = 0
    bbo_books: dict[tuple[str, str], dict[tuple[str, int], tuple[float, float]]] = defaultdict(dict)
    key_columns = (("retrieved_at", "symbol", "side", "level") if bbo
                   else ("timestamp", "symbol"))
    value_columns = (("price", "volume") if bbo else ("open", "high", "low", "close", "volume"))
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            raw_stamp = (row.get("retrieved_at") or row.get("collected_at") if bbo
                         else row.get("timestamp"))
            stamp = local_time(raw_stamp)
            if stamp is None:
                malformed += 1
                continue
            if stamp.date() != DAY:
                continue
            rows += 1
            symbol = str(row.get("symbol", ""))
            symbols.add(symbol)
            stamps.append(stamp)
            per_symbol[symbol].append(stamp)
            key = tuple(str(row.get(k, "")) for k in key_columns)
            value = tuple(str(row.get(k, "")) for k in value_columns)
            if key in seen:
                duplicates += 1
                conflicts += int(seen[key] != value)
            else:
                seen[key] = value
            try:
                volume = float(row.get("volume", "") or 0)
                if volume < 0:
                    negative_volume += 1
                if bbo:
                    side = str(row.get("side", "")).lower()
                    level = int(float(row.get("level", 0) or 0))
                    price = float(row.get("price", 0) or 0)
                    bbo_books[(stamp.isoformat(), symbol)][(side, level)] = (price, volume)
                else:
                    op, hi, lo, cl = (float(row[k]) for k in ("open", "high", "low", "close"))
                    if min(op, hi, lo, cl) <= 0 or hi < max(op, lo, cl) or lo > min(op, hi, cl):
                        invalid += 1
            except (ValueError, TypeError, KeyError):
                invalid += 1
    gap_count = gap_intervals = 0
    minutes = int(timeframe.removesuffix("m")) if timeframe.endswith("m") else None
    if minutes:
        for points in per_symbol.values():
            points.sort()
            for left, right in zip(points, points[1:]):
                left_t, right_t = left.time(), right.time()
                same_session = ((left_t.hour == 10 and right_t.hour == 10) or
                                (left_t.hour == 11 and right_t.hour == 11) or
                                (left_t.hour == 12 and right_t < time(12, 31)) or
                                (left_t.hour in (14, 15) and right_t.hour in (14, 15)) or
                                (left_t.hour == 16 and right_t.hour == 16))
                delta = (right - left).total_seconds() / 60
                if same_session and delta > minutes * 1.5:
                    gap_count += 1
                    gap_intervals += max(0, int(delta // minutes) - 1)
    crossed = 0
    if bbo:
        for levels in bbo_books.values():
            bid = levels.get(("bid", 1), (0.0, 0.0))[0]
            ask = levels.get(("ask", 1), (0.0, 0.0))[0]
            if bid > 0 and ask > 0 and bid > ask:
                crossed += 1
    return {
        "path": str(path.relative_to(ROOT)), "rows": rows, "symbols": len(symbols),
        "symbol_list": sorted(symbols),
        "first_local_timestamp": min(stamps).isoformat() if stamps else None,
        "last_local_timestamp": max(stamps).isoformat() if stamps else None,
        "duplicate_keys": duplicates, "conflicting_duplicate_keys": conflicts,
        "invalid_rows": invalid, "negative_volume_rows": negative_volume,
        "possible_within_session_gap_pairs": gap_count if minutes else None,
        "estimated_missing_intervals": gap_intervals if minutes else None,
        "gap_interpretation": "Timestamp gaps are candidates only; no-trade/API/session semantics are not resolved." if minutes else None,
        "bbo_snapshots": len(bbo_books) if bbo else None,
        "bbo_max_levels_per_side": max((sum(side == s for s, _ in book) for book in bbo_books.values() for side in ("bid", "ask")), default=0) if bbo else None,
        "crossed_top_snapshots": crossed if bbo else None,
        "csv_malformed_or_unparseable_timestamp_rows": malformed,
    }


def _raw_bbo_stats(path: Path) -> dict[str, Any]:
    events = 0
    malformed = 0
    symbols: set[str] = set()
    stamps: list[datetime] = []
    source_counts: Counter[str] = Counter()
    env_counts: Counter[str] = Counter()
    for line in path.open("r", encoding="utf-8", errors="replace"):
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            malformed += 1
            continue
        stamp = local_time(item.get("received_at") or item.get("collected_at"))
        if stamp is None:
            malformed += 1
            continue
        if stamp.date() != DAY:
            continue
        events += 1
        stamps.append(stamp)
        symbols.add(str(item.get("symbol") or item.get("payload", {}).get("symbol") or ""))
        source_counts[str(item.get("source", "UNKNOWN"))] += 1
        env_counts[str(item.get("source_environment", "UNKNOWN"))] += 1
    return {"path": str(path.relative_to(ROOT)), "events": events, "symbols": len(symbols),
            "symbol_list": sorted(symbols), "first_local_timestamp": min(stamps).isoformat() if stamps else None,
            "last_local_timestamp": max(stamps).isoformat() if stamps else None,
            "malformed_lines_file_total": malformed,
            "source_counts_for_day": dict(source_counts), "environment_counts_for_day": dict(env_counts),
            "timestamp_semantics": "callback receipt time; event_timestamp is absent in retained raw callback records"}


def main() -> None:
    scheduler = json.loads((ROOT / "reports/settrade_scheduler_status.json").read_text(encoding="utf-8"))
    comparison = {}
    try:
        inventory = json.loads((ROOT / "reports/local_bbo_inventory.json").read_text(encoding="utf-8"))
        current = json.loads((ROOT / "reports/current_market_data_status.json").read_text(encoding="utf-8"))
        for day in ("2026-10-26", "2026-10-27", "2026-10-28"):
            bbo_day = inventory.get("days", {}).get(day, {})
            comparison[day] = {"bbo_events": bbo_day.get("events"), "bbo_depth_rows": bbo_day.get("depth_rows"),
                               "bbo_symbols": bbo_day.get("symbols"), "bbo_first": bbo_day.get("first"),
                               "bbo_last": bbo_day.get("last"),
                               "candles": {key.removeprefix("candles_"): value.get("days", {}).get(day)
                                           for key, value in current.get("datasets", {}).items()
                                           if key.startswith("candles_")}}
    except (OSError, ValueError, TypeError):
        comparison = {"status": "PRIOR_DAILY_INVENTORY_UNAVAILABLE"}
    datasets = {
        "raw_bbo": _raw_bbo_stats(DATA / "raw/bid_offer/events.jsonl"),
        "normalized_bbo": _csv_day_stats(DATA / "normalized/bid_offer/data.csv", "bbo", bbo=True),
        "1m": _csv_day_stats(DATA / "normalized/bars_1m/data.csv", "1m"),
        "5m": _csv_day_stats(DATA / "normalized/bars_5m/data.csv", "5m"),
        "15m": _csv_day_stats(DATA / "normalized/bars_15m/data.csv", "15m"),
        "daily": _csv_day_stats(DATA / "normalized/bars_1d/data.csv", "1d"),
    }
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "date": DAY.isoformat(), "timezone": "Asia/Bangkok",
        "classification": "PARTIAL_COLLECTION" if datasets["raw_bbo"]["events"] and datasets["1m"]["rows"] else "TASK_STARTED_BUT_RUNNER_FAILED" if log_audit()["errors_or_tracebacks"] else "UNKNOWN",
        "collector_activity_status": "COLLECTOR_RAN_AND_DATA_PERSISTED" if datasets["raw_bbo"]["events"] and datasets["1m"]["rows"] else "NO_PERSISTED_MARKET_DATA",
        "scheduled_task_invocation_status": "UNVERIFIED_HISTORICAL_TASK_SCHEDULER_EVENT_HISTORY_UNAVAILABLE",
        "scheduler_snapshot_at_audit": scheduler,
        "comparison_with_oct26_28": comparison,
        "runner": log_audit(), "datasets": datasets,
        "gap_probe": json.loads((ROOT / "reports/settrade_backfill_probe.json").read_text(encoding="utf-8"))
        if (ROOT / "reports/settrade_backfill_probe.json").is_file() else None,
        "daily_recovery": json.loads((ROOT / "reports/settrade_historical_recovery_manifest.json").read_text(encoding="utf-8"))
        if (ROOT / "reports/settrade_historical_recovery_manifest.json").is_file() else None,
        "process_and_lock_check": {
            "checked_at": datetime.now(TZ).isoformat(),
            "lock_exists": (ROOT / ".settrade-runtime/daily.lock").exists(),
            "live_collector_process_observed": False,
            "basis": "read-only process listing and runner lock path check at audit time; no process was terminated",
        },
        "task_history_limitations": "The runner log begins at 00:21, before the 09:45 scheduled trigger, and shows a later 09:45 login/open-window event. Persisted rows prove collector activity, but neither current last-run metadata (now 2026-10-30) nor available historical Task Scheduler events prove that Task Scheduler itself launched the 2026-10-29 runner.",
        "real_orders_placed": 0,
    }
    output = ROOT / "reports/oct29_collection_audit.json"
    output.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "classification": report["classification"],
                      "runner_cycles": report["runner"]["collector_cycles_exit_0"],
                      "datasets": {k: {x: v.get(x) for x in ("rows", "events", "symbols", "first_local_timestamp", "last_local_timestamp", "duplicate_keys", "conflicting_duplicate_keys") if x in v} for k, v in datasets.items()}}, indent=2))


if __name__ == "__main__":
    main()

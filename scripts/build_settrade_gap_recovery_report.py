"""Build a read-only, source-aware Settrade coverage and gap report."""
from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ZoneInfo("Asia/Bangkok")
UTC = ZoneInfo("UTC")
DATASETS = {
    "raw_bbo": ("raw/bid_offer/events.jsonl", "received_at", "jsonl"),
    "normalized_bbo": ("normalized/bid_offer/data.csv", "retrieved_at", "csv"),
    "candles_1m": ("normalized/bars_1m/data.csv", "timestamp", "csv"),
    "candles_5m": ("normalized/bars_5m/data.csv", "timestamp", "csv"),
    "candles_15m": ("normalized/bars_15m/data.csv", "timestamp", "csv"),
}
MARKET_SESSIONS = ((time(9, 30), time(12, 30), "morning"), (time(14, 30), time(16, 40), "afternoon"), (time(16, 40), time(17, 0), "pre_close"))
STAMP = re.compile(r"\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:\+\d{2}:\d{2}|Z)?")
NETWORK = re.compile(r"dns|name resolution|connection reset|connection refused|network is unreachable|temporary failure|timed? out|timeout|socket|websocket.*disconnect|connection.*lost", re.I)
AUTH = re.compile(r"unauthori[sz]ed|authentication|auth failure|invalid credential|token expired|permission denied", re.I)


def parse_stamp(value: object) -> datetime | None:
    try:
        stamp = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return stamp.replace(tzinfo=LOCAL) if stamp.tzinfo is None else stamp.astimezone(LOCAL)
    except (TypeError, ValueError, OverflowError):
        return None


def session_for(stamp: datetime) -> str | None:
    local_time = stamp.astimezone(LOCAL).time()
    return next((name for start, end, name in MARKET_SESSIONS if start <= local_time < end), None)


def gap_severity(gaps: list[dict]) -> dict:
    """Rank estimated candle gaps separately by timeframe and summarize overlaps."""
    output = {}
    minute_by_dataset = {"candles_1m": 1, "candles_5m": 5, "candles_15m": 15}
    for dataset, minutes in minute_by_dataset.items():
        by_symbol: dict[str, list[dict]] = defaultdict(list)
        for gap in gaps:
            if gap.get("dataset") == dataset and gap.get("environment") == "PRODUCTION":
                by_symbol[str(gap.get("symbol", "UNKNOWN"))].append(gap)
        rankings = []
        expected_daily = sum(int((datetime.combine(datetime.today(), end) - datetime.combine(datetime.today(), start)).total_seconds() // 60 // minutes)
                             for start, end, _ in MARKET_SESSIONS)
        for symbol, items in by_symbol.items():
            estimated = sum(int(item.get("missing_intervals_estimate", 0)) for item in items)
            longest = max((float(item.get("duration_seconds", 0)) for item in items), default=0)
            rankings.append({"symbol": symbol, "gap_count": len(items),
                             "estimated_missing_intervals": estimated,
                             "longest_gap_minutes": round(longest / 60, 2),
                             "timeframe": f"{minutes}m",
                             "estimated_session_coverage_pct": round(max(0, 1 - estimated / expected_daily) * 100, 2) if expected_daily else None,
                             "denominator_note": f"Estimated against {expected_daily} configured session intervals for one full day; not a measured per-symbol trade-activity completeness score."})
        output[f"{minutes}m"] = sorted(rankings, key=lambda row: (-row["gap_count"], -row["estimated_missing_intervals"], -row["longest_gap_minutes"], row["symbol"]))[:20]
    groups: dict[tuple[str, str], dict[str, list[dict]]] = defaultdict(lambda: defaultdict(list))
    for gap in gaps:
        if gap.get("dataset") in minute_by_dataset and gap.get("environment") == "PRODUCTION":
            groups[(str(gap.get("date")), str(gap.get("symbol")))][gap["dataset"]].append(gap)
    overlaps = []
    for (date_key, symbol), frames in groups.items():
        names = sorted(frames)
        for index, left_name in enumerate(names):
            for right_name in names[index + 1:]:
                for left in frames[left_name]:
                    for right in frames[right_name]:
                        left_start, left_end = parse_stamp(left.get("gap_start")), parse_stamp(left.get("gap_end"))
                        right_start, right_end = parse_stamp(right.get("gap_start")), parse_stamp(right.get("gap_end"))
                        if left_start and left_end and right_start and right_end and max(left_start, right_start) <= min(left_end, right_end):
                            overlaps.append({"date": date_key, "symbol": symbol, "timeframes": [left_name, right_name],
                                             "overlap_start": max(left_start, right_start).isoformat(),
                                             "overlap_end": min(left_end, right_end).isoformat(),
                                             "interpretation": "Overlapping estimated candle gaps; counts are timeframe observations and may represent one underlying interval."})
    return {"top_20_by_timeframe": output, "cross_timeframe_overlaps": overlaps,
            "overlap_count": len(overlaps),
            "interpretation": "1m, 5m, and 15m gaps are not additive; only explicit temporal overlaps are identified here."}


def _read_rows(path: Path, fmt: str):
    if not path.exists():
        return
    if fmt == "csv":
        with path.open(encoding="utf-8", newline="") as handle:
            yield from csv.DictReader(handle)
    else:
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    continue


def _log_evidence(day: str) -> dict:
    path = ROOT / "logs" / "settrade" / f"daily-{day}.log"
    if not path.exists():
        return {"path": str(path.relative_to(ROOT)), "exists": False, "runtime_windows_bangkok": [], "collector_cycle_windows_bangkok": [], "market_window_transitions": [], "network_errors": [], "auth_errors": []}
    stamps: list[datetime] = []
    cycle_windows = []
    market_transitions = []
    network_errors, auth_errors = [], []
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line_no, line in enumerate(handle, 1):
            for match in STAMP.finditer(line):
                stamp = parse_stamp(match.group(0))
                if stamp and stamp.date().isoformat() == day:
                    stamps.append(stamp)
            if "collector diagnostics=" in line:
                cycle_stamps = [parse_stamp(value) for value in STAMP.findall(line)]
                cycle_stamps = [value for value in cycle_stamps if value and value.date().isoformat() == day]
                if len(cycle_stamps) > 1:
                    cycle_windows.append({"start_bangkok": min(cycle_stamps).isoformat(), "end_bangkok": max(cycle_stamps).isoformat(), "basis": "SDK subscription start and daily-runner collector diagnostics receipt"})
            if "market window state=" in line or "midday break; API collection paused" in line:
                market_transitions.append({"line": line_no, "timestamp_bangkok": next((value.isoformat() for value in (parse_stamp(found) for found in STAMP.findall(line)) if value and value.date().isoformat() == day), None), "event": line.strip()[:240]})
            if NETWORK.search(line):
                network_errors.append({"line": line_no, "excerpt": line.strip()[:300]})
            if AUTH.search(line):
                auth_errors.append({"line": line_no, "excerpt": line.strip()[:300]})
    windows = []
    if stamps:
        windows = [{"first_log_timestamp": min(stamps).isoformat(), "last_log_timestamp": max(stamps).isoformat(), "basis": "timestamps embedded in collector/SDK log lines; not a process uptime interval"}]
    return {"path": str(path.relative_to(ROOT)), "exists": True, "runtime_log_timestamp_bounds_bangkok": windows, "collector_cycle_windows_bangkok": cycle_windows, "collector_cycle_count": len(cycle_windows), "market_window_transitions": market_transitions, "network_errors": network_errors, "auth_errors": auth_errors, "log_bytes": path.stat().st_size}


def build_report(now: datetime | None = None) -> dict:
    now_local = (now or datetime.now(UTC)).astimezone(LOCAL)
    day = now_local.date().isoformat()
    roots = {
        "production": ROOT / "data" / "pilot" / "settrade" / "production",
        "sandbox": ROOT / "data" / "pilot" / "settrade",
    }
    inventory: dict[str, dict] = {}
    day_rows: dict[str, dict[str, dict]] = defaultdict(lambda: defaultdict(lambda: {"rows": 0, "symbols": set(), "stamps": [], "per_symbol_stamps": defaultdict(list)}))
    current: dict[str, dict] = {}
    all_dates: set[str] = set()
    for environment, root in roots.items():
        inventory[environment] = {}
        for name, (relative, timestamp_field, fmt) in DATASETS.items():
            path = root / relative
            item = {"path": str(path.relative_to(ROOT)), "rows": 0, "symbols": set(), "first_timestamp_bangkok": None, "last_timestamp_bangkok": None, "today_rows": 0, "today_symbols": set(), "today_stamps": [], "today_by_symbol": defaultdict(list), "today_bbo_latest": {}}
            for row in _read_rows(path, fmt):
                stamp = parse_stamp(row.get(timestamp_field) or row.get("event_timestamp") or row.get("timestamp"))
                symbol = str(row.get("symbol") or "").strip().upper()
                if stamp is None:
                    continue
                date_key = stamp.date().isoformat()
                all_dates.add(date_key)
                item["rows"] += 1
                if symbol:
                    item["symbols"].add(symbol)
                if item["first_timestamp_bangkok"] is None or stamp.isoformat() < item["first_timestamp_bangkok"]:
                    item["first_timestamp_bangkok"] = stamp.isoformat()
                if item["last_timestamp_bangkok"] is None or stamp.isoformat() > item["last_timestamp_bangkok"]:
                    item["last_timestamp_bangkok"] = stamp.isoformat()
                day_item = day_rows[date_key][f"{environment}:{name}"]
                day_item["rows"] += 1
                if symbol:
                    day_item["symbols"].add(symbol)
                    day_item["per_symbol_stamps"][symbol].append(stamp)
                day_item["stamps"].append(stamp)
                if date_key == day:
                    item["today_rows"] += 1
                    item["today_stamps"].append(stamp)
                    if symbol:
                        item["today_symbols"].add(symbol)
                        item["today_by_symbol"][symbol].append(stamp)
                        side = str(row.get("side", "")).lower()
                        if name == "normalized_bbo" and str(row.get("level", "")) == "1" and side in {"bid", "ask"}:
                            current_bbo = item["today_bbo_latest"].get(symbol)
                            if current_bbo is None or stamp > current_bbo["timestamp"]:
                                current_bbo = {"timestamp": stamp, "bid": None, "ask": None}
                                item["today_bbo_latest"][symbol] = current_bbo
                            if stamp == current_bbo["timestamp"]:
                                current_bbo[side] = row.get("price")
            item["symbols"] = len(item["symbols"])
            item["today_symbols"] = sorted(item["today_symbols"])
            if item["today_stamps"]:
                item["today_first_bangkok"] = min(item["today_stamps"]).isoformat()
                item["today_last_bangkok"] = max(item["today_stamps"]).isoformat()
            else:
                item["today_first_bangkok"] = item["today_last_bangkok"] = None
            item["today_bbo_by_symbol"] = {
                symbol: {"timestamp_bangkok": value["timestamp"].isoformat(), "bid": value["bid"], "ask": value["ask"]}
                for symbol, value in sorted(item["today_bbo_latest"].items())
            }
            item["today_symbol_coverage"] = {
                symbol: {"rows": len(stamps), "first_timestamp_bangkok": min(stamps).isoformat(), "last_timestamp_bangkok": max(stamps).isoformat()}
                for symbol, stamps in sorted(item["today_by_symbol"].items()) if stamps
            }
            # Event-driven BBO quiet time is reported as an observation gap only;
            # it is never used alone to diagnose connectivity failure.
            today_gaps = []
            if name.startswith("candles_"):
                minutes = {"candles_1m": 1, "candles_5m": 5, "candles_15m": 15}[name]
                for symbol, stamps in item["today_by_symbol"].items():
                    ordered = sorted(set(stamps))
                    for before, after in zip(ordered, ordered[1:]):
                        before_session, after_session = session_for(before), session_for(after)
                        if before_session is None or before_session != after_session:
                            continue
                        missing = int((after - before).total_seconds() // (minutes * 60)) - 1
                        if missing > 0:
                            today_gaps.append({"symbol": symbol, "after": before.isoformat(), "before": after.isoformat(), "missing_intervals_estimate": missing, "classification": "UNKNOWN"})
            item["today_gap_segments"] = sorted(today_gaps, key=lambda gap: (gap["symbol"], gap["after"]))
            del item["today_stamps"], item["today_by_symbol"], item["today_bbo_latest"]
            inventory[environment][name] = item

    for date_key, datasets in day_rows.items():
        for dataset, value in datasets.items():
            value["symbols"] = len(value["symbols"])
            value["symbol_coverage"] = {
                symbol: {"rows": len(stamps), "first_timestamp_bangkok": min(stamps).isoformat(), "last_timestamp_bangkok": max(stamps).isoformat()}
                for symbol, stamps in sorted(value["per_symbol_stamps"].items()) if stamps
            }
            if value["stamps"]:
                value["first_timestamp_bangkok"] = min(value["stamps"]).isoformat()
                value["last_timestamp_bangkok"] = max(value["stamps"]).isoformat()
            value.pop("stamps", None)
            value.pop("per_symbol_stamps", None)
    today_logs = _log_evidence(day)
    today_runtime = ROOT / "reports" / "runtime" / f"settrade_daily_{day}.json"
    runtime_summary = {}
    if today_runtime.exists():
        try:
            runtime_summary = json.loads(today_runtime.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            runtime_summary = {"parse_error": True}
    network_evidence = today_logs["network_errors"]
    backfill_path = ROOT / "reports" / "settrade_backfill_probe.json"
    backfill_records = []
    backfill_paths = [backfill_path, *sorted(backfill_path.parent.glob("settrade_backfill_probe_*.json"))]
    for probe_path in backfill_paths:
        try:
            probe = json.loads(probe_path.read_text(encoding="utf-8")) if probe_path.exists() else {}
        except (OSError, json.JSONDecodeError):
            continue
        if probe.get("environment") == "PRODUCTION" and probe.get("backfill_applied"):
            probe["report_path"] = str(probe_path.relative_to(ROOT))
            backfill_records.append(probe)
    matrix_path = ROOT / "reports" / "settrade_candle_capability_matrix.json"
    try:
        matrix = json.loads(matrix_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        matrix = {}
    for call in matrix.get("calls", []):
        if call.get("backfill_applied") and int(call.get("rows_appended") or 0):
            backfill_records.append({
                "requested_at_utc": matrix.get("generated_at"), "date": call.get("date"),
                "symbol": call.get("symbol"), "timeframe": call.get("timeframe"),
                "requested_start_bangkok": call.get("requested_start"),
                "requested_end_bangkok": call.get("requested_end"),
                "api_source": "Settrade Open API MarketData.get_candlestick",
                "raw_rows": call.get("raw_rows"), "in_range_rows": call.get("returned_rows"),
                "returned_first_bangkok": call.get("returned_first"),
                "returned_last_bangkok": call.get("returned_last"),
                "existing_rows": call.get("existing_rows"), "new_rows": call.get("would_append_rows"),
                "identical_duplicates": call.get("identical_duplicates"), "conflicts": call.get("conflicts"),
                "validation_issues": call.get("validation_issues"), "backfill_applied": True,
                "rows_appended": call.get("rows_appended"),
                "report_path": str(matrix_path.relative_to(ROOT)),
            })
    backfill_records.sort(key=lambda item: item.get("requested_at_utc", ""))
    backfill_record = backfill_records[-1] if backfill_records else {}
    bbo_items = [inventory["production"].get("raw_bbo", {}), inventory["production"].get("normalized_bbo", {})]
    candle_items = [inventory["production"].get(f"candles_{tf}", {}) for tf in ("1m", "5m", "15m")]
    event_gaps = []
    for name in ("raw_bbo", "normalized_bbo"):
        relative, timestamp_field, fmt = DATASETS[name]
        source = roots["production"] / relative
        for row in _read_rows(source, fmt):
            stamp = parse_stamp(row.get(timestamp_field) or row.get("event_timestamp"))
            if stamp and stamp.date().isoformat() == day:
                symbol = str(row.get("symbol") or "").upper()
                if symbol and (name == "raw_bbo" or str(row.get("level", "")) == "1"):
                    event_gaps.append((symbol, stamp))
    bbo_longest_observation_gap = None
    if event_gaps:
        per_symbol: dict[str, list[datetime]] = defaultdict(list)
        for symbol, stamp in event_gaps:
            per_symbol[symbol].append(stamp)
        candidates = []
        for symbol, stamps in per_symbol.items():
            ordered = sorted(stamps)
            for left, right in zip(ordered, ordered[1:]):
                candidates.append((right - left, symbol, left, right))
        if candidates:
            duration, symbol, left, right = max(candidates)
            bbo_longest_observation_gap = {"symbol": symbol, "start": left.isoformat(), "end": right.isoformat(), "duration_seconds": int(duration.total_seconds()), "interpretation": "Event-driven quiet interval; not proof of a collector or network failure."}

    if network_evidence:
        outage_classification, confidence = "CONFIRMED_NETWORK_OUTAGE", "HIGH (transport errors in today's collector log)"
    elif today_logs["exists"] and (runtime_summary.get("reconnects", 0) or runtime_summary.get("retries", 0)):
        outage_classification, confidence = "LIKELY_NETWORK_OUTAGE", "MEDIUM (retry/reconnect counters without a specific transport line)"
    elif any(item.get("today_rows", 0) for item in bbo_items + candle_items):
        outage_classification, confidence = "UNKNOWN", "LOW (data persisted, but no network outage evidence located in retained logs)"
    elif runtime_summary:
        outage_classification, confidence = "COLLECTOR_NOT_RUNNING_OR_NO_DATA", "LOW (no persisted current-day rows; runtime summary alone does not identify cause)"
    else:
        outage_classification, confidence = "UNKNOWN", "LOW (no current-day source or runtime evidence)"

    gaps = []
    for environment in roots:
        for dataset in DATASETS:
            item = inventory[environment][dataset]
            if environment == "production" and not item.get("today_rows"):
                gaps.append({"date": day, "dataset": dataset, "environment": environment.upper(), "symbol": None, "gap_start": None, "gap_end": None, "classification": "NO_DATA", "recoverability": "REALTIME_ONLY_NOT_RECOVERABLE" if dataset.endswith("bbo") else "UNKNOWN", "evidence": "No persisted rows for this date."})
            for segment in item.get("today_gap_segments", []):
                gaps.append({"date": day, "dataset": dataset, "environment": environment.upper(), "symbol": segment["symbol"], "gap_start": segment["after"], "gap_end": segment["before"], "duration_seconds": (parse_stamp(segment["before"]) - parse_stamp(segment["after"])).total_seconds(), "missing_intervals_estimate": segment["missing_intervals_estimate"], "classification": "UNKNOWN", "recoverability": "UNKNOWN", "evidence": "Genuine candle timestamps separated within the same configured market session; no network error evidence establishes cause."})
    trading_day_observed = any(inventory["production"][name]["today_rows"] for name in DATASETS)
    historical_days = []
    incomplete_days = []
    for date_key, dataset_rows in sorted(day_rows.items()):
        runtime_path = ROOT / "reports" / "runtime" / f"settrade_daily_{date_key}.json"
        runtime = {}
        if runtime_path.exists():
            try:
                runtime = json.loads(runtime_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                runtime = {"parse_error": True}
        counts = {f"{environment}:{name}": dataset_rows.get(f"{environment}:{name}", {}).get("rows", 0) for environment in roots for name in DATASETS}
        symbols = {f"{environment}:{name}": dataset_rows.get(f"{environment}:{name}", {}).get("symbols", 0) for environment in roots for name in DATASETS}
        has_candles = any(counts.get(f"{environment}:candles_{tf}", 0) for environment in roots for tf in ("1m", "5m", "15m"))
        present_timeframes = all(counts.get(f"production:candles_{tf}", 0) or counts.get(f"sandbox:candles_{tf}", 0) for tf in ("1m", "5m", "15m"))
        has_bbo = bool(counts.get("production:raw_bbo", 0) or counts.get("sandbox:raw_bbo", 0))
        has_rows = any(counts.values())
        if runtime.get("market_day") and (runtime.get("retries", 0) or runtime.get("reconnects", 0)):
            classification = "OUTAGE_PARTIAL"
        elif runtime and runtime.get("market_day") is False and str(runtime.get("shutdown_status", "")).startswith("MARKET_CLOSED") and not has_rows:
            classification = "MARKET_CLOSED"
        elif runtime.get("market_day") and runtime.get("candle_status") == "NO_DATA" and not has_candles:
            classification = "API_NO_DATA"
        elif not runtime and has_rows:
            classification = "NO_RUNTIME_EVIDENCE"
        elif runtime.get("market_day") and present_timeframes and has_bbo and runtime.get("candle_status") == "SUCCESS" and runtime.get("shutdown_status") not in {"FAILED", "NOT_READY", "DISK_CRITICAL"}:
            classification = "COMPLETE"
        elif has_rows:
            classification = "PARTIAL"
        else:
            classification = "UNKNOWN"
        if date_key == "2026-10-16":
            classification = "CUTOVER_PARTIAL"
        row = {"date": date_key, "classification": classification, "environment_provenance": [env.upper() for env in roots if any(counts.get(f"{env}:{name}", 0) for name in DATASETS)], "rows_by_dataset": counts, "symbols_by_dataset": symbols, "first_last_by_dataset": {name: {"first": value.get("first_timestamp_bangkok"), "last": value.get("last_timestamp_bangkok")} for name, value in dataset_rows.items()}, "runtime_evidence": bool(runtime), "runtime_summary": runtime or None}
        historical_days.append(row)
        if classification not in {"COMPLETE"}:
            incomplete_days.append(date_key)

    report = {
        "generated_at": now_local.isoformat(), "timezone": "Asia/Bangkok", "today": day,
        "today_trading_day_evidence": {"weekday": now_local.weekday() < 5, "observed_market_rows": trading_day_observed, "collector_runtime_market_day": runtime_summary.get("market_day"), "summary_shutdown_status": runtime_summary.get("shutdown_status"), "classification": "TRADING_DAY_OBSERVED" if trading_day_observed else "UNKNOWN_OR_CLOSED", "calendar_note": "Persisted production market rows prove collection occurred today even when a separate after-session runner summary reports MARKET_CLOSED."},
        "runtime_evidence": {"runtime_summary_path": str(today_runtime.relative_to(ROOT)), "summary": runtime_summary, "log": today_logs},
        "outage_assessment": {"classification": outage_classification, "confidence": confidence, "network_errors": network_evidence, "statement": "Absence of transport errors is not evidence that the user-reported internet outage did not occur; exact timing is not established."},
        "today_dataset_coverage": {environment: {name: {key: value for key, value in item.items() if key not in {"path"}} | {"path": item["path"]} for name, item in datasets.items()} for environment, datasets in inventory.items()},
        "historical_day_coverage": {date_key: {name: value for name, value in datasets.items()} for date_key, datasets in sorted(day_rows.items())},
        "historical_day_coverage_summary": historical_days,
        "bbo_longest_event_observation_gap": bbo_longest_observation_gap,
        "gap_records": gaps,
        "gap_severity": gap_severity(gaps),
        "recovery": {"historical_bbo": "BBO GAP — HISTORICAL RECOVERY NOT AVAILABLE (SDK exposes realtime callbacks; no historical depth method verified).", "candle_backfill": "BOUNDED_BACKFILL_APPLIED" if backfill_records else "NOT_ATTEMPTED", "backfill_evidence": {key: backfill_record.get(key) for key in ("symbol", "timeframe", "requested_start_bangkok", "requested_end_bangkok", "api_source", "api_schema_fields", "raw_rows", "in_range_rows", "returned_first_bangkok", "returned_last_bangkok", "validation_issues", "merge_preview", "backfill_applied", "rows_appended", "report_path")}, "backfill_evidence_records": [{key: record.get(key) for key in ("symbol", "timeframe", "requested_start_bangkok", "requested_end_bangkok", "api_source", "raw_rows", "in_range_rows", "returned_first_bangkok", "returned_last_bangkok", "backfill_applied", "rows_appended", "report_path")} for record in backfill_records], "rows_backfilled": sum(int(record.get("rows_appended") or 0) for record in backfill_records), "rows_still_missing": None, "missing_intervals_estimate": sum(gap.get("missing_intervals_estimate", 0) for gap in gaps), "missing_data_note": "Exact missing row count is unknown; gaps are estimated only between observed rows inside a configured market session, and BBO callback gaps cannot be reconstructed.", "fabricated_rows": 0},
        "orders_placed": 0,
        "historical_incomplete_dates": incomplete_days,
        "source_roots": {name: str(path.relative_to(ROOT)) for name, path in roots.items()},
    }
    return report


def main() -> int:
    report = build_report()
    target = ROOT / "reports" / "settrade_gap_recovery.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    summaries = {
        "settrade_current_day_gap_summary.json": {"generated_at": report["generated_at"], "today": report["today"], "trading_day_evidence": report["today_trading_day_evidence"], "outage_assessment": report["outage_assessment"], "runtime_evidence": report["runtime_evidence"], "production_coverage": report["today_dataset_coverage"]["production"], "gap_records": report["gap_records"], "longest_bbo_event_observation_gap": report["bbo_longest_event_observation_gap"], "recovery": report["recovery"]},
        "settrade_historical_day_coverage.json": {"generated_at": report["generated_at"], "historical_days": report["historical_day_coverage_summary"], "incomplete_dates": report["historical_incomplete_dates"]},
        "settrade_collector_resilience_summary.json": {"generated_at": report["generated_at"], "before_changes": "Runner retried every exception up to three attempts with fixed 30/60 second waits; auth errors were not distinguished; retry/reconnect counters were not incremented; each retry starts a fresh collector subprocess which restores configured subscriptions and re-reads current-day candle history.", "after_changes": "Runner classifies AUTH_FAILURE, NETWORK_FAILURE, RATE_LIMIT, and API_FAILURE; auth stops without retry; retry delay is capped exponential backoff (5, 10 seconds for the runner's two retries); retries start a fresh process/session, re-register subscriptions on the next cycle, and run the existing health scan after success.", "current_day_log_evidence": report["runtime_evidence"]["log"], "current_state_telemetry": "State transitions, PID, retries, reconnect count, last success, reason, and current delay are written to new runner summaries after the updated runner is used.", "checkpoint_policy": "Per-symbol candle checkpoints are not reset during reconnect. Current-day request spans midnight to next midnight; the existing deduplicating append path retains genuine rows and flags conflicts.", "historical_bbo": "Realtime callback gaps cannot be reconstructed; no synthetic BBO is created.", "orders_placed": 0},
        "settrade_ui_implementation_summary.json": {"generated_at": report["generated_at"], "dark_theme": "Streamlit base dark theme with shared slate surfaces, readable status colors, and Plotly dark template.", "tradingview_reference": "docs/TRADINGVIEW_UX_RESEARCH.md; anonymous public chart inspected with Playwright after the REA CDP endpoint proved unreachable.", "working_tools": ["Market Overview", "Multi-Stock Trends", "Correlation Lab", "Market Breadth", "Stock Detail", "Historical Data Explorer", "Candle Explorer", "Order Book Explorer", "Collection Health", "Data Quality", "Official TradeSim Validation"], "watchlist": "Daily close, 1D/5D/20D return, volume activity, volatility, and market-date freshness with sort/filter.", "heatmap": "Available daily-source metric selections include 1D/5D/20D return, volatility, ATR%, volume activity, and freshness; unsupported intraday return/spread explicitly report unavailable.", "data_truth": "Charts retain genuine source timestamps; gaps and stale values are not filled or labeled live.", "orders_placed": 0},
    }
    for filename, contents in summaries.items():
        (target.parent / filename).write_text(json.dumps(contents, indent=2, ensure_ascii=False), encoding="utf-8")
    summary = {"report": str(target.relative_to(ROOT)), "today": report["today"], "outage": report["outage_assessment"]["classification"], "production_counts": {key: value["today_rows"] for key, value in report["today_dataset_coverage"]["production"].items()}, "gap_records": len(report["gap_records"]), "orders_placed": 0}
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

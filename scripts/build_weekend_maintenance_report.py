"""Build a source-preserving weekly maintenance summary from audit artifacts."""
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WEEK = ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23"]
TRADING_DATES = WEEK[:4]


def _name(path: str) -> str:
    return str(path).replace("\\", "/").split("/")[-1]


def trading_dates_for_week(week_dates: list[str], holidays: set[str]) -> list[str]:
    """Return weekday dates excluding explicitly sourced exchange holidays."""
    from datetime import date
    return [day for day in week_dates if date.fromisoformat(day).weekday() < 5 and day not in holidays]


def classify_gap(settrade_present: bool, tradesim_present: bool, semantics_differ: bool = False) -> str:
    if settrade_present and tradesim_present and semantics_differ:
        return "SOURCE_SEMANTIC_DIFFERENCE"
    if settrade_present and not tradesim_present:
        return "TRADESIM_ONLY_GAP"
    if tradesim_present and not settrade_present:
        return "SETTRADE_ONLY_GAP"
    if not settrade_present and not tradesim_present:
        return "BOTH_SOURCES_GAP"
    return "UNKNOWN"


def manifest_delta(previous: dict[str, str], current: dict[str, str]) -> dict:
    return {"added": sorted(set(current) - set(previous)),
            "removed": sorted(set(previous) - set(current)),
            "changed": sorted(name for name in set(previous) & set(current) if previous[name] != current[name]),
            "unchanged": sorted(name for name in set(previous) & set(current) if previous[name] == current[name])}


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _archive(path: Path) -> dict:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        return {"path": str(path.relative_to(ROOT)), "sha256": digest,
                "size_bytes": path.stat().st_size, "member_count": len(archive.namelist()),
                "zip_integrity": "PASS" if corrupt is None else "FAIL",
                "corrupt_member": corrupt}


def _weekly_raw_bbo_quality() -> dict[str, dict]:
    path = ROOT / "data/pilot/settrade/production/raw/bid_offer/events.jsonl"
    accum: dict[str, dict] = {day: {"timestamps": [], "exact": set(), "key_payload": {}, "exact_duplicates": 0, "timestamp_symbol_conflicts": 0} for day in TRADING_DATES}
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            try:
                item = json.loads(line)
                received = datetime.fromisoformat(str(item["received_at"]).replace("Z", "+00:00"))
                local = received.astimezone(__import__("zoneinfo").ZoneInfo("Asia/Bangkok"))
                day = local.date().isoformat()
                if day not in accum:
                    continue
                signature = json.dumps(item, sort_keys=True, separators=(",", ":"))
                record = accum[day]
                if signature in record["exact"]:
                    record["exact_duplicates"] += 1
                else:
                    record["exact"].add(signature)
                event_key = (str(item.get("symbol")), local.isoformat())
                payload = json.dumps(item.get("payload"), sort_keys=True, separators=(",", ":"))
                previous = record["key_payload"].get(event_key)
                if previous is not None and previous != payload:
                    record["timestamp_symbol_conflicts"] += 1
                record["key_payload"][event_key] = payload
                record["timestamps"].append(local)
            except (KeyError, ValueError, TypeError, json.JSONDecodeError):
                continue
    result = {}
    for day, record in accum.items():
        times = sorted(record["timestamps"])
        gaps = [(right - left).total_seconds() for left, right in zip(times, times[1:])]
        result[day] = {"event_count": len(times), "longest_aggregate_event_silence_seconds": max(gaps, default=None),
                       "aggregate_silence_intervals_over_60s": sum(gap > 60 for gap in gaps),
                       "aggregate_silence_intervals_over_300s": sum(gap > 300 for gap in gaps),
                       "aggregate_silence_intervals_over_900s": sum(gap > 900 for gap in gaps),
                       "exact_duplicate_records": record["exact_duplicates"],
                       "same_symbol_timestamp_conflicts": record["timestamp_symbol_conflicts"],
                       "interpretation": "Aggregate callback silence only; BBO is event-driven and this is not an outage/stale-market classification."}
    return result


def build() -> dict:
    audit = _load("reports/settrade_collection_audit.json")
    gaps = _load("reports/settrade_gap_recovery.json")
    comparison = _load("reports/tradesim_vs_settrade_data_comparison.json")
    ticks_manifest = _load("reports/tradesim_official_tick_inventory.json")
    history_manifest = _load("reports/tradesim_official_history_inventory.json")
    archives = ROOT / "data/official/tradesim/archives"
    archive_rows = [_archive(archives / name) for name in ("Daily_Ticks.zip", "tradeSim_history.zip", "tradeSim_ticks.zip")]
    assert trading_dates_for_week(WEEK, {"2026-10-23"}) == TRADING_DATES
    coverage = {day: {"settrade": day in audit["raw_bbo"].get("days", {}),
                      "tradesim_ticks": day in ticks_manifest.get("dates", []),
                      "tradesim_history": day in history_manifest.get("dates", [])}
                for day in TRADING_DATES}
    bbo_quality = _weekly_raw_bbo_quality()
    weekly_gap_classes = {}
    for day in TRADING_DATES:
        both = coverage[day]["settrade"] and (coverage[day]["tradesim_ticks"] or coverage[day]["tradesim_history"])
        weekly_gap_classes[day] = "SOURCE_SEMANTIC_DIFFERENCE" if both else classify_gap(coverage[day]["settrade"], coverage[day]["tradesim_ticks"] or coverage[day]["tradesim_history"])
    weekly_gap_classes["2026-10-23"] = "MARKET_CLOSED"
    daily = {}
    for day in TRADING_DATES:
        bbo = audit["raw_bbo"].get("days", {}).get(day, {})
        normalized = audit["bbo"].get("days", {}).get(day, {})
        candle = {tf: details.get("days", {}).get(day, {}) for tf, details in audit["candles"]["timeframes"].items()}
        runtime = audit.get("daily_collection", {}).get(day, {})
        daily[day] = {
            "raw_bbo": {"events": bbo.get("events", 0), "symbols": bbo.get("symbols", 0),
                        "first_local": bbo.get("first_local"), "last_local": bbo.get("last_local"), **bbo_quality.get(day, {})},
            "normalized_bbo": {"depth_rows": normalized.get("rows", 0), "symbols": normalized.get("symbols", 0),
                               "first_local": normalized.get("first_local"), "last_local": normalized.get("last_local"),
                               "duplicate_keys": audit["bbo"].get("duplicate_keys", 0),
                               "locked_or_crossed_best_quotes": audit["bbo"].get("locked_or_crossed_best_quotes")},
            "candles": {tf: {key: item.get(key) for key in ("rows", "symbols", "first_local", "last_local", "duplicates", "invalid_ohlc", "missing_intervals", "missing_intervals_estimate", "status", "coverage_pct")}
                        for tf, item in candle.items()},
            "collector": {key: runtime.get(key) for key in ("runner_start_local", "runner_end_local", "bbo_events", "bbo_symbols", "candle_rows_by_timeframe", "retries", "errors", "termination", "quality", "runtime_log_clock_conflict")},
            "audit_quality": audit.get("daily_collection", {}).get(day, {}).get("quality"),
        }
    cross_source = {}
    for tf, result in comparison.get("history_settrade_comparison", {}).items():
        production = result.get("PRODUCTION", {})
        cross_source[tf] = {"overlap_dates": [day for day in production.get("overlap_dates", []) if day in TRADING_DATES],
                            "source_only_dates": {k: [day for day in v if day in TRADING_DATES] for k, v in production.get("source_only_dates", {}).items()},
                            "counts": production.get("counts", {}),
                            "interpretation": "Broad comparison includes the 2026-10-19 through 2026-10-21 overlap; Oct 22 is Settrade-only at this archive cutoff. Never merge or force equality."}
    tick_inventory = {key: ticks_manifest.get(key) for key in ("generated_at_utc", "source", "archive_identity", "dates", "file_count", "total_rows", "symbols") if key in ticks_manifest}
    history_inventory = {key: history_manifest.get(key) for key in ("generated_at_utc", "source", "archive_identity", "dates", "file_count", "total_rows", "symbols") if key in history_manifest}
    expected_hashes = {
        "Daily_Ticks.zip": ticks_manifest.get("archive_identity", {}).get("outer_sha256"),
        "tradeSim_history.zip": ticks_manifest.get("archive_identity", {}).get("nested_archives", {}).get("tradeSim_history.zip", {}).get("sha256"),
        "tradeSim_ticks.zip": ticks_manifest.get("archive_identity", {}).get("nested_archives", {}).get("tradeSim_ticks.zip", {}).get("sha256"),
    }
    hash_checks = {_name(row["path"]): {"current_sha256": row["sha256"], "manifest_sha256": expected_hashes.get(_name(row["path"])), "unchanged": row["sha256"].lower() == str(expected_hashes.get(_name(row["path"]))).lower()} for row in archive_rows}
    tick_files = [item for item in ticks_manifest.get("files", []) if any(day in item.get("path", "") for day in TRADING_DATES)]
    weekly_tick_quality = [{key: item.get(key) for key in ("path", "rows", "symbol_count", "earliest_timestamp", "latest_timestamp", "duplicate_full_rows", "duplicate_symbol_timestamp_rows", "out_of_order_timestamps_global", "out_of_order_timestamps_within_symbol", "invalid_timestamps", "invalid_numeric_values", "invalid_price_rows", "negative_volume_rows", "malformed_rows", "sha256")} for item in tick_files]
    return {
        "schema_version": 1, "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "audited_week": {"start": WEEK[0], "end": WEEK[-1], "trading_dates": TRADING_DATES,
                         "holiday_or_nontrading": [{"date": "2026-10-23", "reason": "SET holiday: H.M. King Chulalongkorn the Great Memorial Day", "source": "https://www.set.or.th/en/about/event-calendar/holiday?year=2026"}],
                         "coverage": coverage,
                         "insufficient_evidence": ["Official TradeSim source coverage for 2026-10-22: archive ends at 2026-10-21; cannot compare that trading date."]},
        "settrade": {"audit_generated_at": audit.get("generated_at"), "provenance": "SETTRADE_PRODUCTION files with production source environment; report-backed collector telemetry", "daily": daily,
                     "overall": {"raw_bbo": {key: audit.get("raw_bbo", {}).get(key) for key in ("valid_events", "malformed_records", "exact_duplicate_records", "timestamp_ordering_issues", "symbol_mismatches", "symbols")},
                                 "normalized_bbo": {key: audit.get("bbo", {}).get(key) for key in ("rows", "symbols", "duplicate_keys", "negative_price", "negative_volume", "malformed_timestamps", "timestamp_ordering_issues_in_file", "locked_or_crossed_best_quotes", "unexpected_symbols")},
                                 "candles": {tf: {key: details.get(key) for key in ("rows", "symbols", "source_type", "timestamp_parse_errors", "duplicate_keys", "first_local", "last_local")} for tf, details in audit.get("candles", {}).get("timeframes", {}).items()},
                                 "daily_dataset": "ABSENT_FROM_SETTRADE_PILOT"}},
        "collector_classification": {"2026-10-19": "UNKNOWN (complete observed data; no reconnect/retry evidence)", "2026-10-20": "UNKNOWN (13 logged errors; zero retries; clock conflict; no exact outage interval established)", "2026-10-21": "UNKNOWN (persisted trading data contradicts prior audit's NON_TRADING_DAY label)", "2026-10-22": "UNKNOWN (persisted sessions show trading data; clock conflict requires telemetry cleanup)", "2026-10-23": "MARKET_CLOSED (official SET holiday; no candles; bounded callback activity does not establish an outage)"},
        "gaps": {"fresh_gap_report_generated_at": gaps.get("generated_at"), "weekly_date_classes": weekly_gap_classes,
                 "weekly_class_counts": {key: list(weekly_gap_classes.values()).count(key) for key in sorted(set(weekly_gap_classes.values()))},
                 "weekly_records": [row for row in gaps.get("gap_records", []) if row.get("date") in WEEK],
                 "recovery": gaps.get("recovery"), "backfills_appended_this_maintenance": 0,
                 "historical_backfill_rows_reported_in_cumulative_gap_artifact": gaps.get("recovery", {}).get("rows_backfilled", 0),
                 "classification_policy": "No missing candle interval is called a network outage absent runtime evidence; realtime BBO history is not recoverable through a verified historical API."},
        "official_tradesim": {"archives": archive_rows, "ticks": tick_inventory, "history": history_inventory,
                              "weekly_tick_file_quality": weekly_tick_quality,
                              "manifest_status": "UNCHANGED" if all(value["unchanged"] for value in hash_checks.values()) else "CHANGED_OR_MANIFEST_MISMATCH",
                              "archive_hash_checks": hash_checks,
                              "manifest_delta": manifest_delta({name: str(values["manifest_sha256"]).lower() for name, values in hash_checks.items() if values["manifest_sha256"]}, {name: values["current_sha256"].lower() for name, values in hash_checks.items()})},
        "cross_source": cross_source,
        "data_quality_scorecard": {"settrade_bbo": "HEALTHY_WITH_WARNINGS", "settrade_1m": "DEGRADED", "settrade_5m": "DEGRADED", "settrade_15m": "HEALTHY_WITH_WARNINGS", "settrade_daily": "UNKNOWN (not persisted in Settrade pilot)", "tradesim_ticks": "HEALTHY_WITH_WARNINGS", "tradesim_history": "HEALTHY_WITH_WARNINGS", "provenance": "HEALTHY", "collector_telemetry": "DEGRADED", "cross_source_diagnostics": "HEALTHY_WITH_WARNINGS"},
        "maintenance_fixes": ["Refreshed persisted Settrade weekly audit, gap report, and source comparison from existing data.", "Refreshed official archive inventory hashes and integrity read-only; no archive content changed.", "No safe API backfill was justified: production historical 1m probe returned no rows; BBO history unavailable; no source was used to replace another."],
        "next_session_checklist": ["Confirm collector's local clock/timezone field is Asia/Bangkok before session start.", "Check collector process and health before opening; verify checkpoints and source_environment=PRODUCTION.", "Check 1m/5m/15m freshness and integrity after close.", "Refresh organizer archives after next official release, then compare per-archive hashes before ingest.", "Do not backfill gaps without a bounded successful read-only API probe and conflict-safe merge preview."],
        "orders_placed": 0, "organizer_raw_data_modified": False, "synthetic_market_data_created": False,
    }


if __name__ == "__main__":
    output = build()
    (ROOT / "reports/weekend_data_maintenance.json").write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"week": output["audited_week"], "trading_dates": output["audited_week"]["trading_dates"], "backfills_this_maintenance": output["gaps"]["backfills_appended_this_maintenance"], "scorecard": output["data_quality_scorecard"]}, indent=2))

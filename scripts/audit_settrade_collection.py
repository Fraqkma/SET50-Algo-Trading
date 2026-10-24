"""Generate the durable, read-only Settrade pilot collection audit."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade.audit import bbo_audit, candle_audit, inventory, runtime_audit
from src.data.settrade.paths import resolve_data_root


def _local_iso(value: object) -> str | None:
    if not value:
        return None
    stamp = pd.Timestamp(value)
    return (stamp.tz_localize("Asia/Bangkok") if stamp.tzinfo is None else stamp.tz_convert("Asia/Bangkok")).isoformat()


def classify_runtime_market_day(runtime: dict, raw_bbo_events: int, candle_rows: int) -> str | None:
    """Do not let a contradictory runtime flag hide persisted market observations."""
    if runtime.get("market_day") is not False:
        return None
    if raw_bbo_events or candle_rows:
        return "RUNTIME_MARKET_DAY_CONFLICT_WITH_DATA"
    return "NON_TRADING_DAY"


def _markdown(report: dict) -> str:
    lines = ["# Settrade collection audit", "", "Generated from persisted pilot artifacts; no source data were modified.", ""]
    lines.append("## Collection summary")
    bbo_days = sorted(report["bbo"].get("days", {}))
    runtime = report.get("runtime", [])
    failures = sum(1 for row in runtime if row.get("shutdown_status") == "FAILED")
    successful = sum(1 for row in runtime if row.get("shutdown_status", "").startswith("MARKET_CLOSED"))
    lines.extend([f"- Collection dates with persisted BBO: {bbo_days[0] if bbo_days else 'none'} to {bbo_days[-1] if bbo_days else 'none'}", f"- Valid raw BBO events: {report.get('raw_bbo', {}).get('valid_events', 0)}; malformed raw records: {report.get('raw_bbo', {}).get('malformed_records', 0)}; normalized depth rows: {report['bbo'].get('rows', 0)}", f"- Candle rows: " + ", ".join(f"{key}={value.get('rows', 0)} ({value.get('symbols', 0)} symbols)" for key, value in report['candles']['timeframes'].items()), f"- Runtime summaries: {len(runtime)}; failed terminations: {failures}; completed/closed runs: {successful}", ""])
    lines.append(f"Weekdays with no Settrade log/runtime/data artifact in the evidence window: {report.get('weekday_dates_without_artifacts', [])}. A calendar weekday alone is not proof the market was open.")
    lines.append("## Daily collection evidence")
    for day, record in report.get("daily_collection", {}).items():
        lines.append(f"- **{day}** — runner/log {record.get('runner_start_local') or 'UNKNOWN'} to {record.get('runner_end_local') or 'UNKNOWN'}; BBO {record.get('bbo_events', 0)} raw events / {record.get('normalized_bbo_depth_rows', 0)} depth rows / {record.get('bbo_symbols', 0)} symbols; morning {record.get('morning_first_local') or 'no observed event'}–{record.get('morning_last_local') or 'no observed event'}, afternoon {record.get('afternoon_first_local') or 'no observed event'}–{record.get('afternoon_last_local') or 'no observed event'}; candle rows {record.get('candle_rows_by_timeframe', {})}; retries/errors {record.get('retries', 0)}/{record.get('errors', 0)}; termination {record.get('termination') or 'UNKNOWN'}; summary/log clock conflict {record.get('runtime_log_clock_conflict')}; quality **{record.get('quality', 'UNKNOWN')}**; gap {record.get('gap_assessment')}.")
    lines.append("")
    lines.append("## Readiness")
    for key, value in report["readiness"].items():
        lines.append(f"- **{key}:** {value}")
    lines.extend(["", "## Candle audit"])
    for timeframe, value in report["candles"]["timeframes"].items():
        lines.append(f"### {timeframe}: {value.get('rows', 0)} rows, {value.get('symbols', 0)} symbols; {value.get('source_type', 'source lineage UNKNOWN')}")
        for day, day_value in value.get("days", {}).items():
            lines.append(f"- {day}: {day_value.get('status')} — observed {day_value.get('rows', 0)} / expected {day_value.get('expected_intervals', 0)}, coverage {day_value.get('coverage_pct', 0)}%, first {day_value.get('first_local')}, last {day_value.get('last_local')}")
    lines.extend(["", "## BBO audit", f"- Status: {report['bbo'].get('status')}", f"- Raw genuine events: {report.get('raw_bbo', {}).get('valid_events', 0)}; normalized depth rows: {report['bbo'].get('rows', 0)}; trading days: {report['bbo'].get('trading_days', 0)}; symbols: {report['bbo'].get('symbols', 0)}", f"- Exact duplicate normalized keys: {report['bbo'].get('duplicate_keys', 0)}; negative prices/sizes: {report['bbo'].get('negative_price', 0)}/{report['bbo'].get('negative_volume', 0)}; malformed timestamps: {report['bbo'].get('malformed_timestamps', 0)}; file-order timestamp regressions: {report['bbo'].get('timestamp_ordering_issues_in_file', 0)}", f"- Locked/crossed best quotes: {report['bbo'].get('locked_or_crossed_best_quotes')}; unexpected symbols: {report['bbo'].get('unexpected_symbols', [])}", "", "BBO is event-driven: absence of callbacks is not itself a gap. Collection windows are judged from runner/log evidence; unresolved causes are UNKNOWN.", ""])
    for day, value in report["bbo"].get("days", {}).items():
        lines.append(f"### {day}: {value['rows']} normalized depth rows, {value['symbols']} symbols, {value.get('raw_event_count', 'UNKNOWN')} raw events; {value.get('first_local')} to {value.get('last_local')}")
        for group in value["groups"]:
            lines.append(f"- Group {group['group']}: {group['observed_symbols']}/{group['expected_topics']} symbols observed; missing {', '.join(group['missing_symbols']) or 'none'}")
    rotation = report.get("rotation_health", {})
    lines.append(f"35/15 rotation: all 50 symbols observed={rotation.get('all_50_symbols_observed')}; opportunity dwell time={rotation.get('opportunity_dwell_time')}")
    for group_id, group in rotation.get("groups", {}).items():
        lines.append(f"- Group {group_id}: {group['observed_symbol_count']}/{group['expected_symbols']} expected symbols observed in {group['raw_callback_count']} callbacks across {group['days_with_callbacks']} days; missing observed symbols {group['missing_observed_symbols']}")
    availability = report.get("candle_availability", {})
    lines.append(f"Current-session candle delays: {availability.get('interpretation', 'UNKNOWN')}")
    lines.append("Non-empty raw candle response counts by date: " + ", ".join(f"{day} ({item['symbols_with_nonempty_response']} symbols)" for day, item in availability.get("days", {}).items()))
    lines.extend(["", "## Runtime summaries", "", "```json", json.dumps(report["runtime"], indent=2, ensure_ascii=False), "```", ""])
    return "\n".join(lines)


def main() -> int:
    config = yaml.safe_load((ROOT / "config" / "settrade_collection.yaml").read_text(encoding="utf-8"))
    symbols = list(config["current_set50"])
    max_topics = int(config["realtime"]["bid_offer_topics_per_rotation"])
    groups = [symbols[index : index + max_topics] for index in range(0, len(symbols), max_topics)]
    pilot = resolve_data_root(ROOT, config.get("storage_root", "data/pilot/settrade"))
    report = {
        "generated_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source": "active Settrade data root and reports/runtime",
        "active_repo_path": str(ROOT.resolve()),
        "active_data_root": str(pilot),
        "universe": {"name": "current_set50", "symbols": symbols, "count": len(symbols), "exactly_50_unique": len(symbols) == 50 and len(set(symbols)) == 50},
        "rotation": {"max_topics": max_topics, "group_sizes": [len(group) for group in groups], "group_count": len(groups)},
        "inventory": inventory(pilot),
        "candles": candle_audit(pilot),
        "bbo": bbo_audit(pilot, symbols, groups),
        "runtime": runtime_audit(ROOT / "reports" / "runtime"),
    }
    raw_path = pilot / "raw" / "bid_offer" / "events.jsonl"
    raw_events: list[dict] = []
    malformed_raw = 0
    duplicate_raw = 0
    raw_seen: set[str] = set()
    raw_order_issues = 0
    previous_ts = None
    raw_symbol_mismatches = 0
    if raw_path.exists():
        with raw_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    malformed_raw += 1
                    continue
                raw_events.append(item)
                signature = json.dumps(item, sort_keys=True, separators=(",", ":"))
                if signature in raw_seen:
                    duplicate_raw += 1
                raw_seen.add(signature)
                stamp = pd.to_datetime(item.get("received_at"), errors="coerce", utc=True)
                if pd.isna(stamp):
                    malformed_raw += 1
                elif previous_ts is not None and stamp < previous_ts:
                    raw_order_issues += 1
                if not pd.isna(stamp):
                    previous_ts = stamp
                if str(item.get("symbol", "")).upper() != str(item.get("payload", {}).get("symbol", "")).upper():
                    raw_symbol_mismatches += 1
    raw_by_day: dict[str, list[dict]] = defaultdict(list)
    for event in raw_events:
        stamp = pd.to_datetime(event.get("received_at"), errors="coerce", utc=True)
        if not pd.isna(stamp):
            local = stamp.tz_convert("Asia/Bangkok")
            event["_timestamp_local"] = local
            raw_by_day[str(local.date())].append(event)
    for day, day_data in report["bbo"].get("days", {}).items():
        day_data["raw_event_count"] = len(raw_by_day.get(day, []))
    report["raw_bbo"] = {
        "valid_events": len(raw_events), "malformed_records": malformed_raw,
        "exact_duplicate_records": duplicate_raw, "timestamp_ordering_issues": raw_order_issues,
        "symbol_mismatches": raw_symbol_mismatches,
        "symbols": len({str(item.get("symbol")) for item in raw_events if item.get("symbol")}),
        "days": {day: {"events": len(events), "symbols": len({str(event.get("symbol")) for event in events}), "first_local": min((event["_timestamp_local"] for event in events)).isoformat(), "last_local": max((event["_timestamp_local"] for event in events)).isoformat(), "groups": dict(Counter(str(event.get("rotation_group", "UNKNOWN")) for event in events)), "generations": sorted({event.get("generation") for event in events if event.get("generation") is not None})} for day, events in raw_by_day.items()},
        "by_symbol": {
            symbol: {
                "events": len(events),
                "first_local": min(event["_timestamp_local"] for event in events).isoformat(),
                "last_local": max(event["_timestamp_local"] for event in events).isoformat(),
                "days": len({event["_timestamp_local"].date() for event in events}),
                "rotation_groups": dict(Counter(str(event.get("rotation_group", "UNKNOWN")) for event in events)),
            }
            for symbol, events in ((symbol, [event for event in raw_events if str(event.get("symbol")) == symbol and event.get("_timestamp_local") is not None]) for symbol in sorted({str(event.get("symbol")) for event in raw_events if event.get("symbol")}))
        },
    }
    candle_probe_path = pilot / "raw" / "candles" / "1m.jsonl"
    candle_availability: dict[str, dict[str, dict]] = defaultdict(dict)
    candle_raw_count = 0
    candle_nonempty_count = 0
    if candle_probe_path.exists():
        with candle_probe_path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError:
                    continue
                candle_raw_count += 1
                response_times = item.get("response", {}).get("time") or []
                if not response_times:
                    continue
                retrieved = pd.to_datetime(item.get("retrieved_at"), errors="coerce", utc=True)
                if pd.isna(retrieved):
                    continue
                candle_nonempty_count += 1
                local = retrieved.tz_convert("Asia/Bangkok")
                day = str(local.date())
                symbol = str(item.get("symbol", "UNKNOWN"))
                existing = candle_availability[day].get(symbol)
                if existing is None or local < pd.Timestamp(existing["first_nonempty_retrieval"]):
                    candle_availability[day][symbol] = {
                        "first_nonempty_retrieval": local.isoformat(), "returned_rows": len(response_times),
                        "requested_start": item.get("request_start"), "requested_end": item.get("request_end"),
                    }
    report["candle_availability"] = {
        "source": "raw persisted 1m candle API responses; first non-empty response time is an observed lower bound, not exact upstream publication time",
        "raw_response_records": candle_raw_count, "nonempty_response_records": candle_nonempty_count,
        "days": {day: {"symbols_with_nonempty_response": len(found), "first_nonempty_by_symbol": dict(sorted(found.items()))} for day, found in candle_availability.items()},
        "interpretation": "Persisted responses demonstrate continued symbol/date-specific delayed availability. Earlier empty responses were not converted into candles; exact upstream first-availability times are unknown.",
    }
    rotation_groups = {}
    for index, expected_group in enumerate(groups):
        group_events = [event for event in raw_events if str(event.get("rotation_group")) == str(index)]
        observed_group_symbols = sorted({str(event.get("symbol")) for event in group_events})
        generations = sorted({int(event["generation"]) for event in group_events if str(event.get("generation", "")).isdigit()})
        rotation_groups[str(index)] = {
            "expected_symbols": len(expected_group), "expected_symbol_list": expected_group,
            "observed_symbols": observed_group_symbols, "observed_symbol_count": len(observed_group_symbols),
            "missing_observed_symbols": sorted(set(expected_group) - set(observed_group_symbols)),
            "unexpected_observed_symbols": sorted(set(observed_group_symbols) - set(expected_group)),
            "raw_callback_count": len(group_events),
            "days_with_callbacks": len({event["_timestamp_local"].date().isoformat() for event in group_events if event.get("_timestamp_local") is not None}),
            "generation_count": len(generations), "first_generation": generations[0] if generations else None,
            "last_generation": generations[-1] if generations else None,
            "subscription_opportunity": "UNKNOWN from artifacts; raw callbacks prove observed updates, not complete subscription dwell time",
        }
    report["rotation_health"] = {
        "design": "neutral 35/15 two-group rotation", "groups": rotation_groups,
        "all_50_symbols_observed": set().union(*(set(item["observed_symbols"]) for item in rotation_groups.values())) == set(symbols),
        "opportunity_dwell_time": "UNKNOWN; retained artifacts do not record per-symbol subscribe/unsubscribe timestamps for every generation",
        "assessment": "Both groups generated callbacks over multiple sessions; callback presence supports operation. Full opportunity and dwell-time verification is not possible from retained checkpoints/logs.",
    }
    generation_checks = {}
    for day, events in raw_by_day.items():
        generations = sorted({int(event["generation"]) for event in events if str(event.get("generation", "")).isdigit()})
        missing = sorted(set(range(generations[0], generations[-1] + 1)) - set(generations)) if generations else []
        parity_mismatches = sum(
            1 for event in events
            if str(event.get("generation", "")).isdigit()
            and str(event.get("rotation_group", "")) in {"0", "1"}
            and int(event["generation"]) % 2 != int(event["rotation_group"])
        )
        generation_checks[day] = {
            "generation_count": len(generations), "first_generation": generations[0] if generations else None,
            "last_generation": generations[-1] if generations else None, "missing_generations": missing,
            "generation_sequence_contiguous": bool(generations) and not missing,
            "group_generation_parity_mismatches": parity_mismatches,
        }
    report["rotation_health"]["generation_checks_by_day"] = generation_checks
    log_records = {}
    log_root = ROOT / "logs" / "settrade"
    for log_path in sorted(log_root.glob("daily-*.log")):
        day = log_path.stem.removeprefix("daily-")
        text = log_path.read_text(encoding="utf-8", errors="replace")
        stamps = re.findall(r"(?m)^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d(?:,\d+)?)", text)
        local_stamps = [
            pd.Timestamp(stamp.replace(",", ".")).tz_localize("Asia/Bangkok").isoformat()
            for stamp in stamps
            if stamp[:10] == day
        ]
        log_records[day] = {"first_log_local": local_stamps[0] if local_stamps else None, "last_log_local": local_stamps[-1] if local_stamps else None, "retry_lines": len(re.findall(r"(?i)retry", text)), "error_lines": len(re.findall(r"(?i)\b(error|exception|failed)\b", text)), "log_bytes": log_path.stat().st_size, "log_gap_classification": "UNKNOWN"}
    runtime_by_day = {str(item.get("date")): item for item in report["runtime"] if item.get("date")}
    candle_day_maps = {tf: value.get("days", {}) for tf, value in report["candles"]["timeframes"].items()}
    all_days = sorted(set(report["bbo"].get("days", {})) | set(report["raw_bbo"]["days"]) | set(runtime_by_day) | set(log_records) | {day for values in candle_day_maps.values() for day in values})
    daily = {}
    for day in all_days:
        runtime = runtime_by_day.get(day, {})
        log = log_records.get(day, {})
        raw_day = report["raw_bbo"]["days"].get(day, {})
        norm_day = report["bbo"].get("days", {}).get(day, {})
        event_times = [event["_timestamp_local"] for event in raw_by_day.get(day, [])]
        morning = [ts for ts in event_times if ts.hour * 60 + ts.minute < 12 * 60 + 30]
        afternoon = [ts for ts in event_times if ts.hour * 60 + ts.minute >= 14 * 60 + 30]
        per_tf = {tf: int(candle_day_maps[tf].get(day, {}).get("rows", 0)) for tf in candle_day_maps}
        termination = runtime.get("shutdown_status")
        quality = "VALID_DATA" if raw_day.get("events", 0) else "NO_BBO_DATA"
        if termination == "FAILED":
            quality = "ABNORMAL_TERMINATION"
        if not runtime and day in log_records:
            quality = "PARTIAL_SESSION_MORNING_ONLY" if raw_day.get("events", 0) and not afternoon else "LOG_ONLY_PARTIAL_OR_UNKNOWN"
        market_day_quality = classify_runtime_market_day(runtime, int(raw_day.get("events", 0)), sum(per_tf.values()))
        if market_day_quality:
            quality = market_day_quality
        last_log = pd.Timestamp(log["last_log_local"]) if log.get("last_log_local") else None
        probable_gap = bool(raw_day.get("events", 0) and not afternoon and last_log is not None and (last_log.hour * 60 + last_log.minute) < 14 * 60 + 30)
        if probable_gap:
            quality = "PARTIAL_SESSION_PROBABLE_COLLECTOR_OR_LOG_GAP"
        daily[day] = {
            "runner_start_local": log.get("first_log_local") or _local_iso(runtime.get("start_time")),
            "runner_end_local": log.get("last_log_local") or _local_iso(runtime.get("end_time")),
            "runtime_summary_start_reported": runtime.get("start_time"),
            "runtime_summary_end_reported": runtime.get("end_time"),
            "runtime_log_clock_conflict": bool(log.get("first_log_local") and runtime.get("start_time") and abs((pd.Timestamp(log["first_log_local"]) - pd.Timestamp(runtime["start_time"]).tz_convert("Asia/Bangkok")).total_seconds()) > 60),
            "morning_first_local": min(morning).isoformat() if morning else None,
            "morning_last_local": max(morning).isoformat() if morning else None,
            "afternoon_first_local": min(afternoon).isoformat() if afternoon else None,
            "afternoon_last_local": max(afternoon).isoformat() if afternoon else None,
            "bbo_events": raw_day.get("events", 0), "bbo_symbols": raw_day.get("symbols", 0),
            "normalized_bbo_depth_rows": norm_day.get("rows", 0),
            "candle_rows_by_timeframe": per_tf,
            "retries": runtime.get("retries", log.get("retry_lines", 0)),
            "errors": runtime.get("rate_limit_errors", 0) + runtime.get("validation_errors", 0) + log.get("error_lines", 0),
            "termination": termination, "log_evidence": log,
            "gap_assessment": "PROBABLE_COLLECTOR_OR_LOG_GAP_AFTER_LAST_LOG; exact cause UNKNOWN" if probable_gap else "No downtime inferred from event silence alone; event-driven silence is normal and other gaps remain UNKNOWN",
            "subscription_opportunity": "UNKNOWN unless evidenced by subscription checkpoint/log; observed callbacks are reported separately",
            "rotation_generations": raw_day.get("generations", []), "rotation_groups_observed": raw_day.get("groups", {}),
            "quality": quality,
        }
    report["daily_collection"] = daily
    if all_days:
        calendar = pd.date_range(min(pd.Timestamp(day) for day in all_days), max(pd.Timestamp(day) for day in all_days), freq="D")
        evidence_days = {pd.Timestamp(day).date() for day in all_days}
        report["weekday_dates_without_artifacts"] = [
            day.date().isoformat() for day in calendar
            if day.weekday() < 5 and day.date() not in evidence_days
        ]
    else:
        report["weekday_dates_without_artifacts"] = []
    report["raw_bbo_event_lines"] = len(raw_events) + malformed_raw
    report["collection_summary"] = {
        "bbo_date_range": sorted(report["bbo"].get("days", {}))[:1] + sorted(report["bbo"].get("days", {}))[-1:] if report["bbo"].get("days") else [],
        "raw_bbo_event_lines": report["raw_bbo_event_lines"],
        "normalized_bbo_depth_rows": report["bbo"].get("rows", 0),
        "candle_rows_by_timeframe": {key: value.get("rows", 0) for key, value in report["candles"]["timeframes"].items()},
    }
    candle_readiness = {}
    for timeframe, value in report["candles"]["timeframes"].items():
        expected = sum(int(day.get("expected_intervals", 0)) for day in value.get("days", {}).values())
        observed = int(value.get("rows", 0))
        coverage = observed / expected if expected else 0
        candle_readiness[timeframe] = "NO_DATA" if not observed else "SPARSE" if coverage < 0.1 else "PARTIAL" if coverage < 0.8 else "READY_FOR_EXPLORATORY_RESEARCH"
    report["readiness"] = {
        "universe": "READY" if report["universe"]["exactly_50_unique"] else "BLOCKED",
        "bbo": "READY_FOR_EXPLORATORY_RESEARCH" if report["raw_bbo"].get("valid_events", 0) > 0 and report["bbo"].get("status") == "READY" else "NEEDS_REVIEW",
        "bbo_raw_events": "READY_FOR_EXPLORATORY_RESEARCH" if report["raw_bbo"].get("valid_events", 0) > 0 else "NO_DATA",
        "bbo_normalized_depth": "READY_FOR_EXPLORATORY_RESEARCH" if report["bbo"].get("status") == "READY" and report["bbo"].get("rows", 0) > 0 else "NEEDS_REVIEW",
        "candles": candle_readiness,
        "orders": "0 (read-only audit)",
    }
    json_path = ROOT / "reports" / "settrade_collection_audit.json"
    md_path = ROOT / "reports" / "settrade_collection_audit.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    md_path.write_text(_markdown(report), encoding="utf-8")
    print(json.dumps({"json": str(json_path), "markdown": str(md_path), "readiness": report["readiness"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

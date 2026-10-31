"""Create a source-aware coverage snapshot without changing market-data rows."""
from __future__ import annotations

import json
import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade.paths import resolve_data_root


DATASETS = {
    "raw_bbo": ("raw/bid_offer/events.jsonl", "jsonl"),
    "normalized_bbo": ("normalized/bid_offer/data.csv", "csv"),
    "candles_1m": ("normalized/bars_1m/data.csv", "csv"),
    "candles_5m": ("normalized/bars_5m/data.csv", "csv"),
    "candles_15m": ("normalized/bars_15m/data.csv", "csv"),
}


def _local_stamp(value: object) -> str | None:
    try:
        raw = str(value).strip()
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=ZoneInfo("Asia/Bangkok"))
        return parsed.astimezone(ZoneInfo("Asia/Bangkok")).isoformat()
    except (TypeError, ValueError, OverflowError):
        return None


def _dataset_day_rows(root: Path, relative: str, fmt: str) -> dict[str, list[dict]]:
    path = root / relative
    groups: dict[str, list[dict]] = defaultdict(list)
    if not path.exists():
        return groups
    try:
        if fmt == "jsonl":
            with path.open(encoding="utf-8") as handle:
                for line in handle:
                    try:
                        row = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    stamp = _local_stamp(row.get("received_at") or row.get("event_timestamp") or row.get("timestamp"))
                    if stamp:
                        groups[stamp[:10]].append({"symbol": row.get("symbol"), "timestamp": stamp})
        else:
            with path.open(encoding="utf-8", newline="") as handle:
                for row in csv.DictReader(handle):
                    # Candles are keyed by market time, never retrieval/cycle time.
                    stamp = _local_stamp(row.get("timestamp") or row.get("event_timestamp") or row.get("retrieved_at"))
                    if stamp:
                        groups[stamp[:10]].append({**row, "symbol": row.get("symbol"), "timestamp": stamp})
    except (OSError, csv.Error, UnicodeDecodeError):
        return groups
    return groups


def _load_dataset_rows(roots: dict[str, tuple[Path, str]]) -> dict[str, dict[str, list[dict]]]:
    loaded: dict[str, dict[str, list[dict]]] = {}
    for env, (root, _) in roots.items():
        for dataset, (relative, fmt) in DATASETS.items():
            loaded[f"{env}:{dataset}"] = _dataset_day_rows(root, relative, fmt)
    return loaded


def _day_by_day(prior: dict, roots: dict[str, tuple[Path, str]], loaded: dict[str, dict[str, list[dict]]] | None = None) -> dict:
    universe = sorted(set(prior.get("universe", {}).get("symbols", [])))
    runtime_days = prior.get("daily_collection", {})
    evidence_days = set(runtime_days) | set(prior.get("weekday_dates_without_artifacts", []))
    loaded = loaded or _load_dataset_rows(roots)
    for env, (root, _) in roots.items():
        for dataset, (relative, fmt) in DATASETS.items():
            evidence_days.update(loaded[f"{env}:{dataset}"].keys())

    result: dict[str, dict] = {}
    for dataset in DATASETS:
        per_day: dict[str, dict] = {}
        for day in sorted(evidence_days):
            day_items = {}
            for env in roots:
                rows = loaded.get(f"{env}:{dataset}", {}).get(day, [])
                symbols = sorted({str(row["symbol"]) for row in rows if row.get("symbol")})
                runtime_quality = runtime_days.get(day, {}).get("quality")
                expect_universe = (
                    env == "sandbox"
                    and dataset.startswith("candles_")
                    and datetime.fromisoformat(day).weekday() < 5
                    and day in runtime_days
                    and runtime_quality != "NON_TRADING_DAY"
                )
                missing = sorted(set(universe) - set(symbols)) if expect_universe else []
                stamps = sorted(str(row["timestamp"]) for row in rows if row.get("timestamp"))
                gaps = []
                approximate_session_coverage = "UNKNOWN (event-driven BBO has no fixed expected interval)"
                if dataset.startswith("candles_"):
                    interval = {"candles_1m": 60, "candles_5m": 300, "candles_15m": 900}[dataset]
                    by_symbol: dict[str, list] = defaultdict(list)
                    for row in rows:
                        if row.get("symbol"):
                            try:
                                by_symbol[str(row["symbol"])].append(datetime.fromisoformat(row["timestamp"]))
                            except ValueError:
                                continue
                    for symbol, points in by_symbol.items():
                        ordered = sorted(set(points))
                        for left, right in zip(ordered, ordered[1:]):
                            # The regular SET midday recess is not an intraday gap.
                            if left.hour < 13 and right.hour >= 14:
                                continue
                            missing_intervals = int((right - left).total_seconds() // interval) - 1
                            if missing_intervals > 0:
                                gaps.append({"symbol": symbol, "after": left.isoformat(), "before": right.isoformat(), "missing_intervals_estimate": missing_intervals})
                    if expect_universe and universe:
                        expected_slots = {"candles_1m": 270, "candles_5m": 54, "candles_15m": 18}[dataset] * len(universe)
                        observed_slots = sum(len(set(points)) for points in by_symbol.values())
                        approximate_session_coverage = round(min(observed_slots / expected_slots, 1.0), 4)
                    elif not expect_universe:
                        approximate_session_coverage = "UNKNOWN (expected universe/session not evidenced)"
                runtime = runtime_days.get(day)
                provenance = "UNKNOWN" if env == "sandbox" else "PRODUCTION"
                if env == "sandbox" and rows:
                    provenance = "SANDBOX"
                calendar_nontrading = datetime.fromisoformat(day).weekday() >= 5 or bool(runtime and runtime.get("quality") == "NON_TRADING_DAY")
                bbo_session_without_events = dataset in {"raw_bbo", "normalized_bbo"} and runtime is not None and not calendar_nontrading and not rows
                has_unclassified_gap = not rows or bool(missing) or bool(gaps)
                day_items[env] = {
                    "path": str(roots[env][0] / DATASETS[dataset][0]),
                    "provenance": provenance,
                    "rows_or_events": len(rows),
                    "observed_symbol_count": len(symbols),
                    "expected_universe_size": len(universe) if expect_universe else None,
                    "missing_symbols": missing,
                    "first_timestamp_bangkok": stamps[0] if stamps else None,
                    "last_timestamp_bangkok": stamps[-1] if stamps else None,
                    "approximate_session_coverage": approximate_session_coverage,
                    "missing_interval_estimates": gaps,
                    "runtime_evidence": runtime is not None,
                    "runtime_summary": runtime,
                    "recoverability_classification": "NOT_A_GAP" if calendar_nontrading else "NOT_RECOVERABLE_WITH_CURRENT_API" if bbo_session_without_events else "UNKNOWN" if has_unclassified_gap else "UNKNOWN (session completeness not proven)",
                    "recoverability_reason": "Weekend or project-evidenced non-trading date." if calendar_nontrading else "Historical BBO callbacks cannot be reconstructed from the installed realtime-only SDK surface." if bbo_session_without_events else "No date/symbol-specific production backfill success establishes recovery; preserve as UNKNOWN.",
                    "reason_code": (
                        "NO_RUNTIME_EVIDENCE" if runtime is None and not rows else
                        "NON_TRADING_DAY" if calendar_nontrading else
                        "PARTIAL_SESSION" if runtime and str(runtime.get("quality", "")).startswith("PARTIAL") else
                        "COLLECTOR_FAILED" if runtime and runtime.get("quality") == "ABNORMAL_TERMINATION" else
                        "COMPLETE_OR_EXPECTED" if runtime and runtime.get("quality") == "VALID_DATA" else
                        "UNKNOWN_CAUSE"
                    ),
                }
            per_day[day] = day_items
        result[dataset] = per_day
    return result


def _inventory(loaded: dict[str, dict[str, list[dict]]], roots: dict[str, tuple[Path, str]]) -> dict:
    result = {}
    for env, (root, _) in roots.items():
        result[env] = {}
        for dataset, (relative, _) in DATASETS.items():
            rows = [row for day_rows in loaded.get(f"{env}:{dataset}", {}).values() for row in day_rows]
            timestamps = sorted(str(row["timestamp"]) for row in rows if row.get("timestamp"))
            result[env][dataset] = {
                "path": str(root / relative),
                "source_environment": env.upper(),
                "rows_or_events": len(rows),
                "symbols": len({str(row["symbol"]) for row in rows if row.get("symbol")}),
                "earliest_timestamp_bangkok": timestamps[0] if timestamps else None,
                "latest_timestamp_bangkok": timestamps[-1] if timestamps else None,
                "row_count_includes_normalized_bbo_depth_rows": dataset == "normalized_bbo",
            }
    return result


def _read(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def build() -> dict:
    prior = _read(ROOT / "reports" / "settrade_collection_audit.json")
    smoke = _read(ROOT / "reports" / "settrade_production_smoke.json")
    cutover = _read(ROOT / "reports" / "settrade_production_cutover.json")
    universe = prior.get("universe", {}).get("symbols", [])
    production_root = resolve_data_root(ROOT)
    persisted_rows = 0
    for relative in ("normalized/bars_1m/data.csv", "normalized/bars_5m/data.csv", "normalized/bars_15m/data.csv", "normalized/bid_offer/data.csv", "normalized/quotes/data.csv"):
        file_path = production_root / relative
        if file_path.exists():
            try:
                with file_path.open(encoding="utf-8", newline="") as handle:
                    persisted_rows += max(0, sum(1 for _ in csv.reader(handle)) - 1)
            except (OSError, csv.Error):
                continue
    availability = prior.get("candle_availability", {}).get("days", {})
    candle_days = {}
    for day, evidence in sorted(availability.items()):
        symbols = evidence.get("first_nonempty_by_symbol", {})
        present = set(symbols)
        candle_days[day] = {
            "source_environment": "sandbox (pre-cutover persisted evidence)",
            "symbols_with_observed_rows": len(present),
            "missing_symbols": sorted(set(universe) - present),
            "missing_symbol_count": len(set(universe) - present),
            "status": "PARTIAL" if len(present) < len(universe) else "OBSERVED",
            "gap_recoverability": "UNKNOWN",
            "reason": "Historical API availability is symbol/date-specific; a zero-row production 1m sample does not prove permanent unavailability.",
        }
    missing_dates = [
        {"date": day, "evidence": "no runtime/data/log artifact in prior audit", "classification": "UNKNOWN", "recoverability": "UNKNOWN"}
        for day in prior.get("weekday_dates_without_artifacts", [])
    ]
    sandbox_root = ROOT / "data" / "pilot" / "settrade"
    roots = {
        "sandbox": (sandbox_root, "sandbox"),
        "production": (production_root, "production"),
    }
    loaded = _load_dataset_rows(roots)
    day_by_day = _day_by_day(prior, roots, loaded)
    from src.data.settrade.integrity import scan_integrity
    integrity_findings = {env: scan_integrity(root) for env, (root, _) in roots.items()}
    missing_symbol_entries = sum(len(day["sandbox"]["missing_symbols"]) for dataset, days in day_by_day.items() if dataset.startswith("candles_") for day in days.values())
    interval_gap_segments = sum(len(day[env]["missing_interval_estimates"]) for data in day_by_day.values() for day in data.values() for env in ("sandbox", "production"))
    bbo_unrecoverable_days = len({
        day for dataset in ("raw_bbo", "normalized_bbo") for day, sources in day_by_day[dataset].items()
        if sources["sandbox"].get("recoverability_classification") == "NOT_RECOVERABLE_WITH_CURRENT_API"
    })
    gap_counts = {
        "missing_trading_dates_with_known_project_evidence": len(missing_dates),
        "missing_symbol_day_entries_sandbox": missing_symbol_entries,
        "missing_interval_gap_segments": interval_gap_segments,
        "estimated_missing_candle_intervals": sum(item["missing_intervals_estimate"] for days in day_by_day.values() for date_item in days.values() for env in date_item.values() for item in env["missing_interval_estimates"]),
        "recoverable_from_api": 0,
        "recoverable_from_existing_other_source": 0,
        "not_recoverable_with_current_api": bbo_unrecoverable_days,
        "historical_bbo_capability_limitations": 1,
        "unknown_gap_records": len(missing_dates) + missing_symbol_entries + interval_gap_segments,
    }
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "cutover": cutover,
        "production_smoke": smoke,
        "production_data_root": str(production_root),
        "production_persisted_market_rows": persisted_rows,
        "historical_sandbox_collection_days": candle_days,
        "weekdays_without_artifacts": missing_dates,
        "bbo_gap_recoverability": "NOT_RECOVERABLE_FROM_HISTORICAL_CANDLE_API; event callbacks are not reconstructible",
        "production_sampled_historical_1m_recoverability": "UNKNOWN_OR_EMPTY",
        "day_by_day_dataset_coverage": day_by_day,
        "persisted_settrade_dataset_inventory": _inventory(loaded, roots),
        "structural_integrity_findings": integrity_findings,
        "missing_data_inventory": {
            "counts": gap_counts,
            "recoverability": "UNKNOWN for absent candle rows until production API request returns data; historical BBO callbacks cannot be reconstructed from observed API capabilities",
            "gap_classification": "RECOVERABLE_FROM_API=0 proven; RECOVERABLE_FROM_EXISTING_OTHER_SOURCE=0 proven; BBO sessions with runtime evidence but no persisted events are NOT_RECOVERABLE_WITH_CURRENT_API; missing candle dates/symbols/intervals without successful targeted repair remain UNKNOWN.",
            "not_recoverable_reason": "The installed SDK exposes realtime BBO subscription only; no historical BBO retrieval method is exposed. The day count is based on BBO collection sessions with runtime evidence and no persisted callbacks.",
            "classification_policy": "No market values inferred; only failed or empty bounded requests are evidence; uncovered legacy days remain UNKNOWN.",
        },
        "backfill_status": smoke.get("backfill_status", "NOT_ATTEMPTED"),
        "source_separation": {"sandbox": "data/pilot/settrade", "production": "data/pilot/settrade/production"},
        "orders_placed": 0,
    }


if __name__ == "__main__":
    result = build()
    output = ROOT / "reports" / "settrade_production_coverage_audit.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"report": str(output), "production_rows": result["production_persisted_market_rows"], "sandbox_days": len(result["historical_sandbox_collection_days"]), "missing_artifact_days": len(result["weekdays_without_artifacts"]), "backfill_status": result["backfill_status"], "orders_placed": 0}, indent=2))

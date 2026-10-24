"""Run a small read-only symbol/timeframe/date capability matrix."""
from __future__ import annotations

import csv
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LOCAL = ZoneInfo("Asia/Bangkok")
SYMBOLS = ("ADVANC", "PTT", "KBANK", "DELTA", "MTC")
TIMEFRAMES = ("1m", "5m", "15m")
DAYS = ("2026-10-20", "2026-10-21")


def _existing(path: Path, symbol: str, interval: str, start: datetime, end: datetime) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    with path.open(encoding="utf-8", newline="") as source:
        for row in csv.DictReader(source):
            if row.get("symbol", "").upper() != symbol or row.get("interval") != interval:
                continue
            stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
            stamp = stamp.astimezone(LOCAL) if stamp.tzinfo else stamp.replace(tzinfo=LOCAL)
            if start <= stamp <= end:
                rows.append(row)
    return rows


def run_matrix(*, apply: bool = False) -> dict:
    from src.data.settrade import SettradeClient, SettradeConfig, normalize_candlestick, validate_bar_records
    from scripts.backfill_settrade_candles import merge_plan
    from src.data.settrade.retry import call_with_retries

    previous_rows_appended = 0
    previous_path = ROOT / "reports" / "settrade_candle_capability_matrix.json"
    if previous_path.exists():
        try:
            previous_summary = json.loads(previous_path.read_text(encoding="utf-8")).get("summary", {})
            previous_rows_appended = int(previous_summary.get("cumulative_rows_appended", previous_summary.get("rows_appended", 0)))
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            previous_rows_appended = 0
    config = SettradeConfig.from_env(ROOT / ".env")
    if (config.broker_id, config.app_code) != ("013", "ALGO_EQ"):
        raise RuntimeError("read-only matrix requires production routing broker 013 / ALGO_EQ")
    client = SettradeClient(config, market_rps=1.0)
    client.authenticate()
    result = {"generated_at": datetime.now(timezone.utc).isoformat(), "environment": "PRODUCTION",
              "requested_symbols": list(SYMBOLS), "timeframes": list(TIMEFRAMES), "dates": list(DAYS),
              "window_local": ["09:30:00", "10:00:00"], "rate_limit_per_second": 1,
              "calls": [], "orders_placed": 0, "backfill_applied": False,
              "note": "Bounded historical candle probes; appends are opt-in and conflict-safe."}
    data_root = ROOT / "data" / "pilot" / "settrade" / "production" / "normalized"
    for day in DAYS:
        start = datetime.fromisoformat(f"{day}T09:30:00").replace(tzinfo=LOCAL)
        end = datetime.fromisoformat(f"{day}T10:00:00").replace(tzinfo=LOCAL)
        for symbol in SYMBOLS:
            for timeframe in TIMEFRAMES:
                row = {"date": day, "symbol": symbol, "timeframe": timeframe,
                       "requested_start": start.isoformat(), "requested_end": end.isoformat(),
                       "status": "UNKNOWN", "raw_rows": 0, "returned_rows": 0,
                       "returned_first": None, "returned_last": None, "inclusive_start_observed": None,
                       "inclusive_end_observed": None, "existing_rows": 0, "would_append_rows": 0,
                       "identical_duplicates": 0, "conflicts": 0, "validation_issues": []}
                try:
                    raw = call_with_retries(lambda: client.candlestick(symbol, timeframe, limit=100, start=start.isoformat(), end=end.isoformat()), retries=1)
                    collected = datetime.now(timezone.utc)
                    records = normalize_candlestick(raw, symbol, timeframe, collected)
                    issues = validate_bar_records(records)
                    in_range = [bar for bar in records if start <= bar.timestamp.astimezone(LOCAL) <= end]
                    path = data_root / f"bars_{timeframe}" / "data.csv"
                    existing = _existing(path, symbol, timeframe, start, end)
                    proposed = [{**bar.__dict__, "timestamp": bar.timestamp.isoformat()} for bar in in_range]
                    merge = merge_plan(existing, proposed)
                    stamps = sorted(bar.timestamp.astimezone(LOCAL) for bar in in_range)
                    row.update({"status": "SUCCESS", "raw_rows": len(records), "returned_rows": len(in_range),
                                "returned_first": stamps[0].isoformat() if stamps else None,
                                "returned_last": stamps[-1].isoformat() if stamps else None,
                                "inclusive_start_observed": bool(stamps and stamps[0] == start),
                                "inclusive_end_observed": bool(stamps and stamps[-1] == end),
                                "existing_rows": len(existing), "would_append_rows": len(merge["additions"]),
                                "identical_duplicates": merge["duplicates"], "conflicts": len(merge["conflicts"]),
                                "validation_issues": [str(issue) for issue in issues],
                                "merge_would_be_blocked": merge["blocked"]})
                    row["rows_appended"] = 0
                    if apply and not issues and not merge["blocked"] and merge["additions"]:
                        from types import SimpleNamespace
                        from scripts.run_settrade_collector import BAR_FIELDS, _collector_provenance
                        from src.data.settrade import PilotStorage

                        provenance = _collector_provenance(SimpleNamespace(config=SimpleNamespace(broker_id="013", app_code="ALGO_EQ")))
                        retrieved = collected.isoformat()
                        append_rows = []
                        for proposed_row in merge["additions"]:
                            item = dict(proposed_row)
                            item["timestamp"] = datetime.fromisoformat(item["timestamp"])
                            item.update({"collected_at": retrieved, "retrieved_at": retrieved, **provenance})
                            append_rows.append(item)
                        relative = f"normalized/bars_{timeframe}/data.csv"
                        storage = PilotStorage(ROOT / "data" / "pilot" / "settrade" / "production")
                        saved = storage.append_csv_deduplicated(relative, append_rows, BAR_FIELDS,
                                                                ("symbol", "interval", "timestamp"))
                        storage.append_jsonl("raw/candles/backfill.jsonl", {
                            "source": "Settrade Open API MarketData.get_candlestick", "environment": "production",
                            "broker_id": "013", "app_code": "ALGO_EQ", "symbol": symbol,
                            "interval": timeframe, "requested_start": start.isoformat(),
                            "requested_end": end.isoformat(), "retrieved_at": retrieved,
                            "rows_appended": saved.get("written", 0), "orders_placed": 0,
                        })
                        row["rows_appended"] = saved.get("written", 0)
                        row["backfill_applied"] = True
                except Exception as exc:  # store only sanitized exception type/message
                    row.update({"status": "ERROR", "error_type": type(exc).__name__, "error": str(exc)[:300]})
                result["calls"].append(row)
                time.sleep(1.0)
    result["summary"] = {
        "successes": sum(call["status"] == "SUCCESS" for call in result["calls"]),
        "failures": sum(call["status"] != "SUCCESS" for call in result["calls"]),
        "dates": {day: sum(call["status"] == "SUCCESS" and call["date"] == day for call in result["calls"]) for day in DAYS},
        "timeframes": {interval: sum(call["status"] == "SUCCESS" and call["timeframe"] == interval for call in result["calls"]) for interval in TIMEFRAMES},
        "rows_would_append": sum(call.get("would_append_rows", 0) for call in result["calls"]),
        "rows_appended": sum(call.get("rows_appended", 0) for call in result["calls"]),
        "cumulative_rows_appended": previous_rows_appended + sum(call.get("rows_appended", 0) for call in result["calls"]),
    }
    result["backfill_applied"] = apply and result["summary"]["rows_appended"] > 0
    return result


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="append validated new rows; conflicts block each range")
    args = parser.parse_args()
    report = run_matrix(apply=args.apply)
    target = ROOT / "reports" / "settrade_candle_capability_matrix.json"
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"report": str(target.relative_to(ROOT)), "summary": report["summary"], "orders_placed": 0}, indent=2))
    return 0 if report["summary"]["failures"] == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())

"""Checkpointed, append-only recovery of bounded Settrade daily candles."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LOCAL = ZoneInfo("Asia/Bangkok")
MANIFEST = ROOT / "reports/settrade_historical_recovery_manifest.json"
FIELDS = ["timestamp", "collected_at", "symbol", "interval", "open", "high", "low", "close", "volume", "turnover", "source", "source_environment", "broker_id", "app_code", "collector_version", "git_head", "retrieved_at", "timezone", "session", "adjustment_status"]


def _write_manifest(data: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(temporary, path)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", default="2026-01-01T00:00:00")
    parser.add_argument("--end", default="2026-10-28T23:59:59")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--resume", action="store_true")
    parser.add_argument("--manifest-path", default=str(MANIFEST))
    return parser


def main() -> int:
    from src.data.settrade import PilotStorage, SettradeClient, SettradeConfig, normalize_candlestick, validate_bar_records
    from scripts.run_settrade_collector import _collector_provenance

    args = _parser().parse_args()
    start = datetime.fromisoformat(args.start).replace(tzinfo=LOCAL)
    end = datetime.fromisoformat(args.end).replace(tzinfo=LOCAL)
    manifest_path = Path(args.manifest_path).resolve()
    if end <= start or args.limit < 1 or args.limit > 2000:
        raise SystemExit("Require end > start and 1 <= limit <= 2000")
    symbols_path = ROOT / "reports/current_set50_universe.csv"
    with symbols_path.open(encoding="utf-8", newline="") as source:
        symbols = [row["symbol"].strip().upper() for row in csv.DictReader(source)]
    if len(symbols) != 50 or len(set(symbols)) != 50:
        raise RuntimeError("Current SET50 universe must have 50 unique symbols")
    data_root = ROOT / "data/pilot/settrade/production"
    storage = PilotStorage(data_root)
    output = data_root / "normalized/bars_1d/data.csv"
    if args.resume and manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (manifest.get("requested_start") != start.isoformat()
                or manifest.get("requested_end") != end.isoformat()
                or manifest.get("interval") != "1d"):
            raise RuntimeError("Existing manifest parameters differ; refusing to mix recovery runs")
    else:
        manifest = {"schema_version": 1, "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_settrade_daily",
                    "generated_at": datetime.now(timezone.utc).isoformat(), "source": "Settrade Open API MarketData.get_candlestick",
                    "environment": "PRODUCTION", "interval": "1d", "requested_start": start.isoformat(),
                    "requested_end": end.isoformat(), "limit_per_request": args.limit, "rate_limit_per_second": 1,
                    "universe": "current SET50 only; not survivorship-safe for historical research",
                    "requests": {}, "summary": {}}
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=1.0)
    client.authenticate()
    provenance = _collector_provenance(client)
    for symbol in symbols:
        if args.resume and symbol in manifest["requests"] and manifest["requests"][symbol].get("api_status") in {"SUCCESS", "API_NO_DATA"}:
            continue
        requested_at = datetime.now(timezone.utc)
        entry = {"symbol": symbol, "requested_start": start.isoformat(), "requested_end": end.isoformat(),
                 "request_timestamp_utc": requested_at.isoformat(), "interval": "1d", "limit": args.limit,
                 "source": "Settrade Open API MarketData.get_candlestick", "api_status": "ERROR",
                 "rows_returned": 0, "earliest_returned": None, "latest_returned": None,
                 "retries": 0, "duplicate_count": 0, "conflict_count": 0,
                 "rows_persisted": 0, "rows_already_present": 0}
        existing_rows = []
        if output.exists():
            with output.open(encoding="utf-8", newline="") as source:
                for row in csv.DictReader(source):
                    if row.get("symbol", "").upper() != symbol:
                        continue
                    try:
                        stamp = datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
                        stamp = stamp.astimezone(LOCAL) if stamp.tzinfo else stamp.replace(tzinfo=LOCAL)
                    except (KeyError, ValueError):
                        continue
                    if start <= stamp <= end:
                        existing_rows.append(row)
        entry["rows_already_present"] = len(existing_rows)
        raw = None
        error = None
        for attempt in range(3):
            try:
                raw = client.candlestick(symbol, "1d", limit=args.limit,
                                         start=args.start, end=args.end)
                break
            except Exception as exc:  # redact before recording SDK/network errors
                error = client.redacted_error(exc)
                entry["retries"] = attempt
                if attempt < 2:
                    time.sleep(2 ** attempt)
        if raw is None:
            entry.update(api_status="ERROR", error=error)
            manifest["requests"][symbol] = entry
            _write_manifest(manifest, manifest_path)
            continue
        retrieved = datetime.now(timezone.utc)
        records = normalize_candlestick(raw, symbol, "1d", retrieved)
        in_range = [row for row in records if start <= row.timestamp.astimezone(LOCAL) <= end]
        issues = validate_bar_records(in_range)
        entry["rows_returned"] = len(in_range)
        entry["earliest_returned"] = min((row.timestamp.astimezone(LOCAL).isoformat() for row in in_range), default=None)
        entry["latest_returned"] = max((row.timestamp.astimezone(LOCAL).isoformat() for row in in_range), default=None)
        entry["validation_issues"] = [str(issue) for issue in issues]
        entry["api_status"] = "API_NO_DATA" if not in_range else "SUCCESS"
        raw_fields = sorted(raw.keys()) if isinstance(raw, dict) else []
        entry["response_fields"] = raw_fields
        storage.append_jsonl("raw/candles/historical_daily.jsonl", {
            "requested_at": requested_at.isoformat(), "retrieved_at": retrieved.isoformat(),
            "symbol": symbol, "interval": "1d", "requested_start": start.isoformat(),
            "requested_end": end.isoformat(), "limit": args.limit, "response": raw,
        })
        if in_range and not issues:
            rows = []
            for bar in in_range:
                row = {**bar.__dict__, "timestamp": bar.timestamp.isoformat(),
                       "collected_at": retrieved.isoformat(), "retrieved_at": retrieved.isoformat(),
                       "turnover": str(bar.turnover) if bar.turnover is not None else None,
                       "adjustment_status": "UNKNOWN", "session": "DAILY",
                       "source_environment": "production", **provenance}
                rows.append(row)
            saved = storage.append_csv_deduplicated("normalized/bars_1d/data.csv", rows, FIELDS,
                                                    ("symbol", "interval", "timestamp"))
            entry.update(rows_persisted=saved["written"], duplicate_count=saved["duplicates"],
                         conflict_count=saved["conflicts"], rows_already_present=saved["duplicates"])
        manifest["requests"][symbol] = entry
        statuses = [item.get("api_status") for item in manifest["requests"].values()]
        manifest["summary"] = {"attempted_symbols": len(statuses), "successes": statuses.count("SUCCESS"),
                               "api_no_data": statuses.count("API_NO_DATA"), "errors": statuses.count("ERROR"),
                               "rows_returned": sum(int(x.get("rows_returned", 0)) for x in manifest["requests"].values()),
                               "rows_persisted": sum(int(x.get("rows_persisted", 0)) for x in manifest["requests"].values()),
                               "rows_already_present": sum(int(x.get("rows_already_present", 0)) for x in manifest["requests"].values()),
                               "conflicts": sum(int(x.get("conflict_count", 0)) for x in manifest["requests"].values()),
                               "orders_placed": 0}
        _write_manifest(manifest, manifest_path)
    print(json.dumps({"run_id": manifest["run_id"], "summary": manifest.get("summary", {}),
                      "manifest": str(manifest_path.relative_to(ROOT)), "orders_placed": 0}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

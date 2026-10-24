"""Probe or append a bounded, conflict-safe Settrade historical candle range."""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
LOCAL = ZoneInfo("Asia/Bangkok")
REPORT = ROOT / "reports" / "settrade_backfill_probe.json"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--symbol", default="PTT")
    parser.add_argument("--timeframe", choices=("1m", "5m", "15m"), default="1m")
    parser.add_argument("--start", default="2026-10-21T11:37:00")
    parser.add_argument("--end", default="2026-10-21T12:29:00")
    parser.add_argument("--limit", type=int, default=1000)
    parser.add_argument("--apply", action="store_true", help="append only validated, non-conflicting rows captured by the previous probe")
    return parser


def _key(row: dict) -> tuple[str, str, str]:
    raw = str(row.get("timestamp", ""))
    try:
        stamp = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if stamp.tzinfo is not None:
            raw = stamp.astimezone(timezone.utc).isoformat()
        else:
            raw = stamp.isoformat()
    except ValueError:
        pass
    return str(row.get("symbol", "")).upper(), str(row.get("interval", "")), raw


def _core(row: dict) -> tuple[str, ...]:
    return tuple(str(row.get(field, "")) for field in ("open", "high", "low", "close", "volume"))


def merge_plan(existing: list[dict], proposed: list[dict]) -> dict:
    """Return an append-only plan; conflicts block the whole proposed batch."""
    indexed = {_key(row): row for row in existing}
    additions, duplicates, conflicts = [], 0, []
    for row in proposed:
        key = _key(row)
        previous = indexed.get(key)
        if previous is None:
            indexed[key] = row
            additions.append(row)
        elif _core(previous) == _core(row):
            duplicates += 1
        else:
            conflicts.append({"key": key, "existing": _core(previous), "proposed": _core(row)})
    return {"additions": [] if conflicts else additions, "duplicates": duplicates, "conflicts": conflicts, "blocked": bool(conflicts)}


def _existing_in_range(path: Path, symbol: str, interval: str, start: str, end: str) -> list[dict]:
    if not path.exists():
        return []
    result = []
    start_local = datetime.fromisoformat(start).replace(tzinfo=LOCAL)
    end_local = datetime.fromisoformat(end).replace(tzinfo=LOCAL)
    with path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            if row.get("symbol", "").upper() != symbol or row.get("interval") != interval:
                continue
            stamp = datetime.fromisoformat(row.get("timestamp", "").replace("Z", "+00:00"))
            stamp = stamp.replace(tzinfo=LOCAL) if stamp.tzinfo is None else stamp.astimezone(LOCAL)
            if start_local <= stamp <= end_local:
                result.append(row)
    return result


def _probe(args: argparse.Namespace) -> dict:
    from src.data.settrade import SettradeClient, SettradeConfig, normalize_candlestick, validate_bar_records
    from src.data.settrade.retry import call_with_retries

    config = SettradeConfig.from_env(ROOT / ".env")
    if config.broker_id != "013" or config.app_code != "ALGO_EQ":
        raise RuntimeError("bounded recovery probe requires configured production routing (broker 013 / ALGO_EQ)")
    client = SettradeClient(config, market_rps=1.0)
    client.authenticate()
    raw = call_with_retries(lambda: client.candlestick(args.symbol, args.timeframe, limit=args.limit, start=args.start, end=args.end), retries=2)
    collected_at = datetime.now(timezone.utc)
    records = normalize_candlestick(raw, args.symbol, args.timeframe, collected_at)
    issues = validate_bar_records(records)
    start = datetime.fromisoformat(args.start).replace(tzinfo=LOCAL)
    end = datetime.fromisoformat(args.end).replace(tzinfo=LOCAL)
    in_range = [record for record in records if start <= record.timestamp.astimezone(LOCAL) <= end]
    frame = getattr(raw, "__dict__", raw)
    fields = sorted(frame[0].keys()) if isinstance(frame, list) and frame and isinstance(frame[0], dict) else sorted(frame.columns) if hasattr(frame, "columns") else sorted(frame.keys()) if isinstance(frame, dict) else []
    return {
        "requested_at_utc": collected_at.isoformat(), "symbol": args.symbol.upper(), "timeframe": args.timeframe,
        "requested_start_bangkok": start.isoformat(), "requested_end_bangkok": end.isoformat(),
        "environment": "PRODUCTION", "broker_id": "013", "app_code": "ALGO_EQ",
        "api_source": "Settrade Open API MarketData.get_candlestick", "api_schema_fields": fields,
        "raw_rows": len(records), "in_range_rows": len(in_range),
        "returned_first_bangkok": min((row.timestamp.astimezone(LOCAL).isoformat() for row in in_range), default=None),
        "returned_last_bangkok": max((row.timestamp.astimezone(LOCAL).isoformat() for row in in_range), default=None),
        "validation_issues": [str(issue) for issue in issues],
        "rows": [{**row.__dict__, "timestamp": row.timestamp.isoformat()} for row in in_range],
        "orders_placed": 0,
    }


def main() -> int:
    args = _parser().parse_args()
    symbol = args.symbol.upper()
    if args.apply:
        if not REPORT.exists():
            raise SystemExit("No probe report exists; run without --apply first.")
        result = json.loads(REPORT.read_text(encoding="utf-8"))
        if (result.get("symbol"), result.get("timeframe"), result.get("requested_start_bangkok", "")[:19], result.get("requested_end_bangkok", "")[:19]) != (symbol, args.timeframe, args.start, args.end):
            raise SystemExit("Probe parameters do not match this apply request.")
    else:
        result = _probe(args)
    data_root = ROOT / "data" / "pilot" / "settrade" / "production"
    relative = f"normalized/bars_{args.timeframe}/data.csv"
    existing_path = data_root / relative
    existing = _existing_in_range(existing_path, symbol, args.timeframe, args.start, args.end)
    proposed = result.get("rows", [])
    plan = merge_plan(existing, proposed)
    result["merge_preview"] = {"existing_rows_in_requested_range": len(existing), "proposed_rows": len(proposed), "would_append": len(plan["additions"]), "identical_duplicates": plan["duplicates"], "conflicts": plan["conflicts"], "blocked": plan["blocked"]}
    result["backfill_applied"] = False
    if args.apply:
        if result.get("validation_issues") or plan["blocked"]:
            raise SystemExit("Backfill blocked: invalid rows or conflicting genuine rows. Existing data was not changed.")
        if not plan["additions"]:
            result["backfill_applied"] = True
            result["rows_appended"] = 0
        else:
            from types import SimpleNamespace
            from scripts.run_settrade_collector import BAR_FIELDS, _collector_provenance
            from src.data.settrade import PilotStorage
            provenance = _collector_provenance(SimpleNamespace(config=SimpleNamespace(broker_id="013", app_code="ALGO_EQ")))
            collected_at = datetime.now(timezone.utc).isoformat()
            rows = []
            for item in plan["additions"]:
                record = dict(item)
                record["timestamp"] = datetime.fromisoformat(record["timestamp"])
                record.update({"collected_at": collected_at, "retrieved_at": collected_at, **provenance})
                rows.append(record)
            storage = PilotStorage(data_root)
            result["storage_result"] = storage.append_csv_deduplicated(relative, rows, BAR_FIELDS, ("symbol", "interval", "timestamp"))
            storage.append_jsonl("raw/candles/backfill.jsonl", {"source": result["api_source"], "environment": "production", "broker_id": "013", "app_code": "ALGO_EQ", "symbol": symbol, "interval": args.timeframe, "requested_start": args.start, "requested_end": args.end, "backfill_at": collected_at, "raw_response_schema": result["api_schema_fields"], "rows_appended": result["storage_result"]["written"], "orders_placed": 0})
            result["backfill_applied"] = True
            result["rows_appended"] = result["storage_result"]["written"]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    print(json.dumps({key: result.get(key) for key in ("symbol", "timeframe", "requested_start_bangkok", "requested_end_bangkok", "raw_rows", "in_range_rows", "returned_first_bangkok", "returned_last_bangkok", "validation_issues", "merge_preview", "backfill_applied", "rows_appended", "orders_placed")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

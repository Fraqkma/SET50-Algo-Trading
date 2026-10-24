"""Print a conservative, bounded plan for candle gap recovery."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

TIMEFRAMES = {"candles_1m": "1m", "candles_5m": "5m", "candles_15m": "15m"}


def build_plan(report: dict, *, date: str | None = None, symbol: str | None = None,
               timeframe: str | None = None, max_requests: int = 20,
               max_minutes: int = 60) -> dict:
    """Group adjacent candle gaps into capped API ranges; never plan BBO synthesis."""
    if max_requests < 1 or max_minutes < 1:
        raise ValueError("request and duration bounds must be positive")
    selected = []
    for row in report.get("gap_records", []):
        tf = TIMEFRAMES.get(row.get("dataset"))
        if not tf or row.get("environment", "").upper() != "PRODUCTION":
            continue
        if date and row.get("date") != date:
            continue
        if symbol and row.get("symbol", "").upper() != symbol.upper():
            continue
        if timeframe and tf != timeframe:
            continue
        if row.get("classification") in {"SESSION_BOUNDARY", "MARKET_CLOSED", "NO_TRADE_CONFIRMED"}:
            continue
        selected.append({**row, "timeframe": tf})
    selected.sort(key=lambda row: (row["date"], row["symbol"], row["timeframe"], row["gap_start"]))
    groups: list[dict] = []
    for row in selected:
        start = datetime.fromisoformat(row["gap_start"])
        end = datetime.fromisoformat(row["gap_end"])
        if groups:
            last = groups[-1]
            last_end = datetime.fromisoformat(last["end"])
            step = timedelta(minutes=int(row["timeframe"][:-1]))
            if (last["date"], last["symbol"], last["timeframe"]) == (row["date"], row["symbol"], row["timeframe"]) and start <= last_end + step:
                last["end"] = max(last_end, end).isoformat()
                last["source_gaps"].append(row)
                continue
        groups.append({"date": row["date"], "symbol": row["symbol"], "timeframe": row["timeframe"],
                       "start": start.isoformat(), "end": end.isoformat(), "source_gaps": [row]})
    bounded = []
    for group in groups:
        start, end = datetime.fromisoformat(group["start"]), datetime.fromisoformat(group["end"])
        cursor = start
        while cursor <= end and len(bounded) < max_requests:
            stop = min(end, cursor + timedelta(minutes=max_minutes))
            bounded.append({"symbol": group["symbol"], "timeframe": group["timeframe"],
                            "date": group["date"], "start": cursor.isoformat(), "end": stop.isoformat(),
                            "source_gap_count": len(group["source_gaps"]),
                            "action": "bounded_candle_probe_only", "apply": False})
            cursor = stop + timedelta(minutes=int(group["timeframe"][:-1]))
    return {"status": "DRY_RUN", "source_gap_records": len(selected), "grouped_ranges": len(groups),
            "planned_requests": bounded, "request_limit": max_requests, "max_range_minutes": max_minutes,
            "synthetic_realtime_recovery": False, "unresolved_non_candle_gaps_skipped": True}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, default=ROOT / "reports" / "settrade_gap_recovery.json")
    parser.add_argument("--date")
    parser.add_argument("--symbol")
    parser.add_argument("--timeframe", choices=("1m", "5m", "15m"))
    parser.add_argument("--max-requests", type=int, default=20)
    parser.add_argument("--max-minutes", type=int, default=60)
    parser.add_argument("--dry-run", action="store_true", help="explicitly keep this planner read-only (default)")
    args = parser.parse_args()
    report = json.loads(args.report.read_text(encoding="utf-8"))
    plan = build_plan(report, date=args.date, symbol=args.symbol, timeframe=args.timeframe,
                      max_requests=args.max_requests, max_minutes=args.max_minutes)
    print(json.dumps(plan, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

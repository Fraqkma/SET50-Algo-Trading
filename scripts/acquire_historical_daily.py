"""Acquire historical daily OHLCV into an isolated, unapproved staging area.

The command is intentionally opt-in: without ``--download`` it only prints the
planned universe.  It never touches ``data/raw`` or the approved manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STAGING = ROOT / "data" / "pilot" / "historical_daily"
MATRIX = ROOT / "reports" / "historical_set50_symbol_matrix.csv"


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def planned_symbols() -> list[str]:
    if not MATRIX.exists():
        return []
    return sorted(pd.read_csv(MATRIX)["symbol"].dropna().astype(str).str.upper().unique())


def acquire(*, start: str = "2010-01-01", end: str = "2026-09-05", download: bool = False) -> dict:
    symbols = planned_symbols()
    result: dict = {
        "status": "PLAN_ONLY" if not download else "STAGING_ONLY",
        "requested_start": start,
        "requested_end_exclusive": end,
        "symbol_count": len(symbols),
        "symbols": symbols,
        "records": [],
        "production_mutated": False,
        "approved_manifest_mutated": False,
        "retrieved_at_utc": datetime.now(timezone.utc).isoformat(),
    }
    if not download:
        return result
    try:
        import yfinance as yf
    except ImportError as exc:
        result["status"] = "BLOCKED_MISSING_DEPENDENCY"
        result["error"] = str(exc)
        return result
    STAGING.mkdir(parents=True, exist_ok=True)
    for symbol in symbols:
        ticker = f"{symbol}.BK"
        record = {"symbol": symbol, "ticker": ticker, "source": "Yahoo Finance via yfinance", "status": "FAILED"}
        try:
            frame = yf.download(ticker, start=start, end=end, auto_adjust=False, actions=True, progress=False)
            if isinstance(frame.columns, pd.MultiIndex):
                frame.columns = [str(a) for a, _ in frame.columns]
            frame = frame.reset_index()
            frame = frame.loc[:, ~frame.columns.duplicated()]
            path = STAGING / f"{symbol}_{start[:4]}_{end[:4]}.csv"
            frame.to_csv(path, index=False)
            if "Date" not in frame.columns or frame.empty:
                record.update({"status": "NO_DATA", "artifact": str(path.relative_to(ROOT)),
                               "sha256": _sha256(path), "rows": int(len(frame)),
                               "actual_first_date": "", "actual_last_date": ""})
                result["records"].append(record)
                continue
            dates = pd.to_datetime(frame.get("Date"), errors="coerce")
            valid_dates = dates.dropna()
            record.update({"status": "ACQUIRED_UNAPPROVED" if len(valid_dates) else "NO_DATA",
                           "artifact": str(path.relative_to(ROOT)), "sha256": _sha256(path), "rows": int(len(frame)),
                           "actual_first_date": valid_dates.min().date().isoformat() if len(valid_dates) else "",
                           "actual_last_date": valid_dates.max().date().isoformat() if len(valid_dates) else ""})
        except Exception as exc:  # pragma: no cover - provider/runtime dependent
            record["error"] = f"{type(exc).__name__}: {exc}"
        result["records"].append(record)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2010-01-01")
    parser.add_argument("--end", default="2026-09-05")
    parser.add_argument("--download", action="store_true", help="perform opt-in staging download")
    parser.add_argument("--output", default="reports/historical_daily_acquisition.json")
    args = parser.parse_args()
    payload = acquire(start=args.start, end=args.end, download=args.download)
    output = ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({k: payload[k] for k in ("status", "symbol_count", "production_mutated")}, indent=2))


if __name__ == "__main__":
    main()

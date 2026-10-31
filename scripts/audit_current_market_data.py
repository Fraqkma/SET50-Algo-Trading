"""Read-only current coverage, process identity and organizer cutoff evidence."""
from __future__ import annotations

import csv
import hashlib
import json
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import psutil

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade.automation import runner_status
from src.data.settrade.paths import resolve_data_root
from scripts.build_weekend_maintenance_report import trading_dates_for_week

START, END = "2026-10-24", "2026-10-28"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8-sig")) if path.exists() else {}


def day_summary(frame: pd.DataFrame) -> dict:
    return {str(day): {"rows": len(part), "symbols": int(part.symbol.nunique()),
                      "first": part.stamp.min().isoformat(), "latest": part.stamp.max().isoformat()}
            for day, part in frame.groupby(frame.stamp.dt.strftime("%Y-%m-%d"))}


def candle_audit(path: Path) -> dict:
    malformed = 0
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        for row in reader:
            if None in row or any(v is None for v in row.values()):
                malformed += 1
                continue
            rows.append(row)
    frame = pd.DataFrame(rows)
    frame["stamp"] = pd.to_datetime(frame.timestamp, utc=True, errors="coerce").dt.tz_convert("Asia/Bangkok")
    current = frame[frame.stamp.dt.strftime("%Y-%m-%d").between(START, END)].copy()
    for field in ("open", "high", "low", "close", "volume"):
        current[field] = pd.to_numeric(current[field], errors="coerce")
    keys = ["symbol", "interval", "timestamp"]
    fields = ["open", "high", "low", "close", "volume"]
    conflict = current.groupby(keys)[fields].nunique().gt(1).any(axis=1)
    invalid = (current[fields].isna().any(axis=1) | (current[["open", "high", "low", "close"]] <= 0).any(axis=1)
               | (current.high < current[["open", "close", "low"]].max(axis=1))
               | (current.low > current[["open", "close", "high"]].min(axis=1)) | (current.volume < 0))
    timeframe = path.parent.name.removeprefix("bars_")
    minutes = {"1m": 1, "5m": 5, "15m": 15}.get(timeframe)
    gaps = []
    if minutes is not None:
        for (symbol, day), part in current.groupby(["symbol", current.stamp.dt.strftime("%Y-%m-%d")]):
            stamps = sorted(set(part.stamp))
            for left, right in zip(stamps, stamps[1:]):
                if left.hour < 13 <= right.hour:
                    continue
                missing = int((right-left).total_seconds() // (minutes*60)) - 1
                if missing > 0:
                    gaps.append({"symbol": symbol, "date": day, "after": left.isoformat(), "before": right.isoformat(),
                                 "estimated_intervals": missing, "classification": "UNKNOWN",
                                 "reason": "Observed timestamp gap; no-trade/API/session aggregation semantics not proven"})
    return {"path": str(path.relative_to(ROOT)), "rows": len(frame), "latest": frame.stamp.max().isoformat(),
            "symbols": int(frame.symbol.nunique()), "days": day_summary(current),
            "malformed_csv_rows_all_dates": malformed, "duplicate_keys_current": int(current.duplicated(keys).sum()),
            "conflicting_ohlcv_current": int(conflict.sum()), "invalid_ohlcv_current": int(invalid.sum()),
            "provenance": {key: current[key].value_counts().to_dict() for key in ("source", "source_environment", "interval")},
            "gaps": gaps, "gap_count": len(gaps), "missing_intervals_estimate": sum(g["estimated_intervals"] for g in gaps)}


def build() -> dict:
    data = resolve_data_root(ROOT)
    timeframes = ("1m", "5m", "15m", "1d")
    datasets = {f"candles_{tf}": candle_audit(data / f"normalized/bars_{tf}/data.csv")
                for tf in timeframes if (data / f"normalized/bars_{tf}/data.csv").exists()}
    raw = []
    malformed = 0
    for line in (data / "raw/bid_offer/events.jsonl").open(encoding="utf-8"):
        try:
            row = json.loads(line)
            raw.append({"symbol": row["symbol"], "stamp": row["received_at"]})
        except (ValueError, KeyError, TypeError):
            malformed += 1
    frame = pd.DataFrame(raw)
    frame.stamp = pd.to_datetime(frame.stamp, utc=True).dt.tz_convert("Asia/Bangkok")
    current = frame[frame.stamp.dt.strftime("%Y-%m-%d").between(START, END)]
    datasets["raw_bbo"] = {"rows": len(frame), "latest": frame.stamp.max().isoformat(), "symbols": int(frame.symbol.nunique()),
                           "days": day_summary(current), "malformed": malformed,
                           "timestamp_semantics": "callback received_at; exchange event timestamp unavailable"}
    book = pd.read_csv(data / "normalized/bid_offer/data.csv", low_memory=False)
    book["stamp"] = pd.to_datetime(book.retrieved_at, utc=True).dt.tz_convert("Asia/Bangkok")
    current = book[book.stamp.dt.strftime("%Y-%m-%d").between(START, END)].copy()
    keys = ["retrieved_at", "symbol", "side", "level", "collector_session_id", "generation"]
    groups = current.groupby(keys, dropna=False)[["price", "volume"]].nunique()
    top = current[current.level == 1].pivot_table(index=["retrieved_at", "symbol"], columns="side", values="price", aggfunc="first")
    valid = (top.get("bid", 0) > 0) & (top.get("ask", 0) > 0)
    datasets["normalized_bbo"] = {"rows": len(book), "latest": book.stamp.max().isoformat(), "symbols": int(book.symbol.nunique()),
        "days": day_summary(current), "duplicate_keys_current": int(current.duplicated(keys).sum()),
        "conflicting_keys_current": int(groups.gt(1).any(axis=1).sum()),
        "zero_price_depth_rows_current": int((current.price == 0).sum()),
        "negative_price_or_volume_current": int(((current.price < 0) | (current.volume < 0)).sum()),
        "crossed_positive_top_snapshots_current": int((valid & (top.bid > top.ask)).sum()),
        "timestamp_semantics": "retrieved_at; no exchange-time freshness claim", "historical_recovery": "UNAVAILABLE"}
    scheduler = load(ROOT / "reports/settrade_scheduler_status.json")
    processes = []
    for process in psutil.process_iter(["pid", "ppid", "name", "create_time", "cmdline", "exe"]):
        try:
            args = process.info.get("cmdline") or []
            scripts = [Path(arg).name for arg in args if Path(arg).name in {"run_settrade_daily.py", "run_settrade_collector.py"}]
            if scripts:
                processes.append({key: process.info[key] for key in ("pid", "ppid", "name", "create_time", "exe")} | {"scripts": scripts})
        except (psutil.Error, OSError, ValueError):
            continue
    logs = {}
    for day in ("2026-10-26", "2026-10-27", "2026-10-28"):
        path = ROOT / f"logs/settrade/daily-{day}.log"
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines() if path.exists() else []
        successes = [line[:23] for line in lines if "collector cycle exit=0" in line]
        logs[day] = {"successful_cycles": len(successes), "first_success": min(successes, default=None), "last_success": max(successes, default=None),
                     "already_running": [line[:23] for line in lines if "ALREADY_RUNNING" in line],
                     "error_count": sum(" ERROR " in line for line in lines),
                     "latest_summary": load(ROOT / f"reports/runtime/settrade_daily_{day}.json")}
    official = load(ROOT / "reports/tradesim_official_daily_ticks_package.json")
    archive = ROOT / "Daily_Ticks.zip"
    with zipfile.ZipFile(archive) as bundle:
        integrity = bundle.testzip()
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    history = official.get("official_history", {}).get("dates", [])
    ticks = official.get("official_ticks", {}).get("dates", [])
    dates = pd.date_range(START, END).strftime("%Y-%m-%d").tolist()
    trading = trading_dates_for_week(dates, set())
    return {"generated_at": datetime.now(ZoneInfo("Asia/Bangkok")).isoformat(), "status": "DEGRADED",
            "audit_start": START, "audit_end": END, "trading_dates": trading,
            "nontrading_dates": [d for d in dates if d not in trading],
            "calendar_evidence": ["https://www.set.or.th/en/about/event-calendar/holiday?year=2026", "https://www.tfex.co.th/en/about/holiday", "persisted candle rows and successful collector logs on Oct 26-28"],
            "datasets": datasets, "settrade_daily": "NOT_COLLECTED",
            "collector": {"status": runner_status(ROOT / ".settrade-runtime/daily.lock", scheduler), "processes": processes,
                          "scheduler": scheduler, "logs": logs, "editor_dependency": False,
                          "unattended_assessment": "Scheduled BAT/python is independent of VS Code while user is logged in; Interactive task does not run logged out. No boot/logon trigger. Actual editor-closed experiment not performed.",
                          "summary_warning": "Daily summary is last invocation, not whole-session evidence; Oct 28 after-hours run superseded session summary. New invocations retain separate run files."},
            "official": {"archive": str(archive), "sha256": digest, "integrity": "PASS" if integrity is None else "FAIL",
                         "unchanged_from_manifest": digest == official.get("archive_identity", {}).get("outer_sha256"),
                         "latest_history": max(history, default=None), "latest_tick": max(ticks, default=None)},
            "source_coverage": {d: "OFFICIAL_SOURCE_NOT_YET_AVAILABLE" if d > max(ticks, default="") else "OVERLAP" for d in trading},
            "backfills_this_task": [], "real_orders_placed": 0}


if __name__ == "__main__":
    report = build()
    path = ROOT / "reports/current_market_data_status.json"
    path.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"report": str(path), "collector": report["collector"]["status"], "latest": {k: v["latest"] for k,v in report["datasets"].items()}}))

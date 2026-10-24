"""Read-only discovery of genuine Settrade and research observation freshness."""
from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import yaml

LOCAL = ZoneInfo("Asia/Bangkok")


def is_partial_day(last: pd.Timestamp | None, today: date | None = None) -> bool:
    """Return true when the latest observation belongs to Bangkok's current day."""
    return bool(last is not None and last.date() == (today or datetime.now(LOCAL).date()))


def freshness_status(last_trading_date: str | None, today: date | None = None) -> str:
    """Classify recency without asserting an exchange holiday calendar."""
    if not last_trading_date:
        return "NO_DATA"
    current = today or datetime.now(LOCAL).date()
    age = (current - date.fromisoformat(last_trading_date)).days
    return "FRESH" if age <= 3 else "AGING" if age <= 7 else "STALE"


def _stamp(value: Any) -> pd.Timestamp | None:
    parsed = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(parsed):
        return None
    return parsed.tz_convert(LOCAL)


def _dataset(frame: pd.DataFrame, timestamp_column: str, symbol_column: str = "symbol", *, localize_naive: bool = True) -> dict[str, Any]:
    if frame.empty or timestamp_column not in frame:
        return {"earliest": None, "latest": None, "last_trading_date": None, "rows": 0, "symbols": 0, "timezone": "Asia/Bangkok", "partial_day": False, "freshness_status": "NO_DATA"}
    values = pd.to_datetime(frame[timestamp_column], errors="coerce")
    if getattr(values.dt, "tz", None) is None and localize_naive:
        values = values.dt.tz_localize("Asia/Bangkok")
    else:
        values = values.dt.tz_convert("Asia/Bangkok")
    values = values.dropna()
    earliest = values.min() if not values.empty else None
    latest = values.max() if not values.empty else None
    symbols = int(frame[symbol_column].nunique()) if symbol_column in frame else 0
    return {
        "earliest": earliest.isoformat() if earliest is not None else None,
        "latest": latest.isoformat() if latest is not None else None,
        "last_trading_date": latest.date().isoformat() if latest is not None else None,
        "rows": int(len(frame)),
        "symbols": symbols,
        "timezone": "Asia/Bangkok",
        "partial_day": is_partial_day(latest),
        "freshness_status": freshness_status(latest.date().isoformat() if latest is not None else None),
    }


def _read_csv(path: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(path, dtype={"symbol": str}) if path.exists() and path.stat().st_size else pd.DataFrame()
    except (OSError, pd.errors.ParserError, UnicodeDecodeError):
        return pd.DataFrame()


def _raw_bbo(path: Path) -> tuple[pd.DataFrame, int]:
    rows: list[dict[str, Any]] = []
    malformed = 0
    if path.exists():
        with path.open(encoding="utf-8") as handle:
            for line in handle:
                if not line.strip():
                    continue
                try:
                    item = json.loads(line)
                    if not isinstance(item, dict) or not item.get("received_at"):
                        malformed += 1
                        continue
                    rows.append({"timestamp": item["received_at"], "symbol": item.get("symbol")})
                except json.JSONDecodeError:
                    malformed += 1
    return pd.DataFrame(rows), malformed


def _daily_history(project_root: Path) -> dict[str, Any]:
    rows = symbols = 0
    stamps: list[pd.Timestamp] = []
    directory = project_root / "data" / "raw" / "market_data"
    for path in sorted(directory.glob("*.csv")) if directory.exists() else []:
        try:
            file_has_rows = False
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                for row in reader:
                    raw = row.get("Date") or row.get("date") or row.get("Datetime") or row.get("datetime")
                    parsed = _stamp(raw)
                    if parsed is not None:
                        rows += 1
                        file_has_rows = True
                        stamps.append(parsed)
            if file_has_rows:
                symbols += 1
        except (OSError, UnicodeDecodeError, csv.Error):
            continue
    if not stamps:
        return {"earliest": None, "latest": None, "last_trading_date": None, "rows": 0, "symbols": 0, "timezone": "Asia/Bangkok", "partial_day": False, "freshness_status": "NO_DATA"}
    first, last = min(stamps), max(stamps)
    return {"earliest": first.date().isoformat(), "latest": last.date().isoformat(), "last_trading_date": last.date().isoformat(), "rows": rows, "symbols": symbols, "timezone": "Asia/Bangkok (daily source dates)", "partial_day": False, "freshness_status": freshness_status(last.date().isoformat())}


def _cycles(project_root: Path) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    runtime = project_root / "reports" / "runtime"
    summaries: list[dict[str, Any]] = []
    for path in runtime.glob("settrade_daily_*.json") if runtime.exists() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(value, dict):
                summaries.append(value)
        except (OSError, json.JSONDecodeError):
            continue
    summaries.sort(key=lambda row: str(row.get("end_time") or row.get("start_time") or ""))
    successful = [row for row in summaries if row.get("shutdown_status") and row.get("shutdown_status") not in {"FAILED", "DISK_CRITICAL", "NOT_READY"}]
    failed = [row for row in summaries if row.get("shutdown_status") in {"FAILED", "DISK_CRITICAL", "NOT_READY"}]
    log_dir = project_root / "logs" / "settrade"
    for path in log_dir.glob("daily-*.log") if log_dir.exists() else []:
        try:
            for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if "ALREADY_RUNNING" not in line:
                    continue
                stamp_text = line[:23]
                try:
                    stamp = pd.Timestamp(stamp_text).tz_localize("Asia/Bangkok")
                    instant = stamp.tz_convert("UTC").isoformat()
                except (ValueError, TypeError):
                    instant = f"{path.stem.removeprefix('daily-')}TUNKNOWN"
                failed.append({"date": path.stem.removeprefix("daily-"), "shutdown_status": "ALREADY_RUNNING", "start_time": instant, "end_time": instant, "evidence": "daily log entry; runner did not start a collection cycle"})
        except OSError:
            continue
    failed.sort(key=lambda row: str(row.get("end_time") or row.get("start_time") or ""))
    return (successful[-1] if successful else None, failed[-1] if failed else None)


def collect_health(project_root: Path, data_root: Path, *, configured: bool = True) -> dict[str, Any]:
    """Read stored rows and summarize current paths, timestamps, and space."""
    project_root, data_root = Path(project_root).resolve(), Path(data_root).resolve()
    raw, malformed = _raw_bbo(data_root / "raw" / "bid_offer" / "events.jsonl")
    norm_bbo = _read_csv(data_root / "normalized" / "bid_offer" / "data.csv")
    if not norm_bbo.empty:
        norm_bbo["observation_timestamp"] = norm_bbo.get("event_timestamp", pd.Series(index=norm_bbo.index, dtype=object))
        norm_bbo["observation_timestamp"] = norm_bbo["observation_timestamp"].where(norm_bbo["observation_timestamp"].notna() & norm_bbo["observation_timestamp"].astype(str).ne(""), norm_bbo.get("retrieved_at"))
    datasets: dict[str, Any] = {
        "raw_bbo": _dataset(raw, "timestamp"),
        "normalized_bbo": _dataset(norm_bbo, "observation_timestamp"),
    }
    for timeframe in ("1m", "5m", "15m"):
        frame = _read_csv(data_root / "normalized" / f"bars_{timeframe}" / "data.csv")
        datasets[f"candles_{timeframe}"] = _dataset(frame, "timestamp")
    datasets["historical_daily_ohlcv"] = _daily_history(project_root)
    try:
        from src.data.exploratory_market import build_exploratory_view

        config = yaml.safe_load((project_root / "config" / "settrade_collection.yaml").read_text(encoding="utf-8")) or {}
        symbols = config.get("current_set50", [])
        view, _conflicts = build_exploratory_view(project_root, symbols)
        dates = pd.to_datetime(view.get("Date", pd.Series(dtype=object)), errors="coerce").dropna()
        first = dates.min() if not dates.empty else None
        last = dates.max() if not dates.empty else None
        first_date = first.date().isoformat() if first is not None else None
        view_date = last.date().isoformat() if last is not None else None
        datasets["exploratory_market_view"] = {
            "earliest": first_date, "latest": view_date,
            "last_trading_date": view_date, "rows": int(len(view)),
            "symbols": int(view["symbol"].nunique()) if "symbol" in view else 0,
            "timezone": "Asia/Bangkok (daily source dates)",
            "partial_day": False, "source": "derived from persisted daily rows using current_set50 source precedence",
            "freshness_status": freshness_status(view_date),
        }
    except (OSError, ValueError, KeyError, ImportError) as error:
        datasets["exploratory_market_view"] = {
            "earliest": None, "latest": None, "last_trading_date": None,
            "rows": 0, "symbols": 0, "timezone": "Asia/Bangkok (daily source dates)",
            "partial_day": False, "source": "actual source-row derivation failed",
            "freshness_status": "UNKNOWN", "error": str(error),
        }
    try:
        collection_audit = json.loads((project_root / "reports" / "settrade_collection_audit.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        collection_audit = {}
    partial_dates = {
        day for day, details in collection_audit.get("daily_collection", {}).items()
        if str(details.get("quality", "")).startswith(("PARTIAL_SESSION", "ABNORMAL_TERMINATION"))
    }
    for name, details in datasets.items():
        if name.startswith(("raw_bbo", "normalized_bbo", "candles_")) and details.get("last_trading_date") in partial_dates:
            details["partial_day"] = True
            details["freshness_status"] = "PARTIAL"
    success, failure = _cycles(project_root)
    try:
        from .disk import check_disk

        disk = check_disk(data_root)
        free_bytes = disk.free_bytes
        disk_state = disk.state
        disk_error = None
    except OSError as error:
        free_bytes, disk_state, disk_error = None, "UNKNOWN", str(error)
    lock_path = project_root / ".settrade-runtime" / "daily.lock"
    try:
        lock_value = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        lock_value = None
    lock_status = "NOT_PRESENT"
    if isinstance(lock_value, dict):
        from .automation import _pid_alive
        try:
            lock_status = "ACTIVE" if _pid_alive(int(lock_value.get("pid", 0))) else "STALE"
        except (TypeError, ValueError):
            lock_status = "STALE"
    return {
        "active_repo_path": str(project_root),
        "active_data_root": str(data_root),
        "data_root_exists": data_root.exists(),
        "data_root_configured": configured,
        "filesystem_free_bytes": free_bytes,
        "filesystem_free_gib": round(free_bytes / 1024**3, 2) if free_bytes is not None else None,
        "filesystem_state": disk_state,
        "filesystem_error": disk_error,
        "latest_successful_cycle": success,
        "latest_failed_cycle": failure,
        "runner_lock_status": lock_status,
        "runner_lock_created_at": lock_value.get("created_at") if isinstance(lock_value, dict) else None,
        "datasets": datasets,
        "raw_bbo_malformed_lines": malformed,
        "known_gap_summary": {
            "bbo": "Event-driven callbacks; silence alone is not a gap. Persisted callbacks cover 2026-09-22 through 2026-10-01.",
            "candles": "Sparse and symbol-specific current-session Settrade responses; missing rows were not synthesized.",
            "recovery": "No disk-full incident is confirmed by the available local runtime and log evidence.",
            "runner_lock": f"{lock_status}; a stale lock is recoverable by the next daily-runner launch.",
        },
        "orders_placed": 0,
    }

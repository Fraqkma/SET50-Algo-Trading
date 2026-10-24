"""Read-only audits for persisted Settrade pilot collection artifacts."""
from __future__ import annotations

import json
from datetime import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from ui.data_catalog import LOCAL_TIMEZONE, SETTRADE_SESSIONS, settrade_candle_quality


def _jsonl_count(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open(encoding="utf-8") as handle:
        return sum(1 for line in handle if line.strip())


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def inventory(root: Path) -> dict[str, Any]:
    """Inventory files and row counts without touching source data."""
    files: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*")) if root.exists() else []:
        if not path.is_file():
            continue
        item: dict[str, Any] = {"path": str(path), "bytes": path.stat().st_size}
        if path.suffix == ".jsonl":
            item["rows"] = _jsonl_count(path)
        elif path.suffix.lower() == ".csv":
            try:
                item["rows"] = int(sum(1 for _ in path.open(encoding="utf-8")) - 1)
            except OSError:
                item["rows"] = None
        files.append(item)
    return {"root": str(root), "files": files, "file_count": len(files)}


def _local_day_series(values: pd.Series) -> pd.Series:
    return pd.to_datetime(values, errors="coerce", utc=True).dt.tz_convert(LOCAL_TIMEZONE)


def candle_audit(root: Path) -> dict[str, Any]:
    result: dict[str, Any] = {"timeframes": {}, "current_set50": {"expected_symbols": 50}}
    for timeframe in ("1m", "5m", "15m"):
        path = root / "normalized" / f"bars_{timeframe}" / "data.csv"
        if not path.exists():
            result["timeframes"][timeframe] = {"rows": 0, "status": "NO_DATA"}
            continue
        frame = pd.read_csv(path)
        if frame.empty:
            result["timeframes"][timeframe] = {"rows": 0, "status": "NO_DATA"}
            continue
        frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
        timestamp_parse_errors = int(frame["timestamp"].isna().sum())
        frame = frame.dropna(subset=["timestamp"])
        ordering_by_symbol = {
            str(symbol): int((group["timestamp"].diff().dropna() < pd.Timedelta(0)).sum())
            for symbol, group in frame.groupby("symbol", sort=False)
        }
        frame["timestamp_local"] = frame["timestamp"].dt.tz_convert(LOCAL_TIMEZONE)
        days: dict[str, Any] = {}
        by_symbol_day: dict[str, Any] = {}
        for day, group in frame.groupby(frame["timestamp_local"].dt.date):
            days[str(day)] = settrade_candle_quality(group, timeframe, expected_session_date=day)
            by_symbol_day[str(day)] = {
                str(symbol): settrade_candle_quality(symbol_group, timeframe, expected_session_date=day)
                for symbol, symbol_group in group.groupby("symbol", sort=True)
            }
        result["timeframes"][timeframe] = {
            "rows": int(len(frame)),
            "symbols": int(frame["symbol"].nunique()),
            "source_type": "direct Settrade API 1m candles" if timeframe == "1m" else "locally aggregated from contiguous observed 1m candles; missing minutes are not filled",
            "timestamp_parse_errors": timestamp_parse_errors,
            "timestamp_ordering_issues_by_symbol": ordering_by_symbol,
            "first_local": frame["timestamp_local"].min().isoformat(),
            "last_local": frame["timestamp_local"].max().isoformat(),
            "days": days,
            "by_symbol_day": by_symbol_day,
            "duplicate_keys": int(frame.duplicated(["symbol", "timestamp"]).sum()),
        }
    return result


def bbo_audit(root: Path, universe: list[str], groups: list[list[str]]) -> dict[str, Any]:
    path = root / "normalized" / "bid_offer" / "data.csv"
    if not path.exists():
        return {"rows": 0, "status": "NO_DATA"}
    frame = pd.read_csv(path)
    if frame.empty:
        return {"rows": 0, "status": "NO_DATA"}
    persisted_rows = int(len(frame))
    columns = set(frame.columns)
    required = {"retrieved_at", "symbol", "side", "level", "price", "volume"}
    missing_columns = sorted(required - columns)
    if missing_columns:
        return {"rows": persisted_rows, "status": "INVALID", "missing_columns": missing_columns}
    original_symbols = frame["symbol"].astype(str)
    file_order_ts = pd.to_datetime(frame["retrieved_at"], errors="coerce", utc=True)
    ordering_issues = int((file_order_ts.diff().dropna() < pd.Timedelta(0)).sum())
    frame["retrieved_at"] = pd.to_datetime(frame["retrieved_at"], errors="coerce", utc=True)
    malformed_timestamps = int(frame["retrieved_at"].isna().sum())
    frame = frame.dropna(subset=["retrieved_at"])
    frame["timestamp_local"] = frame["retrieved_at"].dt.tz_convert(LOCAL_TIMEZONE)
    key = [column for column in ["retrieved_at", "symbol", "side", "level", "price", "volume", "collector_session_id", "generation", "rotation_group"] if column in frame]
    days: dict[str, Any] = {}
    for day, group in frame.groupby(frame["timestamp_local"].dt.date):
        observed = set(group["symbol"].astype(str))
        groups_report = []
        for index, symbols in enumerate(groups):
            expected = set(symbols)
            groups_report.append({"group": index, "expected_topics": len(expected), "observed_symbols": len(expected & observed), "missing_symbols": sorted(expected - observed), "rows": int(group[group["symbol"].isin(expected)].shape[0])})
        days[str(day)] = {"rows": int(len(group)), "raw_event_rows": _jsonl_count(root / "raw" / "bid_offer" / "events.jsonl"), "symbols": int(group["symbol"].nunique()), "first_local": group["timestamp_local"].min().isoformat(), "last_local": group["timestamp_local"].max().isoformat(), "groups": groups_report}
    price = pd.to_numeric(frame["price"], errors="coerce")
    volume = pd.to_numeric(frame["volume"], errors="coerce")
    top = frame[pd.to_numeric(frame["level"], errors="coerce").eq(1)]
    event_index = [column for column in ["retrieved_at", "symbol", "collector_session_id", "generation", "rotation_group"] if column in top]
    two_sided = top.pivot_table(index=event_index, columns="side", values="price", aggfunc="first")
    bid_ask_valid = bool({"bid", "ask"}.issubset(two_sided.columns))
    complete = two_sided[["bid", "ask"]].notna().all(axis=1) if bid_ask_valid else pd.Series(False, index=two_sided.index)
    valid_positive = (two_sided["bid"] > 0) & (two_sided["ask"] > 0) if bid_ask_valid else complete
    crossed_or_locked = int(((two_sided["bid"] >= two_sided["ask"]) & valid_positive).sum()) if bid_ask_valid else None
    missing_side_events = int((~complete).sum())
    zero_or_negative_best_side_events = int((complete & ~valid_positive).sum())
    locked_best_events = int(((two_sided["bid"] == two_sided["ask"]) & valid_positive).sum()) if bid_ask_valid else None
    crossed_best_events = int(((two_sided["bid"] > two_sided["ask"]) & valid_positive).sum()) if bid_ask_valid else None
    symbol_mismatches = int((original_symbols.loc[frame.index].str.upper() != frame.get("payload_symbol", original_symbols.loc[frame.index]).astype(str).str.upper()).sum()) if "payload_symbol" in frame else None
    ordering_by_symbol = {}
    order_frame = frame.assign(_source_order=range(len(frame)))
    for symbol, group in order_frame.groupby("symbol", sort=True):
        order_frame_ts = group["retrieved_at"]
        ordering_by_symbol[symbol] = {"rows": int(len(group)), "first_local": group["timestamp_local"].min().isoformat(), "last_local": group["timestamp_local"].max().isoformat(), "out_of_order_rows": int((order_frame_ts.diff().dropna() < pd.Timedelta(0)).sum())}
    return {
        "rows": int(len(frame)), "persisted_rows": persisted_rows, "symbols": int(frame["symbol"].nunique()),
        "trading_days": len(days), "days": days, "symbol_coverage": ordering_by_symbol,
        "duplicate_keys": int(frame.duplicated(key).sum()), "negative_price": int((price < 0).sum()),
        "negative_volume": int((volume < 0).sum()), "malformed_timestamps": malformed_timestamps,
        "timestamp_ordering_issues_in_file": ordering_issues, "bid_ask_fields_available": bid_ask_valid,
        "top_of_book_events": int(len(two_sided)), "missing_best_bid_or_ask": missing_side_events,
        "zero_or_negative_best_side": zero_or_negative_best_side_events,
        "locked_best_quotes": locked_best_events, "crossed_best_quotes": crossed_best_events,
        "locked_or_crossed_best_quotes": crossed_or_locked,
        "malformed_numeric_price_or_size": int((price.isna() | volume.isna()).sum()),
        "unexpected_symbols": sorted(set(frame["symbol"].astype(str)) - set(universe)),
        "status": "READY" if not frame.duplicated(key).any() and not missing_columns else "NEEDS_REVIEW",
    }


def runtime_audit(reports: Path) -> list[dict[str, Any]]:
    rows = []
    for path in sorted(reports.glob("settrade_daily_*.json")) if reports.exists() else []:
        value = _read_json(path)
        if value:
            rows.append({"summary_file": path.name, **{key: value.get(key) for key in ("date", "start_time", "end_time", "shutdown_status", "startup_status", "rotation_generations", "bbo_events_written", "one_minute_rows_written", "symbols_with_1m_data", "candle_status", "api_requests", "retries", "rate_limit_errors", "orders_placed", "market_day", "runtime_seconds", "reconnects", "validation_errors", "conflicts")}})
    return rows

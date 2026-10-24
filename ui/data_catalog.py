"""Read-only catalog of the repository's historical SET50 data artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import time
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from src.data.settrade.paths import resolve_data_root

LOCAL_TIMEZONE = "Asia/Bangkok"
SETTRADE_SESSIONS = (
    (time(9, 30), time(12, 30), "morning"),
    (time(14, 30), time(16, 40), "afternoon"),
    (time(16, 40), time(17, 0), "pre_close"),
)
COMPLETENESS_THRESHOLDS = {
    "complete_coverage": 0.95,
    "sparse_coverage": 0.50,
    "sparse_gap_intervals": 10,
}


@dataclass(frozen=True)
class DataPaths:
    root: Path
    constituents: Path
    ticker_audit: Path
    acquisition_report: Path
    metadata: Path
    settrade_root: Path
    raw_directories: tuple[Path, ...]


def discover_paths(root: str | Path | None = None) -> DataPaths:
    """Discover current and legacy data locations without writing to them."""
    project_root = Path(root).resolve() if root is not None else Path(__file__).resolve().parents[1]
    reports = project_root / "reports"
    metadata = reports / "data_acquisition_metadata.json"
    raw_directories: list[Path] = []
    if metadata.exists():
        try:
            configured = json.loads(metadata.read_text(encoding="utf-8")).get("raw_directory")
            if configured:
                raw_directories.append(project_root / configured)
        except (OSError, json.JSONDecodeError):
            pass
    raw_directories.extend([project_root / "data" / "raw" / "market_data", project_root / "data" / "raw" / "prices"])
    configured_storage = "data/pilot/settrade"
    config_path = project_root / "config" / "settrade_collection.yaml"
    if config_path.exists():
        try:
            import yaml

            configured_storage = (yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}).get("storage_root", configured_storage)
        except (OSError, ValueError):
            pass
    return DataPaths(
        root=project_root,
        constituents=project_root / "data" / "processed" / "constituents" / "historical_set50.csv",
        ticker_audit=reports / "yahoo_ticker_audit.csv",
        acquisition_report=reports / "market_data_acquisition.csv",
        metadata=metadata,
        settrade_root=resolve_data_root(project_root, configured_storage),
        raw_directories=tuple(dict.fromkeys(raw_directories)),
    )


def load_csv(path: Path, **kwargs: Any) -> pd.DataFrame:
    """Load a CSV for display, returning an empty frame when it is absent."""
    return pd.read_csv(path, **kwargs) if path.exists() else pd.DataFrame()


def load_constituents(paths: DataPaths) -> pd.DataFrame:
    frame = load_csv(paths.constituents, dtype=str).fillna("")
    if frame.empty:
        return frame
    frame["effective_from"] = pd.to_datetime(frame["effective_from"], errors="coerce")
    frame["effective_to"] = pd.to_datetime(frame["effective_to"], errors="coerce")
    return frame.sort_values(["effective_from", "symbol"])


def load_audit(paths: DataPaths) -> pd.DataFrame:
    return load_csv(paths.ticker_audit, dtype=str).fillna("")


def load_acquisition(paths: DataPaths) -> pd.DataFrame:
    frame = load_csv(paths.acquisition_report, dtype=str).fillna("")
    if not frame.empty and "Rows" in frame:
        frame["Rows"] = pd.to_numeric(frame["Rows"], errors="coerce").fillna(0).astype(int)
    return frame


def load_metadata(paths: DataPaths) -> dict[str, Any]:
    if not paths.metadata.exists():
        return {}


def load_settrade_audit(paths: DataPaths) -> dict[str, Any]:
    """Load the measured Settrade collection audit, if it has been generated."""
    path = paths.root / "reports" / "settrade_collection_audit.json"
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def load_settrade_runtime(paths: DataPaths) -> pd.DataFrame:
    """Load daily runner summaries without exposing secrets or changing them."""
    directory = paths.root / "reports" / "runtime"
    rows: list[dict[str, Any]] = []
    for path in sorted(directory.glob("settrade_daily_*.json")) if directory.exists() else []:
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(value, dict):
            value["summary_file"] = path.name
            rows.append(value)
    if not rows:
        return pd.DataFrame()
    frame = pd.DataFrame(rows)
    for column in ("start_time", "end_time"):
        if column in frame:
            frame[column] = pd.to_datetime(frame[column], errors="coerce", utc=True).dt.tz_convert(LOCAL_TIMEZONE)
    return frame.sort_values("start_time", na_position="last").reset_index(drop=True)
    try:
        return json.loads(paths.metadata.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def market_data_files(paths: DataPaths) -> dict[str, Path]:
    """Return ticker files, preferring the current Gate 2 CSV format."""
    files: dict[str, Path] = {}
    for directory in paths.raw_directories:
        if not directory.exists():
            continue
        for path in sorted(directory.glob("*")):
            if path.suffix.lower() not in {".csv", ".parquet", ".pq"}:
                continue
            key = path.stem.replace("_BK", ".BK").upper()
            files.setdefault(key, path)
    return files


def load_market_frame(path: Path) -> pd.DataFrame:
    """Load one raw file without cleaning, filling, or changing its values."""
    frame = pd.read_csv(path) if path.suffix.lower() == ".csv" else pd.read_parquet(path)
    if not isinstance(frame.index, pd.RangeIndex):
        frame = frame.reset_index()
    frame.columns = [str(column).strip() for column in frame.columns]
    column_names = {str(column).lower().replace(" ", "_"): column for column in frame.columns}
    rename = {
        column_names[name]: name.title() if name != "adj_close" else "Adj Close"
        for name in ("date", "open", "high", "low", "close", "volume", "adj_close")
        if name in column_names
    }
    frame = frame.rename(columns=rename)
    date_column = next((column for column in frame.columns if column.lower() in {"date", "datetime"}), None)
    if date_column:
        frame[date_column] = pd.to_datetime(frame[date_column], errors="coerce")
        frame = frame.sort_values(date_column)
    return frame


def quality_summary(frame: pd.DataFrame, symbol: str = "") -> dict[str, Any]:
    """Return display diagnostics while preserving the input frame."""
    columns = {str(column).lower().replace(" ", "_"): column for column in frame.columns}
    date_column = next((columns[name] for name in ("date", "datetime") if name in columns), None)
    required = ["open", "high", "low", "close", "volume"]
    missing_values = {column.title(): int(frame[columns[column]].isna().sum()) for column in required if column in columns}
    missing_values.update({column.title(): int(len(frame)) for column in required if column not in columns})
    duplicate_dates = int(frame[date_column].duplicated().sum()) if date_column else 0
    invalid_relationships = 0
    if all(column in columns for column in ["open", "high", "low", "close"]):
        high = frame[columns["high"]]
        low = frame[columns["low"]]
        open_price = frame[columns["open"]]
        close = frame[columns["close"]]
        invalid_relationships = int(((high < pd.concat([open_price, close], axis=1).max(axis=1)) | (low > pd.concat([open_price, close], axis=1).min(axis=1))).sum())
    missing_dates: list[str] = []
    if date_column:
        dates = pd.to_datetime(frame[date_column], errors="coerce").dropna().sort_values()
        if len(dates) > 1:
            gaps = dates.diff().dt.days
            missing_dates = [f"{dates.iloc[index - 1].date()} -> {dates.iloc[index].date()} ({int(gaps.iloc[index] - 1)} calendar days)" for index in range(1, len(dates)) if gaps.iloc[index] > 10]
    return {"symbol": symbol, "rows": len(frame), "missing_values": missing_values, "duplicate_dates": duplicate_dates, "invalid_relationships": invalid_relationships, "missing_dates": missing_dates}


@st.cache_data(show_spinner=False, ttl=60, max_entries=32)
def load_settrade_candles(paths: DataPaths, timeframe: str, symbol: str, start: Any = None, end: Any = None) -> pd.DataFrame:
    """Read only normalized pilot candles and expose exchange-local timestamps."""
    path = paths.settrade_root / "normalized" / f"bars_{timeframe}" / "data.csv"
    if not path.exists():
        return pd.DataFrame()
    frame = pd.read_csv(path)
    if symbol and "symbol" in frame:
        frame = frame[frame["symbol"].astype(str).str.upper() == symbol.upper()]
    if "timestamp" not in frame:
        return frame
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["timestamp"])
    if start is not None:
        frame = frame[frame["timestamp"].dt.tz_convert("Asia/Bangkok").dt.date >= pd.Timestamp(start).date()]
    if end is not None:
        frame = frame[frame["timestamp"].dt.tz_convert("Asia/Bangkok").dt.date <= pd.Timestamp(end).date()]
    frame["timestamp_local"] = frame["timestamp"].dt.tz_convert(LOCAL_TIMEZONE)
    frame["source_label"] = "SETTRADE_API_CANDLE"
    return frame.sort_values("timestamp")


def filter_settrade_candles(frame: pd.DataFrame, session_filter: str = "All timestamps") -> pd.DataFrame:
    """Filter observed candles without filling, resampling, or changing values."""
    if frame.empty:
        return frame.copy()
    result = frame.copy()
    if "timestamp_local" not in result:
        result["timestamp"] = pd.to_datetime(result["timestamp"], errors="coerce", utc=True)
        result["timestamp_local"] = result["timestamp"].dt.tz_convert(LOCAL_TIMEZONE)
    local_times = result["timestamp_local"].dt.time
    if session_filter in {"Continuous sessions only", "Exclude midday break"}:
        result = result[(local_times >= time(9, 30)) & (local_times < time(17, 0))]
    if session_filter == "Exclude midday break":
        local_times = result["timestamp_local"].dt.time
        result = result[(local_times < time(12, 30)) | (local_times >= time(14, 30))]
    result = result.sort_values(["timestamp", "symbol"] if "symbol" in result else ["timestamp"]).reset_index(drop=True)
    result["session_segment"] = result["timestamp_local"].map(_session_segment)
    return result


def _session_segment(timestamp: pd.Timestamp) -> str:
    local_time = timestamp.time()
    for start, end, label in SETTRADE_SESSIONS:
        if start <= local_time < end:
            return label
    if local_time < time(9, 30):
        return "pre_open"
    if local_time < time(14, 30):
        return "midday_break"
    return "after_close"


def prepare_settrade_chart_frame(frame: pd.DataFrame, compact: bool = True) -> pd.DataFrame:
    """Prepare chart coordinates while retaining every observed source row.

    Compact coordinates are ordinal positions within observed trading days. They
    compress overnight, weekend, and midday gaps without creating candles or
    changing the source timestamp/OHLCV columns.
    """
    if frame.empty:
        return frame.copy()
    result = frame.copy().sort_values("timestamp").reset_index(drop=True)
    if "session_segment" not in result:
        result["session_segment"] = result["timestamp_local"].map(_session_segment)
    result["trading_day"] = result["timestamp_local"].dt.date.astype(str)
    result["row_in_day"] = result.groupby("trading_day", sort=False).cumcount()
    result["day_separator"] = result["trading_day"].ne(result["trading_day"].shift()).fillna(True)
    result["compact_x"] = 0.0
    cursor = 0
    for _, indices in result.groupby("trading_day", sort=False).groups.items():
        positions = list(indices)
        day = result.loc[positions]
        local_times = day["timestamp_local"].dt.time
        compact_minutes = []
        for local_time in local_times:
            if local_time < time(12, 30):
                minutes = (local_time.hour * 60 + local_time.minute) - (9 * 60 + 30)
            elif local_time < time(14, 30):
                minutes = 180
            else:
                minutes = 180 + (local_time.hour * 60 + local_time.minute) - (14 * 60 + 30)
            compact_minutes.append(max(0, minutes) + local_time.second / 60)
        result.loc[positions, "compact_x"] = [cursor + offset for offset in compact_minutes]
        cursor += max(compact_minutes, default=0) + 60
    result["observed_gap_minutes"] = result["timestamp_local"].diff().dt.total_seconds().div(60).fillna(0)
    result["active_session_gap"] = (result["observed_gap_minutes"] > 1) & result["trading_day"].eq(result["trading_day"].shift()) & result["session_segment"].eq(result["session_segment"].shift())
    result["plot_x"] = result["compact_x"] if compact else result["timestamp_local"]
    result["hover_time"] = result["timestamp_local"].dt.strftime("%Y-%m-%d %H:%M:%S %Z")
    return result


def _session_interval_count(day: Any, interval_seconds: int, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None) -> int:
    """Count diagnostic slots in active sessions without constructing rows."""
    day_value = pd.Timestamp(day).date()
    windows = [(time(9, 30), time(12, 30)), (time(14, 30), time(17, 0))]
    count = 0
    for window_start, window_end in windows:
        left = pd.Timestamp.combine(day_value, window_start).tz_localize(LOCAL_TIMEZONE)
        right = pd.Timestamp.combine(day_value, window_end).tz_localize(LOCAL_TIMEZONE)
        if start is not None:
            left = max(left, start)
        if end is not None:
            right = min(right, end)
        if right > left:
            count += int((right - left).total_seconds() // interval_seconds)
    return count


def settrade_candle_quality(frame: pd.DataFrame, timeframe: str, collector_start: Any = None, expected_session_date: Any = None) -> dict[str, Any]:
    """Return transparent quality and sparse-coverage diagnostics for observed rows."""
    if frame.empty:
        return {"rows": 0, "trading_days": 0, "duplicates": 0, "invalid_ohlc": 0, "missing_values": {}, "expected_intervals": 0, "coverage_pct": 0.0, "missing_intervals": 0, "gaps_over_interval": 0, "missing_intervals_estimate": 0, "largest_gap_seconds": 0, "morning_rows": 0, "afternoon_rows": 0, "status": "NO_DATA", "estimated_coverage_pct": 0.0, "collector_expected_intervals": None, "collector_observed_rows": 0, "coverage_since_collector_start_pct": None}
    result = frame.copy().sort_values("timestamp")
    required = ["open", "high", "low", "close", "volume"]
    missing_values = {column: int(result[column].isna().sum()) for column in required if column in result}
    for column in required:
        missing_values.setdefault(column, len(result))
    invalid_ohlc = 0
    if all(column in result for column in ["open", "high", "low", "close"]):
        high = pd.to_numeric(result["high"], errors="coerce")
        low = pd.to_numeric(result["low"], errors="coerce")
        open_price = pd.to_numeric(result["open"], errors="coerce")
        close = pd.to_numeric(result["close"], errors="coerce")
        invalid_ohlc = int(((high < pd.concat([open_price, close], axis=1).max(axis=1)) | (low > pd.concat([open_price, close], axis=1).min(axis=1))).fillna(False).sum())
    interval_seconds = {"1m": 60, "5m": 300, "15m": 900}.get(timeframe, 60)
    result["trading_day"] = result["timestamp_local"].dt.date
    result["session_segment"] = result["timestamp_local"].map(_session_segment)
    gaps = result.groupby(["symbol", "trading_day", "session_segment"], dropna=False)["timestamp_local"].diff().dt.total_seconds().dropna()
    excessive = gaps[gaps > interval_seconds]
    missing_intervals = int(sum(max(0, round(value / interval_seconds) - 1) for value in excessive))
    expected_per_day = (180 * 60 + 150 * 60) // interval_seconds
    symbol_count = max(1, int(result["symbol"].nunique()) if "symbol" in result else 1)
    expected_slots = max(1, result["trading_day"].nunique() * expected_per_day * symbol_count)
    observed_unique = int(result.drop_duplicates(["symbol", "timestamp"]).shape[0])
    coverage = observed_unique / expected_slots
    morning_rows = int(result["session_segment"].eq("morning").sum())
    afternoon_rows = int(result["session_segment"].isin(["afternoon", "pre_close"]).sum())
    max_missing_intervals = max((round(value / interval_seconds) - 1 for value in excessive), default=0)
    if result.empty:
        status = "NO_DATA"
    elif expected_session_date is not None and result["trading_day"].ne(pd.Timestamp(expected_session_date).date()).all():
        status = "STALE"
    elif coverage >= COMPLETENESS_THRESHOLDS["complete_coverage"] and max_missing_intervals < 2:
        status = "COMPLETE"
    elif coverage < COMPLETENESS_THRESHOLDS["sparse_coverage"] or max_missing_intervals >= COMPLETENESS_THRESHOLDS["sparse_gap_intervals"]:
        status = "SPARSE"
    else:
        status = "PARTIAL"
    collector_start_local = None
    collector_expected = None
    collector_observed = 0
    collector_coverage = None
    if collector_start is not None:
        collector_start_local = pd.Timestamp(collector_start)
        if collector_start_local.tzinfo is None:
            collector_start_local = collector_start_local.tz_localize(LOCAL_TIMEZONE)
        else:
            collector_start_local = collector_start_local.tz_convert(LOCAL_TIMEZONE)
        if result["trading_day"].nunique() == 1 and collector_start_local.date() == result["trading_day"].iloc[0]:
            collector_expected = _session_interval_count(collector_start_local.date(), interval_seconds, start=collector_start_local)
            collector_observed = int((result["timestamp_local"] >= collector_start_local).sum())
            collector_coverage = round(100 * collector_observed / max(1, collector_expected), 2)
    return {
        "rows": int(len(result)),
        "symbols": int(result["symbol"].nunique()) if "symbol" in result else 0,
        "trading_days": int(result["trading_day"].nunique()),
        "first_local": result["timestamp_local"].min().isoformat(),
        "last_local": result["timestamp_local"].max().isoformat(),
        "duplicates": int(result.duplicated([column for column in ["symbol", "timestamp"] if column in result]).sum()),
        "invalid_ohlc": invalid_ohlc,
        "missing_values": missing_values,
        "expected_intervals": int(expected_slots),
        "coverage_pct": round(100 * coverage, 2),
        "missing_intervals": max(0, int(expected_slots - observed_unique)),
        "gaps_over_interval": int(len(excessive)),
        "missing_intervals_estimate": missing_intervals,
        "largest_gap_seconds": int(gaps.max()) if not gaps.empty else 0,
        "estimated_coverage_pct": round(100 * observed_unique / expected_slots, 2),
        "morning_rows": morning_rows,
        "afternoon_rows": afternoon_rows,
        "status": status,
        "collector_start_local": collector_start_local.isoformat() if collector_start_local is not None else None,
        "collector_expected_intervals": collector_expected,
        "collector_observed_rows": collector_observed,
        "coverage_since_collector_start_pct": collector_coverage,
        "coverage_note": "Estimated from observed rows versus configured SET trading session minutes; no rows are synthesized.",
        "volume_note": "Volume is displayed exactly as persisted by Settrade and is not inferred or used to create candles.",
    }


@st.cache_data(show_spinner=False, ttl=60, max_entries=16)
def load_settrade_bbo(paths: DataPaths, symbol: str, start: Any = None, end: Any = None) -> pd.DataFrame:
    """Read normalized genuine BBO events; never derive events from prices."""
    path = paths.settrade_root / "normalized" / "bid_offer" / "data.csv"
    if not path.exists():
        return pd.DataFrame()
    columns = list(pd.read_csv(path, nrows=0).columns)
    useful_columns = [column for column in (
        "event_timestamp", "collected_at", "retrieved_at", "symbol", "side", "level", "price", "volume",
        "source", "source_environment", "broker_id", "app_code", "collector_version", "git_head",
        "collector_session_id", "rotation_group", "generation", "subscription_started_at",
    ) if column in columns]
    chunks = []
    for chunk in pd.read_csv(path, usecols=useful_columns, chunksize=500_000):
        if symbol and "symbol" in chunk:
            chunk = chunk[chunk["symbol"].astype(str).str.upper() == symbol.upper()]
        if chunk.empty:
            continue
        if "retrieved_at" in chunk:
            stamps = pd.to_datetime(chunk["retrieved_at"], errors="coerce", utc=True)
            chunk = chunk.assign(retrieved_at=stamps).dropna(subset=["retrieved_at"])
            local_dates = chunk["retrieved_at"].dt.tz_convert(LOCAL_TIMEZONE).dt.date
            if start is not None:
                chunk = chunk[local_dates >= pd.Timestamp(start).date()]
                local_dates = local_dates.loc[chunk.index]
            if end is not None:
                chunk = chunk[local_dates <= pd.Timestamp(end).date()]
        if not chunk.empty:
            chunks.append(chunk)
    frame = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame(columns=columns)
    if "retrieved_at" not in frame:
        return frame
    frame["retrieved_at"] = pd.to_datetime(frame["retrieved_at"], errors="coerce", utc=True)
    frame = frame.dropna(subset=["retrieved_at"])
    if start is not None:
        frame = frame[frame["retrieved_at"].dt.tz_convert("Asia/Bangkok").dt.date >= pd.Timestamp(start).date()]
    if end is not None:
        frame = frame[frame["retrieved_at"].dt.tz_convert("Asia/Bangkok").dt.date <= pd.Timestamp(end).date()]
    frame["timestamp_local"] = frame["retrieved_at"].dt.tz_convert("Asia/Bangkok")
    return frame.sort_values("retrieved_at")


@st.cache_data(show_spinner=False, ttl=60, max_entries=8)
def settrade_availability(paths: DataPaths, include_bbo: bool = True) -> pd.DataFrame:
    """Build a bounded in-memory availability index from normalized pilot data."""
    rows: list[dict[str, Any]] = []
    for timeframe in ("1m", "5m", "15m"):
        frame = load_settrade_candles(paths, timeframe, "")
        if frame.empty:
            continue
        for (symbol, date), group in frame.groupby(["symbol", frame["timestamp_local"].dt.date], dropna=True):
            path = paths.settrade_root / "normalized" / f"bars_{timeframe}" / "data.csv"
            rows.append({"symbol": symbol, "date": str(date), "datatype": "candles", "timeframe": timeframe, "rows": len(group), "first_timestamp": group["timestamp"].min().isoformat(), "last_timestamp": group["timestamp"].max().isoformat(), "path": path.relative_to(paths.root).as_posix() if path.is_relative_to(paths.root) else str(path)})
    bbo_path = paths.settrade_root / "normalized" / "bid_offer" / "data.csv"
    if include_bbo and bbo_path.exists():
        report_path = paths.root / "reports" / "settrade_gap_recovery.json"
        report = {}
        try:
            report = json.loads(report_path.read_text(encoding="utf-8")) if report_path.exists() else {}
        except (OSError, json.JSONDecodeError):
            report = {}
        environment = "production" if paths.settrade_root.name.lower() == "production" else "sandbox"
        grouped: dict[tuple[str, str], dict[str, Any]] = {}
        for date, datasets in report.get("historical_day_coverage", {}).items():
            detail = datasets.get(f"{environment}:normalized_bbo", {})
            for symbol, summary in detail.get("symbol_coverage", {}).items():
                grouped[(symbol, date)] = summary
        if not grouped:
            columns = set(pd.read_csv(bbo_path, nrows=0).columns)
            if {"symbol", "retrieved_at"}.issubset(columns):
                for chunk in pd.read_csv(bbo_path, usecols=["symbol", "retrieved_at"], chunksize=250_000):
                    chunk["retrieved_at"] = pd.to_datetime(chunk["retrieved_at"], errors="coerce", utc=True)
                    chunk = chunk.dropna(subset=["retrieved_at"])
                    chunk["date"] = chunk["retrieved_at"].dt.tz_convert(LOCAL_TIMEZONE).dt.date.astype(str)
                    for (symbol, date), group in chunk.groupby(["symbol", "date"], dropna=True, sort=False):
                        key = (str(symbol).upper(), date)
                        info = grouped.setdefault(key, {"rows": 0, "first_timestamp_bangkok": None, "last_timestamp_bangkok": None})
                        info["rows"] += len(group)
                        first = group["retrieved_at"].min().tz_convert(LOCAL_TIMEZONE).isoformat()
                        last = group["retrieved_at"].max().tz_convert(LOCAL_TIMEZONE).isoformat()
                        info["first_timestamp_bangkok"] = min(info["first_timestamp_bangkok"], first) if info["first_timestamp_bangkok"] else first
                        info["last_timestamp_bangkok"] = max(info["last_timestamp_bangkok"], last) if info["last_timestamp_bangkok"] else last
        relative = bbo_path.relative_to(paths.root).as_posix() if bbo_path.is_relative_to(paths.root) else str(bbo_path)
        rows.extend({"symbol": symbol, "date": date, "datatype": "bbo", "timeframe": "event", "rows": info.get("rows", 0), "first_timestamp": info.get("first_timestamp_bangkok"), "last_timestamp": info.get("last_timestamp_bangkok"), "path": relative} for (symbol, date), info in grouped.items())
    return pd.DataFrame(rows)

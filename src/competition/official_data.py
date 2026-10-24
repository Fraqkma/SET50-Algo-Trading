"""Read-only loaders for organizer-provided TradeSim history and tick files."""
from __future__ import annotations

from datetime import date, datetime
import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from src.competition.data_sources import TRADESIM_OFFICIAL_HISTORY, TRADESIM_OFFICIAL_TICKS

DEFAULT_ROOT = Path(__file__).resolve().parents[2] / "data" / "official" / "tradesim"
INTERVALS = {"1D": "daily_history", "1m": "1m", "3m": "3m", "5m": "5m",
             "10m": "10m", "15m": "15m", "30m": "30m", "60m": "60m",
             "120m": "120m", "240m": "240m"}
_LOCAL_TZ = "Asia/Bangkok"


def _provenance(source_archive: str) -> dict[str, str | None]:
    report_path = DEFAULT_ROOT.parents[2] / "reports" / "tradesim_official_daily_ticks_package.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"archive_sha256": None, "outer_archive_sha256": None,
                "archive_path": None, "original_archive_member": None, "ingested_at_utc": None}
    detail = report.get("archive_identity", {}).get("nested_archives", {}).get(source_archive, {})
    extracted = report.get("extraction", {}).get("nested_archives", {}).get(source_archive, {})
    return {"archive_sha256": detail.get("sha256"),
            "outer_archive_sha256": report.get("archive_identity", {}).get("outer_sha256"),
            "archive_path": detail.get("path") or extracted.get("archive_path"),
            "original_archive_member": extracted.get("outer_member"),
            "ingested_at_utc": report.get("generated_at_utc")}


def list_history_dates(root: Path = DEFAULT_ROOT, timeframe: str = "1D") -> list[str]:
    """Return dates present for a history interval without reading CSV contents."""
    folder = _history_folder(root, timeframe)
    dates: set[str] = set()
    if folder.exists():
        for path in folder.glob("*.csv"):
            try:
                column = "Date" if timeframe == "1D" else "Timestamp"
                values = pd.read_csv(path, usecols=[column], dtype=str)[column]
                stamps = pd.to_datetime(values, errors="coerce")
                dates.update(stamps.dropna().dt.strftime("%Y-%m-%d").tolist())
            except (OSError, ValueError, KeyError, pd.errors.ParserError):
                continue
    return sorted(dates)


def _history_folder(root: Path, timeframe: str) -> Path:
    try:
        interval = INTERVALS[timeframe]
    except KeyError as exc:
        raise ValueError(f"Unsupported timeframe {timeframe!r}; expected one of {sorted(INTERVALS)}") from exc
    if timeframe == "1D":
        return root / "history" / "daily_history"
    return root / "history" / "intraday_history" / interval


def _normalise_symbol(value: str) -> str:
    symbol = value.strip().upper()
    if not symbol or any(character not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-" for character in symbol):
        raise ValueError(f"Unsafe or empty symbol: {value!r}")
    return symbol


def _localized(series: pd.Series) -> pd.Series:
    stamps = pd.to_datetime(series, errors="coerce")
    if stamps.dt.tz is None:
        return stamps.dt.tz_localize(_LOCAL_TZ, ambiguous="NaT", nonexistent="NaT")
    return stamps.dt.tz_convert(_LOCAL_TZ)


def load_official_history(
    symbol: str,
    *,
    timeframe: str = "1D",
    start: str | date | datetime | None = None,
    end: str | date | datetime | None = None,
    root: Path = DEFAULT_ROOT,
) -> pd.DataFrame:
    """Load one official symbol series with provenance and a Bangkok-aware timestamp.

    Raw CSV files are read-only. History timestamps in this package are naive;
    the organizer workflow implies local exchange time, so normalized timestamps
    are localized to Asia/Bangkok while ``source_timestamp`` retains the text.
    """
    normalized_symbol = _normalise_symbol(symbol)
    path = _history_folder(Path(root), timeframe) / f"{normalized_symbol}.csv"
    if not path.is_file():
        return pd.DataFrame(columns=["symbol", "timestamp", "source_timestamp", "open", "high", "low", "close", "volume", "source"])
    frame = pd.read_csv(path, dtype={"Date": "string", "Timestamp": "string"})
    timestamp_column = "Date" if timeframe == "1D" else "Timestamp"
    required = {timestamp_column, "Open", "High", "Low", "Close", "Volume"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"{path} is missing columns: {sorted(missing)}")
    frame = frame.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})
    frame["source_timestamp"] = frame[timestamp_column].astype("string")
    frame["timestamp"] = _localized(frame[timestamp_column])
    frame["symbol"] = normalized_symbol
    frame["source"] = TRADESIM_OFFICIAL_HISTORY
    frame["source_path"] = path.as_posix()
    for column, value in _provenance("tradeSim_history.zip").items():
        frame[column] = value
    frame["timestamp_valid"] = frame["timestamp"].notna()
    for column in ("open", "high", "low", "close", "volume"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame["ohlc_valid"] = (frame[["open", "high", "low", "close"]].notna().all(axis=1)
                           & (frame["low"] <= frame[["open", "close"]].min(axis=1))
                           & (frame["high"] >= frame[["open", "close"]].max(axis=1))
                           & (frame["low"] > 0))
    if frame["timestamp"].duplicated().any():
        frame["duplicate_timestamp"] = frame["timestamp"].duplicated(keep=False)
    else:
        frame["duplicate_timestamp"] = False
    lower = pd.Timestamp(start) if start is not None else None
    upper = pd.Timestamp(end) if end is not None else None
    if lower is not None:
        lower = lower.tz_localize(_LOCAL_TZ) if lower.tzinfo is None else lower.tz_convert(_LOCAL_TZ)
        frame = frame[frame["timestamp"] >= lower]
    if upper is not None:
        upper = upper.tz_localize(_LOCAL_TZ) if upper.tzinfo is None else upper.tz_convert(_LOCAL_TZ)
        frame = frame[frame["timestamp"] <= upper]
    return frame.reset_index(drop=True)


def list_tick_dates(root: Path = DEFAULT_ROOT) -> list[str]:
    """List organizer tick dates from filenames, avoiding a data rescan."""
    folder = Path(root) / "ticks" / "ticks"
    return sorted(path.stem for path in folder.glob("*.csv")) if folder.exists() else []


def load_official_ticks(
    *,
    trading_date: str | date | None = None,
    symbols: Iterable[str] | None = None,
    start: str | datetime | None = None,
    end: str | datetime | None = None,
    root: Path = DEFAULT_ROOT,
) -> pd.DataFrame:
    """Load official ticks in original file order; this function never aggregates or sorts.

    ``start`` and ``end`` are inclusive. Naive bounds mean Asia/Bangkok local time.
    ``tick_sequence`` is the original zero-based CSV row position.
    """
    folder = Path(root) / "ticks" / "ticks"
    if not folder.exists():
        return pd.DataFrame(columns=["symbol", "timestamp", "price", "volume", "tick_sequence", "source"])
    if trading_date is not None:
        day = pd.Timestamp(trading_date).date().isoformat()
        paths = [folder / f"{day}.csv"]
    elif start is not None and end is not None and pd.Timestamp(start).date() == pd.Timestamp(end).date():
        paths = [folder / f"{pd.Timestamp(start).date().isoformat()}.csv"]
    else:
        paths = sorted(folder.glob("*.csv"))
    wanted = {_normalise_symbol(symbol) for symbol in symbols} if symbols is not None else None
    pieces: list[pd.DataFrame] = []
    for path in paths:
        if not path.is_file():
            continue
        frame = pd.read_csv(path, dtype={"ShareCode": "string", "TradeDateTime": "string"})
        required = {"ShareCode", "TradeDateTime", "LastPrice", "Volume"}
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{path} is missing columns: {sorted(missing)}")
        frame["tick_sequence"] = range(len(frame))
        frame["symbol"] = frame["ShareCode"].astype("string").str.strip().str.upper()
        frame["source_timestamp"] = frame["TradeDateTime"].astype("string")
        frame["timestamp"] = _localized(frame["TradeDateTime"])
        frame["price"] = pd.to_numeric(frame["LastPrice"], errors="coerce")
        frame["volume"] = pd.to_numeric(frame["Volume"], errors="coerce")
        frame["source"] = TRADESIM_OFFICIAL_TICKS
        frame["source_path"] = path.as_posix()
        for column, value in _provenance("tradeSim_ticks.zip").items():
            frame[column] = value
        frame["timestamp_valid"] = frame["timestamp"].notna()
        frame["price_valid"] = frame["price"].gt(0) & frame["price"].notna()
        frame["volume_valid"] = frame["volume"].ge(0) & frame["volume"].notna()
        if wanted is not None:
            frame = frame[frame["symbol"].isin(wanted)]
        if start is not None:
            lower = pd.Timestamp(start)
            lower = lower.tz_localize(_LOCAL_TZ) if lower.tzinfo is None else lower.tz_convert(_LOCAL_TZ)
            frame = frame[frame["timestamp"] >= lower]
        if end is not None:
            upper = pd.Timestamp(end)
            upper = upper.tz_localize(_LOCAL_TZ) if upper.tzinfo is None else upper.tz_convert(_LOCAL_TZ)
            frame = frame[frame["timestamp"] <= upper]
        pieces.append(frame)
    if not pieces:
        return pd.DataFrame(columns=["symbol", "timestamp", "source_timestamp", "price", "volume", "tick_sequence", "source"])
    return pd.concat(pieces, ignore_index=True)

"""Read-only catalog of the repository's historical SET50 data artifacts."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class DataPaths:
    root: Path
    constituents: Path
    ticker_audit: Path
    acquisition_report: Path
    metadata: Path
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
    return DataPaths(
        root=project_root,
        constituents=project_root / "data" / "processed" / "constituents" / "historical_set50.csv",
        ticker_audit=reports / "yahoo_ticker_audit.csv",
        acquisition_report=reports / "market_data_acquisition.csv",
        metadata=metadata,
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
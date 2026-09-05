"""Yahoo Finance-backed historical data downloader for research use."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import PurePosixPath
from pathlib import Path
from typing import Any

import pandas as pd
import yfinance as yf

from .constituents import get_required_symbols

logger = logging.getLogger(__name__)


def get_project_root(project_root: str | Path | None = None) -> Path:
    """Return the project root directory."""
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[2]


def normalize_yahoo_symbol(symbol: str) -> str:
    """Normalize SET50 symbol names to the Yahoo Finance ticker format."""
    normalized = str(symbol).strip().upper()
    if not normalized:
        raise ValueError("Ticker symbol cannot be empty.")
    if "." in normalized:
        return normalized
    return f"{normalized}.BK"


def build_raw_price_path(symbol: str, project_root: str | Path | None = None) -> Path | PurePosixPath:
    ticker = normalize_yahoo_symbol(symbol)
    relative_path = PurePosixPath("data/raw/prices") / f"{ticker}.parquet"
    if project_root is None:
        return relative_path
    root = get_project_root(project_root)
    return root / "data" / "raw" / "prices" / f"{ticker}.parquet"


def build_processed_price_path(symbol: str, project_root: str | Path | None = None) -> Path | PurePosixPath:
    ticker = normalize_yahoo_symbol(symbol)
    relative_path = PurePosixPath("data/processed/prices") / f"{ticker}.parquet"
    if project_root is None:
        return relative_path
    root = get_project_root(project_root)
    return root / "data" / "processed" / "prices" / f"{ticker}.parquet"


def _load_data_config(project_root: str | Path | None = None) -> dict[str, Any]:
    root = get_project_root(project_root)
    config_path = root / "config" / "data.yaml"
    if not config_path.exists():
        return {
            "data_source": "yfinance",
            "default_start_date": "2020-01-01",
            "default_end_date": None,
            "interval": "1d",
            "price_source": "raw",
            "storage_format": "parquet",
            "auto_discover_symbols": True,
            "skip_existing": True,
            "retry_count": 3,
        }

    import yaml

    with config_path.open("r", encoding="utf-8") as handle:
        loaded = yaml.safe_load(handle) or {}
    return loaded


def _save_download_report(report: dict[str, Any], project_root: str | Path | None = None) -> Path:
    root = get_project_root(project_root)
    report_dir = root / "results" / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "data_download_report.json"
    with report_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, ensure_ascii=False)
    return report_path


def download_set50_data(
    start_date: str,
    end_date: str,
    force: bool = False,
    project_root: str | Path | None = None,
    skip_existing: bool | None = None,
) -> dict[str, Any]:
    """Download missing Yahoo Finance data for the historical SET50 universe."""
    root = get_project_root(project_root)
    config = _load_data_config(root)
    skip_cache = config.get("skip_existing", True) if skip_existing is None else skip_existing

    raw_prices_dir = root / "data" / "raw" / "prices"
    raw_prices_dir.mkdir(parents=True, exist_ok=True)

    if skip_cache and not force and any(raw_prices_dir.glob("*.parquet")):
        logger.info("Skipping Yahoo Finance download because the local raw price cache already contains files.")
        return {
            "requested_symbols": [],
            "successful_symbols": [],
            "failed_symbols": [],
            "date_range": {"start": start_date, "end": end_date},
            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
            "failures": [],
        }

    requested_symbols = get_required_symbols(start_date, end_date)
    successful_symbols: list[str] = []
    failed_symbols: list[str] = []
    failure_details: list[dict[str, Any]] = []

    for symbol in requested_symbols:
        raw_path = build_raw_price_path(symbol, root)
        if raw_path.exists() and not force and skip_cache:
            logger.info("Skipping cached symbol %s from %s", symbol, raw_path)
            continue

        try:
            frame = yf.download(
                tickers=symbol,
                start=start_date,
                end=end_date,
                interval=config.get("interval", "1d"),
                auto_adjust=False,
                progress=False,
                threads=False,
                actions=False,
            )

            if frame is None or getattr(frame, "empty", True):
                raise ValueError("empty response from Yahoo Finance")

            if isinstance(frame.columns, pd.MultiIndex):
                frame = frame.droplevel(0, axis=1)

            price_frame = frame.copy()
            price_frame = price_frame.rename(columns=lambda name: str(name).strip().lower().replace(" ", "_"))
            if "adj_close" in price_frame.columns and "adjusted_close" not in price_frame.columns:
                price_frame = price_frame.rename(columns={"adj_close": "adjusted_close"})

            required_columns = {"open", "high", "low", "close", "volume"}
            missing_columns = sorted(required_columns - set(price_frame.columns))
            if missing_columns:
                raise ValueError(f"missing required price columns: {missing_columns}")

            price_frame.index = pd.to_datetime(price_frame.index)
            price_frame = price_frame.sort_index()
            raw_path.parent.mkdir(parents=True, exist_ok=True)
            price_frame.to_parquet(raw_path)
            successful_symbols.append(symbol)
            logger.info("Downloaded %s to %s", symbol, raw_path)
        except Exception as exc:  # pragma: no cover - exercised via tests with monkeypatch
            logger.exception("Failed to download %s", symbol)
            failed_symbols.append(symbol)
            failure_details.append(
                {
                    "symbol": symbol,
                    "error": str(exc),
                    "date_range": {"start": start_date, "end": end_date},
                }
            )

    report = {
        "requested_symbols": requested_symbols,
        "successful_symbols": successful_symbols,
        "failed_symbols": failed_symbols,
        "date_range": {"start": start_date, "end": end_date},
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "failures": failure_details,
    }
    _save_download_report(report, root)
    return report

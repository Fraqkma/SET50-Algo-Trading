"""Market-data validation utilities for raw Yahoo Finance data."""

from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_PRICE_COLUMNS = {"open", "high", "low", "close", "volume"}


def validate_market_data(dataframe: pd.DataFrame, symbol: str | None = None) -> dict[str, Any]:
    """Validate a raw OHLCV DataFrame and return a structured diagnosis."""
    issues: list[str] = []

    if dataframe is None or dataframe.empty:
        return {"is_valid": False, "symbol": symbol, "issues": ["empty dataframe"]}

    frame = dataframe.copy()
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]

    if not isinstance(frame.index, pd.DatetimeIndex):
        try:
            frame.index = pd.to_datetime(frame.index)
        except (TypeError, ValueError):
            issues.append("invalid datetime index")

    if frame.index.has_duplicates:
        issues.append("duplicate timestamps detected")

    if not frame.index.is_monotonic_increasing:
        issues.append("chronological ordering violated")

    missing_columns = sorted(REQUIRED_PRICE_COLUMNS - set(frame.columns))
    if missing_columns:
        issues.append(f"missing required columns: {missing_columns}")

    if len(frame) > 1:
        diffs = frame.index.to_series().diff().dropna()
        if not diffs.empty and (diffs > pd.Timedelta(days=2)).any():
            issues.append("unexpected time gaps detected")

    for column in ("open", "high", "low", "close"):
        if column in frame.columns:
            if frame[column].isna().any():
                issues.append(f"missing {column} values")
            if (frame[column] <= 0).any():
                issues.append(f"invalid price values in {column}")

    if "volume" in frame.columns:
        if frame["volume"].isna().any():
            issues.append("missing volume values")
        if (frame["volume"] <= 0).any():
            issues.append("invalid volume values")

    if "adjusted_close" in frame.columns and (frame["adjusted_close"] <= 0).any():
        issues.append("invalid adjusted_close values")

    return {
        "is_valid": not issues,
        "symbol": symbol,
        "issues": issues,
    }

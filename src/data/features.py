"""Leakage-safe feature engineering for explicitly approved market data.

This module contains pure transformations.  Production callers should obtain
their frame with :func:`src.data.research.load_approved_market_data` first;
that loader applies the date-aware eligibility gate to every retained row.
"""

from __future__ import annotations

import pandas as pd


def build_features(
    dataframe: pd.DataFrame,
    *,
    momentum_window: int = 20,
    short_window: int = 20,
    long_window: int = 50,
    volatility_window: int = 20,
    volume_window: int = 20,
) -> pd.DataFrame:
    """Build causal daily features from a single approved symbol.

    Every value at date ``t`` uses only prices/volume at or before ``t``.
    Rolling features deliberately keep their initial ``NaN`` values; no
    interpolation, forward-fill, or other repair is performed.  The input is
    copied and never modified.  ``dataframe`` must have a unique,
    date-like index (or a ``Date`` column) and a ``Close``/``close`` column.
    """
    if dataframe is None:
        raise ValueError("Input dataframe cannot be None.")
    windows = {
        "momentum_window": momentum_window,
        "short_window": short_window,
        "long_window": long_window,
        "volatility_window": volatility_window,
        "volume_window": volume_window,
    }
    if any(not isinstance(value, int) or value < 1 for value in windows.values()):
        raise ValueError("Feature windows must be positive integers.")

    frame = dataframe.copy(deep=True)
    if "Date" in frame.columns and not isinstance(frame.index, pd.DatetimeIndex):
        frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
        frame = frame.set_index("Date")
    elif not isinstance(frame.index, pd.DatetimeIndex):
        frame.index = pd.to_datetime(frame.index, errors="raise")
    if frame.index.has_duplicates:
        raise ValueError("Feature input contains duplicate dates; no silent deduplication is allowed.")
    frame = frame.sort_index()

    canonical_names = {
        original: str(original).strip().lower().replace(" ", "_")
        for original in frame.columns
    }
    frame = frame.rename(columns=canonical_names)
    columns = {str(column): str(column) for column in frame.columns}
    close_column = columns.get("close") or columns.get("adj_close") or columns.get("adjusted_close")
    if close_column is None:
        raise ValueError("Feature input must contain Close or Adj Close.")
    close = pd.to_numeric(frame[close_column], errors="coerce")
    if close.isna().any():
        raise ValueError("Close contains missing or non-numeric values; repair data before feature engineering.")

    features = frame.copy()
    features["daily_return"] = close.pct_change()
    features[f"momentum_{momentum_window}"] = close.pct_change(periods=momentum_window)
    features[f"sma_{short_window}"] = close.rolling(short_window, min_periods=short_window).mean()
    features[f"sma_{long_window}"] = close.rolling(long_window, min_periods=long_window).mean()
    features[f"trend_{short_window}_{long_window}"] = (
        features[f"sma_{short_window}"] / features[f"sma_{long_window}"] - 1.0
    )
    features[f"volatility_{volatility_window}"] = features["daily_return"].rolling(
        volatility_window, min_periods=volatility_window
    ).std(ddof=0)

    volume_column = columns.get("volume")
    if volume_column is not None:
        volume = pd.to_numeric(frame[volume_column], errors="coerce")
        if volume.isna().any():
            raise ValueError("Volume contains missing or non-numeric values; do not fabricate volume.")
        volume_mean_name = f"volume_sma_{volume_window}"
        features[volume_mean_name] = volume.rolling(volume_window, min_periods=volume_window).mean()
        features[f"volume_ratio_{volume_window}"] = volume / features[volume_mean_name]
    return features

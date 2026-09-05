"""Deterministic cleaning for raw market data."""

from __future__ import annotations

import pandas as pd


def clean_market_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Normalize names and timestamps while preserving missing values explicitly."""
    if dataframe is None:
        raise ValueError("Input dataframe cannot be None.")

    cleaned = dataframe.copy()
    cleaned.columns = [str(column).strip().lower().replace(" ", "_") for column in cleaned.columns]

    if "adj_close" in cleaned.columns and "adjusted_close" not in cleaned.columns:
        cleaned = cleaned.rename(columns={"adj_close": "adjusted_close"})

    if "adj_close" in cleaned.columns and "close" not in cleaned.columns:
        cleaned = cleaned.rename(columns={"adj_close": "close"})

    cleaned.index = pd.to_datetime(cleaned.index)
    cleaned = cleaned.sort_index()
    cleaned = cleaned.loc[~cleaned.index.duplicated(keep="last")]
    return cleaned
"""Feature engineering interfaces for market data."""

from __future__ import annotations

import pandas as pd


def build_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Return a cleaned feature frame without introducing lookahead bias."""
    if dataframe is None:
        raise ValueError("Input dataframe cannot be None.")
    return dataframe.copy()
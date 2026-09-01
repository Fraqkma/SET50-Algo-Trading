"""Data cleaning interfaces for market data."""

from __future__ import annotations

import pandas as pd


def clean_market_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean market data.

    TODO: Add deterministic validation and explicit missing-value handling.
    """

    raise NotImplementedError("Market data cleaning is not implemented yet.")
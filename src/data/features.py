"""Feature engineering interfaces for market data."""

from __future__ import annotations

import pandas as pd


def build_features(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Build reusable features from cleaned market data.

    TODO: Add only reproducible feature transforms with no lookahead bias.
    """

    raise NotImplementedError("Feature generation is not implemented yet.")
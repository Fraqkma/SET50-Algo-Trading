"""Market data loading interfaces.

The project skeleton does not load or synthesize any market data yet.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def load_market_data(source: str | Path | Any) -> pd.DataFrame:
    """Load market data from a source.

    TODO: Implement validated data loading when the data pipeline is added.
    """

    raise NotImplementedError("Market data loading is not implemented yet.")
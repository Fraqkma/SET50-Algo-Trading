"""Reusable market-data loading helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd


def get_project_root(project_root: str | Path | None = None) -> Path:
    """Resolve the repository root for data access."""
    if project_root is not None:
        return Path(project_root).resolve()
    return Path(__file__).resolve().parents[2]


def load_market_data(source: str | Path | pd.DataFrame | Any) -> pd.DataFrame:
    """Load market data from a CSV, Parquet file, or an in-memory DataFrame."""
    if isinstance(source, pd.DataFrame):
        return source.copy()

    path = Path(source)
    if not path.exists():
        raise FileNotFoundError(f"Data file does not exist: {path}")

    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path)
    if suffix in {".parquet", ".pq"}:
        return pd.read_parquet(path)
    if suffix == ".feather":
        return pd.read_feather(path)

    raise ValueError(f"Unsupported market-data format: {suffix}")
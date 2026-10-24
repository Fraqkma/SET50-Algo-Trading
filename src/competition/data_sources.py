"""Source labels and side-by-side comparisons for official/research market data."""
from __future__ import annotations

from typing import Any

import pandas as pd

SETTRADE_PRODUCTION = "SETTRADE_PRODUCTION"
TRADESIM_OFFICIAL_HISTORY = "TRADESIM_OFFICIAL_HISTORY"
TRADESIM_OFFICIAL_TICKS = "TRADESIM_OFFICIAL_TICKS"
TRADESIM_0_2_5_PRACTICE = "TRADESIM_0_2_5_PRACTICE"
TRADESIM_0_2_6_PRACTICE = "TRADESIM_0_2_6_PRACTICE"

KNOWN_MARKET_SOURCES = {
    SETTRADE_PRODUCTION,
    TRADESIM_OFFICIAL_HISTORY,
    TRADESIM_OFFICIAL_TICKS,
    TRADESIM_0_2_5_PRACTICE,
    TRADESIM_0_2_6_PRACTICE,
}


def compare_market_sources(
    left: pd.DataFrame,
    right: pd.DataFrame,
    *,
    left_source: str,
    right_source: str,
    keys: tuple[str, ...] = ("symbol", "timestamp"),
    values: tuple[str, ...] = ("open", "high", "low", "close", "volume"),
) -> dict[str, Any]:
    """Compare two source frames without merging them into a persisted dataset.

    Duplicate comparison keys are rejected because an arbitrary row pairing
    would hide source conflicts. Missing rows and differing values remain
    visible as separate outcomes.
    """
    if left_source not in KNOWN_MARKET_SOURCES or right_source not in KNOWN_MARKET_SOURCES:
        raise ValueError("Unknown market-data source label")
    if left_source == right_source:
        raise ValueError("Source comparison requires distinct source labels")
    required = set(keys)
    for name, frame in (("left", left), ("right", right)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} frame missing comparison keys: {sorted(missing)}")
        if frame.duplicated(list(keys)).any():
            raise ValueError(f"{name} frame has duplicate comparison keys")
    common_values = [column for column in values
                     if column in left.columns and column in right.columns]
    joined = left[list(keys) + common_values].merge(
        right[list(keys) + common_values], on=list(keys), how="outer",
        suffixes=("_left", "_right"), indicator=True, validate="one_to_one",
    )
    rows = []
    for item in joined.to_dict(orient="records"):
        match = item.pop("_merge")
        if match == "left_only":
            status, differences = "LEFT_ONLY", []
        elif match == "right_only":
            status, differences = "RIGHT_ONLY", []
        else:
            differences = [column for column in common_values
                           if not _values_equal(item.get(f"{column}_left"), item.get(f"{column}_right"))]
            status = "DIVERGENCE" if differences else "MATCH"
        rows.append({"status": status, "differences": differences,
                     "left_source": left_source, "right_source": right_source,
                     **{key: item[key] for key in keys},
                     **{key: value for key, value in item.items() if key not in keys}})
    counts = {name: sum(row["status"] == name for row in rows)
              for name in ("MATCH", "DIVERGENCE", "LEFT_ONLY", "RIGHT_ONLY")}
    return {"left_source": left_source, "right_source": right_source,
            "keys": list(keys), "compared_values": common_values,
            "row_count": len(rows), "counts": counts, "rows": rows,
            "persisted_data_modified": False}


def _values_equal(left: Any, right: Any) -> bool:
    if pd.isna(left) and pd.isna(right):
        return True
    if pd.isna(left) or pd.isna(right):
        return False
    return bool(left == right)

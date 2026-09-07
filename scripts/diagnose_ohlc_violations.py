"""Report the largest raw OHLC bound violations by ticker.

This diagnostic reads raw files only and never modifies them. It is intended to
inform the validation tolerance, not to clean or rewrite market data.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd



def max_violation(path: Path) -> dict[str, object] | None:
    frame = pd.read_csv(path)
    numeric = frame[["Open", "High", "Low", "Close"]].apply(pd.to_numeric, errors="coerce")
    high_gap = (numeric[["Open", "Close"]].max(axis=1) - numeric["High"]).clip(lower=0)
    low_gap = (numeric["Low"] - numeric[["Open", "Close"]].min(axis=1)).clip(lower=0)
    high_index = high_gap.idxmax()
    low_index = low_gap.idxmax()
    if high_gap.loc[high_index] >= low_gap.loc[low_index]:
        row_index, gap = high_index, high_gap.loc[high_index]
        direction = "high"
    else:
        row_index, gap = low_index, low_gap.loc[low_index]
        direction = "low"
    if not gap or pd.isna(gap):
        return None
    close = numeric.loc[row_index, "Close"]
    return {
        "Ticker": path.stem.replace("_", "."),
        "Date": frame.loc[row_index, "Date"],
        "Direction": direction,
        "Violation": float(gap),
        "Violation % of Close": float(gap / abs(close) * 100) if close else float("nan"),
    }



def main() -> None:
    parser = argparse.ArgumentParser(description="Find largest raw OHLC violations.")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/market_data"))
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    results = [
        result
        for path in sorted(args.raw_dir.glob("*.csv"))
        if ".invalid." not in path.name and (result := max_violation(path)) is not None
    ]
    report = pd.DataFrame(results).sort_values("Violation % of Close", ascending=False).head(args.limit)
    print(report.to_string(index=False, float_format=lambda value: f"{value:.6f}"))


if __name__ == "__main__":
    main()

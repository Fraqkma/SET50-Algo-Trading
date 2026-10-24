"""Regenerate the read-only exploratory OHLCV source catalog report."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.exploratory_market import build_exploratory_view, inventory_sources


def main() -> int:
    inventory = inventory_sources(ROOT)
    # Intraday Settrade candles remain inventory-only: their field semantics,
    # sampling cadence and pilot approval status differ from daily Yahoo OHLCV.
    intraday = []
    for timeframe in ("1m", "5m", "15m"):
        path = ROOT / "data" / "pilot" / "settrade" / "normalized" / f"bars_{timeframe}" / "data.csv"
        if not path.exists():
            continue
        frame = pd.read_csv(path)
        timestamps = pd.to_datetime(frame.get("timestamp", pd.Series(dtype=str)), errors="coerce", utc=True).dropna()
        duplicate_keys = [c for c in ("symbol", "timestamp") if c in frame]
        intraday.append({
            "symbol": "*", "source_type": "settrade_pilot_intraday",
            "path": path.relative_to(ROOT).as_posix(),
            "first_date": timestamps.min().date().isoformat() if not timestamps.empty else "",
            "last_date": timestamps.max().date().isoformat() if not timestamps.empty else "",
            "rows": len(frame), "usable_close_rows": int(frame.get("close", pd.Series(dtype=float)).notna().sum()),
            "duplicate_dates": int(frame.duplicated(duplicate_keys).sum()) if duplicate_keys else 0,
            "missing_trading_day_gaps_gt4_calendar_days": "", "invalid_ohlc": "",
            "volume_available": "volume" in frame,
            "volume_non_null_rows": int(frame.get("volume", pd.Series(dtype=float)).notna().sum()),
            "missing_close_rows": int(frame.get("close", pd.Series(dtype=float)).isna().sum()),
            "approved_from": "", "approved_to": "",
            "identity_note": f"{timeframe} pilot intraday only; excluded from daily exploratory continuity.",
            "notes": f"{frame['symbol'].nunique() if 'symbol' in frame else 0} symbols; volume semantics not used for daily trend matrix.",
        })
    if intraday:
        inventory = pd.concat([inventory, pd.DataFrame(intraday)], ignore_index=True)
    bars, conflicts = build_exploratory_view(ROOT)
    inventory_path = ROOT / "reports" / "exploratory_market_source_catalog.csv"
    conflicts_path = ROOT / "reports" / "exploratory_market_source_conflicts.csv"
    summary_path = ROOT / "reports" / "exploratory_market_view_summary.json"
    inventory.to_csv(inventory_path, index=False)
    conflicts.to_csv(conflicts_path, index=False)
    current_path = ROOT / "reports" / "current_set50_universe.csv"
    current = pd.read_csv(current_path, dtype=str)["symbol"].str.upper().tolist()
    current_bars = bars[bars["symbol"].isin(current)]
    summary = {
        "view": "EXPLORATORY_CURRENT_SET50_DISPLAY_UNIVERSE",
        "survivorship_safe": False,
        "current_universe_expected": len(current),
        "current_universe_with_data": int(current_bars["symbol"].nunique()),
        "current_universe_symbols_missing": sorted(set(current) - set(current_bars["symbol"])),
        "first_date": current_bars["Date"].min().date().isoformat() if not current_bars.empty else None,
        "last_date": current_bars["Date"].max().date().isoformat() if not current_bars.empty else None,
        "rows": int(len(current_bars)),
        "current_symbols_under_50_observed_closes": sorted(
            current_bars.groupby("symbol").size().loc[lambda sizes: sizes < 50].index.tolist()
        ),
        "invalid_ohlc_rows_retained_as_flagged_close_observations": int(current_bars["ohlc_status"].eq("INVALID").sum()),
        "source_files": int(len(inventory)),
        "conflicting_symbol_dates_excluded": int(len(conflicts)),
        "synthetic_rows": 0,
        "orders_placed": 0,
        "formal_eligibility_or_backtest_input": False,
        "reports": [str(p.relative_to(ROOT)) for p in (inventory_path, conflicts_path)],
    }
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

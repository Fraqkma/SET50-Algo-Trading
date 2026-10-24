# Market Data Acquisition Report

- Total historical symbols: 2
- Verified Yahoo tickers: 2
- Unresolved symbols: 0
- Requested inclusive date range: 2024-01-01 to 2026-09-05
- Source: Yahoo Finance via yfinance with `auto_adjust=False`, `actions=True`.
- Raw data is preserved under `data/raw/market_data/`; validation issues are reported, not cleaned in place.

## Status breakdown
- SUCCESS: 1
- PARTIAL: 0
- PARTIAL_KNOWN_GAP: 0
- FAILED: 1
- NO_DATA: 0

## Issues
- `BBB` / `BBB.BK` — FAILED: download failed after 1 attempts: unexpected download for BBB.BK
- None

No strategy, feature engineering, backtest, or optimization was performed.

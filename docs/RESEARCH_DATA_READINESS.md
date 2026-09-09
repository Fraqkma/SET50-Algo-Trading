# Final Research-Data Readiness

Run `python src/data/market_data_remediation.py` to regenerate the remediation
record, final readiness report, and approved manifest. The command does not
modify `data/raw/market_data`.

The current decision set is 18 `APPROVED`, 2
`APPROVED_WITH_KNOWN_GAP` (GULF and TIDLOR), 42 `NEEDS_REVIEW`, and 1
`REJECTED` (INTUCH). The machine-readable downstream manifest is
`data/processed/approved_market_data_manifest.csv`; it contains only the 20
explicitly approved symbols with bounded dates.

`MarketDataEligibilityGate` requires both an explicit remediation approval and a
matching manifest row. It also enforces SET50 membership, exact raw-date
presence, continuity boundaries, and known suspension rules. No raw OHLC value
is repaired, interpolated, or replaced. Feature engineering and backtesting
must not begin until the remaining 42 symbols are adjudicated or deliberately
excluded.

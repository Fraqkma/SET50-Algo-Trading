# Market Data Eligibility Gate

`MarketDataEligibilityGate` is the one read-only entry point for future Features
and Backtest code to determine whether a `(SET symbol, calendar date)` has
approved research data.  Consumers must call `gate.assess(symbol, date)` before
opening a raw file and must respect an excluded decision; they must not recreate
these checks locally.

The gate reads, without changing them:

- `data/processed/constituents/historical_set50.csv` for date-aware SET50 membership;
- `reports/yahoo_ticker_audit.csv` for an explicitly verified provider mapping;
- `reports/market_data_acquisition.csv` for source, output path, status, and validation findings;
- `reports/market_data_remediation.csv` for the explicit approval decision; and
- `data/processed/approved_market_data_manifest.csv` for the final approved symbol/date ranges; and
- the report-named raw CSV only to confirm that the requested date exists.

Eligibility requires active membership, a `VERIFIED` audit mapping, an explicit
`APPROVED` or `APPROVED_WITH_KNOWN_GAP` remediation status, any configured
approved date range, a report-named existing raw file, and an exact raw `Date`
row. Acquisition status alone never grants approval. The gate never guesses tickers, appends `.BK`,
forward-fills dates, or fabricates OHLCV.

Exclusion reasons include `OUTSIDE_SET50_MEMBERSHIP_PERIOD`,
`YAHOO_MAPPING_UNAVAILABLE`, `ACQUISITION_STATUS_<status>`,
`RAW_FILE_MISSING`, and `DATE_NOT_IN_RAW_DATA`.  `BANPU_KNOWN_SUSPENSION`
explicitly records the 17 July–3 August 2026 suspension without treating it as a
fillable data error.

Continuity policy is intentionally conservative: INTUCH remains its own
historical identity but is excluded from 1 April 2025 onward as
`INTUCH_POST_MERGER_IDENTITY_RETIRED`; GULF is excluded before that date as
`GULF_PRE_MERGER_CONTINUITY_BOUNDARY`.  Neither rule rewrites membership or
joins price histories.

Example:

```python
from src.data.eligibility import MarketDataEligibilityGate

decision = MarketDataEligibilityGate().assess("BDMS", "2024-06-03")
if decision.eligible:
    raw_file = decision.raw_file
else:
    log_exclusion(decision.reason)
```

The manifest is a projection, not a substitute for the gate: downstream code
must still call `assess` for every symbol/date and consume only `eligible=True`.

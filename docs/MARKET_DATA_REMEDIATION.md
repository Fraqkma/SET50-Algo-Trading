# Raw Data Remediation and Approval

`src.data.market_data_remediation` converts the immutable Gate 2 acquisition
report into one deterministic approval record per symbol. Run
`write_approval_reports()` after an acquisition-report refresh. It writes
`reports/market_data_remediation.csv` and `.md`; it never writes under
`data/raw/market_data`.

The workflow preserves all validation findings and classifies non-success data
as expected market/calendar gap, known suspension, insufficient coverage,
missing Yahoo data, OHLC anomaly, corporate action, ticker/identity issue, or
unknown/unresolved. A `PARTIAL` status is never automatically promoted:

- `APPROVED` is limited to acquisition rows already reported `SUCCESS`.
- `APPROVED_WITH_KNOWN_GAP` is limited to explicitly bounded GULF and TIDLOR
  post-corporate-action raw windows.
- `REJECTED` means no usable provider data is available (currently INTUCH).
- `NEEDS_REVIEW` retains unresolved warnings, notably every OHLC anomaly and BANPU.

Future Features and Backtest code must use `MarketDataEligibilityGate`, which
requires these approval records and their date boundaries. No consumer may
fill dates, infer tickers, or bypass a rejection.

## OHLC adjudication

Run `python src/data/ohlc_adjudication.py` after generating the remediation
report. It records each raw date that breaches `Low <= min(Open, Close) <=
max(Open, Close) <= High` beyond the acquisition tolerance. Each finding is
classified `YAHOO_VENDOR_DATA_ISSUE_SUSPECTED` and remains `NEEDS_REVIEW` until
the team obtains an authoritative SET EOD comparison. The official SET
historical EOD service is an evidence source, not a replacement feed: this
workflow never overwrites Yahoo rows or imports a substitute price.

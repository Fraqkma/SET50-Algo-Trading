# OHLC Anomaly Adjudication

The acquisition validator flags a bar when either `High < max(Open, Close)` or
`Low > min(Open, Close)` by more than the configured 0.1% tolerance. These are
mathematical OHLC-envelope violations: a valid high cannot be below a trade at
the open or close, and a valid low cannot be above one.

`src/data/ohlc_adjudication.py` re-reads every immutable raw CSV for symbols
already classified with `OHLC_ANOMALY`. It writes one record for every violating
date to `reports/ohlc_anomaly_adjudication.csv`, including the four prices,
volume, breached rule, gap, and decision. It does not edit, fill, or replace a
Yahoo value.

All current records are classified `YAHOO_VENDOR_DATA_ISSUE_SUSPECTED` and
remain `NEEDS_REVIEW`. This is not a claim that Yahoo is conclusively wrong:
the repository has no authoritative per-security, per-date SET EOD extract for
the affected dates. The official comparison source is SET's licensed
[Historical Data Request service](https://www.set.or.th/en/services/connectivity-and-data/data/historical), which offers end-of-day trading data by security. Until that evidence is supplied, the conservative outcome is no promotion.

The validator itself is not waived: each raw row is preserved as evidence and
the eligibility gate continues to exclude its `NEEDS_REVIEW` symbol. Corporate
action/identity controls for INTUCH/GULF, BANPU, and TIDLOR remain independent
of this OHLC process.

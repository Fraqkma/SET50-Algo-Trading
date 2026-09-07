# Yahoo Finance Ticker Audit

Gate 1 report for every symbol appearing in `historical_set50.csv`.
Only Yahoo quote metadata was queried. Historical OHLCV was not downloaded.

## Source coverage
- Constituent records: 400
- Unique SET symbols: 63
- Membership date bounds: 2023-01-01 to 2026-12-31
- Candidate rule: `<SET symbol>.BK`; each candidate was individually checked against Yahoo metadata.
- First/Last Data are intentionally `NOT_QUERIED_PRE_GATE`; coverage testing belongs after human approval.

## Status summary
- VERIFIED: 62
- UNVERIFIED: 0
- AMBIGUOUS: 0
- NOT_FOUND: 1

## Manual review required
- INTUCH — Yahoo metadata returned HTTP 404 for `INTUCH.BK`. Corporate-action resolution: INTUCH was combined into Gulf Development Public Company Limited (`GULF`) effective **2025-04-01**. Retain INTUCH for pre-merger historical review; use GULF as the post-merger security without silently rewriting history.

## Audit limitations
- Yahoo metadata confirms ticker identity and exchange, not historical date coverage.
- No raw data files, processed datasets, or downloader were created.

Audit generated: 2026-09-07T15:00:10.034981+00:00

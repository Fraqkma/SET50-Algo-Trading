# Settrade Pilot Data Pipeline

The isolated pipeline is separate from approved research data:

```text
runtime .env -> official SDK client -> rate limiter/retry classifier
  -> raw JSONL -> typed normalization -> non-repairing validation
  -> normalized pilot CSV -> atomic checkpoint -> later approval gate
```

The client loads `SETTRADE_APP_ID` and `SETTRADE_APP_SECRET` only at runtime.
Representations, redacted errors, health output, reports, and logs do not
contain secrets or access tokens. The sandbox environment is set in SDK memory;
no credential or user config file is edited by the client.

Normalized bars contain timestamp, symbol, interval, OHLC, volume, turnover,
source, retrieval time, timezone, session, and adjustment status. Turnover is
null unless supplied by the source. Validators detect duplicates,
non-monotonic time, invalid OHLC, negative volume/turnover, crossed quotes, and
invalid prices. No questionable record is repaired or filled.

The 1m-to-5m/15m aggregator uses first open, maximum high, minimum low, last
close, and summed observed volume. It never manufactures missing minutes and
marks incomplete buckets. Observed `value` semantics did not justify deriving
turnover.

No file under `data/raw`, `data/processed`, or the approved manifest is written
by this pipeline. Promotion requires separate review of licensing, identity,
corporate actions, membership, timestamp/session semantics, and discrepancies.

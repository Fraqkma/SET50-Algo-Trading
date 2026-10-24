# Settrade Collector Guide

The collector is pilot-only and bounded. It defaults to the current 20-symbol
universe in `config/settrade_collection.yaml`; it never expands automatically
to all SET50 names and never sends orders.

```powershell
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode candles --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode realtime --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode bid-offer --duration-seconds 30
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode combined --probe-first --probe-symbol PTT --once
.venv\Scripts\python.exe scripts/check_settrade_collector_health.py
```

`candles` requests the current Asia/Bangkok calendar-day window, stores raw 1m
responses, and derives 5m/15m bars. `realtime` stores quote snapshots.
`bid-offer` starts genuine official SDK subscriptions for a bounded duration,
persists callback payloads under `raw/bid_offer/events.jsonl`, and rotates
symbols in groups no larger than the configured 35-topic ceiling. Subscription
acknowledgements are not counted as market events. Normalized ten-level rows
are written to `normalized/bid_offer/data.csv`. The installed SDK exposes no
verified equity transaction/times-and-sales stream; `price_info` is a price
update, not an executed trade tick, and is never relabeled as one.

Writes are append-safe JSONL/CSV writes. Checkpoints are replaced atomically,
so restart does not truncate prior data. The collector uses a monotonic 3
requests/sec default and two bounded transient retries. Authentication,
malformed requests, entitlement errors, and permission errors are not retried.
No indefinite process is started by this task.

Pilot data is unapproved and may not be consumed by production backtests until
an explicit approval process exists.

With KGI routing (`013` / `ALGO_EQ`), the collector writes under the separate
`data/pilot/settrade/production` root. The sandbox root remains intact. Confirm
the current mode and bounded read-only API access with:

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_production_readiness.py
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
.\.venv\Scripts\python.exe scripts\audit_settrade_production_coverage.py
```

The readiness command never creates an Equity trading request. Account and
portfolio state remain untested until an account number is configured in the
runtime environment. The UI has no order actions. See
`docs/SETTRADE_PRODUCTION_CUTOVER.md` for capability evidence and the cutover
marker.

The daily runner uses `--probe-first --probe-symbol PTT` before a full combined
cycle. An authenticated `NO_DATA` or `STALE_RESPONSE` probe still allows the
independent BBO rotation but skips 50 candle requests; the next scheduled cycle
probes again. Once the probe has a current-session row, the full universe candle
collection runs. This accommodates the pilot API exposing BBO/quotes before
current-session candles. No stale response is promoted and no missing candle is
fabricated.

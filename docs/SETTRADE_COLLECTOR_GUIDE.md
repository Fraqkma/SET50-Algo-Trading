# Settrade Collector Guide

The collector is pilot-only and bounded. It defaults to the current 20-symbol
universe in `config/settrade_collection.yaml`; it never expands automatically
to all SET50 names and never sends orders.

```powershell
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode candles --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode realtime --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --mode bid-offer --duration-seconds 30
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

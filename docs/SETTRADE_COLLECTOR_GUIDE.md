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

`candles` stores recent 1m raw responses and derives 5m/15m bars. `realtime`
stores quote snapshots. `bid-offer` prepares the official realtime dispatcher
boundary and records a checkpoint; the empirical topic probe is limited to four
topics.

Writes are append-safe JSONL/CSV writes. Checkpoints are replaced atomically,
so restart does not truncate prior data. The collector uses a monotonic 3
requests/sec default and two bounded transient retries. Authentication,
malformed requests, entitlement errors, and permission errors are not retried.
No indefinite process is started by this task.

Pilot data is unapproved and may not be consumed by production backtests until
an explicit approval process exists.

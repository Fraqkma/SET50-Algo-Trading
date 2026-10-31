# Nov 2 Settrade Collector Verification

## Before/after check

The task metadata last captured on Oct 30 showed enabled `Ready`, user `server`, a daily 09:45 trigger, Password logon, `interactive_only=false`, `start_when_available=true`, wake enabled, `IgnoreNew`, action `scripts/start_settrade_daily.bat`, and working directory set to the repository. This configuration can launch logged out, but logged-out runtime execution is **not yet demonstrated**. The Oct 30 task run returned result `1` and its runner log ended `FAILED`; Oct 29 remains `PARTIAL_COLLECTION` with historical scheduler invocation `UNVERIFIED` despite 41 runner cycles exiting 0 and persisted data.

Run shortly after 09:45 Bangkok on Monday, 2026-11-02:

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_collector_readonly.py --target-date 2026-11-02
```

The script only queries Task Scheduler, process listing, existing runner log, checkpoints, and normalized CSVs. It does not start/stop the task, delete a lock, mutate files, call the broker, or place orders. It labels the outcome `SUCCESS`, `PARTIAL`, `NO_START`, or `UNKNOWN`; successful scheduler metadata alone is insufficient. Review the runner exit, fresh per-source timestamps/row counts, candle/BBO checkpoints, lock PID and process evidence, and exact next run together.

## Evidence snapshot to preserve

- Task Scheduler last/next run, result, state, enabled flag, user/logon mode, interactive-only, trigger, action, working directory and multiple-instance policy.
- Matching date's runner log start/finish/status and exit result.
- Separate daily, 1m, 5m, 15m and BBO target-date rows, latest timestamps and unique symbols.
- Candle/BBO checkpoints, `.settrade-runtime/daily.lock`, referenced PID and actual process list. A lock without a live owner is stale-state evidence, not proof of a running collector.
- Preserve raw collector evidence; do not infer missing candles, BBO or fills.

## Known comparison state

Oct 29 has 50 daily records (recovered 50/50, adjustment status unknown), 13,169 1m rows, 3,953 5m rows, 2,717 15m rows, and 17,389 BBO events / 347,780 normalized snapshots. Runner activity and persistence were evidenced; original scheduler invocation was not. Oct 30 is a separate partial snapshot: task result 1; runner failed after health-check timeouts; BBO checkpoint had 190 events; candle checkpoint status `NO_DATA` although later persisted intraday candles reached 16:37 Bangkok. Do not use Oct 30 evidence to revise Oct 29 counts.

No claim about Nov 2 success is made before the check is run and evidence reviewed.

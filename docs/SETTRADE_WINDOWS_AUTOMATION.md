# Settrade Windows Automation

The pilot collector is started by `scripts/start_settrade_daily.bat`, which
resolves the repository from the launcher location and uses the repository
`.venv`. It only calls the market-data collector; it never initializes an
account or submits orders.

## Daily lifecycle

- Task Scheduler trigger: Monday-Friday at 09:45 local Windows time.
- The runner acquires a PID lock, runs readiness, checks Asia/Bangkok session
  state, and exits cleanly for weekends, holidays reported as closed, or outside
  session hours.
- During continuous sessions it runs the existing `combined --once` collector
  in bounded cycles and reads the existing health checkpoint after each cycle.
  The midday break pauses API work.
- The fallback cutoff is the existing session classification at/after 17:00;
  Task Scheduler's one-day execution limit is only a secondary safety bound.
- Each exit writes an ignored JSON summary under `reports/runtime/` and a daily
  operational log under `logs/settrade/`.

## Safety and recovery

- `.settrade-runtime/daily.lock` prevents duplicate runners and recovers stale
  locks after verifying the recorded PID is no longer alive.
- `scripts/stop_settrade_daily.bat` writes a PID-targeted stop request. The
  runner checks it between API cycles and shuts down gracefully.
- Collector failures receive at most three attempts with 30/60-second backoff.
  Authentication, configuration, entitlement, and critical-disk failures are
  not retried by the existing retry layer.
- Shutdown releases the lock, removes the stop request, runs a health snapshot,
  and writes the final summary. Pilot files are append-only/checkpointed; no
  retention deletion is performed.

## Task Scheduler commands

From the repository root:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1 -DryRun
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1
PowerShell -ExecutionPolicy Bypass -File .\scripts\check_settrade_task.ps1
PowerShell -ExecutionPolicy Bypass -File .\scripts\uninstall_settrade_task.ps1
```

The registration uses the current Windows user with `InteractiveToken` and
limited privileges, `IgnoreNew` duplicate policy, `StartWhenAvailable`, and
`WakeToRun`. It does not embed credentials. If Windows requires elevation or a
password, stop at that prompt and run the registration manually with the exact
command above.

Manual operation:

```powershell
.\scripts\start_settrade_daily.bat --once
.\.venv\Scripts\python.exe scripts\check_settrade_collection_readiness.py
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
.\scripts\stop_settrade_daily.bat
```

Wake-from-sleep is subject to Windows power policy. Task Scheduler cannot power
on a fully shut-down machine; BIOS RTC or Wake-on-LAN would require a separate
human-approved configuration.

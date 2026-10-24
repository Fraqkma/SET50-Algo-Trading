# SET50 Settrade Collector

Run these commands from the repository root:

```powershell
The launcher resolves the active repository from its own location, so this guide
works after moving the research checkout to another drive.

Settrade files default to the repo-relative `data/pilot/settrade` path. To keep
large data outside the checkout, set `SET50_DATA_ROOT` in the process environment
or `.env`; the collector and research UI will both use `<root>/pilot/settrade`.
The warning and critical disk checks follow that same filesystem.
```

## Run the daily collector

```powershell
.\scripts\start_settrade_daily.bat
```

This is the normal command to start the session-aware daily collector.

## Watch the live log

```powershell
Get-Content .\logs\settrade\daily-$(Get-Date -Format yyyy-MM-dd).log -Wait
```

## Check collector health

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
```

## Run the collector directly

```powershell
.\.venv\Scripts\python.exe scripts\run_settrade_collector.py --universe current_set50 --mode combined
```

Use this mainly for manual testing/debugging. For normal collection, prefer `start_settrade_daily.bat`.

## Check Windows scheduled task

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\check_settrade_task.ps1
```

## Install / reinstall the scheduled task

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1
```

## Stop the daily collector

```powershell
.\scripts\stop_settrade_daily.bat
```

Notes:
- Run commands from the repository root.
- The scheduled collector normally starts Monday-Friday at 09:45.
- BBO updates are event-driven; records appear when the feed publishes changes.
- Orders must remain 0.

# Settrade collector scheduler readiness

Audit date: 2026-10-28 (Asia/Bangkok). Task: `SET50 Settrade Daily Collector`.

## Finding

The collector command is launched by Task Scheduler through `cmd.exe` and `scripts/start_settrade_daily.bat`, with working directory `D:\GitHub\SET50-Algo-Trading`. It does not require VS Code or an open terminal. A manual Task Scheduler launch at 23:41 Bangkok time authenticated, queried market status, wrote an after-hours summary, and exited with result `0`. Its process chain was the scheduled command and Python runner, not a VS Code child. VS Code happened to be open during this observation, so editor-closed runtime was not directly tested.

The task is **not logged-out capable yet**. The existing principal is the same Windows user at Limited run level with `Interactive` logon. It is enabled for Monday-Friday at 09:45, `StartWhenAvailable`, `WakeToRun`, and `IgnoreNew`. It was last run on 2026-10-28 at 23:41 after the manual trigger, result 0; the next scheduled run is 2026-10-29 at 09:45.

## Attempted change and blocker

The installer now accepts `-LogonType S4U`, preserving the same principal, action, directory, weekday schedule, limited run level, and duplicate controls. Updating the existing task through `Register-ScheduledTask` was denied by Windows (`0x80070005`, Access is denied), including the approved elevated attempt. The task remains `Interactive`; the report explicitly distinguishes that from the requested logged-out configuration. No password was requested, entered, or stored.

If Windows requires password-backed task registration, the single manual step is: in Task Scheduler, open **Task Scheduler Library → SET50 Settrade Daily Collector → Properties → General**, select **Run whether user is logged on or not**, click **OK**, and enter the account password only into Windows' native credential prompt. Do not send or save the password. Afterward, rerun `scripts/check_settrade_task.ps1`, confirm `logon_type=Password` (or S4U if Windows accepts it), then perform a separate logged-out validation. This repository cannot claim that validation yet.

## Locks and duplicate protection

The post-trigger runner lock was valid while the task ran and released on exit; there is no current stale lock or competing collector. Task Scheduler uses `IgnoreNew`; the runner also uses a PID, process creation time, executable identity, and atomic lock. One `ALREADY_RUNNING` log entry on 2026-10-26 is evidence that a duplicate launch was rejected, not a stale lock. Lock state now distinguishes `ACTIVE`, `STALE_LOCK`, `NOT_RUNNING`, `SCHEDULED_WAITING`, `ERROR`, and `UNVERIFIABLE`.

## State

- `EDITOR_INDEPENDENCE`: supported by the scheduled action and observed Task Scheduler launch; editor-closed test not performed.
- `LOGGED_OUT_RUNTIME`: pending; current task remains Interactive.
- `SCHEDULED_TASK_CHANGE`: Windows denied the requested update; no task settings were changed.
- Real orders: 0.

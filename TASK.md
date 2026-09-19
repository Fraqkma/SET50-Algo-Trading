# SET50 Algo Trading — Windows Automated Daily Collector Task

You are continuing the existing SET50 algorithmic trading repository.

This task is focused on OPERATIONS AUTOMATION for the existing Settrade pilot collector.

Do NOT redesign the market-data pipeline.
Do NOT change MODEL_V1.
Do NOT create a new alpha strategy.
Do NOT place any order.

The objective is to make the Windows server capable of automatically starting,
monitoring, and gracefully stopping the Settrade collector every Thai market
trading day with minimal human intervention.

All meaningful human decisions must be collected only at the END.

==================================================
AUTONOMOUS EXECUTION POLICY
==================================================

Do not stop for ordinary implementation decisions.

For safe, reversible engineering choices:

- inspect existing conventions
- choose conservative defaults
- document them
- test them
- continue

Only stop for a true hard blocker such as:

- missing administrator capability required for Task Scheduler registration
- unavailable Windows Task Scheduler
- missing runtime credentials
- Settrade authentication failure
- dangerous behavior that could place an order
- inability to guarantee graceful shutdown/data integrity
- severe repository correctness issue

If Task Scheduler registration itself requires human/admin approval:

still complete all scripts/configuration/tests first,
then leave only the registration step as a final human decision.

==================================================
MANDATORY STARTUP
==================================================

Before modifying anything:

1. Read `AGENTS.md` completely.
2. Read this `TASK.md` completely.
3. Inspect:
   - `git status`
   - `git diff`
   - current collector CLI
   - current readiness script
   - current health script
   - current Settrade config
   - checkpoint/storage logic
   - Windows helper scripts if any
4. Do NOT redo completed Settrade infrastructure.
5. Use:
   `.venv\Scripts\python.exe`
6. Confirm Python version.
7. Confirm `.env` remains ignored.
8. Never print credentials.
9. Never commit credentials.
10. Orders placed must remain exactly 0.

==================================================
KNOWN CURRENT STATE
==================================================

Repository already has:

- authenticated official Settrade SDK
- current H2 2026 SET50 universe with 50 symbols
- 1m collector
- derived 5m / 15m
- 35/15 BBO rotation
- combined collector mode
- readiness command
- health command
- checkpoints
- duplicate/conflict detection
- disk guardrails
- Asia/Bangkok session labels
- zero-order dry-run execution protection

Known commands include:

Readiness:

`.venv\Scripts\python.exe scripts/check_settrade_collection_readiness.py`

Collector:

`.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode combined`

Health:

`.venv\Scripts\python.exe scripts/check_settrade_collector_health.py`

Adapt exact commands to current CLI implementation.

==================================================
SAFETY REQUIREMENTS
==================================================

Automation must NEVER:

- initialize an account object
- submit an order
- modify approved production data
- alter MODEL_V1
- change strategy logic
- delete pilot market data automatically
- expose credentials
- run multiple duplicate collector instances accidentally
- hard-kill the process unless graceful shutdown has irrecoverably failed
- bypass Settrade rate/topic limits

The automated collector remains:

PILOT / STAGING / RESEARCH ONLY.

==================================================
PHASE 1 — AUDIT CURRENT COLLECTOR LIFECYCLE
==================================================

Inspect how the collector currently handles:

- startup
- Ctrl+C
- SIGINT / Windows console events
- checkpoint flush
- file flush/close
- realtime unsubscribe/disconnect
- API client shutdown
- exceptions
- process exit codes

Identify anything needed for unattended daily operation.

Do not rewrite functioning code unnecessarily.

==================================================
PHASE 2 — CREATE DAILY RUNNER
==================================================

Create a Windows-safe daily orchestration script.

Preferred Python entrypoint:

`scripts/run_settrade_daily.py`

or repository-consistent equivalent.

This runner should orchestrate:

1. readiness check
2. market/day validation
3. collector startup
4. session-aware collection
5. health monitoring
6. graceful shutdown
7. final health/status report
8. meaningful exit code

The runner must NOT call trading/account methods.

==================================================
PHASE 3 — SINGLE-INSTANCE LOCK
==================================================

Prevent duplicate simultaneous collector runs.

Implement a Windows-safe single-instance mechanism.

Possible methods:

- lock file with active PID validation
- Windows named mutex
- another simple robust repository-compatible method

Requirements:

- stale lock detection
- active process verification where possible
- do not start second collector if one is already running
- clear lock on clean exit
- recover safely from prior crash

Log:

ALREADY_RUNNING

when appropriate.

==================================================
PHASE 4 — TRADING-DAY AWARENESS
==================================================

The automation should not blindly run full collection every calendar weekday.

Implement a conservative trading-day check.

At minimum:

- weekend detection
- market/API status confirmation

Prefer actual Settrade market status over maintaining a hand-written holiday list.

If the day is a weekday but SET is closed for a holiday:

exit cleanly with:

MARKET_CLOSED / NON_TRADING_DAY

Do not treat this as an error.

Do not hard-code a long future holiday calendar unless an authoritative existing
source is already available.

==================================================
PHASE 5 — DAILY START WINDOW
==================================================

Use Asia/Bangkok time.

Target automated Windows Task Scheduler launch:

09:45 Asia/Bangkok
Monday–Friday

The daily runner should:

- start
- authenticate
- verify readiness
- prepare storage/checkpoints
- observe market state
- wait safely for the relevant pre-open/open period if needed

Do not aggressively poll while waiting.

==================================================
PHASE 6 — MARKET SESSION AWARENESS
==================================================

Use existing session labels / source market status.

Handle:

- pre-open
- morning continuous
- midday break
- afternoon pre-open
- afternoon continuous
- pre-close / auction
- market closed

During midday break:

avoid unnecessary aggressive candle polling.

Realtime subscriptions may be paused or maintained according to existing SDK
stability and conservative design.

Choose the simpler reliable implementation.

Document behavior.

==================================================
PHASE 7 — DAILY STOP CONDITION
==================================================

The process should shut itself down automatically after the final market session.

Preferred logic:

use market status first.

Provide a hard safety cutoff around:

17:05 Asia/Bangkok

The hard cutoff is only a fallback.

At shutdown:

1. stop new API work
2. unsubscribe realtime safely
3. flush raw events
4. flush normalized data
5. commit checkpoints
6. write session summary
7. run health snapshot
8. release single-instance lock
9. exit cleanly

Never rely only on Windows force termination.

==================================================
PHASE 8 — GRACEFUL SHUTDOWN SUPPORT
==================================================

Ensure the collector supports a programmatic stop request.

If necessary implement:

- stop event
- cancellation token
- graceful shutdown method

Windows Ctrl+C / console interruption should continue to work.

Test clean exit.

==================================================
PHASE 9 — CRASH RECOVERY
==================================================

Unexpected failure must not corrupt data.

Implement conservative behavior:

- bounded restart attempts
- restart only for transient/process failures
- preserve checkpoints
- append safely
- do not restart infinitely

Suggested default:

maximum 3 restart attempts per daily session

with conservative delay such as:

30 seconds
60 seconds
120 seconds

or equivalent bounded backoff.

Do NOT retry:

- credential failure
- entitlement failure
- invalid configuration
- critical disk-space condition

==================================================
PHASE 10 — DAILY SESSION LOGGING
==================================================

Create a clear operational log structure under an ignored runtime/log path.

Example:

`logs/settrade/`

or existing repository convention.

Partition by date/session.

Log:

- startup
- readiness
- authentication success/failure
- universe
- market status transitions
- collector mode
- rows/events written
- BBO rotations
- retries
- reconnects
- validation issues
- disk warnings
- shutdown reason
- final status

Never log credentials or tokens.

==================================================
PHASE 11 — DAILY SUMMARY
==================================================

At end of session generate a compact machine-readable summary.

Suggested:

`reports/runtime/settrade_daily_YYYY-MM-DD.json`

Fields:

date
timezone
start_time
end_time
runtime_seconds
market_day
startup_status
shutdown_status
symbols_expected
symbols_with_1m_data
one_minute_rows_written
bbo_events_written
rotation_generations
api_requests
retries
reconnects
rate_limit_errors
validation_errors
conflicts
disk_free_start
disk_free_end
orders_placed

orders_placed must always be 0.

Keep runtime reports ignored if repository convention says generated operational
reports should not be committed.

==================================================
PHASE 12 — HEALTH WATCHDOG
==================================================

During an active session periodically check:

- collector process alive
- latest candle lag
- BBO activity when expected
- API connectivity
- disk state
- recent exceptions

Do not overreact to illiquid symbols.

Use conservative thresholds.

The watchdog should distinguish:

HEALTHY
DEGRADED
FAILED

Do not trigger infinite restart loops.

==================================================
PHASE 13 — BBO ROTATION AUTOMATION
==================================================

Use the existing:

35 / 15 neutral rotation

Keep it strategy-neutral.

Verify automated daily startup correctly initializes:

- rotation group
- generation
- subscription metadata

and automated shutdown unsubscribes cleanly.

Do not increase topic ceiling.

==================================================
PHASE 14 — WINDOWS LAUNCHER SCRIPT
==================================================

Create a simple launcher:

`scripts/start_settrade_daily.bat`

It should:

1. determine repository root
2. use the repository `.venv`
3. run the daily runner
4. preserve meaningful exit codes
5. avoid embedding credentials

The launcher should work even when Task Scheduler's working directory is not the
repo directory.

Use absolute paths derived from the script location, not a machine-specific hard
coded user path where avoidable.

==================================================
PHASE 15 — OPTIONAL MANUAL STOP SCRIPT
==================================================

Create a safe manual stop helper if practical.

Example:

`scripts/stop_settrade_daily.bat`

Preferred behavior:

request graceful stop.

Do not use `taskkill /F` as the normal path.

If current architecture cannot support cross-process graceful stop cleanly,
document Ctrl+C/manual process stop instead rather than adding fragile machinery.

==================================================
PHASE 16 — WINDOWS TASK SCHEDULER DEFINITION
==================================================

Prepare automation for Windows Task Scheduler.

Preferred task name:

`SET50 Settrade Daily Collector`

Trigger:

Monday–Friday
09:45 local Windows time

Action:

launch:
`scripts/start_settrade_daily.bat`

Configuration goals:

- run whether user is logged in or not, if safely configurable
- wake computer to run task if Windows supports it
- start task as soon as possible after missed scheduled start
- do not start a new instance if already running
- allow task to run long enough for full market day
- do not force stop at an arbitrary short timeout

Do NOT assume administrator privileges.

==================================================
PHASE 17 — TASK REGISTRATION SCRIPT
==================================================

Create an idempotent registration helper.

Preferred PowerShell:

`scripts/install_settrade_task.ps1`

Requirements:

- inspect whether task already exists
- create/update safely
- use correct repo paths
- no credentials embedded
- clear output
- support dry-run if practical

Also create:

`scripts/uninstall_settrade_task.ps1`

that removes ONLY this scheduler task.

It must not delete data/logs/config.

If Windows asks for permission/password/admin interaction:

do not work around it.

Document the exact human step.

==================================================
PHASE 18 — TASK SCHEDULER STATUS CHECK
==================================================

Create:

`scripts/check_settrade_task.ps1`

Report:

- installed yes/no
- enabled yes/no
- next run
- last run
- last result
- current state

Do not expose credentials.

==================================================
PHASE 19 — MISSED START HANDLING
==================================================

If the machine boots after 09:45:

Task Scheduler should start the task as soon as possible.

The daily runner should inspect current market state.

Examples:

Machine starts 10:30:
start collection immediately.

Machine starts 13:00:
wait safely for afternoon session.

Machine starts 15:30:
collect remaining session.

Machine starts 18:00:
do not start a pointless collector;
write CLOSED and exit.

==================================================
PHASE 20 — MACHINE SLEEP / WAKE
==================================================

Support Task Scheduler setting:

Wake the computer to run this task

where available.

Do not claim this can power on a fully shut-down machine.

Document clearly:

Sleep:
Windows may wake via Task Scheduler configuration.

Shutdown:
Task Scheduler cannot power on the machine.

Future options for fully powered-off startup may include:

- BIOS RTC wake
- Wake-on-LAN

Do not configure BIOS/WOL automatically.

==================================================
PHASE 21 — CLOCK / TIMEZONE GUARD
==================================================

Verify Windows timezone/runtime interpretation.

The collector's exchange-local time must remain:

Asia/Bangkok

Task Scheduler uses local Windows clock.

Add readiness warning if system-local clock/timezone appears materially inconsistent
with expected operation.

Do not automatically change Windows timezone.

==================================================
PHASE 22 — MARKET CLOSED TEST
==================================================

Because current execution may occur outside market hours:

run the daily runner in a safe closed-market test mode if useful.

Verify:

- readiness
- lock creation
- closed-market detection
- no unwanted long wait
- no unnecessary realtime loop
- summary writing
- clean exit
- lock removal

==================================================
PHASE 23 — SIMULATED SESSION TESTS
==================================================

Using deterministic mocks/fixtures, test runner behavior for:

- 09:45 pre-open
- 10:30 open
- 12:45 lunch break
- 14:30 afternoon
- 16:35 auction
- 17:10 closed
- market holiday
- API transient failure
- authentication failure
- disk critical
- duplicate process
- collector crash/restart
- clean shutdown

Do not alter system clock for tests.

==================================================
PHASE 24 — FULL TESTING
==================================================

Add tests for:

- daily runner state machine
- Bangkok time handling
- single-instance lock
- stale lock recovery
- graceful stop
- restart policy
- market-closed exit
- summary generation
- secret redaction
- Task Scheduler command generation
- safe launcher paths

Run:

full pytest suite
focused automation tests
Settrade tests
execution tests
Python compilation
JSON validation
CSV validation
git diff --check
secret scan

==================================================
PHASE 25 — DRY RUN TASK SCHEDULER REGISTRATION
==================================================

If possible:

run registration script in dry-run/validation mode.

Verify:

- trigger
- path
- task name
- schedule
- instance policy

Do not require actual installation for tests.

==================================================
PHASE 26 — INSTALL TASK IF SAFE
==================================================

If:

- Windows Task Scheduler is available
- no elevated credential prompt is required
- registration can be completed safely
- repository environment is valid

then register the task.

If registration requires human interaction or elevation:

DO NOT bypass it.

Leave exact command for the human.

==================================================
PHASE 27 — FINAL READINESS
==================================================

Run:

Settrade readiness check

automation readiness check

Task Scheduler status check if installed

Report one of:

AUTOMATION_READY
AUTOMATION_READY_REGISTRATION_REQUIRED
NOT_READY

with reasons.

==================================================
PHASE 28 — DOCUMENTATION
==================================================

Update collector documentation.

Create/update one concise operations document such as:

`docs/SETTRADE_WINDOWS_AUTOMATION.md`

Include:

- architecture
- schedule
- startup behavior
- market-session behavior
- shutdown behavior
- crash recovery
- log paths
- daily reports
- install command
- uninstall command
- status command
- manual run command
- manual stop procedure
- sleep/wake limitation
- shutdown limitation
- troubleshooting

Avoid redundant docs.

==================================================
FINAL CONSOLIDATED REPORT
==================================================

Do not stop before this section unless hard-blocked.

Report:

## AUTOMATION STATUS

- readiness status
- Task Scheduler installed yes/no
- task name
- trigger
- next run if installed

## DAILY LIFECYCLE

Describe:

09:45 start
readiness
market-state handling
collection
midday behavior
afternoon
auction
graceful close
final summary

## FAILURE HANDLING

Report:

- single-instance protection
- retries
- crash restart count
- auth failure behavior
- disk-critical behavior

## WINDOWS BEHAVIOR

Report:

- logged-in requirement
- wake-from-sleep capability
- missed-start behavior
- shutdown limitation

## EXACT COMMANDS

Give exact commands for:

install scheduler task

check scheduler task

uninstall scheduler task

manual daily run

manual readiness

manual health check

manual safe stop

## VERIFICATION

Report:

pytest
focused tests
compile
JSON/CSV checks
git diff
secret scan

Required:

credentials exposed = NO
orders placed = 0
MODEL_V1 changed = NO
approved data changed = NO

==================================================
FINAL HUMAN DECISIONS
==================================================

Only include decisions that truly require the human.

Possible decisions:

1. Install/enable Windows Task Scheduler task if elevation is required.
2. Run task while user is logged out or logged in only.
3. Enable Windows “Wake the computer to run this task”.
4. Whether to later configure BIOS RTC/Wake-on-LAN for fully powered-off startup.
5. Whether automated collection should run every eligible market day or selected days.

For each decision include:

- Option A
- Option B
- implications
- exact action required

Do not make irreversible system decisions automatically.

==================================================
END CONDITION
==================================================

After the final report and FINAL HUMAN DECISIONS:

STOP.

Do NOT:

- change strategy logic
- change MODEL_V1
- optimize alpha
- promote pilot data
- place orders
- enable real-money trading
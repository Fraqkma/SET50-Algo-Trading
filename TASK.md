# SET50 Algo Trading — Tick Data Probe + Historical Visualizer + Collector Hardening

You are continuing the existing SET50 algorithmic trading repository.

This is an autonomous implementation/research task intended to run end-to-end.

The human researcher will be away while this task runs.

The objectives are:

1. Fix remaining collector issues discovered from the latest automated run.
2. Determine whether Settrade Open API exposes true transaction-level trade/ticker data.
3. If available, implement safe raw trade-tick collection.
4. Continue collecting 10-level bid/offer updates.
5. Build a historical visualizer/dashboard for collected Settrade data.
6. Make the visualizer useful for manual inspection and research.
7. Keep all new data PILOT/STAGING only.
8. Do not alter strategy logic or MODEL_V1.
9. Put all human decisions only at the END.

==================================================
AUTONOMOUS EXECUTION POLICY
==================================================

Do not stop for ordinary engineering choices.

For reversible implementation choices:

- inspect repository conventions
- choose the simplest conservative design
- document assumptions
- test
- continue

Only stop early for a true hard blocker such as:

- Settrade authentication failure
- unavailable runtime credentials
- undocumented API behavior that creates access/compliance risk
- risk of placing a real-money order
- unrecoverable data corruption
- inability to preserve raw source fidelity
- critical disk shortage
- severe correctness issue that invalidates later phases

If one phase is blocked:
- record the blocker
- continue independent safe phases
- do not terminate the entire task unnecessarily

Collect all human decisions only in FINAL HUMAN DECISIONS.

==================================================
MANDATORY STARTUP
==================================================

Before modifying anything:

1. Read `AGENTS.md` completely.
2. Read this `TASK.md` completely.
3. Inspect:
   - `git status`
   - `git diff`
   - current branch
   - Settrade collector code
   - Windows daily automation
   - readiness/health scripts
   - current pilot data
   - existing Streamlit UI
   - existing reports
   - existing realtime schemas
4. Do NOT redo completed infrastructure unnecessarily.
5. Use:
   `.venv\Scripts\python.exe`
6. Confirm Python version.
7. Confirm `.env` is ignored.
8. Never print credentials.
9. Never commit credentials.
10. Real orders placed must remain exactly 0.

==================================================
KNOWN CURRENT STATE
==================================================

Current project already has:

- official Settrade SDK authentication working
- current H2 2026 SET50 universe with exactly 50 symbols
- quote access 50/50
- daily candles 50/50
- 1m candles 50/50
- 5m candles 50/50
- 15m candles 50/50
- realtime dispatcher
- realtime price_info
- realtime 10-level bid/offer
- 35/15 BBO rotation
- Windows Task Scheduler automation
- daily runner
- readiness/health checks
- per-symbol checkpoints
- duplicate/conflict detection
- disk guardrails
- Asia/Bangkok session handling
- dry-run zero-order execution protection
- Streamlit UI already exists in repository

Production MODEL_V1 remains:

- next-session execution
- LIMIT / IOC
- one adverse tick
- daily bar fill logic
- fees
- VAT
- cash constraints

Do not modify MODEL_V1.

==================================================
KNOWN LATEST COLLECTOR ISSUES
==================================================

From the most recent health report:

1. Candle checkpoints still showed timestamps from 2026-09-18 during the 2026-09-21 automated run.
2. Global candles checkpoint showed 49 completed symbols instead of 50.
3. BBO persisted event count remained 0.
4. Existing bid_offer checkpoint still reflected only the earlier 4-symbol preparation/probe.
5. Authentication/log activity continued much later than expected after market close.

These issues MUST be investigated before trusting tomorrow's automated collection.

==================================================
SETTRADE SAFETY LIMITS
==================================================

Known official limits supplied by the human:

General data API:
5 requests/sec

Market Data:
60 requests/sec

Order-changing:
60 requests/minute

Realtime subscription:
40 topics

Continue using conservative internal limits.

Do not attempt to bypass subscription limits through multiple connections.

==================================================
GLOBAL SAFETY RULES
==================================================

Do NOT:

- modify approved historical production data
- modify approved manifest
- weaken eligibility logic
- alter A/C/D0 strategy rules
- alter MODEL_V1
- promote pilot data automatically
- fabricate market events
- synthesize fake trade ticks
- infer transaction-level trades from price_info unless documentation proves that semantics
- interpolate missing bars
- hard-code credentials
- expose tokens
- exceed API limits
- initialize real trading/account paths
- place orders
- enable live trading

All new Settrade data remains:

PILOT / STAGING / UNAPPROVED.

==================================================
PHASE 1 — FIX LATEST COLLECTOR FAILURES FIRST
==================================================

Inspect:

- September 21 logs
- runtime summaries
- raw pilot files
- normalized files
- checkpoints
- Windows daily-runner logs

Determine exact root causes of:

A. stale 1m checkpoint timestamps
B. only 49 completed symbols
C. zero persisted BBO events
D. late-night runner/API activity

Specifically inspect whether:

- current-session request windows are stale/fixed
- UTC vs Asia/Bangkok conversion is wrong
- `combined --once` subscribes then exits too quickly for realtime events
- realtime callbacks are not wired to persistent storage
- one symbol fails due to response/checkpoint edge case
- session-close logic compares UTC to local time incorrectly
- daily runner keeps cycling after market close

Fix the smallest root causes.

Add regression tests reproducing the failures.

==================================================
PHASE 2 — VERIFY CURRENT-SESSION CANDLE COLLECTION
==================================================

After fixes:

ensure the collector requests the ACTUAL current trading session.

Requirements:

- all 50 symbols attempted
- current-session 1m bars can advance checkpoints
- stale historical response must not be mistaken for current-session success
- rows from previous days must remain preserved
- per-symbol checkpoint must reflect latest real retained timestamp
- global checkpoint must accurately report completeness

Add explicit stale-data detection.

If a request succeeds but latest returned timestamp is older than expected:
classify as STALE_RESPONSE rather than success.

==================================================
PHASE 3 — FIX REALTIME BBO PERSISTENCE
==================================================

The system currently observes BBO fields but has persisted 0 rotating events.

Inspect the full path:

subscription
→ callback
→ normalization
→ raw persistence
→ normalized persistence
→ checkpoint/update
→ rotation

Ensure genuine realtime events received from Settrade are persisted.

Do not create synthetic events.

Each raw BBO event should preserve:

- original payload
- retrieval timestamp
- symbol
- collector session ID
- rotation group
- generation
- subscription start timestamp

Each normalized BBO event should preserve 10 levels.

==================================================
PHASE 4 — REALTIME DWELL TIME
==================================================

Determine whether current `--once` behavior exits too quickly to receive events.

If yes:

implement a bounded realtime dwell interval.

Example configurable defaults:

- 30 seconds for smoke test
- 5 minutes for regular rotation group

Do not hard-code unnecessarily.

The daily runner should keep the realtime connection alive long enough to receive real events.

==================================================
PHASE 5 — CONFIRM AUTO SHUTDOWN
==================================================

Fix any timezone/session bug causing post-close execution.

Internal exchange-local decision time must be:

Asia/Bangkok.

Ensure:

- market-close detection works
- fallback cutoff works
- no normal API polling continues hours after market close
- daily runner exits gracefully
- summary records shutdown reason

Add deterministic tests around:

16:30
16:40
17:00
17:05
23:00

Thailand time.

==================================================
PHASE 6 — PROBE FOR TRUE TRADE/TICK STREAM
==================================================

This is a key research task.

Inspect:

1. installed `settrade-v2==2.2.1`
2. official SDK surface
3. official Settrade Open API documentation available locally / publicly accessible from the environment
4. realtime dispatcher methods

Look specifically for:

- trade tick
- transaction stream
- ticker
- last trade event
- time-and-sales
- trade-by-trade data
- deal event
- execution prints
- intraday transaction feed

Do NOT assume `price_info` is transaction-level.

Record exact methods and semantics.

Classify result as:

TRUE_TRADE_STREAM_AVAILABLE
PRICE_UPDATE_ONLY
NO_TRADE_STREAM_EXPOSED
INSUFFICIENT_EVIDENCE

==================================================
PHASE 7 — SAFE EMPIRICAL TRADE-STREAM PROBE
==================================================

If a documented trade/ticker stream exists:

subscribe to a SMALL test set:

PTT
ADVANC

or equivalent liquid symbols.

Capture a bounded sample.

Determine actual payload fields:

- symbol
- timestamp
- price
- volume/quantity
- side/aggressor if present
- sequence
- cumulative vs per-trade volume
- market state
- trade condition flags

Do not infer unavailable fields.

If market is closed:
do not fabricate evidence.
Implement/test subscription plumbing and continue.

==================================================
PHASE 8 — IMPLEMENT RAW TRADE-TICK COLLECTION IF SUPPORTED
==================================================

Only if true transaction-level semantics are verified.

Preferred path:

`data/pilot/settrade/raw/trades/`

Normalized:

`data/pilot/settrade/normalized/trades/`

Suggested schema:

event_timestamp
retrieved_at
symbol
price
quantity
sequence
side
trade_condition
source
collector_session_id

Fields unavailable from source remain null.

Preserve raw event separately.

==================================================
PHASE 9 — DO NOT FAKE TICKS
==================================================

If Settrade exposes only price_info updates:

DO NOT label them trades.

Store them separately as:

`price_info_updates`

Possible path:

`data/pilot/settrade/raw/price_info/`

and normalized equivalent.

Explicitly document:

price-info update != executed trade tick.

==================================================
PHASE 10 — MAXIMUM-GRANULARITY RAW DATA MODEL
==================================================

Target architecture should clearly separate:

RAW:
- trade ticks, if genuinely available
- BBO/depth updates
- price_info updates
- API candles

DERIVED:
- 1m
- 5m
- 15m
- spread
- midpoint
- depth
- imbalance
- execution diagnostics

Do not merge distinct event types into one ambiguous schema.

==================================================
PHASE 11 — DERIVE BARS FROM TRUE TRADE TICKS IF AVAILABLE
==================================================

If true trade ticks exist and include transaction quantity:

implement diagnostic-only local bar derivation.

For 1m:

open = first trade
high = max trade
low = min trade
close = last trade
volume = sum per-trade quantity

Then derive:

5m
15m

Do NOT replace Settrade candle API as canonical pilot source yet.

Instead compare:

trade-derived 1m
vs Settrade API 1m

Classify:

MATCH
SMALL_DIFFERENCE
MATERIAL_DIFFERENCE
INSUFFICIENT_TICKS

==================================================
PHASE 12 — TICK / BBO TIME ALIGNMENT
==================================================

If true trade ticks exist:

implement alignment utilities between:

trade event
nearest preceding BBO snapshot
nearest following BBO snapshot

Do not use future BBO for causal execution analysis unless explicitly labeled.

Support:

previous_book
next_book
time_gap_ms

This will later help study:

- spread at trade
- book depletion
- IOC plausibility
- intrabar execution

==================================================
PHASE 13 — STORAGE IMPACT OF TICK DATA
==================================================

Measure:

raw bytes/event
normalized bytes/event
events/minute/symbol

If market is open and enough events are observed.

Estimate 50-symbol storage:

1 month
3 months
6 months
12 months

Separately:

trade ticks
BBO
price_info
1m bars

Use LOW / BASE / HIGH if sample remains limited.

==================================================
PHASE 14 — STREAMLIT HISTORICAL DATA EXPLORER
==================================================

Build or extend the existing Streamlit UI.

Do NOT create a separate web framework.

Add a clear page/section:

`Settrade Data Explorer`

or repository-consistent name.

It must read ONLY pilot/staging data by default.

==================================================
PHASE 15 — EXPLORER CONTROLS
==================================================

Provide controls for:

Symbol

Date / date range

Data type:
- Candles
- BBO / Depth
- Price info
- Trades, only if supported

Timeframe:
- 1m
- 5m
- 15m
- 1d if available

Optional session filter.

Keep UI usable even if some data types are unavailable.

==================================================
PHASE 16 — CANDLE CHART
==================================================

Display historical OHLC as a candlestick chart.

Prefer an existing plotting dependency already available.

Do not add heavy dependencies unnecessarily.

Show:

OHLC
timestamp
volume if allowed for display

Important:

Volume may be shown as raw source volume with a warning if semantics remain unresolved.

Do not use it as a research feature automatically.

==================================================
PHASE 17 — TIME NAVIGATION
==================================================

Allow the human to inspect historical collected data easily.

Support:

- select exact date
- select range
- zoom/pan if plotting library supports it
- hover timestamp/OHLC values

For intraday:
show exchange-local Asia/Bangkok timestamps.

==================================================
PHASE 18 — DEPTH / ORDER-BOOK VIEW
==================================================

For BBO data:

allow selecting a timestamp/event.

Display 10 levels:

Bid:
level
price
volume

Ask:
level
price
volume

Prefer side-by-side tables.

Also display:

best bid
best ask
spread
spread bps
midpoint
depth 1
depth 5
depth 10
imbalance 1/5/10

Clearly show:

collector session
rotation group
event timestamp
retrieval timestamp

==================================================
PHASE 19 — DEPTH VISUALIZATION
==================================================

Add an intuitive depth visualization where practical.

For selected snapshot:

- bid-side cumulative depth
- ask-side cumulative depth

Do not fabricate levels.

If plotting library supports horizontal depth bars cleanly, use it.

Keep raw values accessible.

==================================================
PHASE 20 — BBO HISTORY CHART
==================================================

For a chosen symbol/date:

plot over time:

best bid
best ask
midpoint

and optionally:

spread bps

Use genuine persisted BBO events only.

If no events exist:
show a clear `No persisted BBO data` message.

==================================================
PHASE 21 — TRADE-TICK CHART IF SUPPORTED
==================================================

If true trade ticks are available:

plot:

trade price vs time

Optional marker sizing only if quantity semantics are confirmed.

Provide a raw trade table.

Do not call price_info events trades.

==================================================
PHASE 22 — PRICE + BBO OVERLAY
==================================================

Where timestamps overlap:

provide a view combining:

1m price
best bid
best ask

Do not over-interpolate.

BBO is event-driven, so use actual event timestamps.

If resampling for visualization:
label it explicitly.

==================================================
PHASE 23 — EXECUTION INSPECTION VIEW
==================================================

Add a manual research view for a selected timestamp.

Show:

symbol
time
current 1m bar
nearest valid BBO
spread
depth
MODEL_V1 one-tick estimate
observed-book crossing diagnostic
IOC plausibility

This is diagnostic only.

Do NOT change production MODEL_V1.

==================================================
PHASE 24 — DATA QUALITY PANEL
==================================================

For selected symbol/date display:

row count
earliest timestamp
latest timestamp
missing intervals
duplicate count
conflict count
validation issues
stale-data flags

This will help the human visually audit the collector.

==================================================
PHASE 25 — DATE AVAILABILITY INDEX
==================================================

Create a lightweight data index so the UI does not recursively scan all files on every render.

Track per:

symbol
date
datatype
timeframe

with:

row/event count
first timestamp
last timestamp
file/path metadata

Rebuild/update incrementally.

Do not move or rewrite raw source data.

==================================================
PHASE 26 — UI PERFORMANCE
==================================================

The viewer should remain usable as data grow.

Use:

- cached reads where appropriate
- date partitions
- symbol filtering before load
- bounded table display

Do not load all 50 symbols/all raw BBO into memory at once.

==================================================
PHASE 27 — UI SAFETY
==================================================

The dashboard must be READ-ONLY.

No:

- order buttons
- trading actions
- data deletion
- canonical promotion
- credential display

==================================================
PHASE 28 — SOURCE LABELS
==================================================

Every chart/table should make data source obvious:

SETTRADE_API_CANDLE
SETTRADE_BBO
SETTRADE_PRICE_INFO
SETTRADE_TRADE_TICK

only use the trade-tick label if verified.

Also show:

PILOT / UNAPPROVED

in the explorer.

==================================================
PHASE 29 — CURRENT DATA DIAGNOSTIC
==================================================

After fixing collector bugs, inspect what data actually exist.

Report:

dates available
symbols available
1m rows
BBO events
price_info events
trade events if available

Do not infer successful collection from file modification time alone.

Use timestamps inside records.

==================================================
PHASE 30 — NEXT-MARKET-SESSION READINESS
==================================================

Before finishing:

ensure tomorrow's automated collection path is genuinely ready.

Check:

Task Scheduler installed/enabled

daily runner

current 50 universe

current-date request windows

BBO dwell/persistence

rotation

market-close shutdown

logs

disk

readiness

==================================================
PHASE 31 — OPTIONAL SHORT LIVE TEST
==================================================

If market is open during execution:

run a bounded live test.

Collect:

current 1m
BBO
trade ticks if supported

Verify persistence.

If market is closed:

do not wait indefinitely.

Use mocks/fixtures for lifecycle tests and leave exact commands for the next session.

==================================================
PHASE 32 — TESTING
==================================================

Add tests for:

- stale candle detection
- 50/50 checkpoint completion
- current-session request windows
- BBO callback persistence
- realtime dwell lifecycle
- BBO rotation persistence
- Asia/Bangkok close cutoff
- price_info vs trade-tick type separation
- trade normalization if supported
- tick-derived bar aggregation if supported
- BBO/trade causal alignment
- data availability index
- explorer data loaders
- missing-data UI behavior
- read-only UI boundaries

Run:

full pytest
focused Settrade tests
automation tests
execution tests
UI/data-loader tests
Python compilation
JSON validation
CSV validation
git diff --check
secret scan

==================================================
PHASE 33 — DOCUMENTATION
==================================================

Update existing docs rather than duplicating unnecessarily.

At minimum cover:

- actual collector data types
- true trade-tick availability status
- raw vs derived architecture
- historical visualizer usage
- BBO/depth viewer
- timestamp/timezone handling
- source labels
- data-quality warnings
- volume semantics warning
- tomorrow automation readiness

Possible docs:

`docs/SETTRADE_COLLECTOR_GUIDE.md`

`docs/SETTRADE_DATA_EXPLORER.md`

`docs/SETTRADE_TICK_DATA_AUDIT.md`

==================================================
PHASE 34 — EXACT RUN COMMANDS
==================================================

Provide exact command for the Streamlit viewer.

Use existing app entrypoint where possible.

Example only:

`.venv\Scripts\python.exe -m streamlit run app.py`

Do not invent an entrypoint if repository uses another one.

Also provide:

readiness
health
manual collector
Task Scheduler status

==================================================
PHASE 35 — FINAL QUALITY AUDIT
==================================================

Inspect:

git diff

Remove:

debug prints
temporary probes
unused helpers
fake/sample empirical reports
duplicate docs

Preserve actual pilot evidence.

Verify:

credentials exposed = NO
orders placed = 0
MODEL_V1 changed = NO
approved data changed = NO
Task Scheduler behavior preserved

==================================================
FINAL CONSOLIDATED REPORT
==================================================

Do not stop before this section unless a true hard blocker occurs.

Report:

## 1. COLLECTOR BUG FIXES

- stale candles root cause
- 49/50 root cause
- zero BBO root cause
- late shutdown root cause
- exact fixes
- regression tests

## 2. TRUE TICK DATA AVAILABILITY

Classification:

TRUE_TRADE_STREAM_AVAILABLE
PRICE_UPDATE_ONLY
NO_TRADE_STREAM_EXPOSED
INSUFFICIENT_EVIDENCE

Report exact SDK method(s) and observed fields.

## 3. CURRENT RAW DATA ARCHITECTURE

List actual supported raw sources:

- candles
- BBO
- price_info
- trade tick if available

## 4. TICK COLLECTION

If supported:

- symbols tested
- events collected
- fields
- event rate
- storage estimate
- persistence paths

If unsupported:
state clearly.

## 5. BBO COLLECTION

- events persisted
- symbols covered
- rotations
- 10 levels status
- event rate if measured

## 6. HISTORICAL VISUALIZER

Report implemented views:

- candle chart
- date selector
- timeframe selector
- BBO table
- depth visualization
- BBO history
- trade chart if supported
- execution inspection
- data-quality panel

Give exact launch command.

## 7. DATA AVAILABLE NOW

Report:

- dates
- symbols
- 1m rows
- 5m rows
- 15m rows
- BBO events
- price_info events
- trade tick events

## 8. TOMORROW READINESS

State:

READY
PARTIALLY_READY
NOT_READY

for the next automated market session.

Explain blockers if any.

## 9. TESTS

Report:

pytest
focused collector tests
automation tests
UI tests
compile
JSON
CSV
git diff
secret scan

Required:

orders placed = 0
credentials exposed = NO
approved production data changed = NO
MODEL_V1 changed = NO

==================================================
FINAL HUMAN DECISIONS
==================================================

ONLY HERE collect real decisions requiring the human.

Potential decisions:

1. Whether to retain true trade ticks continuously if available.
2. Trade-tick retention duration.
3. Whether to retain price_info in addition to trades + BBO.
4. BBO retention duration.
5. Whether the visualizer should later become the main research UI.
6. Whether tick-derived bars should ever replace API candles after enough validation.
7. Whether to expand execution research after 1–2 weeks of tick/BBO data.

For each decision:

- Option A
- Option B
- evidence
- trade-off

Do not choose for the human.

==================================================
END CONDITION
==================================================

After the final report and FINAL HUMAN DECISIONS:

STOP.

Do NOT:

- optimize a strategy
- modify MODEL_V1
- promote pilot data
- enable live trading
- submit orders
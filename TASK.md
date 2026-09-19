# SET50 Algo Trading — Overnight Collector Hardening & Execution Research Task

You are continuing an existing SET50 algorithmic trading research repository.

This is an autonomous overnight engineering and research task.

The human researcher will be away while this task runs.

Your job is to complete as much SAFE, REVERSIBLE, TESTABLE work as possible
without repeatedly stopping for human approval.

The two primary objectives are:

A. Harden the Settrade pilot data infrastructure for the full current SET50 universe.

B. Build a rigorous execution-research framework using Settrade 1-minute data
   and 10-level bid/offer data so the current backtest assumptions can later be
   validated against observed market microstructure.

Do NOT create or optimize a new alpha strategy in this task.

==================================================
AUTONOMOUS EXECUTION POLICY
==================================================

Do NOT stop for ordinary engineering decisions.

For reversible implementation choices:

1. inspect existing repository conventions
2. choose the simplest conservative solution
3. document the assumption
4. test it
5. continue

Examples that do NOT require human approval:

- module names
- internal schemas
- batching details
- CSV vs Parquet when repository dependencies make one clearly preferable
- bounded retry count
- checkpoint implementation
- test fixture design
- directory organization
- deterministic sampling methodology
- conservative rate-limit scheduling
- whether to add a helper module
- whether to run a read-only API probe
- whether to perform a bounded pilot backfill
- whether to create diagnostic-only outputs

Only stop early for a TRUE HARD BLOCKER such as:

- Settrade authentication stops working
- required credentials disappear
- official API behavior indicates the task would violate access restrictions
- continuing could place a real-money order
- continuing requires irreversible modification of approved research data
- a severe correctness failure makes later phases unsafe
- local storage is unavailable or critically insufficient
- a required source is completely inaccessible and later phases depend on it

If one phase is blocked:

- record the blocker
- continue every logically independent safe phase
- do not terminate the whole task unnecessarily

Collect all meaningful human decisions at the END only.

==================================================
MANDATORY STARTUP
==================================================

Before modifying anything:

1. Read `AGENTS.md` completely.
2. Read this `TASK.md` completely.
3. Follow all repository-specific rules.
4. Inspect:
   - `git status`
   - `git diff`
   - relevant recent commits if useful
   - current Settrade code
   - current collector
   - current config
   - current reports
   - current tests
   - current approved-data boundaries
   - A/C/D0 execution assumptions
5. Do NOT redo completed phases.
6. Use:

   `.venv\Scripts\python.exe`

7. Confirm Python version.
8. Confirm `.env` is ignored by Git.
9. Never print credential values.
10. Never modify or commit `.env`.
11. Never initialize an account/order interface unless a later phase explicitly
    requires a zero-risk dry-run abstraction.
12. Real orders placed must remain ZERO.

==================================================
KNOWN PROJECT STATE
==================================================

The project already contains:

- approved daily research data approximately 2023–2026
- historical membership-aware eligibility
- Design A
- Design C
- D0 turnover-control diagnostic design
- backtest execution simulation
- LIMIT / IOC behavior
- one-tick adverse pricing
- fees and VAT
- universe-boundary exits
- walk-forward evaluation
- historical Yahoo staging
- historical identity audits
- transaction-cost attribution
- Settrade pilot infrastructure
- current H2 2026 SET50 universe
- Settrade 50-symbol capability probe
- realtime price_info probe
- realtime 10-level bid/offer probe

Do not alter A/C/D0 strategy behavior in this task.

==================================================
KNOWN D0 RESEARCH RESULT
==================================================

D0 classification:

MIXED

Known full-period result:

Design A:
- final equity approximately THB 2.881M
- net return approximately -71.19%
- turnover approximately 72.90x

D0:
- final equity approximately THB 4.953M
- net return approximately -50.47%
- turnover approximately 46.82x

D0 materially reduced turnover and transaction costs but remained materially
loss-making.

Positive D0 OOS folds:
1 / 5

Interpretation:

turnover/execution friction is a major problem, but alpha quality remains weak.

Do not optimize D0 further here.

==================================================
KNOWN SETTRADE STATE
==================================================

SDK:

`settrade-v2==2.2.1`

Authentication:

SUCCESS

Environment:

Broker ID:
`SANDBOX`

App Code:
`SANDBOX`

Known empirical capabilities:

- MarketData authentication works
- quote requests work
- daily candles work for recent history
- 1m candles work
- 5m candles work
- 15m candles work
- current H2 2026 SET50 universe = exactly 50 securities
- quote probe = 50/50
- daily probe = 50/50
- 1m probe = 50/50
- 5m probe = 50/50
- 15m probe = 50/50
- realtime dispatcher works
- price_info subscription works
- bid_offer subscription works
- 10 bid levels observed
- 10 ask levels observed
- bid/ask volumes observed
- historical daily evidence extends to approximately late 2023
- pre-2023 long historical coverage is not established
- historical SET50 constituent API is not exposed
- historical security master API is not exposed
- corporate-action API is not exposed
- real orders placed = 0

Existing collector smoke test:

- 3,527 1m rows
- 1,478 derived 5m rows
- 1,320 derived 15m rows
- zero validation issues

==================================================
KNOWN CURRENT SET50 UNIVERSE
==================================================

Use the already verified:

`reports/current_set50_universe.csv`

It contains exactly 50 unique H2 2026 SET50 securities.

Do NOT research the universe again unless integrity validation fails.

Do NOT infer membership from the old approved 20-symbol research universe.

==================================================
SETTRADE RATE LIMITS
==================================================

The human supplied official Settrade Open API limits:

General retrieval APIs:
maximum 5 requests / second

Market Data API:
maximum 60 requests / second

Order-changing APIs:
maximum 60 requests / minute

Market Data subscriptions:
maximum 40 topics

Treat these as HARD ceilings.

Use conservative internal limits.

Recommended defaults:

general_rps = 3

market_data_rps = 20
(prefer 20 rather than 30 unless existing implementation already safely uses 30)

order_change_per_minute = 30

subscription_topic_limit = 35

Never intentionally hit a limit.

Never attempt to use multiple connections to circumvent the subscription limit.

==================================================
GLOBAL SAFETY RULES
==================================================

Do NOT:

- modify approved historical raw data
- modify approved manifest
- weaken eligibility checks
- promote Settrade pilot data automatically
- fabricate historical membership
- silently merge ticker identities
- forward-fill missing market bars
- interpolate missing bars
- manufacture order-book snapshots
- hard-code credentials
- expose tokens
- exceed API rate limits
- create real orders
- enable live trading
- optimize strategy parameters
- introduce a new alpha strategy
- use future data in execution research
- change production execution assumptions solely to improve returns

All new Settrade outputs remain:

PILOT
STAGING
DIAGNOSTIC
UNAPPROVED

==================================================
PHASE 1 — AUDIT EXISTING SETTRADE INFRASTRUCTURE
==================================================

Inspect the actual implementation under:

`src/data/settrade/`

and:

`scripts/run_settrade_collector.py`

`scripts/check_settrade_collector_health.py`

`config/settrade_collection.yaml`

Review:

- credential loading
- API client lifecycle
- rate limiter
- retry classifier
- raw storage
- normalized storage
- checkpoints
- aggregation
- validation
- realtime subscription handling
- shutdown behavior
- restart behavior
- current universe configuration
- dry-run execution foundation

Do not rewrite working components unnecessarily.

Create a concise internal checklist of:

WORKING
PARTIAL
MISSING
NEEDS_HARDENING

Continue immediately to implementation.

==================================================
PHASE 2 — MAKE CURRENT SET50 THE FULL PILOT COLLECTION UNIVERSE
==================================================

The full current H2 2026 SET50 universe should be supported as a first-class
collector universe.

Keep compatibility with:

- approved_20
- current_set50
- custom

or equivalent existing modes.

Current SET50 must be loaded from a versioned artifact/config and validated:

- exactly 50
- unique
- correct effective period
- source provenance present

Do not dynamically scrape the universe on every collector launch.

==================================================
PHASE 3 — FINALIZE COLLECTION POLICY
==================================================

Use the following conservative DEFAULT PILOT policy unless repository evidence
requires a safer implementation.

For all 50 symbols:

PRIMARY retained bar:
1-minute

DERIVED locally:
5-minute
15-minute

Direct Settrade 5m/15m endpoints:
validation/cross-check only

Realtime:

10-level bid/offer

Price-info realtime:

optional diagnostic only, NOT required for every one of the 50 symbols if doing
so would unnecessarily consume realtime topics.

Do not duplicate equivalent information unnecessarily.

==================================================
PHASE 4 — HANDLE 40-TOPIC LIMIT CORRECTLY
==================================================

Current universe:
50 symbols

Official limit:
40 topics

Internal safety limit:
35 topics

The collector must NOT subscribe to 50 simultaneous BBO topics.

Implement and test a compliant rotation scheduler.

==================================================
4.1 Default BBO rotation policy
==================================================

Use <=35 simultaneous BBO topics.

Design a deterministic rotation policy covering all 50 symbols.

A reasonable conservative default:

GROUP A:
25 symbols

GROUP B:
25 symbols

or:

GROUP A:
35 symbols

GROUP B:
15 symbols

Choose the structure that makes lifecycle/reconnect handling simplest and gives
clear coverage metadata.

Do not optimize based on strategy outcome.

==================================================
4.2 Rotation metadata
==================================================

Every BBO event must preserve enough metadata to know:

- current subscription group
- subscription start
- subscription end where known
- rotation generation
- collector session ID

This is essential because rotated BBO data are NOT continuous observations.

Never pretend otherwise.

==================================================
4.3 Rotation interval
==================================================

Choose a conservative configurable default such as:

5 minutes

or another simple interval supported by architecture.

Document why.

Do not attempt high-frequency subscription churn.

==================================================
4.4 Strategy-neutral default
==================================================

Default rotation must NOT depend on A/C/D0 signals.

Support future priority overrides, but do not connect production strategy logic.

==================================================
PHASE 5 — HARDEN 1-MINUTE COLLECTION FOR 50 SYMBOLS
==================================================

The 1m collector must support all current 50.

Requirements:

- rate-limit safe
- bounded retries
- per-symbol checkpoint
- restartable
- append-safe
- no destructive overwrite
- duplicate detection
- conflicting-row detection
- timestamp normalization
- market-session awareness
- source/retrieval metadata
- SDK version metadata

Do not continuously refetch entire historical windows.

Fetch only what is required to close the recent gap where possible.

==================================================
PHASE 6 — MARKET-DAY AND SESSION MODEL
==================================================

Use source market status and official Settrade/SET documentation where available.

Model enough states to distinguish:

- pre-open
- continuous morning
- midday break
- continuous afternoon
- pre-close / auction
- closed

Do not poll 1m endpoints aggressively when market is closed.

Avoid assuming a 390-minute US-style session.

Use Thailand/SET-specific session behavior.

All internal exchange-local timestamps:

Asia/Bangkok

Raw epoch timestamps should remain recoverable.

==================================================
PHASE 7 — DERIVED 5M / 15M QUALITY
==================================================

Continue deterministic local aggregation from 1m.

For each target bucket:

open = first observed open
high = maximum observed high
low = minimum observed low
close = last observed close
volume = sum observed volume

Only aggregate `value` if its semantics become proven later.

Do NOT currently derive turnover from `value`.

Persist:

source_bar_count
expected_bar_count where determinable
incomplete_bucket
first_source_timestamp
last_source_timestamp

Do not fill missing source minutes.

==================================================
PHASE 8 — DIRECT-vs-DERIVED BAR CROSS-CHECK
==================================================

Use a bounded sample to compare:

derived 5m
vs Settrade direct 5m

derived 15m
vs Settrade direct 15m

For multiple symbols and dates.

Compare:

- open
- high
- low
- close
- volume
- timestamp alignment

Classify:

MATCH
SMALL_DIFFERENCE
MATERIAL_DIFFERENCE
INCOMPLETE_DERIVED_BUCKET

Investigate discrepancies.

Do not automatically alter aggregation logic merely to force equality.

==================================================
PHASE 9 — VOLUME / VALUE SEMANTICS INVESTIGATION
==================================================

This is a priority research task.

Known state:

Settrade OHLC matched Yahoo/approved observations in sampled dates.

Volume differed materially.

Settrade candle payload includes:

- volume
- value

but `value` has not been trusted as turnover.

==================================================
9.1 Build broader comparison sample
==================================================

Use a bounded but meaningful sample across:

- multiple dates
- at least 20 symbols where possible
- preferably all 50 if cheap
- approved/Yahoo overlap

Compare:

Settrade volume
Yahoo volume
approved volume

and where available:

Settrade value

Calculate:

Settrade / Yahoo volume ratio
Settrade / approved volume ratio
Yahoo / approved ratio

By:

symbol
date
price range if useful

==================================================
9.2 Inspect possible units
==================================================

Test descriptive hypotheses:

- shares vs lots
- shares vs board-lot units
- thousands
- cumulative semantics
- adjusted vs unadjusted
- endpoint aggregation difference

Do NOT choose a conversion simply because a ratio appears close to 100.

Require strong deterministic evidence.

==================================================
9.3 Official documentation
==================================================

Search official Settrade documentation for exact definitions of:

`volume`
`value`
`totalVolume`
`totalValue`

Record evidence.

==================================================
9.4 Result classification
==================================================

Classify volume semantics:

CONFIRMED_MATCH
CONFIRMED_UNIT_CONVERSION
CONFIRMED_DIFFERENT_SEMANTICS
UNRESOLVED

Until confirmed:

Settrade volume/value must NOT enter existing alpha features.

==================================================
PHASE 10 — NORMALIZE 10-LEVEL ORDER BOOK
==================================================

Observed realtime BBO fields include:

bid_price1 ... bid_price10
bid_volume1 ... bid_volume10

ask_price1 ... ask_price10
ask_volume1 ... ask_volume10

Normalize to a long-form depth schema.

Fields:

event_timestamp
retrieved_at
symbol
side
level
price
volume
source
collector_session_id
rotation_group
subscription_started_at
market_status if available

Preserve raw event separately.

==================================================
PHASE 11 — ORDER-BOOK DERIVED METRICS
==================================================

Create diagnostic-only derived metrics.

For each snapshot:

best_bid
best_ask

mid_price =
(best_bid + best_ask) / 2
when both are valid

spread =
best_ask - best_bid

spread_bps =
spread / mid_price * 10000
when valid

bid_depth_1
ask_depth_1

bid_depth_5
ask_depth_5

bid_depth_10
ask_depth_10

total_depth_1
total_depth_5
total_depth_10

imbalance_1
imbalance_5
imbalance_10

Suggested imbalance definition:

(bid_depth - ask_depth) /
(bid_depth + ask_depth)

when denominator > 0.

Document exact definitions.

These are diagnostics, NOT alpha factors.

==================================================
PHASE 12 — ORDER-BOOK VALIDATION
==================================================

Validate:

- nonnegative prices
- nonnegative volumes
- bid ordering
- ask ordering
- zero/empty levels
- best bid / ask relationship
- crossed book
- stale event
- duplicate event where identifiable
- malformed snapshot
- missing level
- unexpected flag fields
- market-status context

Important:

Previous smoke testing suggested ask-side ordering may not always match a naive
assumption.

Do not automatically reject observations until actual SDK field semantics are
confirmed.

Investigate field ordering from official docs if possible.

Separate:

INVALID
SUSPICIOUS
VALID
AUCTION_OR_SPECIAL_STATE

==================================================
PHASE 13 — RAW EVENT STORAGE HARDENING
==================================================

BBO can be high volume.

Ensure raw event storage is:

- append-safe
- restart-safe
- partitioned
- not one giant unbounded file

Prefer partitioning by:

date
event type
symbol or manageable group

Use repository dependencies.

If Parquet already exists and is reliable:

normalized depth may use Parquet.

Raw API/realtime events may remain JSONL if that preserves source fidelity.

Do not introduce an unnecessary database unless strongly justified.

==================================================
PHASE 14 — MEASURE ACTUAL BBO EVENT RATE
==================================================

If the market is OPEN during execution:

run a bounded realtime collection window.

Examples:

5–15 minutes.

Use a small compliant symbol group.

Measure:

events / minute / symbol

payload bytes / event

normalized bytes / event

Do not run indefinitely.

If the market is CLOSED:

do not fabricate this result.

Instead:

- preserve previous empirical sample
- mark event-rate measurement pending
- continue every other phase

==================================================
PHASE 15 — STORAGE MODEL
==================================================

Improve storage estimates.

For:

20 symbols
50 symbols

Estimate:

1 month
3 months
6 months
12 months

Separately:

1m bars
derived 5m
derived 15m
raw BBO
normalized depth

Use:

MEASURED

when based on real samples.

Use:

ESTIMATED

otherwise.

Provide:

LOW
BASE
HIGH

BBO scenarios if event rate remains uncertain.

==================================================
PHASE 16 — COLLECTOR DISK GUARDS
==================================================

Implement safe disk monitoring.

Before writing large data:

check available disk.

Define configurable warning threshold.

Examples:

warning below:
10 GB free

critical:
5 GB free

Choose conservative defaults appropriate for repository/system.

Do NOT automatically delete old data.

At critical threshold:

stop collection gracefully and report.

==================================================
PHASE 17 — COLLECTOR OBSERVABILITY
==================================================

Extend health metrics:

authentication status
collector start
collector session ID

bars:
- last 1m timestamp each symbol
- symbol lag
- missing symbols
- rows written
- duplicate attempts
- conflict count

BBO:
- current rotation group
- active topics
- events per symbol
- last event time
- stale symbols
- reconnect count

API:
- request count
- request rate
- retry count
- failures
- rate-limit errors

Storage:
- raw bytes
- normalized bytes
- free disk
- recent growth rate

==================================================
PHASE 18 — COLLECTOR CRASH/RESTART TEST
==================================================

Perform deterministic safe tests for:

start
collect/write small sample
checkpoint
shutdown
restart
resume

Ensure:

no existing valid rows are destroyed.

No conflicting duplicates are silently dropped.

Conflicting duplicates must be flagged.

==================================================
PHASE 19 — BUILD EXECUTION RESEARCH DATA MODEL
==================================================

Create an isolated execution research package.

Preferred location:

`src/research/execution/`

or repository-consistent equivalent.

Potential modules:

`book.py`
`spread.py`
`slippage.py`
`ioc.py`
`alignment.py`
`metrics.py`

Do NOT modify the production backtest engine.

==================================================
PHASE 20 — FORMALIZE CURRENT EXECUTION MODEL
==================================================

Document exactly what the current backtester assumes.

At minimum:

- next-session execution
- LIMIT / IOC
- one adverse tick
- daily bar High/Low fill condition
- commission
- VAT
- cash constraints

Document mathematical interpretation of current slippage.

This becomes the baseline model:

MODEL_V1

==================================================
PHASE 21 — DESIGN OBSERVED-BOOK SLIPPAGE MODEL
==================================================

Develop a DIAGNOSTIC candidate model.

Do not promote it.

Call it:

MODEL_OBSERVED_BOOK

Inputs where available:

decision time
next eligible execution timestamp
best bid
best ask
depth levels
order side
requested quantity
tick size

Potential diagnostic measures:

quoted spread
half-spread
full-spread crossing cost
one-tick cost
available size at best level
depth needed to fill quantity

If quantity exceeds best-level volume:

estimate depth-weighted executable price using successive observed book levels.

Call that metric something explicit such as:

`book_sweep_vwap`

Do not assume an order would necessarily execute through all levels.

This is a hypothetical liquidity diagnostic.

==================================================
PHASE 22 — ONE-TICK ASSUMPTION COMPARISON
==================================================

Build utilities comparing:

one adverse tick cost

versus:

best opposite quote crossing cost

and where possible:

depth-weighted book cost

Calculate:

cost THB
cost bps
difference from one-tick model

Classify each observation:

ONE_TICK_CHEAPER
ONE_TICK_SIMILAR
ONE_TICK_MORE_EXPENSIVE
INSUFFICIENT_BOOK

Choose a transparent tolerance for SIMILAR.

Do not optimize tolerance to results.

==================================================
PHASE 23 — PRICE-BUCKET ANALYSIS
==================================================

Current transaction-cost diagnostics found tick-size effects were not simply
monotonic by price.

Prepare analysis by deterministic price buckets, consistent where possible with
existing reports:

<5
5–10
10–25
25–50
50–100
>100

Compare:

tick bps
spread bps
book-crossing bps
depth cost

No strategy changes.

==================================================
PHASE 24 — SYMBOL COST ANALYSIS
==================================================

Existing largest slippage contributors include symbols such as:

BDMS
OSP
COM7
IVL
KTB

Do not assume those remain worst intraday.

Prepare a diagnostic to compare observed microstructure across symbols:

median spread bps
95th percentile spread
median level-1 depth
median depth-5
median depth-10
frequency of shallow book
frequency one-tick differs materially from spread

This becomes future evidence explaining why certain symbols were costly.

==================================================
PHASE 25 — IOC FILL PLAUSIBILITY MODEL
==================================================

Create a diagnostic model for whether an IOC LIMIT order would be plausibly
fillable at an observed snapshot.

For BUY:

requested limit >= observable ask required for fill

For SELL:

requested limit <= observable bid required for fill

Then incorporate quantity/depth.

Define diagnostic statuses:

FULL_DEPTH_AVAILABLE
PARTIAL_DEPTH_AVAILABLE
NO_MARKETABLE_QUOTE
NO_BOOK
SPECIAL_MARKET_STATE

This is NOT a claim about actual matching-engine priority.

Explicitly document limitations:

- queue priority
- hidden orders
- event latency
- cancellations
- inter-event movement
- timestamp synchronization
- auction behavior

==================================================
PHASE 26 — DAILY-BAR IOC MODEL COMPARISON
==================================================

Current backtest uses bar-range logic.

Create a future alignment framework to compare:

DAILY_BAR_MODEL

versus:

OBSERVED_BOOK_MODEL

For hypothetical orders where timestamps/data permit.

Do NOT manufacture historical BBO before data collection existed.

Only use genuinely observed periods.

Metrics:

daily model fill yes/no
book model fill plausibility
agreement/disagreement

Classify:

BOTH_FILL
DAILY_ONLY
BOOK_ONLY
NEITHER
INSUFFICIENT_DATA

==================================================
PHASE 27 — HISTORICAL ORDER REPLAY ALIGNMENT
==================================================

Do NOT pretend current realtime BBO existed during old 2023 trades.

Instead build architecture for future alignment.

If any overlapping newly collected execution-order dates exist in the future,
it should be able to ingest:

- strategy decision/order
- 1m bars
- nearest valid BBO event

Add deterministic tests using fixtures.

Do not fabricate retrospective market microstructure.

==================================================
PHASE 28 — PAPER-TRADING OBSERVATION MODE
==================================================

Build or harden a ZERO-ORDER observation mode.

It should:

- run strategy decision logic only if explicitly invoked in the future
- generate hypothetical intended orders
- attach current BBO/depth
- calculate MODEL_V1 cost
- calculate observed-book diagnostic cost
- log intended action

Must NOT call Settrade order submission.

Use an explicit name such as:

`shadow`
or
`dry-run`

Tests must prove order submission methods are unreachable in this mode.

Do not run A/C/D0 live strategy tonight unless there is already a safe
well-defined replay mode and doing so adds real value.

Infrastructure is the priority.

==================================================
PHASE 29 — EXECUTION RESEARCH REPORTING
==================================================

Create reusable reports for future collected data.

Examples:

`reports/execution_spread_summary.csv`

`reports/execution_depth_summary.csv`

`reports/execution_one_tick_comparison.csv`

`reports/execution_ioc_fill_diagnostics.csv`

`reports/execution_microstructure_by_symbol.csv`

If insufficient real data exist tonight:

create schemas and test-generated examples only where appropriate,

BUT DO NOT publish synthetic values as empirical results.

Clearly separate:

EMPIRICAL
PENDING_DATA
TEST_FIXTURE

==================================================
PHASE 30 — HISTORICAL DAILY STATUS CLEANUP
==================================================

Do not spend excessive time on historical Settrade API.

Current evidence indicates approximately late-2023 retention.

Confirm reports clearly state:

Settrade recent history:
useful

Settrade long-history replacement for Yahoo:
not supported by evidence

pre-2023 survivorship-safe research:
still blocked by historical membership

Do not continue hammering old date ranges.

==================================================
PHASE 31 — CONTINUOUS COLLECTION READY STATE
==================================================

Prepare clear commands.

Examples only; adapt to actual CLI.

50-symbol candles:

`.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode candles`

50-symbol rotating BBO:

`.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode bid-offer`

combined safe mode if supported:

`.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode combined`

one-shot diagnostic:

`--once`

bounded duration if implemented:

`--duration-minutes N`

Prefer providing bounded runtime options.

Do not automatically start an orphaned indefinite process from Codex.

==================================================
PHASE 32 — WINDOWS OPERATIONAL SUPPORT
==================================================

Because the repository runs on Windows:

provide simple optional helpers for later use.

Examples:

`scripts/start_settrade_collector.bat`

`scripts/check_settrade_collector.bat`

Do not embed credentials.

Do not install Windows services automatically.

If a reliable foreground workflow is sufficient, prefer it.

==================================================
PHASE 33 — COLLECTION READINESS CHECK
==================================================

Create one command that checks:

credentials available
authentication works
current universe valid
disk sufficient
config valid
API reachable
checkpoint readable
output writable
rate-limit config safe

Return:

READY
or
NOT_READY

with reasons.

Suggested script:

`scripts/check_settrade_collection_readiness.py`

==================================================
PHASE 34 — TESTING
==================================================

Add or expand deterministic tests for:

- 50-symbol universe integrity
- config parsing
- credential redaction
- rate limiting
- retry classification
- rotation group scheduler
- active topics <=35
- rotation metadata
- 1m storage
- 1m→5m
- 1m→15m
- direct-vs-derived comparison
- checkpoint resume
- conflicting duplicate detection
- disk guard
- BBO normalization levels 1–10
- depth ordering validation
- spread
- midpoint
- imbalance
- depth sums
- one-tick cost
- observed-book crossing cost
- depth-weighted cost
- IOC fill plausibility
- zero-order shadow mode
- order-submit method unreachable from dry-run
- timestamp normalization
- Asia/Bangkok handling

Run:

full pytest suite

plus:

Python compilation
JSON validation
CSV validation
`git diff --check`

If formatter/linter such as Ruff is unavailable:

report it but do not install unrelated tooling unless repository already expects it.

==================================================
PHASE 35 — SECURITY REVIEW
==================================================

Before finishing:

search changed files for:

- App ID
- App Secret
- tokens
- authorization headers
- account identifiers
- accidental `.env` content

Verify:

credentials exposed = NO

`.env` tracked = NO

==================================================
PHASE 36 — PRODUCTION ISOLATION REVIEW
==================================================

Verify this task did NOT modify:

approved raw historical data
approved manifest
eligibility semantics
Design A
Design C
D0 strategy rules
production execution assumptions

If shared utility modifications were required:

prove existing regression tests still pass.

==================================================
PHASE 37 — DOCUMENTATION
==================================================

Update existing documentation rather than creating many redundant files.

Core docs should cover:

1. Settrade full SET50 collection
2. collector operation
3. realtime rotation
4. volume/value semantics
5. order-book schema
6. execution research framework
7. one-tick model validation plan
8. IOC diagnostic limitations
9. storage estimates
10. safe startup commands

Possible files:

`docs/SETTRADE_COLLECTOR_GUIDE.md`

`docs/SETTRADE_FULL_SET50_COLLECTION.md`

`docs/SETTRADE_EXECUTION_RESEARCH.md`

`docs/SETTRADE_VOLUME_SEMANTICS_AUDIT.md`

Avoid documentation duplication.

==================================================
PHASE 38 — FINAL QUALITY AUDIT
==================================================

Inspect:

`git diff`

Remove:

debug prints
temporary probes no longer useful
placeholder outputs
dead code
duplicated documentation
unused helpers

Ensure every generated report reflects actual current implementation.

==================================================
FINAL CONSOLIDATED REPORT
==================================================

Do not stop before reaching this section unless a true hard blocker occurs.

Return one final report containing:

--------------------------------------------------
A. COLLECTOR HARDENING
--------------------------------------------------

Report:

- current SET50 symbols: expected 50
- validated count
- supported modes
- rate-limit configuration
- topic-limit configuration
- BBO rotation implementation
- rotation interval
- checkpoint behavior
- restart behavior
- disk guard
- market-session behavior
- readiness status

--------------------------------------------------
B. BAR DATA
--------------------------------------------------

Report:

- 1m support
- direct 5m support
- direct 15m support
- derived 5m status
- derived 15m status
- direct-vs-derived agreement
- any discrepancies

--------------------------------------------------
C. VOLUME / VALUE SEMANTICS
--------------------------------------------------

Report:

- Settrade vs Yahoo volume ratios
- Settrade vs approved ratios
- official documentation findings
- classification:
  CONFIRMED_MATCH
  CONFIRMED_UNIT_CONVERSION
  CONFIRMED_DIFFERENT_SEMANTICS
  UNRESOLVED

State explicitly whether Settrade volume is safe for research features.

--------------------------------------------------
D. ORDER BOOK
--------------------------------------------------

Report:

- number of levels
- observed fields
- normalization status
- validation findings
- spread support
- midpoint support
- depth metrics
- imbalance metrics
- any ordering ambiguity

--------------------------------------------------
E. BBO EVENT RATE / STORAGE
--------------------------------------------------

If empirically measured:

report measured event rate.

If market was closed:

state NOT_MEASURED_THIS_RUN.

Report estimated storage:

20 symbols:
1 / 3 / 6 / 12 months

50 symbols:
1 / 3 / 6 / 12 months

for:

- 1m
- derived 5m
- raw BBO
- normalized BBO

--------------------------------------------------
F. EXECUTION MODEL RESEARCH
--------------------------------------------------

Report whether framework can calculate:

- one-tick cost
- quoted spread
- crossing cost
- depth-1 cost
- depth-5/10 cost
- book-sweep diagnostic cost
- IOC fill plausibility
- daily-vs-book agreement

Clearly distinguish:

implemented framework

from

empirical conclusion

Do NOT claim empirical validation if not enough realtime data exist.

--------------------------------------------------
G. SLIPPAGE MODEL STATUS
--------------------------------------------------

State:

Current MODEL_V1:
one adverse tick

Observed-book diagnostic model:
implemented / partial / blocked

State exactly what additional live observations are needed before changing
production execution assumptions.

--------------------------------------------------
H. IOC MODEL STATUS
--------------------------------------------------

State:

what can be tested now

what remains unknowable because of:

- queue priority
- latency
- hidden liquidity
- matching-engine state

--------------------------------------------------
I. SHADOW / DRY-RUN TRADING
--------------------------------------------------

Report:

- dry-run implementation
- whether account object is required
- whether order submission is reachable
- number of actual orders placed

Required:
actual real orders = 0

--------------------------------------------------
J. HISTORICAL RESEARCH
--------------------------------------------------

Restate briefly:

- Settrade recent daily usable
- Settrade pre-2023 long history not supported by current evidence
- historical membership still unavailable
- Yahoo historical staging remains relevant
- pre-2023 survivorship-safe walk-forward remains blocked unless membership is solved

--------------------------------------------------
K. EXACT RUN COMMANDS
--------------------------------------------------

Give exact commands for:

1. readiness check

2. one-shot candle collection

3. continuous/foreground 50-symbol 1m collection

4. rotating BBO collection

5. combined mode if implemented

6. health check

7. graceful stop procedure

--------------------------------------------------
L. TEST RESULTS
--------------------------------------------------

Report:

- full pytest
- focused Settrade tests
- execution-research tests
- compilation
- JSON validation
- CSV validation
- git diff check
- secret scan

--------------------------------------------------
M. FILE SUMMARY
--------------------------------------------------

Report:

- files created
- files modified
- pilot data generated
- bytes/rows/events if relevant
- production files modified: YES/NO
- credentials exposed: MUST BE NO
- real orders placed: MUST BE 0

==================================================
FINAL HUMAN DECISIONS
==================================================

ONLY HERE list real decisions requiring the human.

Do not include trivial engineering choices.

For each decision:

- Option A
- Option B
- Option C where appropriate
- evidence
- trade-off
- what happens next under each option

At minimum consider:

--------------------------------------------------
DECISION 1 — START CONTINUOUS COLLECTION
--------------------------------------------------

A:
start collection next market session

B:
keep pilot-only and delay

Consider:

collector readiness
test status
API stability
storage
retention/licensing uncertainty

--------------------------------------------------
DECISION 2 — BBO RETENTION
--------------------------------------------------

Options may include:

3 months
6 months
12 months
indefinite

Show expected storage.

Do not automatically delete anything.

--------------------------------------------------
DECISION 3 — BBO COVERAGE STRATEGY
--------------------------------------------------

Examples:

A:
rotate all 50 neutrally

B:
continuous selected subset + rotating remainder

C:
BBO only during defined research windows

Explain topic-limit implications.

Do not select based on alpha.

--------------------------------------------------
DECISION 4 — VOLUME USE
--------------------------------------------------

If semantics resolved:

consider approving Settrade volume for pilot execution research.

If unresolved:

recommend keeping it excluded.

Do not silently promote.

--------------------------------------------------
DECISION 5 — EXECUTION MODEL RESEARCH PRIORITY
--------------------------------------------------

A:
collect enough BBO then empirically validate one-tick model first

B:
start new alpha research immediately in parallel

C:
both tracks in parallel with strict separation

Provide evidence from current loss/cost diagnostics.

Do not choose for the human.

--------------------------------------------------
DECISION 6 — FUTURE BACKTEST EXECUTION MODEL
--------------------------------------------------

Do NOT change it tonight.

Present criteria required before replacing MODEL_V1.

Examples:

minimum realtime sample
number of symbols
number of sessions
spread distribution stability
IOC diagnostic sample

--------------------------------------------------
DECISION 7 — HISTORICAL MEMBERSHIP
--------------------------------------------------

A:
request official historical membership/reference data

B:
continue current 2023–2026 approved universe only

C:
research another legitimate source

Explain effect on larger walk-forward.

--------------------------------------------------
DECISION 8 — SANDBOX ACCOUNT INTEGRATION
--------------------------------------------------

A:
continue zero-order shadow mode only

B:
later integrate an explicitly safe sandbox account

No real-money integration is allowed from this decision alone.

==================================================
END CONDITION
==================================================

After the FINAL HUMAN DECISIONS and execution summary are complete:

STOP.

Do not:

- optimize a strategy
- implement D1/D2
- alter production execution model
- promote pilot data
- submit orders
- enable live trading
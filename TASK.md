# TASK — Production Settrade Readiness, API Capability Audit, Data Refresh, and UI Upgrade

Repository root:

`D:\GitHub\SET50-Algo-Trading`

This is the primary research workspace.

The user will update `.env` manually before or during this task.

Known production routing values:

- `SETTRADE_BROKER_ID=013`
- `SETTRADE_APP_CODE=ALGO_EQ`

Do **not** ask for, print, log, commit, or echo the user's App ID, App Secret, PIN, account number, tokens, or any other secret.

Do **not** place, change, or cancel any real order.

Do **not** access the separate official KGI submission repository.

Do **not** commit or push.

Preserve all existing dirty work.

Never run:

- `git reset --hard`
- `git clean -fd`

---

## 0. Read instructions and inspect current state first

Read `AGENTS.md` first.

Then read all relevant repository docs and current implementations, including at minimum:

- `README.md`
- existing `TASK.md`
- Settrade collector docs
- market research terminal docs
- competition / TradeSim docs
- current Streamlit navigation/pages
- `scripts/run_settrade_daily.py`
- `scripts/check_settrade_collector_health.py`
- `scripts/run_settrade_collector.py`
- Settrade client/config/storage modules under `src/`
- existing tests around Settrade, health, UI, and data loaders

If `SKILL.md` or `skill.md` exists in the repository, read it completely before editing.

Do not assume the current implementation still matches old reports; inspect the actual code and data.

---

## 1. Main objective

Transition the research workspace from the old Settrade SANDBOX assumptions to a **safe production-readiness workflow** using the user's real KGI Settrade Open API access, while remaining strictly read-only for this task.

Deliver four outcomes:

1. Production authentication/readiness verification
2. Production-vs-sandbox API capability audit
3. Existing persisted market-data audit + safe incremental refresh
4. Streamlit UI upgrades so the user can visibly inspect connection state, account/read-only information, data freshness, and refreshed market data

No real order placement is allowed.

---

## 2. Production configuration detection

The user will manually edit `.env`.

Expected non-secret routing values:

```text
SETTRADE_BROKER_ID=013
SETTRADE_APP_CODE=ALGO_EQ
```

The App ID / App Secret must remain secret.

Inspect how environment variables are currently loaded.

Verify the application is no longer silently forcing:

- `SANDBOX`
- sandbox endpoints
- sandbox account naming conventions
- sandbox-only defaults

Add a safe configuration summary that may display only non-secret values, for example:

- environment mode: PRODUCTION / SANDBOX / UNKNOWN
- broker id
- app code
- SDK version
- account capability detected: yes/no/unknown

Never display App ID or App Secret.

---

## 3. Fix the known daily health timeout bug

There is a deterministic operational issue:

`run_settrade_daily.py` invokes:

`scripts/check_settrade_collector_health.py`

with a 30-second subprocess timeout.

The health command has recently taken approximately 40–45 seconds and therefore causes a false `FAILED` result.

Inspect and measure the current health path.

Make the smallest safe correction.

Preferred order:

1. identify why deep health takes >30 seconds
2. separate lightweight runtime health from expensive/deep health if this is clean and low risk
3. otherwise introduce a realistic configurable timeout
4. preserve genuine non-zero failures and exceptions

Do not simply hide failures.

Add regression tests proving a valid but slow health check no longer causes a false failed daily run.

Do not rewrite the collector.

---

## 4. Production authentication smoke test — READ ONLY

After the `.env` has production values, perform a safe authentication/readiness test.

Allowed:

- initialize official Settrade SDK objects
- authenticate
- create MarketData object
- create RealtimeDataConnection object
- create Equity/account object if supported and an account number is configured
- call read-only account / portfolio / order-list / deal-list methods if exposed and safe
- query market data
- subscribe briefly to realtime data
- disconnect cleanly

Forbidden:

- place order
- change order
- cancel order
- any method that can mutate the brokerage account

If an account number is required but not configured, do not guess it.

Report `ACCOUNT_NUMBER_REQUIRED`.

Never print secrets.

---

## 5. API capability audit: production vs old sandbox usage

Determine what this production KGI equity connection actually makes available.

Do not answer from assumptions alone.

Use three evidence layers:

1. current installed `settrade-v2` package and its actual Python objects/methods
2. current official Settrade Open API documentation
3. safe read-only production smoke tests

Create a capability matrix with at least:

### Market data

- historical candlestick
- realtime price info
- realtime bid/offer
- any market status / instrument metadata methods actually exposed
- supported intervals / parameters where discoverable
- actual returned BBO depth/fields
- production-vs-sandbox differences observed

### Equity account data

Where supported:

- account information
- cash balance / line available
- portfolio
- holdings
- orders
- order status
- deals / fills / executions
- realized / unrealized fields
- fee/commission-related fields
- subscriptions to order status if available

### Trading methods

Inventory only; do not call them.

Record existence/signatures for:

- place order
- change order
- cancel order

The UI may show that trading methods exist, but the task must keep them disabled.

### Important conclusion

Explicitly answer:

> What new capabilities do we gain from using the real KGI production investor connection instead of the old sandbox workflow?

Separate:

- genuinely new production account/private-state capabilities
- market-data capabilities that already existed in sandbox
- data-quality / realism differences
- methods that exist in the SDK but are not enabled for this account
- anything still unknown

Do not claim a capability unless supported by code/docs/read-only verification.

---

## 6. Official documentation research

Use the official Settrade Open API reference as the primary documentation source:

`https://developer.settrade.com/open-api/api-reference`

Where the site is difficult to crawl, inspect:

- installed SDK objects
- package source/docstrings
- official SDK examples
- authoritative broker documentation only as secondary evidence

Document the sources used.

Do not use old unofficial tutorials as the only authority for production behavior.

---

## 7. Existing data audit before refresh

Before collecting anything new, audit what is already persisted.

At minimum inspect:

### Settrade realtime/pilot data

- raw BBO
- normalized BBO
- 1m candles
- 5m candles
- 15m candles
- checkpoints
- runtime reports
- logs

### Historical/research data

- `data/raw/market_data`
- current daily OHLCV
- exploratory market view inputs/outputs
- current SET50 coverage
- latest genuine date per symbol
- known invalid OHLC rows
- conflicts / duplicates

For each dataset report:

- path
- row count
- symbol count
- earliest timestamp/date
- latest timestamp/date
- latest-day coverage
- obvious gaps
- malformed/conflicting rows
- provenance/source

Do not silently merge incompatible sources.

---

## 7A. Historical day-by-day coverage audit before any backfill

Do not inspect only the latest day. Audit prior trading days across the available Settrade collection history.

Build a day-by-day coverage report for every persisted Settrade dataset, especially:

- raw BBO
- normalized BBO
- 1m candles
- 5m candles
- 15m candles

For each trading date, calculate where applicable:

- expected universe size
- observed symbol count
- first timestamp
- last timestamp
- row/event count
- approximate session coverage
- symbols with zero observations
- symbols with partial observations
- obvious intraday gaps
- collector/log evidence for that date
- whether host/runtime evidence exists
- whether the day is SANDBOX, PRODUCTION, MIXED, or UNKNOWN provenance

Use the exchange calendar / actual trading-day evidence already available in the project. Do not treat weekends or holidays as missing collection days.

Produce a report that makes historical gaps easy to inspect rather than only reporting a single latest timestamp.

Classify each date with reason codes such as:

- COMPLETE_OR_EXPECTED
- PARTIAL_SESSION
- NO_RUNTIME_EVIDENCE
- COLLECTOR_FAILED
- AUTH_FAILED
- UPSTREAM_NO_DATA
- HOST_LIKELY_OFFLINE
- DATA_WRITE_FAILURE
- UNKNOWN_CAUSE

Only use a cause when supported by logs/runtime evidence. Otherwise use UNKNOWN.

## 7B. Missing-data inventory

Create an explicit inventory of data that should have been collected but is absent.

At minimum identify:

- missing trading dates
- missing symbols by date
- missing intraday intervals by symbol/date
- days where BBO exists but candles do not
- days where candles exist but BBO does not
- partial starts / early stops
- collector sessions that started but produced no usable data
- gaps caused by authentication/readiness failures
- gaps where no collector runtime evidence exists

Do not infer that all absent data can be recovered.

Separate missing data into:

- RECOVERABLE_FROM_API
- RECOVERABLE_FROM_EXISTING_OTHER_SOURCE
- NOT_RECOVERABLE_WITH_CURRENT_API
- UNKNOWN

Save a machine-readable gap report under the project's report convention and expose a concise version in Streamlit.

## 8. Re-check previous stale-data findings

The last readiness audit observed approximately:

- BBO newer than candles
- candles older than BBO
- daily OHLCV stale relative to Settrade data
- exploratory market view stale

Recalculate all of this from current files.

Do not blindly reuse old numbers.

Classify freshness as:

- LIVE
- FRESH
- STALE
- PARTIAL
- OFFLINE
- UNKNOWN

Use Asia/Bangkok timestamps.

---

## 9. Safe production market-data smoke collection

After successful production authentication, perform a small bounded test.

Use a tiny number of SET50 symbols first.

Verify:

- historical candle response
- realtime price response
- realtime BBO response
- schemas
- timestamps
- symbol naming
- depth structure
- volume/value fields
- session behavior

Do not immediately run a giant full-universe collection.

Compare production observations with persisted sandbox observations.

Document any schema/value differences.

---

## 10. Determine whether production resolves the old candle issue

The previous sandbox collector had cases where:

- realtime quote/BBO worked
- current-session candles returned `NO_DATA`

Now test the same candle path safely under production.

Determine whether production:

- returns current-session historical candles
- has the same delay
- behaves differently by interval
- behaves differently by symbol
- still produces `NO_DATA`

Do not forward-fill or fabricate missing bars.

This comparison is important.

---

## 10A. Historical backfill capability test

Before performing any historical repair, determine what the production API can actually backfill.

For a small sample of known missing dates/symbols, test read-only historical requests and document:

- how far back the API allows retrieval
- available candle intervals
- whether current and prior trading days behave differently
- whether BBO/depth history can be retrieved historically or is realtime-only
- returned timestamp boundaries
- pagination/limit behavior if any
- symbol/date-specific `NO_DATA` behavior

Do not assume realtime BBO gaps can be reconstructed historically.

Use these results to decide which historical gaps are genuinely recoverable.

## 11. Data refresh plan

If production authentication and market-data smoke tests succeed, refresh the research data safely.

### Intraday / Settrade

Use the existing collector architecture.

Do not create a parallel duplicate collector.

Before normal forward collection, execute a controlled backfill pass for gaps classified as `RECOVERABLE_FROM_API`.

Backfill rules:

- oldest missing trading date first unless API constraints require otherwise
- bounded requests; do not hammer the API
- respect existing rate limiting
- never fabricate unavailable BBO history
- never overwrite a valid persisted observation silently
- use duplicate/conflict detection on every recovered row
- preserve the original source/provenance
- mark recovered rows as backfilled where the schema permits
- produce before/after gap counts

If a gap cannot be recovered, retain it explicitly in the gap report rather than filling it synthetically.

Preserve:

- raw provenance
- normalized outputs
- checkpoints
- duplicate detection
- conflict detection
- session-aware behavior
- no interpolation
- no gap filling

### Daily OHLCV

Determine the best currently-supported source already used by this repository.

Refresh stale current-SET50 daily data incrementally from the last genuine observation through the latest available trading date.

Do not overwrite historical identity boundaries or synthesize merger histories.

Preserve symbol-identity policies for known sensitive names.

### Exploratory view

After source refresh:

- rebuild derived/exploratory metrics
- update freshness metadata
- rerun data-quality checks

Do not treat the current-SET50 exploratory view as survivorship-safe historical research.

---

## 12. Protect sandbox provenance

Existing sandbox data must remain distinguishable from new production data.

Do not silently append production observations into a dataset whose provenance says SANDBOX unless the storage format already has an explicit environment/source field that makes this safe.

If current schema cannot distinguish source environment cleanly:

design the smallest safe migration.

Preferred approaches:

- explicit `environment` / `source` field
- environment-specific subdirectories
- documented cutover marker

Do not destroy old sandbox data.

## 12A. Create an explicit production API cutover marker

Create a durable, human-readable marker for the exact point where this project begins using the new production KGI Settrade API configuration.

This marker must make it possible to distinguish:

- data collected before production cutover
- the first verified production API session
- data collected after production cutover

Record at minimum:

- cutover timestamp in Asia/Bangkok
- first successful production-auth timestamp
- first successful production market-data timestamp
- broker id = `013`
- app code = `ALGO_EQ`
- previous environment = SANDBOX where supported by evidence
- new environment = PRODUCTION
- git HEAD
- collector/runtime version if available
- latest persisted timestamp immediately before cutover
- first persisted timestamp after cutover

Never record secrets.

Preferred implementation:

- machine-readable cutover metadata under the existing runtime/report metadata convention, and
- a visible cutover marker in Streamlit / data-status UI.

The UI should clearly display something equivalent to:

`Production API cutover: YYYY-MM-DD HH:MM Asia/Bangkok`

Where charts/tables span both eras, visibly mark the cutover boundary so later differences in fields, coverage, latency, or data quality can be investigated rather than mistaken for market behavior.

Do not manufacture a historical cutover time. If the first successful production API use cannot be proven, mark it UNKNOWN until observed.

---

## 13. Production data provenance

Every newly persisted production observation should be traceable to:

- environment = production
- broker id = 013 where appropriate
- app code = ALGO_EQ where appropriate
- collector version / git HEAD if already supported
- collected timestamp
- market timestamp
- symbol
- source type

Never store secrets.

---

## 14. Account/private-state read-only adapter

If production auth exposes equity account/private state, create or reuse a clean **read-only adapter**.

It may expose normalized methods such as:

- connection status
- account summary
- portfolio
- holdings
- order list
- deal/fill list

Do not expose mutation methods through this adapter.

Do not add trading buttons to Streamlit.

If account number is required, use environment/configuration only.

Never hardcode it.

---

## 15. Streamlit UI — production status header

Update the Streamlit application so the user can immediately see:

- Settrade mode: PRODUCTION / SANDBOX / OFFLINE
- broker id
- app code
- authentication status
- market-data connectivity
- account-data connectivity
- latest successful API check
- collector running/not running
- latest data timestamp
- freshness badge

Do not display secrets.

---

## 15A. Streamlit UI — API cutover and historical gaps

Add visible operational history to the UI.

Show:

- production API cutover timestamp
- last sandbox observation
- first production observation
- whether a displayed dataset spans the cutover boundary
- historical day-by-day collection coverage
- missing-data count by dataset
- recoverable gap count
- unrecoverable/unknown gap count
- latest backfill run timestamp
- backfill success/failure summary

Where practical, add a timeline/calendar-style coverage view with one row per trading day so the user can immediately see which dates are complete, partial, missing, or unknown.

For selected dates, allow drill-down into missing symbols/intervals and evidence/reason codes.

## 16. Streamlit UI — Settrade / Data Status page

Create or upgrade a first-class status page that shows:

### Connection

- environment
- SDK version
- auth status
- MarketData status
- realtime status
- account/private API status
- last checked timestamp

### Collector

- daily runner status
- lock/process status
- last cycle
- last success
- last failure
- health duration
- current timeout configuration
- scheduler state

### Data freshness

Table for:

- raw BBO
- normalized BBO
- 1m
- 5m
- 15m
- daily OHLCV
- exploratory market view

Columns:

- latest timestamp
- symbols
- rows
- freshness
- source/environment

---

## 17. Streamlit UI — account summary (read only)

If production account access succeeds, show a **READ ONLY** account section.

Display only safe financial/account data already returned by the API, for example where available:

- cash balance
- line available
- portfolio value
- holdings count
- unrealized P/L
- realized P/L
- pending order count
- recent deal/fill count

Do not show:

- PIN
- secret
- token
- authentication material

Do not add any order-placement control.

Clearly label:

`READ ONLY — NO LIVE ORDER ACTIONS ENABLED`

---

## 18. Streamlit UI — portfolio/holdings

If available through the API, show a sortable table containing normalized fields such as:

- symbol
- quantity
- average cost
- market price
- market value
- unrealized P/L
- unrealized P/L %
- realized P/L if supported

Use actual API field semantics.

Do not invent unavailable values.

---

## 19. Streamlit UI — orders and deals

If read-only API methods are available, show:

### Orders

- order number/id
- symbol
- side
- quantity
- matched quantity
- price
- price type
- status
- timestamp

### Deals/fills

- symbol
- side
- quantity
- price
- timestamp
- order reference

Only if fields are genuinely available.

No Cancel / Change / Place controls.

---

## 20. Streamlit UI — API capability page/panel

Add a visible capability matrix so the user can see what the current production connection supports.

Example statuses:

- VERIFIED
- AVAILABLE_NOT_TESTED
- UNAVAILABLE
- REQUIRES_ACCOUNT_NUMBER
- UNKNOWN

Include:

- historical candles
- realtime price
- realtime BBO
- account info
- portfolio
- orders
- deals/fills
- order-status subscription
- trading methods present (disabled)

This should answer the user's question visually.

---

## 21. Market Research Terminal refresh

Update existing market/research pages so they use refreshed source data and expose source freshness.

At minimum ensure:

- latest daily date is visible
- latest BBO timestamp is visible
- candle freshness is visible
- source environment is visible
- stale warnings are not hidden

Do not blend sources with different timestamps without labeling them.

---

## 22. BBO / liquidity page upgrade

Use production BBO schema actually returned by the API.

Where supported, display:

- best bid/ask
- spread THB
- spread ticks
- spread bps
- available depth levels
- cumulative depth
- timestamp
- source environment

Do not assume the depth is 5 or 10 levels; detect and document what the production SDK actually returns.

Preserve the distinction between visible depth and fill probability.

---

## 23. Historical candle page/data audit

Expose:

- latest 1m/5m/15m bars
- coverage by symbol
- latest timestamps
- current-session availability
- missing/NO_DATA symbols
- production-vs-sandbox comparison

This should make it easy to confirm whether production fixed the earlier candle limitation.

---

## 24. Commands for the user

Provide exact commands from:

`D:\GitHub\SET50-Algo-Trading`

for:

### Activate research env

```powershell
.\.venv\Scripts\Activate.ps1
```

### Read-only production readiness check

Create/reuse a command such as:

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_production_readiness.py
```

If an equivalent script already exists, reuse it.

It must not place orders.

### Existing collector health

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
```

### Start collector manually

```powershell
.\scripts\start_settrade_daily.bat
```

### Direct collector debug

```powershell
.\.venv\Scripts\python.exe scripts\run_settrade_collector.py --universe current_set50 --mode combined
```

### Streamlit

```powershell
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

### Scheduler status

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\check_settrade_task.ps1
```

### Scheduler install

Only after readiness passes:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\scripts\install_settrade_task.ps1
```

Do not install the task automatically unless the current task explicitly requires it and all readiness checks pass.

---

## 25. Production readiness script

Create or improve a dedicated read-only script:

`scripts/check_settrade_production_readiness.py`

Desired checks:

1. environment variables present
2. broker id = 013
3. app code = ALGO_EQ
4. secrets present but never printed
5. SDK import/version
6. authentication
7. MarketData initialization
8. one safe historical candle query
9. one safe realtime capability probe
10. Equity/account adapter availability
11. account info read if account number configured
12. portfolio read if supported
13. order/deal list read if supported
14. disk/write health
15. collector health summary
16. source freshness summary

Final state:

- `READY`
- `READY_WITH_WARNINGS`
- `NOT_READY`

No real orders.

---

## 26. Safety guard against accidental real trading

Because the repo is now connected to a real brokerage environment, add explicit safeguards.

At minimum:

- production readiness scripts must be read-only
- UI must contain no trade action
- collector must not place orders
- test scripts must not place orders
- any existing order helper must not be invoked by readiness or data-refresh code
- tests should verify readiness flow never calls place/change/cancel methods

If practical, create a reusable production read-only guard/context for operational scripts.

Do not break existing competition simulation code.

---

## 27. Test plan

Add focused deterministic tests for:

### Configuration

- production broker/app code detection
- sandbox detection
- secret redaction

### Readiness

- auth success
- auth failure
- missing account number
- market data success/failure
- account API success/failure
- no order mutation

### Health timeout

- slow valid health succeeds
- real health failure remains failure
- timeout configuration

### Data

- production provenance
- sandbox provenance preserved
- duplicate/conflict behavior
- freshness classification

### UI/data models

- production status
- capability matrix
- account summary
- portfolio
- orders/deals
- stale state
- offline state

No tests may place real orders.

---

## 28. Validation

Before finishing:

- production readiness script (read only)
- collector health
- bounded production market-data smoke test
- focused tests
- full pytest
- Python compile checks
- Streamlit smoke
- manual Streamlit inspection at normal desktop size
- git diff --check
- git status
- secret scan if available

Do not print `.env`.

Do not place real orders.

---

## 29. Documentation

Update concise docs covering:

- transition from SANDBOX to KGI production
- broker id / app code as non-secret routing config
- what production adds compared with sandbox
- which capabilities were actually verified
- how to run readiness
- how to run collector
- how to inspect the UI
- data provenance/cutover
- account/private-state read-only policy
- current limitations

Do not duplicate large documents unnecessarily.

---

## 30. Final report

Report:

1. repo root / branch / HEAD
2. dirty work preserved
3. current environment mode
4. broker/app routing values detected
5. SDK version
6. production authentication result
7. market-data capability result
8. realtime capability result
9. equity/account capability result
10. portfolio capability result
11. orders/deals capability result
12. exact production-vs-sandbox differences discovered
13. trading methods present but not invoked
14. latest raw BBO timestamp
15. latest normalized BBO timestamp
16. latest 1m/5m/15m candle timestamps
17. latest daily OHLCV date
18. latest exploratory view date
19. current SET50 coverage
20. invalid/conflicting row findings
21. whether production current-session candles work
22. whether production BBO schema/depth differs
23. data refreshed
24. provenance approach
25. health timeout fix
26. readiness result
27. scheduler status
28. Streamlit changes
29. account/portfolio UI result
30. API capability UI result
31. tests
32. full pytest
33. Streamlit inspection
34. git diff --check
35. git status
36. files modified
37. blockers / unknowns
38. exact commands the user should run tomorrow morning
39. recommended next step before enabling automatic scheduled collection
40. production API cutover marker timestamp/status
41. last verified sandbox observation
42. first verified production observation
43. historical day-by-day coverage summary
44. missing trading dates/symbols/intervals discovered
45. recoverable vs unrecoverable gap counts
46. historical backfill capability discovered
47. backfill performed and exact recovered coverage
48. remaining unrecovered gaps and reason codes
49. confirmation that real orders placed = 0

Do not commit.
Do not push.
Do not place, change, or cancel any real order.

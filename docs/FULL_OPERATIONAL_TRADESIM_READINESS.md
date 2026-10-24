# Operational recovery and TradeSim upgrade readiness

This workspace keeps Settrade collection read-only for operational checks. Candle
recovery is bounded and append-only; realtime BBO history cannot be reconstructed
from candle bars. Missing timestamps are evidence of a gap in persisted bars, not
proof of a network outage or of a trade having occurred. The gap report records
estimated missing intervals separately for 1m, 5m, and 15m and identifies temporal
overlaps so those estimates are not added as if they were independent.

## Safe reconnect validation

`scripts/validate_settrade_reconnect.py` injects a local mock transport failure and
records `LIVE -> DEGRADED -> OFFLINE -> RECONNECTING -> RECOVERED -> LIVE` in
`reports/settrade_reconnect_validation.json`. It does not toggle Windows networking
or contact the broker. `LIVE_NETWORK_INTERRUPTION_NOT_OBSERVED` remains the status
until an actual interruption is safely observed during normal operation. The real
collector retry path starts a new read-only collection session, re-registers its
configured subscriptions, and re-reads current-day candle history; per-symbol
checkpoints and deduplicating storage remain in place.

## Bounded candle recovery

Plan candidate ranges without API calls:

```powershell
.\.venv\Scripts\python.exe scripts\plan_settrade_backfill.py --dry-run --date 2026-10-21 --symbol PTT --timeframe 1m
```

The planner defaults to at most 20 bounded requests, excludes BBO, and does not
apply data. `scripts/backfill_settrade_candles.py` is the single-range production
probe/append tool. Use its explicit `--symbol`, `--timeframe`, `--start`, and `--end`
for each limited recovery. Review the recorded validation and merge preview before
using `--apply`; a conflicting existing OHLCV row blocks the entire append. Raw
responses, source environment, request interval, retrieval time, and row counts are
retained as provenance. There is no unrestricted fill-all command.

## TradeSim runtime and next archive

The current official local baseline is `tradeSim0.2.5.zip` (SHA-256 is recorded in
`reports/tradesim_version_comparison.json`). It remains extracted in the existing
unversioned `tools/kgi_tradesim/` path for compatibility. The adapter requires
exactly Python 3.13.0; another 3.13 patch release must not be substituted. Run:

```powershell
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --check
.\.venv\Scripts\python.exe scripts\manage_tradesim_versions.py --check
```

When an official new ZIP is supplied locally, place it in the workspace root and
run `scripts/manage_tradesim_versions.py --check`. The tool hashes and inventories
local TradeSim ZIP files without extracting them and writes
`reports/tradesim_version_comparison.json`. Review requirements, package files,
strategy templates, notebook workflow, matching, order APIs, costs, persistence,
metrics, and practice-data layout. An unknown version is `NEEDS_ADAPTER_UPDATE`;
the 0.2.5 runner must not be used for it. After review, extract only to a new
`tools/kgi_tradesim/<version>/` directory with `--extract-version X.Y.Z`. Existing
directories are never overwritten and ZIP traversal paths are rejected. The tool
does not download archives or access the separate KGI submission repository.

The generated version report distinguishes `SUPPORTED`,
`SUPPORTED_WITH_WARNINGS`, `NEEDS_ADAPTER_UPDATE`, and `BLOCKED`. Capability fields
for a future version remain unknown until its archive is actually provided and
inspected. Current 0.2.5 runtime simulation is blocked on this machine because the
installed runtime list has Python 3.13.16 but not the required exact Python 3.13.0.

## Normal next trading day commands

From the repository root, use the already-configured research environment:

```powershell
.\.venv\Scripts\python.exe scripts\check_settrade_production_readiness.py
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
.\.venv\Scripts\python.exe scripts\audit_settrade_production_coverage.py
.\.venv\Scripts\python.exe scripts\build_settrade_gap_recovery_report.py
.\.venv\Scripts\python.exe scripts\plan_settrade_backfill.py --dry-run --date YYYY-MM-DD
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

Review the readiness result, source freshness, collector health, coverage and dry
run before a human decides whether to start the collector. These commands do not
place, change, or cancel orders. The scheduled collector remains separate and
should only be enabled after operational review.

## Verification evidence from 2026-10-21

The read-only candle capability matrix queried ADVANC, PTT, KBANK, DELTA, and MTC
for 1m/5m/15m bars over 09:30–10:00 on 2026-10-20 and 2026-10-21. All 30 requests
returned data. The first returned timestamp varied by interval (09:57, 09:55, and
09:45); the 10:00 end boundary was observed. This sample confirms those two dates
for these five symbols and intervals but does not prove a global lookback limit or
inclusive-start behavior. The matrix run appended 40 validated rows (20 5m and 20
15m); the 1m timestamps were already present. Merge conflicts: zero. The exact
request outcomes and provenance are retained in
`reports/settrade_candle_capability_matrix_apply_2026-10-21.json`.

The reconnect harness records `MOCK`, with the live interruption explicitly
`LIVE_NETWORK_INTERRUPTION_NOT_OBSERVED`. It injects a local transport error,
exercises the state transitions, verifies unique subscription restoration, and
checks the checkpoint hash before and after. It does not toggle Windows networking
or contact the brokerage API.

The REA MCP CDP endpoint `http://127.0.0.1:9222` returned `endpoint_unreachable`.
The configured Playwright browser inspected the local Streamlit app at 1440×960;
Overview, Gap Inspector, and Production API Status rendered without app exceptions.
TradeSim Results stays read-only and references only the local archive and saved
run artifacts. Watchlist and heatmap are embedded in Market Overview; the session
timeline is in Collection Health.

## TradeSim 0.2.6 readiness update (2026-10-22)

The organizer has designated TradeSim 0.2.6. The local archive is intact and
extracted to `tools/kgi_tradesim/0.2.6`; the 0.2.5 extraction remains in its
original unversioned compatibility location. Archive hash, changelog behavior,
source comparison, ingestion workflow, bridge/UI updates, and exact validation
commands are in [TradeSim 0.2.6 final readiness](TRADESIM_026_READINESS.md).

Runtime readiness is BLOCKED: `py -0p` shows Python 3.13.16 and 3.14.7, but not
3.13.0. Do not substitute another patch version. Requirements installation,
imports, one-day/multi-day simulation, matching regressions, and full Streamlit
inspection against a saved 0.2.6 run have not been completed. The official
history/tick archives are absent; this does not block the source and bridge work.
The read-only inventory command is `scripts/inspect_official_tradesim_data.py`.

## Current official daily data and runtime update (2026-10-22)

The earlier 0.2.5 baseline and runtime-blocked notes are historical. The designated 0.2.6 runtime now passes its exact Python 3.13.0 readiness check. The organizer's `Daily_Ticks.zip` has been extracted source-separately, inventoried, and integrated into the TradeSim runner behind explicit `--data-source official` selection. See the latest hash, coverage, source comparisons, and operational smoke evidence in [TradeSim 0.2.6 readiness](TRADESIM_026_READINESS.md) and [the integration guide](OFFICIAL_TRADESIM_INTEGRATION.md). Practice remains the default and is not overwritten.

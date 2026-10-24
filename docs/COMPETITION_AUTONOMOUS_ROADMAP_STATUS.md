# Competition autonomous roadmap status

Audit date: 2026-10-23 (Asia/Bangkok). Repository HEAD at inspection: `5c29ba0128155d50352ddd15a26cb0f9883d1627`; branch `main`; existing dirty work preserved. No commit or push was made.

This report reconciles the roadmap against code and fresh checks. Older reports are retained as historical evidence; where they conflict with this report, use the newer checked command output and the evidence artifacts listed below. The supplement's `docs/CODEX-NAVIGATION-GUIDE.md` is absent; `docs/README.md` was used for documentation navigation.

## Readiness scorecard

| Area | Status | Evidence / blocker |
|---|---|---|
| DATA | READY_WITH_WARNINGS | Official history and ticks are source-separated; Settrade current intraday observations exist. Daily exploratory data is stale (latest market date 2026-10-15 in the last health audit); history and source adjustment semantics differ. |
| LIVE COLLECTION | READY_WITH_WARNINGS | Collection readiness check passed; collector health sees recent production BBO callbacks but candle responses are NO_DATA. Scheduler is not installed/enabled. |
| OFFICIAL DATA | READY_WITH_WARNINGS | TradeSim history 2023-09-21–2026-10-21; tick archive 13 dates 2026-10-01–2026-10-21, 2,417,570 rows. Exact archive hashes in `reports/tradesim_official_daily_ticks_package.json`. |
| TRADESIM | READY_WITH_WARNINGS | Official 0.2.6 `--check` READY with Python 3.13.0; one-/three-day no-order and partial-fill/EOD fixtures passed. Market-to-Limit/IOC compatibility remains unconfirmed. |
| STRATEGY INFRA | READY_WITH_WARNINGS | Existing point-in-time data gate, features, backtest, official bridge, FIFO metrics, plus new descriptive eligibility helper. No final candidate selected. |
| RESEARCH EVIDENCE | NOT_READY | Prior A/C/D0 evidence is preserved. D0 walk-forward was mixed and loss-making; H1–H5 in the roadmap have not been evaluated in this run. No positive candidate currently clears the whole funnel. |
| STATE MACHINE | READY_WITH_WARNINGS | Pure state derivation and explicit order eligibility checks added in `src/competition/state.py`; it is descriptive, and unresolved official rules remain UNKNOWN. |
| COCKPIT | READY_WITH_WARNINGS | New read-only Competition Cockpit uses existing Market Overview, collection/production pages, and TradeSim results. It clearly labels missing portfolio/session state and exposes no order actions. |
| METRICS | READY_WITH_WARNINGS | FIFO, NAV/returns, drawdown, benchmark/excess, Calmar, exposure, Win Rate and Expected Payoff exist. Exact organizer performance PDF is absent; some formulas remain provisional. |
| QUALIFICATION | READY_WITH_WARNINGS | PASS/FAIL/UNKNOWN metrics exist for supplied criteria, but the authoritative performance document and exact criterion definitions need human confirmation. No official strategy run qualifies. |
| REPRODUCIBILITY | READY_WITH_WARNINGS | Official runs retain strategy hash, data/archive identity, runtime metadata, stdout/stderr and normalized artifacts. `reports/experiment_registry.json` imports prior A/C/D0 evidence and records this run's smoke tests; it is not a substitute for a complete per-variant registry of legacy experiments. |
| SAFETY | READY | Read-only production calls and simulator-only local runs; no real orders; no raw archive overwritten; no commit/push; official submission repository untouched. |
| SUBMISSION PORTABILITY | READY_WITH_WARNINGS | Portable value objects/state/metrics and bridge are separate from Streamlit. Final migration, exact submission interface verification and rule mapping remain for human review; official submission repository was not accessed. |

## Environment and data

- Research `.venv`: Python 3.13.0. TradeSim `.venv-kgi313`: exact Python 3.13.0; pip available in both environments.
- TradeSim 0.2.6 archive SHA-256: `38e928e62190204d4f2edde4aa8ce2d324d08e99ba6caa2ffab30b94a568389a`; 64-bit runtime and dependencies pass.
- Official history: 492 files / 603,513 rows / 747 represented dates / 48 symbols; earliest 2023-09-21, latest 2026-10-21. Official ticks: 13 files / 2,417,570 rows / 48 symbols, latest 2026-10-21. Repeated raw tick rows are retained; no deduplication was applied.
- Latest production readiness probe: authentication SUCCESS, market-data initialization SUCCESS, realtime quote failed `Login required`, candle probes returned `Service is not ready yet, Please try again later`, account reads `REQUIRES_ACCOUNT_NUMBER`. This was checked after hours and is not proof of an in-session entitlement failure.
- Latest collection health: recent BBO callback evidence; all 50 current-session candle symbols returned NO_DATA for the expected session. Do not synthesize candles. Latest production candle data found by the health audit: 2026-10-22 16:35 Asia/Bangkok (1m and 5m); 15m latest requires separate current inventory. BBO callback in the after-hours check: 2026-10-23 02:54 Asia/Bangkok; after-hours freshness is not market-session freshness.
- Historical Settrade coverage/recovery and cross-source comparison reports exist. Official-vs-Settrade OHLCV mismatch is classified as `SOURCE_SEMANTIC_DIFFERENCE` where matched timestamps differ; official adjusted-history behavior versus unknown Settrade adjustment status and different volume/session semantics prevent silent merging. Missing expected-grid gaps remain UNKNOWN where no exchange-calendar/session expectation is established.
- Production cutover marker: 2026-10-16 19:12:02 Asia/Bangkok; first successful production response exact timestamp UNKNOWN; first persisted production market observation UNKNOWN. Do not convert the cutover/session bound into an exact response time.

## Architecture and UI

- Normalized contracts: Settrade schemas/storage retain symbol, market/retrieval times, source/environment, timeframe, and validation/provenance; official ticks preserve source order and repeats with sequence/provenance; TradeSim normalized run schema carries engine/version, strategy identity, dates, orders, actual fills, partials, pending/cancellations, fees, holdings/NAV, metrics and artifacts.
- Features: leakage-aware approved daily feature engine covers causal returns/momentum, moving averages/trend, volatility and volume activity; explicit PIT membership, identity, data validity and timestamp contexts are required. Intraday features from the roadmap (ATR, activity baselines, direction efficiency and context) are not all implemented as one common rank engine.
- Ranking/market view: existing Market Overview has a filterable 50-name current-universe watchlist, daily returns/volatility/ATR/activity, stored production BBO spread and age, and selectable heatmap. It does not provide a single calibrated Opportunity Rank; no rank is inferred from stale BBO. The live-market pane is descriptive and uses the current display universe, not historical membership.
- Volatility/liquidity matrix: not implemented as a percentile quadrant matrix. Current tables expose separate metrics; a rank/quadrant would need validated synchronized inputs and thresholds.
- State/eligibility: new pure state helper returns MARKET_CLOSED, DATA_DEGRADED, QUALIFICATION_AT_RISK, SIMULATION_ONLY, POSITION_REDUCING, POSITION_OPEN or FLAT according to safety precedence. Order eligibility checks symbol, positive quantity, board lot when provided, side, cash/holdings, order type, session and freshness; unresolved board lot or organizer approval stays UNKNOWN. No submit method exists in the helper.
- Cockpit: provides status cards and embeds Market Overview; links/pages already cover Data Quality, Gap Inspector, Collection Health, Production API Status, TradeSim validation/results and research results. The underlying market/collector/TradeSim pages remain separate. No controls place/change/cancel orders.
- Local events/alerts and award target optimization are not implemented. The cockpit currently surfaces source warnings, not an event-sourced alert timeline.
- Competition state transition unit cases cover closed/stale inputs, simulation-only rule status, open/reducing position, unconfirmed order eligibility and oversell rejection.

## Competition metrics and execution

- FIFO ledger supports multiple lots per symbol, actual partial fills, sells across lots, fee allocation, cross-day lots and duplicate-event checks when event IDs are stable. Pending or canceled quantity never enters the FIFO ledger.
- Portfolio metrics include return/NAV, max drawdown, benchmark return/drawdown, excess return, Calmar, average exposure, completed roundtrips, Win Rate and Expected Payoff. Qualification returns PASS/FAIL/UNKNOWN; award metrics are descriptive only.
- The performance rules PDF named in previous docs is not present. Exact tie/zero-drawdown/breakeven/benchmark-alignment/award formulas remain RULE_CONFIRMATION_REQUIRED. The supplied competition rules and source docs differ on allowed order types: local rule allows Limit and Market-to-Limit IOC; TradeSim strategy API exposes Limit and Market and the packaged example uses Market. Simulator acceptance does not establish organizer legality.
- Market-to-Limit IOC is not supported by the inspected TradeSim strategy API. Candidate validation using a supposed MTL/IOC mode is blocked pending organizer guidance or a documented simulator adapter contract.

## TradeSim 0.2.6 validation

- `--check`: READY, `SUPPORTED_WITH_WARNINGS`, exact Python 3.13.0, imports and requirements passed.
- Official 2026-10-21 no-order run: success; 0 orders, 0 fills, ending NAV THB 10,000,000.
- Official three-date no-order run 2026-10-19, 20, 21: success; 0 orders/fills, ending NAV THB 10,000,000.
- Limit partial-fill fixture (simulator only): one 200,000-share PTT order filled through 87 actual fill rows; run succeeded, ending NAV THB 9,986,308.81. The fixture order became fully filled; this validates actual multi-fill capture and volume-capped matching, not a candidate or real fill.
- EOD residual fixture (simulator only): 100-share limit order produced zero fills and status `EOD_CANCELED`, canceled quantity 100.
- All run directories are retained under `artifacts/official_tradesim_runs/`; IDs and metadata are in each folder. Practice/official data were selected explicitly; no practice fallback occurred.
- Research-vs-official strategy divergence was not measured because smoke fixtures intentionally submit no strategy orders. Existing official-vs-Settrade market source comparisons remain diagnostic, not execution-performance comparisons.

## Research status and candidate review

- Prior Design A/C/D0 evidence remains in its original reports. D0 walk-forward documentation reports five expanding folds; D0 reduces turnover and transaction costs but fold returns are mixed and it remains loss-making. It is not a validated candidate.
- Current registry: `reports/experiment_registry.json`. It includes historical evidence references and official smoke runs. It lists H1–H5 as unrun. No new signal/parameter search was performed and no candidate was promoted through all eight stages.
- Candidate shortlist for human review: no PROMISING candidate can be responsibly nominated from the new evidence. Design A, C and D0 may be inspected as historical baselines, with D0's known mixed/loss-making result visible; none is recommended as the final strategy.
- Current daily research view is current-universe exploratory and stale at 2026-10-15; the official history extends to 2026-10-21 but has adjusted-price semantics. Do not use the comparison display as an unqualified backtest dataset.

## Operations and migration

- Before market: run `scripts/check_settrade_production_readiness.py`, `scripts/check_settrade_collector_health.py`, `scripts/audit_settrade_production_coverage.py`, `scripts/build_settrade_gap_recovery_report.py`, then `scripts/run_official_tradesim.py --check` and inspect official data dates. Confirm market-session candle freshness before relying on intraday features. Open the cockpit for read-only review.
- During market: monitor Collection Health, Data Quality, Gap Inspector and Competition Cockpit; watch BBO and candles independently. Do not interpret BBO silence as a gap or a quote as a trade. No research UI order controls exist.
- After market: audit collector health and gaps; plan bounded candle backfills and inspect conflicts before applying; never backfill BBO from candles. If new organizer ZIP arrives, hash/validate it, run `scripts/ingest_official_daily_ticks.py` (append/source-specific/refuses conflict), compare sources, then replay only explicit official dates.
- Scheduler recommendation: NOT INSTALLED; keep manual until collector health, runtime windows, and market-session candle service are stable. Do not auto-install.
- Migration checklist: select only portable Python modules; validate exact Python 3.13.0; lock supported dependencies; implement organizer-confirmed strategy interface/order validity; keep config separate; exclude Streamlit, research-only paths and credentials; run official 0.2.6 smoke on the exact strategy hash; do not access the separate submission repository until separately authorized.

## Human decisions required

1. Ask the organizer to resolve allowed order types and validity (especially Market-to-Limit IOC versus TradeSim Limit/Market semantics).
2. Supply/identify authoritative competition performance and award criteria document; confirm qualification formulas and edge cases.
3. Choose the preferred return/drawdown tradeoff before any strategy ranking is used for a final choice.
4. Human review of historical A/C/D0 evidence; no final strategy is selected here.
5. Decide whether/when to configure account number for strictly read-only account APIs; do not place orders.
6. Decide scheduler installation only after operational stability review.
7. Approve any future official submission repository migration separately.

## Validation performed

- Production readiness: `READY_WITH_WARNINGS`; authentication successful, quote/candle probes failed as described; no account number; orders placed 0.
- Collection readiness: `READY`; 50-symbol current universe; disk OK.
- Collector health: completed successfully; reported recent BBO callbacks and NO_DATA current-session candle results; no row fabrication.
- TradeSim `--check`: READY on Python 3.13.0.
- Official history/tick inventory: 492 history files/603,513 rows; 13 tick dates/2,417,570 rows; latest date 2026-10-21.
- Focused state/competition/feature/UI validation: **39 passed** across the new state tests, competition metrics/core, feature validation, market research rendering and Streamlit navigation.
- A wider focused selection reported 56 passing tests but its tmp-path cases errored because Windows denied access to existing/test-created temporary directories. A full pytest run was not completed for the same environment limitation; do not treat the earlier historical full-suite PASS in old reports as validation of this code state.
- `compileall -q src scripts ui tests`: PASS. `git diff --check`: PASS with existing LF-to-CRLF warnings only. Streamlit UI smoke through AppTest: PASS (included in the 39-test set). Manual browser inspection was not repeated.
- A dedicated secret scanner was unavailable; the new state/UI/docs/registry changes contain no credential configuration or secret values. Existing `.env` was not read or printed.

## Safety declarations

- No final strategy selected without human review.
- Official submission repository not accessed.
- Organizer raw data was not modified in place; source archives remain preserved.
- No market data fabricated and no simulator fills synthesized; the local official simulator produced all recorded smoke fills.
- No commit; no push.
- `REAL ORDERS PLACED = 0`.

# TASK — Weekend Maintenance Audit + Research Round 2

Repository root: `D:\GitHub\SET50-Algo-Trading`

Goals:
1. Audit the most recent completed Thai trading week across Settrade production data, collector telemetry, official TradeSim data, gap/backfill state, and UI/reporting.
2. Start a pre-registered Research Round 2 focused on lower-turnover, regime-conditioned mean reversion, using Round 1 only as diagnostic evidence.

Safety:
- Preserve dirty work.
- No `git reset --hard`.
- No `git clean -fd`.
- No commit or push.
- Do not access the separate official submission repository.
- No real brokerage orders.
- Do not modify organizer raw data in place.
- Do not fabricate market data.
- Do not synthesize BBO.

## 0. Read first

Read completely:
- `AGENTS.md`
- current `TASK.md`
- README
- `docs/RESEARCH_CANDIDATE_DISCOVERY_STATUS.md`
- `reports/research_candidate_summary.json`
- `reports/research_hypothesis_specs.json`
- `reports/no_lookahead_candidate_audit.json`
- `reports/experiment_registry.json`
- `docs/TRADESIM_026_READINESS.md`
- `docs/FULL_OPERATIONAL_TRADESIM_READINESS.md`
- Settrade collector/gap/recovery docs
- official TradeSim ingestion/comparison docs
- backtest/execution model docs
- Decision Support / Competition Cockpit docs
- relevant tests

Read `SKILL.md` / `skill.md` if present.

Inspect actual filesystem/repo state before relying on earlier reports.

# PART A — Determine maintenance week

Determine the latest fully completed Thai trading week represented by available data.

Do not assume every weekday is a trading day.

Report:
- week start/end
- actual trading dates
- holidays/non-trading dates
- Settrade-covered dates
- official TradeSim-covered dates
- dates with insufficient evidence

Never classify a holiday as an outage.

# PART B — Settrade weekly audit

Audit the completed week for:

### Raw BBO
Per date:
- first/last timestamp
- event count
- symbol count
- duplicates/conflicts
- longest event silence
- stale intervals
- reconnect evidence
- provenance

Remember BBO is event-driven; silence alone is not automatically a gap.

### Normalized BBO depth
Check:
- rows
- symbol coverage
- timestamp range
- duplicate keys
- malformed levels
- crossed books
- stale snapshots

Do not auto-delete suspicious records.

### 1m / 5m / 15m candles
Per date/symbol:
- first/last bar
- expected/observed timestamps where a defensible session grid exists
- missing intervals
- duplicates
- conflicting OHLCV
- malformed OHLC
- volume anomalies
- provenance

### Daily data
If present:
- freshness
- completeness
- symbols
- duplicates
- adjustment status

If absent, report it.

# PART C — Collector/connectivity audit

Review the week for:
- collector state transitions
- checkpoints
- retries
- reconnect logs
- timeout/DNS/network failures
- auth errors
- process restarts
- stale-state detection

Classify only with evidence:
- CONFIRMED_OUTAGE
- CONFIRMED_RECONNECT
- API_NO_DATA
- MARKET_CLOSED
- PROCESS_NOT_RUNNING
- DATA_STALE
- UNKNOWN

Do not infer exact outage windows from candle absence alone.

Improve telemetry safely if needed for future sessions.

# PART D — Gap audit and safe recovery

Re-run weekly gap analysis.

Classify:
- SETTRADE_ONLY_GAP
- TRADESIM_ONLY_GAP
- BOTH_SOURCES_GAP
- SOURCE_SEMANTIC_DIFFERENCE
- RECOVERABLE_FROM_SETTRADE_API
- API_NO_DATA
- UNKNOWN

For genuinely recoverable Settrade candle gaps:
- issue bounded read-only historical requests
- validate rows
- append only if conflict/provenance checks pass

Never:
- synthesize bars
- synthesize BBO
- overwrite Settrade using TradeSim data

# PART E — Official TradeSim weekly audit

Audit:
- `tradeSim_history.zip`
- `tradeSim_ticks.zip`
- extracted history/ticks
- manifests/inventories

Verify:
- hashes
- latest dates
- files
- symbols
- rows
- corruption
- malformed data
- duplicates
- out-of-order ticks
- schema drift

Compare against previous manifests.

If unchanged, explicitly say unchanged.

# PART F — Official vs Settrade weekly comparison

For overlapping dates/symbols/timeframes compare:
- timestamps
- OHLC
- volume
- first/last bars
- session boundaries
- source-only bars

Update the existing comparison report.

Possible explanations:
- aggregation boundaries
- incomplete buckets
- adjusted/unadjusted
- session semantics
- auction inclusion
- no-trade-bar policy
- source correction
- timezone
- UNKNOWN

Never force equality.

# PART G — Weekly data-quality scorecard

Create/update scorecard for:
- Settrade BBO
- Settrade 1m
- Settrade 5m
- Settrade 15m
- Settrade daily
- TradeSim ticks
- TradeSim history
- provenance
- collector telemetry
- cross-source diagnostics

Statuses:
- HEALTHY
- HEALTHY_WITH_WARNINGS
- DEGRADED
- INCOMPLETE
- UNKNOWN

# PART H — Maintenance fixes

Perform safe maintenance where justified:
- manifest refresh
- cache refresh
- safe index rebuild
- checkpoint validation
- better telemetry/logging
- temp-directory test isolation
- path normalization
- stale UI cache fixes
- stronger data-quality warnings

Do not:
- mutate organizer raw data
- delete unexplained market data
- force-dedupe official ticks without sequence/trade IDs

# PART I — Research Round 2 pre-registration

Do NOT tune MeanRev5 directly.

Round 1 showed:
- Trend20 / Breakout20 / RelativeStrength had negative gross edge.
- MeanRev5 had positive gross return but negative net after heavy turnover/costs.
- MeanRev5 is diagnostic evidence only, not a surviving candidate.

Create a NEW pre-registered hypothesis, conceptually:

`H6_REGIME_CONDITIONED_LOW_TURNOVER_MEAN_REVERSION`

Core idea:
Short pullbacks may show positive expectancy only when:
- long-term trend is not structurally weak
- pullback is meaningful but not distress
- directional efficiency is low
- broader market regime is neutral/positive
- portfolio churn is constrained
- entries are selective
- holdings persist long enough to avoid needless turnover

This is a falsifiable hypothesis, not an assumption.

# PART J — Separate signal edge from execution/portfolio edge

Before full backtesting, create signal-level diagnostics.

For every valid signal event compute forward returns:
- next open -> next close
- next open -> +2 sessions
- +3 sessions
- +5 sessions
- +10 sessions

Report:
- mean
- median
- hit rate
- sample size
- distribution
- confidence intervals where practical

Label:
`SIGNAL_DIAGNOSTIC_ONLY`

Do not present as executable PnL.

# PART K — Regime features

Use only defensible historical inputs.

Possible market features:
- SET50 trend
- medium-horizon benchmark return
- benchmark volatility
- cross-sectional median return
- dispersion
- PIT breadth only if coverage is adequate

Do not fabricate historical spread/depth/BBO.

If breadth is too incomplete, exclude it.

# PART L — Stock-level features

Potential features:
- 3/5/10-session returns
- SMA20/50/100 where available
- ATR%
- realized volatility
- directional efficiency
- distance from moving average
- drawdown from recent high
- volume ratio as ACTIVITY proxy only

Volume is not liquidity.

# PART M — Lower-turnover portfolio design

Round 2 must explicitly reduce churn.

Consider a small, pre-registered set of mechanisms:
- fewer selected names
- stricter entry threshold
- longer minimum hold
- cooldown after exit
- event-driven entry
- independent exit logic
- no sell/rebuy for unchanged holdings
- position persistence while thesis remains valid

Do not combine everything without reason.

Prefer a simple design such as top 3 or top 5 equal-weight positions.

No leverage.

# PART N — Exit design

Pre-register a small set of simple exits:
- fixed holding horizon
- recovery toward moving average
- thesis invalidation
- maximum holding horizon

Do not grid-search many exits.

# PART O — Cost decomposition

Keep `RESEARCH_EXECUTION_V1` as the baseline for comparability.

Always report separately:
1. signal diagnostic
2. portfolio gross return
3. commission
4. VAT
5. modeled slippage
6. final net return

Do not weaken the cost model merely to create a winner.

Optional sensitivity tests may include:
- baseline V1
- zero extra slippage diagnostic
- defensible half-tick-style diagnostic
- worse-cost case

Clearly label sensitivity runs.

# PART P — Research period discipline

Do not silently retune the same 2023–2026 history.

Document which periods are already seen.

Prefer:
- pre-register Round 2 now
- use expanding/rolling chronological folds
- preserve the latest meaningful period from repeated tuning as much as practical

Do not call repeatedly inspected history untouched.

# PART Q — Stage 0 signal gate

Before portfolio construction, test signal expectancy.

Reject as:
`REJECTED_SIGNAL_DIAGNOSTIC`

if:
- sample too small
- expectancy clearly negative
- all horizons negative
- result depends on one symbol/event

# PART R — Stage 1 portfolio backtest

Only if signal diagnostic is not clearly poor.

Record:
- gross
- net
- max DD
- turnover
- exposure
- fills
- non-fills
- FIFO roundtrips
- win rate
- expected payoff
- average hold
- symbol contribution
- temporal contribution

Compare directly to Round 1 MeanRev5.

Central question:
`Did turnover fall materially without destroying gross expectancy?`

# PART S — Walk-forward

If Stage 1 passes:
- run chronological expanding/rolling folds
- no random splits
- report each OOS fold
- return
- DD
- turnover
- exposure
- trades
- win rate
- expected payoff
- positive-fold count
- median/worst fold

Do not promote on one good fold.

# PART T — Robustness

If walk-forward is not clearly poor, test only nearby pre-registered alternatives:
- pullback threshold
- holding horizon
- position count
- regime threshold
- cost severity

No broad grid search.

Track every variant.

# PART U — Mandatory regime analysis

Break Round 2 results down by defensible regimes such as:
- benchmark above/below SMA
- positive/negative medium-term benchmark return
- high/low benchmark volatility
- high/low dispersion

Report:
- sample count
- gross/net
- hit rate
- DD
- turnover

Determine whether any apparent edge is genuinely regime-specific.

# PART V — Concentration audits

Symbol:
- top positive/negative contributors
- PnL share top 1 / top 3
- profitable vs losing symbols

Temporal:
- year
- half-year
- quarter if meaningful

Flag concentrated results.

# PART W — Multiple-testing control

Update experiment registry with:
- Round 1
- Round 2 signal diagnostics
- portfolio variants
- robustness variants

Preserve failures.

Add multiplicity warning.

# PART X — Promotion gate

Promote only if evidence supports:
- positive net evidence
- materially lower turnover than MeanRev5
- reasonable DD
- signal diagnostic not clearly negative
- OOS consistency
- nearby robustness
- adequate sample
- no severe symbol/date concentration
- no lookahead

Otherwise report:
`NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE`

Do not force a shortlist.

# PART Y — Official TradeSim 0.2.6 validation

Only for promoted candidates.

Use:
- exact Python 3.13.0
- TradeSim 0.2.6
- official ticks
- explicit date/source
- portable strategy module

Run:
- one-day smoke
- multi-day replay
- full available official period if practical

Analyze:
- intended orders
- fills
- partial fills
- non-fills
- EOD cancellations
- fill ratio
- fees
- NAV
- holdings
- roundtrips

If order legality remains unclear:
`BLOCKED_BY_ORDER_RULE_CLARIFICATION`

Do not guess.

# PART Z — UI

Update read-only Competition Cockpit with:

### Weekend Maintenance
- audited week
- coverage
- collector status
- gap summary
- official freshness
- cross-source warnings

### Research Round 2
- pre-registered hypothesis
- signal diagnostic
- turnover comparison
- stage status
- walk-forward
- robustness
- evidence classification

No trading controls.

# REPORTS

Create/update:
- `docs/WEEKEND_MAINTENANCE_2026-10-24.md` (or actual run date)
- `docs/RESEARCH_ROUND2_LOW_TURNOVER_MEAN_REVERSION.md`
- `reports/weekend_data_maintenance.json`
- `reports/research_round2_summary.json`
- `reports/experiment_registry.json`

# TESTS

Add/update tests for:

Maintenance:
- weekly date detection
- holiday handling
- gap classification
- safe bounded backfill
- no BBO synthesis
- official archive immutability
- manifest delta

Round 2:
- causal signals
- forward-return alignment
- no same-bar execution
- regime causality
- position persistence
- min-hold/cooldown if used
- cost decomposition
- registry
- promotion gate

UI:
- maintenance panel
- Round 2 panel

# FINAL VALIDATION

Run:
1. TradeSim `--check`
2. Settrade production readiness
3. collector health
4. weekly Settrade audit
5. official data audit
6. cross-source comparison
7. gap audit
8. safe bounded backfill where justified
9. focused maintenance tests
10. focused Round 2 tests
11. no-lookahead audit
12. full pytest
13. compileall
14. Streamlit AppTest
15. manual UI inspection if available
16. `git diff --check`
17. `git status`
18. secret scan if available

If Windows temp permissions recur, use the known safe/elevated/project-local approach.

# HUMAN DECISIONS

Do not interrupt the run for decisions that can wait.

At the end collect only genuine blockers under:
`HUMAN_DECISIONS_REQUIRED`

Examples:
- organizer order-type clarification
- qualification/award authority
- execution-model approval
- scheduler decision
- account-number read-only configuration
- candidate promotion decision

# FINAL REPORT

Report at minimum:

Maintenance:
- audited week/trading dates
- Settrade BBO/1m/5m/15m/daily coverage
- collector incidents/reconnects
- gap counts/classes
- safe backfills
- official tick/history latest dates
- archive changes
- cross-source comparison
- data-quality scorecard
- maintenance fixes
- next-session checklist

Round 2:
- pre-registered hypothesis
- signal diagnostic
- sample sizes
- forward-return results
- regime definitions
- candidate definition
- turnover
- gross
- fees
- slippage
- net
- DD
- exposure
- roundtrips
- holding time
- Round1 vs Round2 comparison
- walk-forward
- robustness
- cost sensitivity
- regime performance
- concentration
- evidence classification
- promotion result
- TradeSim validation if promoted

Validation:
- focused tests
- full pytest
- compileall
- Streamlit
- git diff --check
- git status
- secret scan

End with:
- `CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW`
- `HUMAN_DECISIONS_REQUIRED`
- recommended next task

Explicitly confirm:
- no final strategy selected
- official submission repo not accessed
- organizer raw data unchanged
- no market data fabricated
- no commit
- no push
- `REAL ORDERS PLACED = 0`

Complete all safe work autonomously.

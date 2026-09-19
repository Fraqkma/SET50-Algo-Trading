# Settrade phase final report

## A. Collector hardening

- Current universe: 50 unique H2 2026 symbols, validated from `reports/current_set50_universe.csv`.
- Modes: `candles`, `realtime` quotes, `bid-offer` preparation, and safe `combined` mode.
- Market-data limiter: 3 requests/second; retries remain bounded at 2.
- Realtime ceiling: 40 official topics; internal BBO rotation ceiling: 35.
- Rotation: deterministic 35/15 groups, 5-minute configurable interval, session/generation metadata, strategy-neutral.
- Checkpoints: global plus per-symbol candle checkpoints; append-safe normalized CSV writes detect duplicates and conflicts without deleting rows.
- Disk guard: warning at 10 GB and critical stop at 5 GB; current readiness check is OK.
- Session labels: Asia/Bangkok metadata for pre-open, morning, midday break, afternoon, auction, and closed states.
- Readiness: `READY`; authentication succeeded; orders placed: 0.

## B. Bar data

The 50-symbol probe returned 50/50 for quote, daily, 1m, direct 5m, and direct 15m access. The collector produced 3,527 1m rows, 1,478 derived 5m rows, and 1,320 derived 15m rows with zero validation issues. A bounded direct-vs-derived sample across five symbols is recorded in `reports/settrade_direct_derived_comparison.csv`; it is pending exact exchange-session bucket alignment and is not promoted as an empirical equality claim.

## C. Volume/value semantics

The five-session, 50-symbol comparison produced 245 overlapping observations. Ratios were approximately 1.0000–1.0050, but endpoint/adjustment semantics and authoritative field definitions remain unproven. Classification remains `UNRESOLVED`. Settrade volume/value are not safe for existing research features or synthetic turnover conversion.

## D. Order book

Observed bid/offer events contain ten bid and ten ask levels with price and volume fields. Long-form normalization and diagnostic quality metrics are implemented. Spread, midpoint, depth totals, imbalance, crossed-book, nonnegative-value, and ordering checks are available. The observed sample had valid non-crossed books, while ask ordering was not consistently ascending; it is recorded as a quality flag, not silently rejected.

## E. BBO event rate and storage

BBO event rate was not measured this run because the bounded probe did not establish an open-session continuous rate. Existing estimates cover 20 and 50 symbols, 1/3/6/12 months, 1m, derived 5m/15m, raw BBO, and normalized BBO under LOW/BASE/HIGH scenarios. They are explicitly marked `ESTIMATED`.

## F–H. Execution research and IOC status

`src/research/execution/` implements diagnostic calculations for one-tick cost, quoted spread, midpoint, depth totals, depth-weighted book-sweep VWAP, IOC fill plausibility, and daily-vs-book outcome labels. It does not modify the production backtester. Queue priority, hidden liquidity, latency, cancellations, timestamp mismatch, and auction matching remain unknowable from snapshots.

`MODEL_V1` remains unchanged: one adverse tick, LIMIT/IOC constraints, daily bar fill logic, fees, VAT, and cash checks. No evidence justifies replacing it.

## I. Shadow / dry-run trading

`DryRunExecutor` records validated intentions only. The Settrade adapter raises if order placement is attempted. No account object was initialized, no account number was required, and real orders placed were exactly 0.

## J. Historical research

Recent Settrade daily history is useful. PTT probes observed data through late 2023, but pre-2023 long-history replacement for Yahoo is unsupported. Historical Settrade membership/security-master/corporate-action APIs remain unavailable in the inspected SDK surface. Yahoo staging and membership-aware research remain relevant; pre-2023 survivorship-safe expansion remains blocked without legitimate membership data.

## K. Exact commands

```powershell
.venv\Scripts\python.exe scripts/check_settrade_collection_readiness.py
.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode candles --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode candles
.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode bid-offer --once
.venv\Scripts\python.exe scripts/run_settrade_collector.py --universe current_set50 --mode combined --once
.venv\Scripts\python.exe scripts/check_settrade_collector_health.py
```

Foreground collection is stopped with Ctrl+C; no service or orphan process is created by this task.

## L. Verification

Final full pytest: 121 passed, 1 skipped, 1 cache warning. Compilation, JSON/CSV validation, `git diff --check`, and secret scanning also completed.

## M. File and safety summary

New pilot/diagnostic files are confined to `src/data/settrade`, `src/research/execution`, `scripts`, `tests`, `reports`, `docs`, and `data/pilot/settrade`. Approved production data, strategy rules, and `.env` are not modified. Credentials exposed: no. Real orders: 0.

## FINAL HUMAN DECISIONS

### Decision 1 — continuous collection

- A: start next market session; uses the tested collector, but accepts storage/licensing responsibility.
- B: remain pilot-only; safest default while retention/licensing is unresolved.

### Decision 2 — BBO retention

- A: 3 months; lower storage and research coverage.
- B: 6 months; balanced longitudinal evidence.
- C: 12 months or indefinite; strongest evidence but highest storage/licensing burden.

### Decision 3 — BBO coverage

- A: neutral 35/15 rotation across all 50.
- B: selected continuous subset plus rotating remainder.
- C: defined research windows only.

The implementation supports A without using strategy signals.

### Decision 4 — volume use

Keep Settrade volume/value excluded until semantics are confirmed. The comparison is close to 1 but not sufficient proof of identity or unit semantics.

### Decision 5 — execution research priority

- A: collect more BBO first and validate one-tick assumptions.
- B: begin unrelated alpha research.
- C: run both in strictly separated tracks.

The current D0 evidence supports prioritizing execution research, but this is a human choice.

### Decision 6 — production execution model

Do not change `MODEL_V1` tonight. Require multi-session, multi-symbol BBO evidence, stable spread/depth distributions, and IOC diagnostics before reconsideration.

### Decision 7 — historical membership

- A: request official historical membership/reference data.
- B: continue the current approved 2023–2026 scope.
- C: research another legitimate licensed source.

### Decision 8 — sandbox account integration

- A: continue zero-order shadow mode only.
- B: later integrate an explicitly safe sandbox account after separate approval.

No option authorizes real-money trading.

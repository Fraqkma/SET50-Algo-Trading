# Phase 3 Final-Direction Addendum: Pre-Registration

**Frozen:** 2026-10-30 16:42 UTC / 23:42 Asia/Bangkok, before the additional Phase 3 signal run, timeline diagnostics, bootstrap outputs, and official-tick fixture in this task. The original `RESEARCH_PHASE3_PRE_REGISTRATION.md` remains unchanged and governs the first Phase 3 screen. This addendum governs the new work below.

## Prior exposure and limits

- HEAD at freeze: `0eb89f3272e1ab17cb4f9fa1a76316ebebb0b76a`, branch `main`.
- Baseline worktree already had 2,169 porcelain entries (SHA-256 of NUL-delimited status: `ccf8ecb5ea3aafc46c21ea96ce8e6ab3558cd28e90d2a2cbaa78fd26b2b2b799`). These include earlier unrelated dirty work and ACL-restricted pytest artifacts; preserve all of it.
- Trend20, Breakout20, RelativeStrength, MeanRev5, H6, and the first S3-A/C/D event screen have been inspected. Daily stock history through 2026-09-04 is **seen data**, not an untouched holdout. Any new estimates on it are retrospective diagnostics even when split chronologically.
- Preliminary benchmark file inventory and a descriptive rolling-window calculation were performed while locating/validating the official archive, before this addendum was frozen. Consequently, the benchmark-envelope calculation below is exploratory and reproducibility work, not a confirmatory test. No signal outcomes for the newly implementable S3-B or new horizon-two endpoint were calculated before this freeze.

## Frozen sources and universe

- Stock bars: `load_approved_market_data` plus `MarketDataEligibilityGate`; only dates eligible for the symbol's explicit PIT membership and approved raw data are included. Existing approved manifest: partial panel, 20 records, 18 core series through 2026-09-04; no current-membership backfill or Settrade current-universe data.
- SET50 benchmark: `data/official/tradesim/history/benchmark/SET50.csv`, source member `marketInfo/benchmark/SET50.csv` inside the organizer-provided `Daily_Ticks.zip` / nested `tradeSim_history.zip`. Archive SHA-256 `7c505a024bf75d2beba09d4edae3544b71ccbece76154085830ee9d4a5ce588d`; benchmark member SHA-256 `cb302826aba0762dd111108c348f1fcab612a9971c4a1af71f62c79f35572267`. It contains daily `Date,Close`, 747 unique positive observations from 2023-09-21 through 2026-10-21. The local 0.2.7 `marketInfo/benchmark/SET50.csv` is only 16 practice dates and is not used for long-window estimates.
- The official historical benchmark archive is the best sourced available historical price-index series; the exact separate scoring feed and correction policy for the future competition remain unconfirmed. Its roughly 3.1 years of history are limited for regime-tail inference.
- Competition session count is fixed to the verified 21 expected SET sessions from `reports/competition_calendar.json`. Refresh the calendar if SET changes it before competition.

## Signal run: unchanged hypotheses, explicit outcomes

The four event definitions are inherited unchanged from the original pre-registration: S3-A volatility contraction + 20-observation breakout + 1.5x prior-20 volume; S3-B top-quintile positive 20-session stock leadership conditioned on official SET50 close above SMA50 and nonnegative 20-session return, requiring at least 10 simultaneously eligible stocks; S3-C next-session raw open gap of at least 1% versus prior raw close, direction-classified at the opening print; and S3-D at least 2x prior-20 volume plus adjusted close-to-close return above 0.5%. No thresholds or economic families may be revised.

- Decisions for A/B/D use completed session-close rows; source files are daily bars and carry date, not a defensible wall-clock close timestamp. Event log must record `SESSION_CLOSE_DATE_ONLY`. C becomes observable only after the opening print; record its date and `OPEN_PRINT_TIME_UNAVAILABLE`, and never assume an executable fill at the open.
- A/B/D diagnostic holding returns: adjusted next-session open to adjusted close after 1, 2, 3, or 5 observed sessions. The primary endpoint remains 5 sessions to retain the original preregistration; 1/2/3 are secondary diagnostics. No missing endpoints are filled.
- C diagnostic: direction-aligned adjusted close-to-close return from the gap-session close through 1/2/3/5 subsequent eligible session closes. This avoids pretending to enter at the opening gap price.
- Benchmark-relative outcomes: official benchmark close-to-close return aligned to the same signal/end dates; report separately from open-referenced stock returns. Benchmark values remain UNKNOWN where dates do not align.
- Primary controls: A/B/D same-signal-date PIT-eligible non-event names. For C, primary control is same-symbol non-gap observations in the same calendar year where available; same-date non-gap cross-sectional controls are a separate diagnostic. Controls are observational, not randomized.
- Required chronological slices: 2023-09-21–2024-12-31, 2025-01-01–2025-12-31, and 2026-01-01–2026-09-04, clipped to available PIT rows. These are descriptive stability checks on seen data, not true OOS validation.
- Minimum evidence: at least 30 matched events, 10 symbols, and 20 dates. Report raw and matched counts, Kish effective date/symbol clusters, overlap, and event concentration. Do not treat event count as independent sample size.
- Uncertainty: 10,000 two-way date/symbol pigeonhole bootstrap replications, fixed seed `20261030`, 95% percentile intervals. Holm correction covers the four calculable primary 5-session matched-control mean effects. If samples are too sparse, report unavailable and fail/postpone.
- Benchmark cost sensitivity only: one 0.16799% commission+VAT side and a one-tick adverse move on each side are illustrative sensitivities; not actual executable PnL, no tick-volume cap is inferred from daily bars.
- Stage G0: approved PIT row, valid source timestamp semantics, no lookahead, and complete future endpoint. G1: adequate matched sample and positive primary uplift with Holm-adjusted clustered uncertainty excluding zero. G2: frozen chronological consistency without reselecting. G3: plausible cost/turnover-adjusted edge and supported liquidity. G4: only G3 survivors receive a portfolio prototype and TradeSim replay. Otherwise stop with `NO_SIGNAL_PASSED_PROMOTION_GATE`.

## Benchmark-risk envelope calculation

- Unit: each rolling window consists of exactly 21 consecutive observations in the official benchmark file, corresponding to the current competition calendar count.
- MDD: over those 21 daily closes, `max(0, 1 - min(close_t / running_max(close_0..close_t)))`, with the first window close as the baseline.
- Window-level prior regime: `BEAR` if the prior 63 close-to-close-session return, ending strictly before the window start, is negative; otherwise `NONNEGATIVE`. Windows without 63 prior observations are `UNKNOWN`. No future return enters the regime.
- Show minimum, 5th/25th/50th/75th/90th/95th/maximum MDD quantiles, representative window dates, corresponding strict 1.5x benchmark threshold, and the remaining margin after a provisional buffer equal to 50% of that threshold. Report bear/nonnegative sensitivity.
- That 50% buffer (portfolio research reference = 0.75x historical benchmark MDD quantile) is a conservative reversible research convention, not the user's accepted maximum drawdown and not an official competition forecast. No candidate's projected DD is available because G1 has not passed.
- If provenance, positivity, uniqueness, or source identity checks fail, emit `RISK_BUDGET_PENDING_BENCHMARK_EVIDENCE`; do not substitute a stock basket.

## Portfolio-count, execution, and competition gates

- Do not build a strategy portfolio unless G4 is reached. Thus 3/5/8 concurrent-position comparison, board-lot fills, actual exposure, and strategy projected DD are `NOT_RUN_AFTER_G1_REJECTION` if no signal passes. Do not infer the right N from the prior MeanRev5/H6 runs.
- Independently preserve V1 and compute a fixed-fill arithmetic frontier for MeanRev5/H6: V1, 0.2.7-informed daily-bar equivalence (no inferred fill quantity), zero-slippage add-back (fixed historical fills and quantities, fee treatment explicit, not a portfolio forecast), and stress (1.5x fees plus a second adverse tick, fixed historical fills). Report actual intended/filled/non-fill counts, fees/VAT, slippage, turnover, DD, exposure, FIFO round-trips. All counterfactuals must be labeled path-dependent and non-official.
- Run at most one one-day local TradeSim 0.2.7 mechanics fixture using a real bundled official tick date; it must place at most one local simulator order. This is not candidate validation or a global fill-rate sample. No real broker actions.

## Provenance and stop rules

Write the exact SHA-256 of this document and the machine hypothesis configuration into the final summary/registry, with UTC run timestamps, source hashes, Git HEAD, dirty baseline fingerprint, Python 3.13.0 and engine versions. Preserve all previous artifacts. No parameter sweep, outcome-driven threshold change, final-strategy selection, or return-target optimization. The 6–7% anecdote is aspirational only.

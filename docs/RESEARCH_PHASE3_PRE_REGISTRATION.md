# Phase 3 Signal Discovery Pre-Registration

**Frozen before Phase 3 event outcomes were calculated.**

## Run identity and research scope

- Repository HEAD at registration: `0eb89f3272e1ab17cb4f9fa1a76316ebebb0b76a`.
- Worktree was already dirty, including earlier research, data-recovery, TradeSim 0.2.7, and competition-date work. Those changes are preserved.
- Scope: four fixed signal-first event hypotheses, one fixed definition each; descriptive evidence only. No portfolio construction is authorized unless a signal passes the gates below.
- Source policy: only `load_approved_market_data` rows admitted by `MarketDataEligibilityGate` and the historical SET50 constituent table. No current-membership backfill, no non-approved Settrade/current-constituent series, no raw-file edits.
- Data dates through 2026-09-04 were already repeatedly used in prior candidate research (Round 1, Round 2, and execution sensitivity). They are **reused, inspected history**, not an unseen test set. Later October market-data dates were inspected for collection/data quality and likewise are not called untouched. This run cannot establish independent OOS confirmation.
- The source approval manifest currently caps eligible daily research data at 2026-09-04 and provides a partial universe, not all 50 constituents. This window is exploratory and subject to Stage A adequacy.

## Timestamp and outcome conventions

- Signal information is formed only from a completed daily row at close `t`; all rolling inputs use observations at or before `t`.
- The earliest hypothetical decision is after close `t`; earliest assumed entry reference is the next eligible observed session's open. This is a signal diagnostic, not an executable fill or TradeSim result.
- Primary outcome: close-to-close absolute return from the next observed session's close through the close five eligible observed sessions after that entry reference. Diagnostic horizons: 1 and 3 observed sessions, measured on the same entry-close basis. Missing endpoints are censored, never forward-filled.
- Benchmark-relative outcome: same-period SET50 price-index return subtracted only where an official, date-aligned benchmark series exists. Otherwise `UNKNOWN`; no proxy is silently substituted.
- Signals require PIT eligibility on signal date. For next-open outcome eligibility, the security must remain an eligible observed series; corporate-action/entity boundaries invalidate the event.
- Controls: within the same signal date (same market context) and approved symbol panel, non-event observations matched to the event's symbol when available; otherwise same-date eligible non-event symbol observations. Report both definitions separately where data permits. This controls date/context and symbol, but is not causal randomization.

## Frozen hypotheses

| ID | Single event definition at close `t` | Mechanism and control | Falsification |
|---|---|---|---|
| S3-A | For each symbol, prior 10-session mean true range divided by close is at least 20% below its preceding 20-session mean; today's close exceeds the maximum high of the prior 20 observations; today's volume is at least 1.5 times the mean volume of the prior 20 observations. | Volatility contraction followed by independently observed activity-confirmed expansion. Same-date/symbol-panel non-event control. | Fail if source/timestamps invalid, adequate event count unavailable, 5-session median uplift versus control is not positive, or clustered interval does not exclude zero. This is not the rejected plain Breakout20 because it requires contraction and stronger relative activity. |
| S3-B | At close `t`, among dates with at least 10 simultaneously approved SET50 symbols, rank adjusted-close 20-session returns; event is top quintile and positive return, only when official SET50 price index is above its trailing 50-session simple average and its 20-session return is nonnegative. | Leadership may add excess return in a separately determined positive benchmark regime. Same-date eligible non-event symbols are the control. | Fail/postpone if official benchmark history or cross-section is inadequate; fail if 5-session median excess uplift is not positive or clustered interval does not exclude zero. No replacement with an unapproved proxy. |
| S3-C | At close `t`, next observed session open differs from prior close by at least +1.0% or at most -1.0%; classify direction at that next open and measure subsequent close returns. | Tests continuation versus reversal after a measurable gap with only pre-gap information used for classification. Control: same-symbol non-gap next sessions, same calendar date where possible. | Fail if open semantics/adjustments cannot be validated, or if 5-session direction-aligned return uplift is not positive with adequate clustered uncertainty. No claim that an open-price fill was executable. |
| S3-D | At close `t`, volume is at least 2.0 times the mean of the prior 20 sessions and close-to-close return is positive and exceeds +0.5%. | Unusual reported activity with directional price confirmation. Same-date/symbol-panel non-event control; volume is activity, never liquidity. | Fail if volume baseline/source is invalid, adequate events unavailable, or 5-session median uplift is not positive with clustered interval excluding zero. |

All thresholds, windows, directions, and horizons above are frozen. No alternate thresholds, grid search, or replacement family will be tested in this pass.

## Adequacy, uncertainty, multiplicity, and gates

- Minimum adequacy per hypothesis: at least 30 events, 10 unique symbols, and 20 unique event dates; additionally report effective date-symbol cluster counts and event overlap. Failing any criterion means `POSTPONED_INADEQUATE_SAMPLE`, not a negative economic finding.
- Report counts, unique symbols/dates, repeated-symbol and repeated-date concentration, overlapping outcome windows, means, medians, hit rates, quantiles, and event-minus-control effects.
- Uncertainty: two-way date/symbol pigeonhole bootstrap with fixed seed `20261030`, 10,000 replications; resample event-date and symbol clusters and use their product weights. If an estimate cannot be calculated reliably due to sparse clusters, report unavailable. Use two-sided 95% percentile intervals.
- Primary familywise multiplicity: Holm adjustment across the four 5-session event-minus-control mean effects. Other horizons and subgroup summaries are diagnostic only.
- Stage A: approved source, chronology, PIT, no lookahead, and valid forward endpoint. Hard fail on violation.
- Stage B: minimum sample, positive primary uplift versus control, and Holm-adjusted evidence inconsistent with zero. Event positivity alone is insufficient.
- Stage C: only if B passes, one predeclared perturbation-free subperiod/regime stability description; no winner reselection.
- Stage D: only if C passes, compare edge with explicit transaction-cost sensitivity; daily data cannot establish queue, spread, depth, or fill probability.
- Stage E: only after D passes, consider a simple long-only portfolio and authentic TradeSim 0.2.7 validation. Otherwise stop before portfolio construction and emit `NO_SIGNAL_PASSED_PROMOTION_GATE`.

## Competition feasibility is not an optimization target

For any Stage D passer only, report descriptive exposure, completed FIFO round trips, drawdown, and payoff against confirmed rules: max DD strictly below 1.5 times benchmark max DD, at least five completed FIFO round trips, average EOD exposure at least 50%, and expected payoff after fees above zero. Best Alpha additionally requires nonnegative portfolio return and excess return. Competition dates are 2026-12-16 through 2027-01-15 Asia/Bangkok. Future official benchmark observations and unresolved organizer boundary rules remain `UNKNOWN`. No artificial churn or strategy selection based on these metrics.

## Independent execution-sensitivity track

Preserve `RESEARCH_EXECUTION_V1` unchanged. Compare only already-rejected MeanRev5 and H6 under the V1 baseline, a conservative 0.2.7-informed sensitivity that does not infer unavailable fills from daily bars, an explicitly idealized upper bound, and a stress-cost case. Run bounded local-only authentic TradeSim 0.2.7 fixtures using actual official tick data where available. Do not infer a global fill probability from fixtures. Daily OHLCV does not reveal exact tick match volume, spread/depth, queue state, or same-tick IOC fill timing.

## Provenance and decision rule

Record source hashes, code hashes, configuration, run time, actual Git HEAD, and pre-existing dirty status with outputs. Preserve every rejection. If none passes Stage B-D, report `NO_SIGNAL_PASSED_PROMOTION_GATE`, do not construct a portfolio, and list only genuinely unresolved user/organizer decisions in `HUMAN_DECISIONS_REQUIRED` / `docs/QUESTIONS_FOR_ORGANIZER.md`.

# Phase 3 Research Decision Report

## Decision

`NO_SIGNAL_PASSED_PROMOTION_GATE`. No candidate is recommended as a competition strategy, and portfolio construction stopped at the pre-registered gate. All actions were research-only.

## What was tested

Four one-definition hypotheses were frozen before the Phase 3 signal run: S3-A volatility contraction plus breakout and 1.5x prior-volume confirmation; S3-B top-quintile positive 20-session leadership in a positive official SET50-index regime; S3-C a next-session raw opening gap of at least 1%; and S3-D at least 2x prior-20-session volume with positive return above 0.5%. The primary horizon was five observed sessions, with one- and three-session diagnostics. Full definitions, timing, controls, gates, and resampling method are in `RESEARCH_PHASE3_PRE_REGISTRATION.md`.

S3-A produced 45 events across 17 symbols and 37 dates, with +0.913% mean uplift versus same-date controls and a two-way clustered interval of −1.150% to +3.597%. S3-C produced 2,269 raw gaps (2,161 matched) across 18 symbols and 681 dates; direction-aligned uplift was +0.017%, interval −0.385% to +0.447%. S3-D produced 485 events across 18 symbols and 316 dates; uplift was +0.160%, interval −0.494% to +0.879%. Every interval crosses zero; Holm adjusted bootstrap p-values are 1.000. Kish effective symbol-cluster counts are only about 13-16; S3-C has 1,552 adjacent same-symbol events within the seven-calendar-day overlap proxy. S3-B is postponed because the official index input is missing. These are re-analyses of previously inspected daily history, not out-of-sample confirmation. Overlapping event horizons and a partial universe further reduce independent information.

## Data and competition constraints

The approved market-data manifest covers a partial PIT universe from 2023-01-03 through 2026-09-04. Historical SET50 membership is used only through the project gate; current constituents are not retroactively substituted. The official KGI PDF exists at repository root (5,014,707 bytes), but this runtime has no installed PDF text/render tools or Python PDF extractor, so its text could not be independently re-read in this resumed environment. The task's supplied scorecard and existing project documentation were used: Max DD strictly below 1.5x benchmark DD; at least five completed FIFO round trips; average EOD exposure at least 50%; expected payoff after fees above zero; Best Alpha additionally requires nonnegative portfolio and excess return. Competition dates are 2026-12-16 through 2027-01-15, inclusive, Asia/Bangkok. Future official benchmark values, exact benchmark source/revisions, portfolio valuation cutoffs, and boundary-lot treatment remain `UNKNOWN` and are listed in `QUESTIONS_FOR_ORGANIZER.md`.

No new portfolio results exist for S3-A/C/D because they failed Stage B; S3-B has no test. Historical rejected MeanRev5 and H6 also fail key descriptive criteria: net returns −4.37% and −3.49%, average exposure 26.31% and 21.94%, respectively. H6 has only 23 round trips; MeanRev5 has 109, but its drawdown is 39.33% and after-fee payoff is negative. Benchmark drawdown comparison remains unknown. No candidate satisfies the Common Criteria based on current evidence.

## Execution sensitivity

V1 remains unchanged. Existing local TradeSim 0.2.7 fixtures validated mechanics in 13 cases/22 checks; they are not a fill-rate calibration. Official tick files exist for 2026-09-09 through 2026-09-30, but the approved PIT daily panel ends on 2026-09-04, so there is no valid MeanRev5/H6 signal state to replay on those ticks. Prior official-data no-order runs validate runtime wiring only. Daily bars do not reveal exact price-time volume, queue, spread/depth, or same-tick IOC execution. No statistically defensible conservative fill estimate is possible from the available daily sample. The idealized pre-cost paths do not establish alpha; the stress case cannot make a negative after-cost result qualify. Full discussion is in `EXECUTION_SENSITIVITY_027_FOLLOWUP.md`.

## Stage outcome

- Stage A: approved PIT chronology used; S3-B postponed for source adequacy. Gap study remains descriptive and cannot assert executable auction fills.
- Stage B: none passed matched-control/clustered-uncertainty criteria.
- Stages C-D: not run after Stage B rejection.
- Stage E: no portfolio construction or candidate TradeSim run.

All failed and prior experiments remain registered; no existing evidence was deleted or rewritten. Phase 3 events, controls, source hashes, and summary are machine-readable under `reports/phase3_signal_*`. Tests and final workspace integrity results are recorded in the task completion message.

## `CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW`

Empty.

## `HUMAN_DECISIONS_REQUIRED`

No strategy-selection decision is ready because no signal passed. Three genuine organizer decisions remain documented in `QUESTIONS_FOR_ORGANIZER.md`: boundary lots/round trips, exact scoring benchmark series and revision policy, and opening/ending NAV valuation cutoffs. A future prospective research round will need the user's explicit risk tradeoff after fresh evidence exists; no choice is requested now.

## Final-direction addendum (2026-10-30)

The five locked research requirements are implemented: balanced risk-adjusted net returns; drawdown scenarios derived from SET50 benchmark history; 1–5 session diagnostics; 3/5/8 concurrent positions studied only after promotion; and 6–7% treated as aspirational only. The competition period remains 2026-12-16 through 2027-01-15, with 21 expected sessions in the current calendar artifact.

The benchmark file `data/official/tradesim/history/benchmark/SET50.csv` contains 747 observations (2023-09-21 to 2026-10-21; SHA-256 `cb302826aba0762dd111108c348f1fcab612a9971c4a1af71f62c79f35572267`). Across 727 overlapping rolling 21-close windows, MDD quantiles were: minimum 1.055%, P5 1.319%, P10 1.541%, P25 2.173%, median 3.193%, P75 4.911%, P90 7.892%, P95 10.043%, maximum 12.685%. The corresponding strict 1.5x thresholds are 1.583%, 1.978%, 2.312%, 3.260%, 4.789%, 7.367%, 11.837%, 15.064%, and 19.027%; the provisional buffer is half the threshold (0.75x historical MDD), not a user-approved cap or future forecast. The pre-freeze exploratory calculation is disclosed in the machine report. Short history and overlapping windows limit tail confidence; exact official scoring feed/revision policy remains unresolved.

Final signal results are in `RESEARCH_PHASE3_SIGNAL_EVIDENCE.md` and `reports/research_phase3_summary.json`. All four hypotheses fail G1 after clustered uncertainty and Holm correction. The 3/5/8 position study and any strategy-specific official TradeSim replay are `NOT_RUN_AFTER_G1_REJECTION`; see `RESEARCH_PHASE3_PORTFOLIO_FEASIBILITY.md`. The independent execution track preserves V1 and prior MeanRev5/H6 evidence; 0.2.7 mechanics fixtures are not fill-rate estimates and daily-bar inputs do not support authentic historical fills. No candidate shortlist is promoted.

The preceding October 29 collector/date audit is reconciled: `reports/oct29_collection_audit.json` classifies it `PARTIAL_COLLECTION`; later recovery found 50/50 daily historical-recovery observations, while the exact historical Task Scheduler invocation remains unverified. Competition dates are already propagated to canonical config and the calendar. No collector/config changes were made during this research addendum.

The official KGI performance PDF could not be independently extracted in this environment; no claim is made that it was read here. The supplied task scorecard and existing project scorecard interpretation were used, while organizer boundary/benchmark/NAV questions remain in `QUESTIONS_FOR_ORGANIZER.md`. No final strategy is selected.

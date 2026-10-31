# Phase 3 Signal Evidence

## Scope and provenance

This report records the fixed first-pass event screen registered in `RESEARCH_PHASE3_PRE_REGISTRATION.md`. The run used only the explicitly approved raw daily CSVs and the date-aware PIT eligibility gate. The panel spans 2023-01-03 through 2026-09-04 and contains 18 approved symbols with sufficient lookback. It is a partial SET50 panel, not all 50 constituents.

All of this price history had already been inspected in prior research. It is reused exploratory evidence, not an unseen holdout. October Settrade collection was also inspected for data-quality work, so October observations are not described as untouched. The official SET50 Price Index daily series is absent from the approved research inputs; S3-B is therefore postponed. No index proxy was substituted.

The event file and control file are `reports/phase3_signal_events.jsonl` and `reports/phase3_signal_controls.jsonl`; the reproducible summary with source/code SHA-256 values is `reports/phase3_signal_screen_summary.json`. `scripts/run_phase3_signal_screen.py` implements the frozen definitions. The signal screen is `RESEARCH_DIAGNOSTIC`; it does not simulate portfolio positions or fills.

## Results

Forward outcomes use adjusted OHLC consistently for hypothetical return measurement. For A/D, signal information is known at close and the return reference uses the next session open adjusted by that session's adjustment factor. C identifies gaps from raw open versus prior raw close and measures direction-aligned returns after the gap session close; it does not assume an executable gap-price fill. Controls are same-date eligible non-event symbols, with C controls oriented by the event gap direction. Controls remain observational and confounded.

| Hypothesis | Events | Symbols | Dates | 5-session event mean | Matched-control mean | Mean uplift | Two-way date/symbol bootstrap 95% CI | Centered bootstrap p | Finding |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---|
| S3-A | 45 | 17 | 37 | +0.792% | −0.121% | +0.913% | −1.150% to +3.597% | 0.442 | Wide interval crosses zero; median event return −0.775%; no Stage B pass. |
| S3-B | 0 | 0 | 0 | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | UNKNOWN | Postponed: required official benchmark series unavailable. |
| S3-C | 2,269 raw gaps (2,161 matched) | 18 | 681 | −0.204% | −0.221% | +0.017% | −0.385% to +0.447% | 0.933 | No meaningful uplift; clustered interval crosses zero. |
| S3-D | 485 | 18 | 316 | −0.063% | −0.223% | +0.160% | −0.494% to +0.879% | 0.644 | Wide interval crosses zero; no Stage B pass. |

Returns are percentages of the stated reference value. Means and intervals are descriptive. Bootstrap resampling used 10,000 date-cluster and symbol-cluster pigeonhole replications with seed `20261030`. Holm adjusted centered bootstrap p-values across the three calculable primary hypotheses are 1.000 for each; S3-B is untestable, not a null result. The interval method is an approximate cluster bootstrap for this small, strongly dependent panel, not a substitute for an untouched sample.

Raw event counts overstate independent evidence. Kish effective date-cluster / symbol-cluster counts were 27.7 / 13.1 for S3-A, 390.5 / 14.8 for S3-C, and 228.2 / 16.2 for S3-D; the conservative minimum-cluster proxy is therefore only about 13, 15, and 16 independent clusters, respectively, not thousands of independent events. Same-symbol signals occurred within a 7-calendar-day overlap proxy 9 times for S3-A, 1,552 times for S3-C, and 132 times for S3-D. This calendar proxy is approximate; the bootstrap resamples date and symbol clusters, while the 1/3/5-session outcomes overlap directly. S3-A only narrowly clears the minimum raw-count/symbol/date rule. S3-C/D clear raw count thresholds but still have only 18 symbols, an incomplete universe, and heavily overlapping windows. No independent confirmation or credible causal effect is established.

## Stage gates and competition feasibility

- **Stage A:** approved-row chronology and PIT checks passed for the analyzed rows. S3-B failed data adequacy. Daily open/close data support a descriptive gap classification but not auction timing, queue, spread, or a fill at the gap price.
- **Stage B:** no hypothesis passed. For all three calculable 5-session effects, the clustered 95% interval includes zero and the Holm adjusted p-value is 1.000. S3-C’s point estimate is close to zero; S3-A/D have large uncertainty.
- **Stages C-D:** not run because Stage B failed. Cost sensitivity cannot repair an unestablished signal edge.
- **Stage E:** not run. No portfolio prototype or new official TradeSim candidate run was justified.

The new hypotheses have no portfolio metrics because portfolio construction was gated off. Prior, already-rejected candidates remain separate evidence: MeanRev5 had 109 completed FIFO round trips but 26.3% average exposure, −39.3% max drawdown, and −4.37% net return; H6 had 23 round trips, 21.9% average exposure, −27.4% max drawdown, and −3.49% net return. Their after-fee expected payoff was negative. The round-trip count alone does not qualify them. Benchmark drawdown/excess-return comparisons are `UNKNOWN` for the future competition window, as are boundary treatments; do not infer eligibility from these historical runs.

**Promotion result: `NO_SIGNAL_PASSED_PROMOTION_GATE`.** No final strategy is selected. Highest-value new evidence: a validated official daily SET50 Price Index series with revision policy and more complete PIT constituent price coverage; then genuinely prospective, frozen evaluation. Historical BBO cannot be substituted for this need.

## Final-direction research addendum (2026-10-30)

This addendum supersedes the earlier S3-B `postponed` status: the official TradeSim-history SET50 daily index was located and used for benchmark conditioning. The original first-screen report, event files, configuration, and registration remain preserved. The final frozen addendum registered all four hypotheses, the five-session primary endpoint, 1/2/3-session descriptive endpoints, the same-symbol/year direction-matched S3-C control, benchmark provenance, and 21-session risk-envelope method before this additional signal run. Hashes and run provenance are in `reports/research_phase3_summary.json`.

| Hypothesis | H5 events / matched | Symbols / dates | Event mean | Control mean | Uplift | Clustered 95% CI | Holm p | Result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| S3-A | 45 / 45 | 17 / 37 | +0.792% | -0.121% | +0.913% | -1.187% to +3.566% | 1.000 | Rejected: interval spans zero |
| S3-B | 724 / 711 | 18 / 319 | -0.399% | -0.131% | -0.269% | -1.063% to +0.494% | 1.000 | Rejected: negative point uplift; interval spans zero |
| S3-C | 2,269 / 2,269 | 18 / 682 | -0.079% | +0.027% | -0.106% | -0.542% to +0.353% | 1.000 | Rejected: negative direction-aligned uplift; interval spans zero |
| S3-D | 486 / 486 | 18 / 317 | -0.051% | -0.223% | +0.172% | -0.506% to +0.866% | 1.000 | Rejected: interval spans zero |

The official index enables S3-B but does not cure the partial PIT breadth universe. Event counts overstate independent evidence because dates/symbols cluster and forward horizons overlap. All stock history was previously inspected; predefined chronological slices are retrospective stability descriptions, not OOS validation. Per-event outcomes with PIT state, source semantics, market regime and feature values are in `reports/research_phase3_event_outcomes.jsonl`; horizon, slice, uncertainty and source/code hash results are in `reports/research_phase3_summary.json`.

All primary five-session intervals cross zero and all four Holm-adjusted p-values are 1.000. `G0=PASS_WITH_LIMITATIONS`; `G1=FAIL_ALL`; G2–G4 were not run. No thresholds were tuned after outcomes. Final result remains `NO_SIGNAL_PASSED_PROMOTION_GATE`.

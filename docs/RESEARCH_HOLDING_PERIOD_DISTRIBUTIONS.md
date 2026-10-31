# Holding-Period Distribution Research

**Experiment:** `PHASE4_HOLDING_DISTRIBUTION_REUSED_PHASE3_20261031`
**Status:** exploratory descriptive reanalysis; all source history had already been inspected.
**Award direction:** Best Alpha first, Best Risk Control second. This affects future eligible-scenario reporting only; it does not relax common gates or make a strategy selection.
**Data purchase budget:** THB 0.

These confirmed directions are recorded in [`phase4_research_direction_lock.json`](../config/phase4_research_direction_lock.json) and the experiment registry.

## Frozen cohort and definition

The event cohort is the unique `(hypothesis, symbol, date)` set in the final Phase 3 event artifact at H=5: S3-A 45, S3-B 724, S3-C 2,269, and S3-D 486. Events were not redefined, thresholds were not retuned, and prior G1 rejections remain rejected. The analysis uses only approved, point-in-time-filtered raw daily files and does not merge Settrade or TradeSim stock bars.

Fixed horizons are 1, 2, 3, 4, 5, 7, 10, and 15 observed eligible trading sessions. The entry session is H=1. S3-A/S3-D use hypothetical next-session adjusted open entry and the adjusted close at the end of H; S3-B uses the next-session open after a close-known signal and the close at H; S3-C is entered hypothetically at the gap-session close and held for H subsequent closes. S3-C does not assume a fill at the observed gap open. A horizon needs all endpoint observations; missing endpoints are reported as attrition, never filled.

These are daily-bar return proxies, not 0.2.7 fills. Fee-only net return subtracts the official round-trip commission/VAT rate (0.33598%). Adverse execution sensitivity subtracts an additional one SET tick at each side using the repository's explicit tick schedule at raw entry and exit prices. The latter is a stress approximation: daily bars do not prove that either order filled at those prices, do not reveal queue/depth, and do not estimate IOC fill probability. Tick costs use the underlying raw-price level, while return observations use adjusted prices.

## Controls and uncertainty

S3-A/B/D compare each event with the mean same-date PIT-eligible non-event securities. S3-C compares its direction-aligned return with same-symbol, same-calendar-year eligible non-gap observations; all qualifying gaps are excluded from its control pool, including gaps without complete H=5 follow-up. The event gap direction is applied to controls. These controls are observational and cannot remove unobserved confounding. Each horizon reports event and paired-uplift uncertainty from a 10,000-replication two-way date/symbol pigeonhole bootstrap (seed 20261101 plus fixed horizon offsets). Holm correction is applied across 32 (four hypotheses times eight horizons) uplift tests separately for each cost scenario. This adjustment family does not cover the many earlier signal families inspected on the same history; these results make no confirmatory inference. Small symbol counts make the percentile intervals approximate; dependence from overlapping event windows remains substantial.

The first-passage report measures daily-close crossings of +1%, +2%, -1%, -2%, and 0% net thresholds, specified before inspecting the first-passage output and recorded in the Phase 4 direction config. The opposite +1%/-1% boundary is treated as a competing event; censored and incomplete events remain in the original cohort denominator. Right-censoring means all 15 closes were observed without either boundary; insufficient follow-up is reported separately. These are close-marked passage times, not intraday threshold ordering or tradable exits. OHLC high/low sequencing is not inferred. The first positive net close is descriptive only and cannot identify an optimal exit. Passage-rate intervals are descriptive; no threshold or time-to-outcome p-value is used for promotion.

## Holding-period distribution results

Machine-readable results contain the full horizon-by-hypothesis curve, sample counts, quantiles, dependence measures, clustered intervals, matched controls, p-values, cost scenarios, source hashes, and first-passage denominators:

- [`research_holding_horizon_curve.json`](../reports/research_holding_horizon_curve.json)
- [`research_time_to_outcome_distribution.json`](../reports/research_time_to_outcome_distribution.json)

The fixed-horizon table is generated from the horizon report; first-passage statistics are generated from the close-path report. Returns and uplift are percentages. `95% CI` is the unadjusted two-way clustered interval for paired uplift; interpret it with the Holm-adjusted p-value in JSON. **No single horizon is selected as the best exit.**

### Full fixed-horizon curve (H1-H15)

| Signal | H | N / matched | Fee-only net mean | Fee-only matched uplift (95% CI) | One-tick/side net mean | One-tick/side uplift |
|---|---:|---:|---:|---:|---:|---:|
| S3-A | 1 | 45 / 45 | -0.38% | +0.08% [-0.77, +0.95] | -1.66% | +0.07% |
| S3-A | 2 | 45 / 45 | -0.11% | +0.10% [-1.30, +1.54] | -1.39% | +0.10% |
| S3-A | 3 | 45 / 45 | +0.28% | +0.69% [-1.16, +2.61] | -1.00% | +0.69% |
| S3-A | 4 | 45 / 45 | +0.09% | +0.49% [-1.46, +2.60] | -1.19% | +0.49% |
| S3-A | 5 | 45 / 45 | +0.46% | +0.91% [-1.17, +3.58] | -0.81% | +0.93% |
| S3-A | 7 | 45 / 45 | +0.53% | +0.68% [-1.76, +3.49] | -0.75% | +0.69% |
| S3-A | 10 | 45 / 45 | +0.57% | +0.29% [-2.39, +3.60] | -0.70% | +0.30% |
| S3-A | 15 | 45 / 45 | +1.19% | +0.71% [-2.23, +4.22] | -0.09% | +0.70% |
| S3-B | 1 | 713 / 713 | -0.49% | -0.03% [-0.27, +0.19] | -1.76% | -0.04% |
| S3-B | 2 | 710 / 710 | -0.65% | -0.19% [-0.61, +0.19] | -1.92% | -0.20% |
| S3-B | 3 | 709 / 709 | -0.65% | -0.16% [-0.71, +0.36] | -1.92% | -0.18% |
| S3-B | 4 | 711 / 711 | -0.73% | -0.21% [-0.85, +0.44] | -2.01% | -0.22% |
| S3-B | 5 | 711 / 711 | -0.79% | -0.21% [-0.98, +0.54] | -2.06% | -0.23% |
| S3-B | 7 | 708 / 708 | -0.77% | -0.15% [-1.05, +0.70] | -2.05% | -0.17% |
| S3-B | 10 | 707 / 707 | -0.93% | -0.23% [-1.33, +0.80] | -2.21% | -0.26% |
| S3-B | 15 | 696 / 696 | -1.09% | -0.11% [-1.41, +1.06] | -2.38% | -0.14% |
| S3-C | 1 | 2269 / 2269 | -0.27% | +0.06% [-0.17, +0.29] | -1.53% | +0.06% |
| S3-C | 2 | 2269 / 2269 | -0.31% | +0.02% [-0.27, +0.32] | -1.57% | +0.02% |
| S3-C | 3 | 2269 / 2269 | -0.39% | -0.07% [-0.40, +0.29] | -1.65% | -0.06% |
| S3-C | 4 | 2269 / 2269 | -0.46% | -0.15% [-0.56, +0.26] | -1.72% | -0.15% |
| S3-C | 5 | 2269 / 2269 | -0.42% | -0.11% [-0.55, +0.35] | -1.68% | -0.11% |
| S3-C | 7 | 2263 / 2263 | -0.46% | -0.17% [-0.64, +0.34] | -1.72% | -0.16% |
| S3-C | 10 | 2260 / 2260 | -0.28% | -0.00% [-0.54, +0.56] | -1.54% | +0.00% |
| S3-C | 15 | 2248 / 2248 | -0.37% | -0.12% [-0.82, +0.57] | -1.63% | -0.12% |
| S3-D | 1 | 486 / 486 | -0.38% | -0.00% [-0.29, +0.28] | -1.66% | -0.01% |
| S3-D | 2 | 486 / 486 | -0.63% | -0.11% [-0.53, +0.29] | -1.92% | -0.12% |
| S3-D | 3 | 486 / 486 | -0.62% | -0.04% [-0.52, +0.45] | -1.91% | -0.05% |
| S3-D | 4 | 486 / 486 | -0.59% | +0.07% [-0.50, +0.67] | -1.88% | +0.06% |
| S3-D | 5 | 486 / 486 | -0.39% | +0.17% [-0.50, +0.87] | -1.68% | +0.16% |
| S3-D | 7 | 485 / 485 | -0.30% | +0.11% [-0.74, +0.99] | -1.59% | +0.11% |
| S3-D | 10 | 484 / 484 | -0.16% | -0.03% [-0.91, +0.89] | -1.45% | -0.03% |
| S3-D | 15 | 476 / 476 | +0.61% | +0.57% [-0.65, +1.91] | -0.68% | +0.57% |

### H=5 check against canonical Phase 3

The cohort remains the final 2026-10-30 Phase 3 event set. Fee-only paired uplift reproduces S3-A (+0.9130%), S3-C (-0.1069%, within rounding of -0.1064%), and S3-D (+0.1719%) with the original controls. Cluster bootstrap intervals are regenerated with a fixed new seed and therefore differ slightly. S3-B is not directly comparable: this horizon analysis enters at the next session open and subtracts the official index close-to-close return through the exit, while Phase 3's primary endpoint used a close-to-close benchmark-relative return. The event counts are unchanged.

## Close-based first passage (fee-only)

The table reports cumulative incidence: the target must be reached before the opposite +/-1% boundary. A prior adverse boundary is a competing event for positive objectives; a prior +1% objective is competing for the -1% risk boundary. Incomplete follow-up and no-hit events remain in each original cohort denominator. Brackets are 95% two-way date/symbol cluster-bootstrap bands (2,000 replications); 18 symbols and overlapping event paths make these descriptive and approximate. Full counts for H1/H2/H3/H4/H5/H7/H10/H15, both cost cases, and all thresholds are in the JSON.

| Signal | Cohort | +1% before -1% by H5 (95% CI) / H15 (95% CI) | Median target-first session | +2% before -1% by H5 / H15 | -1% before +1% by H5 / H15 |
|---|---:|---:|---:|---:|---:|
| S3-A | 45 | 33.3% [12.2, 57.8] / 33.3% [11.6, 56.4] | 1.0 | 31.1% / 31.1% | 66.7% / 66.7% |
| S3-B | 724 | 33.1% [27.1, 39.3] / 34.1% [28.3, 40.1] | 1.0 | 25.4% / 28.0% | 62.4% / 63.5% |
| S3-C | 2269 | 40.4% [36.4, 44.5] / 41.8% [37.7, 45.9] | 1.0 | 32.4% / 35.5% | 56.8% / 58.2% |
| S3-D | 486 | 34.8% [27.5, 41.4] / 37.0% [29.9, 44.4] | 2.0 | 26.3% / 30.7% | 61.7% / 62.6% |

## Competition feasibility and award implications

The 21-session competition calendar makes holding duration relevant to completed FIFO round trips. In a simplified, single-capital serial schedule, at most `floor(21 / (H + 1))` complete buy/hold/sell cycles fit: H=1: 10; H=2: 7; H=3: 5; H=4: 4; H=5: 3; H=7: 2; H=10: 1; H=15: 1. This is an arithmetic upper bound for serial use of all capital, not a portfolio execution forecast; parallel positions can complete several round trips together, depending on fills, allocation, FIFO, and boundary treatment. The minimum five round trips may therefore remain mechanically feasible at longer H with concurrent holdings, but this was not tested as a candidate portfolio. The KGI scoring source also requires minimum average exposure, positive expected payoff, and a strict benchmark-relative MDD gate (see [`COMPETITION_SOURCE_AUTHORITY_AUDIT.md`](COMPETITION_SOURCE_AUTHORITY_AUDIT.md)). No tested Phase 3 signal has passed G1, so portfolio ranking is not run.

For a future *eligible* portfolio, report Best Alpha using the official excess-return, Calmar, and total-return ranking, and Best Risk Control using the official Calmar, excess-return, and drawdown ranking. Do not infer future award outcomes or game ratios with low exposure or tiny activity. The 6–7% return remains aspirational, not a hurdle.

## Interpretation and remaining limits

Every interval shown here reuses the previously inspected partial 18-name PIT panel. The addendum's baseline-only 20-name panel (THAI/MRDIYT included under their bounded approvals) is not used to add new Phase 3 signals. S3-C outcomes are direction-aligned diagnostics; negative-gap alignment is not a long-only executable strategy. No horizon reanalysis is independent OOS. No result meets multiplicity-adjusted and independent-OOS promotion requirements. The provisional preference remains a research focus on H=1–5, while H=7–15 stays in descriptive comparison; available evidence does not justify a signal-specific horizon preference.

Independent validation requires prospective, untouched, PIT-eligible data with source and adjustment status verified, adequate breadth beyond the partial panel, frozen rules before outcomes, and sufficient independent symbol/date clusters. Tick-level spread/depth and 0.2.7 replay evidence are required before execution claims. No paid data was purchased or queried.

**Decision:** `NO_SIGNAL_PASSED_PROMOTION_GATE`
**Candidate shortlist:** empty; no candidate is ready for human strategy review.

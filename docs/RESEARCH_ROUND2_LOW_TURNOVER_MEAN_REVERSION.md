# Research Round 2 — regime-conditioned low-turnover mean reversion

**Evidence class:** signal diagnostics and exploratory portfolio backtest only. **Final strategy:** not selected. **Promotion:** `NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE`.

## Pre-registration and data

Hypothesis `H6_REGIME_CONDITIONED_LOW_TURNOVER_MEAN_REVERSION` was added to `reports/research_hypothesis_specs.json` and the experiment registry before evaluating H6 outcomes. Round 1 remains diagnostic evidence: Trend20, Breakout20, and Relative Strength had negative gross edges; MeanRev5 had positive gross but negative net after substantial costs. No MeanRev5 tuning occurred.

The H6 stock setup requires a 5-session adjusted return from −8% to −3%, close above SMA50, SMA50 at least SMA100, and 10-session directional efficiency at most 0.35. The broad regime requires the official SET50 benchmark above SMA50 with 20-session return at least −1%. Stock inputs use the approved PIT daily loader; market regime uses the local official TradeSim SET50 daily index file. Benchmark volatility and cross-sectional dispersion are diagnostic splits only. Dispersion is computed from same-date approved stock returns only when at least 10 names are present; volume/BBO is not treated as liquidity.

The single portfolio variant was registered as top 3 equal weight, five-observation selection cadence, persistent unchanged holdings while trend/regime thesis remains valid, and next-observed-session execution under the unchanged `RESEARCH_EXECUTION_V1` assumptions. It uses one tick, LIMIT/IOC research orders, 0.157% commission and 7% VAT. No leverage or synthetic bars/BBO are used. Round 1 and Round 2 both use repeatedly inspected 2023–2026 history; this is not independent confirmation.

## Stage 0 — signal expectancy

The pre-registered signal produced **137 events across 17 symbols**. All event decisions use the close at time *t*; execution reference begins at the next observed session open. The adjusted open is derived using the same row's adjusted-close/raw-close factor. Forward prices do not enter the selector.

| Forward horizon from next open | N | Mean | Median | Hit rate | Approx. 95% CI for mean |
|---|---:|---:|---:|---:|---|
| Next open → next close | 137 | +0.315% | 0.000% | 43.1% | −0.005% to +0.634% |
| Next open → +2 sessions | 137 | +0.418% | +0.000% | 52.6% | −0.088% to +0.925% |
| Next open → +3 sessions | 137 | +0.520% | +0.448% | 53.3% | −0.087% to +1.126% |
| Next open → +5 sessions | 137 | +0.333% | −0.481% | 45.3% | −0.476% to +1.143% |
| Next open → +10 sessions | 137 | +1.063% | 0.000% | 49.6% | −0.096% to +2.222% |

All five sample means are positive, so the signal screen was not clearly poor and Stage 1 was run. All confidence intervals cross zero. The 137 events overlap by time and symbol; the intervals are approximate normal intervals without dependence correction. They are not executable PnL or evidence of a statistically established edge.

## Stage 1 — portfolio and cost separation

| Metric | Round 1 MeanRev5 | Round 2 H6 top 3 |
|---|---:|---:|
| Gross return (slippage already reflected) | +11.26% | +0.082% |
| Commission | THB 1,461,235 | THB 333,369 |
| VAT | THB 102,286 | THB 23,336 |
| Total fees | THB 1,563,521 | THB 356,705 |
| Modeled one-tick slippage attribution | THB 6,458,230 | THB 1,316,274 |
| Net return | −4.37% | −3.49% |
| Maximum drawdown | −39.33% | −27.42% |
| Turnover | 93.07× | 21.23× |
| Filled / non-filled orders | 205 / 83 | 58 / 33 |
| Average equity exposure | 26.31% | 21.94% |
| FIFO completed roundtrips | 109 | 23 |
| Average holding period | 6.22 calendar days | 16.09 observed sessions |
| FIFO win rate / expected payoff | 42.2% / not reported | 34.8% / 1.69 |
| Unique symbols actually traded | 18 | 12 |

Round 2 turnover is **77.2% lower** than Round 1 MeanRev5. Gross edge was nearly flat and did not cover the THB 356,705 fees, leaving net PnL of about **−THB 348,551**. Modeled slippage is reported separately but already affects gross return; it is not subtracted a second time. The net reconciliation difference is zero.

The FIFO symbol ledger attributes closed-lot net PnL to 5 profitable and 7 losing symbols. Largest positive contributors were KKP (+THB 1.12m) and KTB (+THB 1.09m); largest negative was BDMS (−THB 1.25m). Top one and top three absolute contributor shares were 19.7% and 42.9%. Open lots are excluded from this FIFO realized attribution. Annual equity changes were negative in 2023, 2024, and 2025, then positive in 2026; this is descriptive and the last year is a partial period.

Stage 1 rejected the candidate because net return was negative. The reduction in turnover did not preserve gross expectancy. As required, chronological OOS folds, alternative parameter runs, and cost-sensitivity cases stopped here. No broad grid search was performed.

## Regime and robustness analysis

The report includes forward-return summaries for the unconditioned stock setup grouped by (a) SET50 above/below SMA50, (b) positive/negative 20-session return, (c) benchmark volatility above/below its expanding past-only median, and (d) cross-sectional dispersion above/below its expanding past-only median. These signal-level returns are gross diagnostics with no portfolio costs. The conditioned H6 events all fall in the neutral/positive benchmark state by construction; no weak-regime conditioned portfolio is implied.

The Stage 1 portfolio also records sample count, gross/net PnL and return, fees, hit rate, maximum observed portfolio drawdown, turnover, fills, and exposure by these four regime definitions. Gross in this decomposition is before commission/VAT and after modeled slippage. The state groups are non-contiguous and overlap across definitions. Their results are descriptive, not independent folds or robustness evidence; Stage 1 failure stopped the OOS and nearby-variant stages. Robustness, walk-forward, and sensitivity outputs are explicitly `NOT_RUN_AFTER_STAGE1_REJECTION` in the machine report.

## Causality, multiplicity, and promotion

The audit confirms trailing feature windows, same-date cross-sectional dispersion, past-only expanding regime thresholds, point-in-time eligibility, signal close before next-session execution, and forward labels excluded from selection. No same-bar execution is used. Pre-2023 membership limitations and partial data coverage from Round 1 still apply. No historical BBO, spread, or depth is used.

The experiment registry preserves Round 1 failures and includes the Round 2 signal and portfolio run. Repeatedly inspected history and overlapping events create material multiple-testing/dependence risk. No candidate passed the documented promotion gate. Therefore no candidate-level TradeSim 0.2.6 smoke or replay was run. The runtime `--check` is READY on exact Python 3.13.0, but runtime readiness is not candidate validation.

Machine-readable event-level results, distributions, regime summaries, fills, costs, FIFO attribution, and orders are in [`research_round2_summary.json`](../reports/research_round2_summary.json). Causal checks are in [`no_lookahead_candidate_audit.json`](../reports/no_lookahead_candidate_audit.json); registration is in [`experiment_registry.json`](../reports/experiment_registry.json). The read-only Competition Cockpit shows the signal and portfolio stages.

## Decision

`NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE`. No candidate is recommended for human selection, and no final strategy was selected. Do not tune this same history further without a new pre-registration and a genuinely later or otherwise independent evaluation period.

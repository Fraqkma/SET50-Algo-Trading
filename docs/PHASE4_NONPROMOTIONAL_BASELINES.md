# Phase 4 Non-Promotional Baselines

**Diagnostic only. No signal or strategy candidate is being promoted.** Machine results: `reports/phase4_nonpromotional_baselines.json`.

## Method

- Source: separate 20-name manifest-approved panel (18 Phase 3 event-panel names plus THAI and MRDIYT), approved start/end bounds, Yahoo adjusted closes, and published date-effective PIT membership intervals. THAI and MRDIYT have 48 admissible PIT rows by the Sep 4 cutoff; that is enough for this baseline's 21-session endpoint but below Phase 3's 55-row feature warmup. A comparator using only the original 18 names is preserved in `reports/phase4_nonpromotional_baselines_phase3_18.json`. No Settrade or TradeSim constituent prices are mixed into either basket.
- For each 21-session window (22 closes), a deterministic random basket of 3, 5, or 8 names is selected from names that are PIT members and have an approved price on the window start. Selection uses only entry-date eligibility; overlapping windows are retrospective and not independent.
- The baseline marks equal-weight holdings at adjusted closes, charges the stated 0.16799% commission+VAT on hypothetical entry and exit, and assumes terminal liquidation solely to measure conditional round-trip mechanics. It does not model tick slippage, board-lot sizing, liquidity or actual fills.
- The report compares the same windows to the separate 747-close official TradeSim-history SET50 series when dates align. It also reports strict `<1.5×` drawdown scenario frequency. That is not a forecast of the future scoring benchmark.
- The null benchmark is random eligible-name selection with no signal. Cash-only remains a zero-return, zero-exposure, zero-roundtrip baseline.

## Results

| Random basket size | Net return median | Net return 10th–90th percentile | Median MDD | Median excess vs TradeSim SET50 series | Median net expected payoff per hypothetical completed lot | EOD exposure | Conditional FIFO round trips |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 3 | -0.87% | -8.62% to +8.79% | 5.34% | -0.49% | -0.93% | 100% | 3 (fails five-lot count) |
| 5 | -0.98% | -8.38% to +8.50% | 5.05% | -0.45% | -0.99% | 100% | 5 if all hypothetical fills occur |
| 8 | -1.09% | -8.40% to +7.66% | 4.62% | -0.52% | -1.13% | 100% | 8 if all hypothetical fills occur |

The five- and eight-name holding baselines exceed 50% EOD exposure and meet the five-roundtrip count only by assuming every entry and terminal exit fills. They fail the positive expected-payoff criterion at the median window, before any tick-slippage stress; the three-name case also falls short of five round trips. The fraction of benchmark-aligned historical windows with portfolio MDD strictly below 1.5× the available TradeSim-history benchmark MDD is 45.9%, 49.6%, and 53.1% for 3/5/8 names, respectively. Those overlapping windows are scenarios, not future qualification probabilities. Overall, these diagnostics do not satisfy all common criteria and provide no evidence of alpha. The hypothetical holdings last the full window, so they do not test the preferred 1–5-session operating cadence.

The 21-session calendar leaves enough order dates to schedule five 1–5-session FIFO lots, but OHLC bars cannot show that they would execute or earn positive net payoff. A separate source-supported fill model is required. The historical `<1.5×` benchmark drawdown scenario fraction is recorded by basket size in the JSON; it must not be read as future qualification probability.

## Cash-only and interpretation

Cash-only is 0% return, 0% exposure and 0 completed round trips by construction; it fails the participation criteria. No strategy was selected or tuned toward the competition's aspirational return. Daily-bar fills, synthetic BBO, or fabricated transaction evidence were not used.

# TradeSim 0.2.7 Execution Sensitivity Follow-up

## Scope

`RESEARCH_EXECUTION_V1` is preserved exactly. This follow-up reuses its prior MeanRev5 and Round 2 H6 results and the local official TradeSim 0.2.7 validation fixtures. It makes no real broker calls and does not promote a strategy. The test matrix was local-only and separately labeled `OFFICIAL_TRADESIM_0_2_7`; it is not a competition portfolio run.

## Sensitivity frontier

| Case | Evidence | MeanRev5 | H6 | What can be concluded |
|---|---|---:|---:|---|
| Research baseline V1 | Approved daily OHLCV, LIMIT/IOC, adverse one tick, bar-range fill assumption, commission 0.157% plus VAT | Gross +11.26%, net −4.37%, DD 39.33%, average exposure 26.31%, 109 FIFO round trips | Gross +0.08%, net −3.49%, DD 27.42%, average exposure 21.94%, 23 FIFO round trips | Both remain rejected; V1 assumptions and outputs remain historically unchanged. |
| Conservative 0.2.7-informed daily-bar case | Not numerically estimated: exact matched tick volume, queue, spread/depth, and same-tick IOC path are unavailable in daily bars | UNKNOWN | UNKNOWN | No defensible daily-bar conversion can model 0.2.7 partial fills or infer a global fill rate. |
| Idealized upper-bound diagnostic | Fee-free counterfactual on the unchanged V1 path; V1 adverse-tick slippage remains embedded | +11.26% before commission/VAT | +0.08% before commission/VAT | This is not a fill-quality bound. It isolates the fee burden only; it ignores feedback of fees on cash, sizing, and future trades. MeanRev5 still fails exposure/drawdown constraints, and H6 has negligible pre-fee return. |
| Stress-cost case | V1 with cost stresses in the preserved candidate report | Remains rejected; commission plus VAT are 138.8% of reported gross P&L, while V1 tick slippage is separately tracked and already affects execution | Remains rejected; near-zero pre-fee gross cannot support costs | Increasing costs cannot turn a failed edge into a passing one. No assumptions were tuned. |

The available 0.2.7 controlled fixture matrix contains 13 cases and 22 checks, all passing. It verifies mechanics such as a 350-share tick volume cap producing 300 filled shares, board-lot clipping, invalid tick rejection, auction restrictions, and no second IOC match. Those fixtures are not a statistical fill sample. The locally preserved 0.2.7 runtime/validation evidence is under `artifacts/tradesim_027_validation/20261028/0.2.7/` and `reports/execution_sensitivity_summary.json`.

Official tick files are locally present for 2026-09-09 through 2026-09-30, and prior 0.2.7 no-order official-data runs are recorded in the readiness evidence. A MeanRev5/H6 tick replay was not run: the approved PIT daily stock panel ends 2026-09-04, so it does not provide approved signal state for those official tick dates. Replaying old signal events against unrelated tick dates or retrofitting the non-PIT current-constituent Settrade recovery would create a false signal/execution match. The real-tick evidence therefore validates runtime/data availability, not strategy-specific 0.2.7 outcomes.

## Observable versus unobservable

- **Observable:** daily OHLCV; the limited official tick data already present in local validation artifacts; the versioned 0.2.7 runtime behavior on controlled cases.
- **Unobservable from historical daily bars:** exact eligible volume at the order price and time, order queue state, spread/depth, competing flow, and whether/when a tick-level IOC order would match.
- **Still assumptions:** entry timing, requested-price rounding, adverse one-tick convention, fee/VAT accounting, and board-lot sizing. They must be explicit in any future run.

The 0.2.7 runtime's mechanics can materially change realized paths compared with V1, but existing data do not support recasting old daily-bar trades into authentic 0.2.7 fills. No global fill probability, fake BBO, or synthetic liquidity estimate is produced. The useful conclusion is that execution uncertainty cannot rescue H6's near-zero gross edge, while MeanRev5 remains a high-drawdown, low-exposure, after-cost rejection under the observed V1 path; the direction of any tick-level fill change is unknown.

## Final fixed-fill arithmetic addendum (2026-10-30)

`reports/execution_sensitivity_027_fixed_fill_arithmetic.json` was calculated from the original MeanRev5 and H6 run aggregates. This is a deliberately narrow arithmetic diagnostic: historical fills/quantities are held fixed, so the counterfactual cash path, drawdown, exposure, future orders, and qualification are not recomputed.

| Candidate | V1 filled / non-fill / intended | Fees (commission + VAT) | One-tick slippage | Turnover | V1 max DD / avg exposure | FIFO roundtrips | Zero-slippage add-back net PnL | 1.5x fee + second adverse tick net PnL |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| MeanRev5 | 205 / 83 / 288 | THB 1,563,521 (1,461,235 + 102,286) | THB 6,458,230 | 93.07x | 39.33% / 26.31% | 109 | THB +6,021,084 | THB -7,677,137 |
| Round2 H6 | 58 / 33 / 91 | THB 356,705 (333,369 + 23,336) | THB 1,316,274 | 21.23x | 27.42% / 21.94% | 23 | THB +967,722 | THB -1,843,177 |

The favorable add-back removes the original one-tick modeled cost while retaining historical fees; the stress keeps baseline slippage and charges one additional adverse tick plus 1.5x baseline fees. These numbers are not strategy return estimates: fixed historical quantities ignore cash-path feedback. The favorable arithmetic does not remove the observed high drawdown and low exposure; the stress is not a cash-feasible portfolio replay. A 0.2.7 V2 portfolio replay remains unsupported because daily data cannot identify exact tick-volume-capped fills. V1 rejection remains unchanged. No additional official-tick fixture was run because no signal passed the promotion gate; the preserved local 0.2.7 matrix already has 13 mechanics fixtures and 22 passing checks, which are not a market fill-rate sample.

# TradeSim 0.2.7 execution-sensitivity research

Classification: `RESEARCH_ESTIMATE`. `RESEARCH_EXECUTION_V1` remains intact; no strategy was selected.

## Pre-registered comparison

V1 remains LIMIT/IOC with one adverse SET tick and a daily-bar range-touch fill approximation. The bounded V2 approximation applies the 0.2.7 valid-price ladder, IOC-only, one adverse tick, no persistent orders, and no same-bar lookahead. For the candidate history (2023-01-03 to 2026-09-04), the official 0.2.7 ladder's effective date is 2026-11-16, after the research sample; the in-sample ladder matches the existing tick schedule. The existing bar model already uses one-tick LIMIT/IOC. Thus the defensible V2 bar assumptions are identical to V1 on this sample. No exact per-tick volume cap is inferred from daily bars, and no synthetic BBO or fills are created.

The official 0.2.7 controlled runtime matrix contains 13 hand-selected simulator fixtures and 22 passing checks. It confirms partial quantity clipping to tick volume and board lots, immediate cancellation/no second match for IOC, invalid-tick rejection, auction exclusion, daily caps, one-tick pricing, and FIFO matching. These are targeted behavior checks, not a statistical estimate of market fill rates. The fixture matrix uses controlled simulator records, not live/historical market observations.

## Candidate conclusions

| Candidate | V1 evidence | 0.2.7-informed conclusion |
|---|---|---|
| Trend20 | Gross return -59.04%; rejected Stage 1 | `ALPHA_FAILURE`; no rerun |
| Breakout20 | Gross return -33.95%; rejected Stage 1 | `ALPHA_FAILURE`; no rerun |
| RelativeStrength | Gross return -57.52%; rejected Stage 1 | `ALPHA_FAILURE`; no rerun |
| MeanRev5 | Gross +11.26%, net -4.37%, max DD 39.33%, average exposure 26.31%, 109 completed FIFO round-trips | `MIXED`, cost-sensitive and execution-sensitive; V2 has no defensible change on these daily bars. Costs erase gross edge; remains rejected. |
| Round2 H6 low-turnover mean reversion | Gross +0.08%, net -3.49%, max DD 27.42%, average exposure 21.94%, 23 completed FIFO round-trips; 77.2% lower turnover than Round1 MeanRev5 | `MIXED`, near-zero gross and negative net; V2 does not change the observed-data conclusion. Remains rejected. |

The positive-gross candidates are the only ones with plausible execution sensitivity; one-tick/IOC equivalence means no model change can be inferred from daily data. Portfolio fill counts, tick-volume clipping, queue position, latency, and partial fills remain unidentified at daily resolution. No candidate was rerun under an invented volume cap, and no final strategy was selected.

Machine-readable results and source fixture references are in `reports/execution_sensitivity_summary.json` and `reports/tradesim_027_execution_semantics.json`.

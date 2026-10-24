# Research and official TradeSim compatibility

The research environment and official engine remain separate. Pure feature or
signal functions may be shared later after they are adapted to the simulator's
per-symbol, live-updating `on_data(bar)` callbacks. The official runner invokes
TradeSim 0.2.5 only through the exact Python 3.13.0 subprocess.

| Area | Status | Evidence / caveat |
|---|---|---|
| Daily OHLCV indicators | NEEDS ADAPTER | Simulator callback receives live-updating bars; historical data is bounded before `current_date`. |
| Intraday features | NEEDS ADAPTER | Callback frequency follows each symbol's ticks and configured timeframe aggregation. |
| Cross-sectional ranking | NEEDS ADAPTER | A handler is constructed per symbol; no built-in synchronized ranking API was identified. |
| Portfolio target weights | NEEDS ADAPTER | Must translate targets into per-symbol legal orders with available cash/holdings. |
| FIFO accounting | IMPLEMENTED IN RESEARCH METRICS | `FifoLotLedger` tracks actual matched quantity and closed buy lots independently of order eligibility. |
| Portfolio persistence | OBSERVED IN SOURCE | Portfolio JSON carries cash/holdings/snapshots; strategy object state resets with new handlers. Runtime multi-day validation is blocked on Python 3.13.0. |
| SET50 membership | SIMULATOR VALIDATES SYMBOL LIST | Historical point-in-time membership was not identified in the API. |
| Limit orders | OFFICIAL API | Exposed by handler and matched against tick stream; unfilled orders can rest during a day. |
| Market orders | OFFICIAL API, RULE CONFLICT | Bundled example uses market orders. Repository competition constraints disallow them; do not treat example as compliant. |
| Market-to-Limit IOC | NOT EXPOSED IN REVIEWED STRATEGY INTERFACE | Neither order type nor IOC validity is passed through the handler calls. Confirm against newest workshop. |
| Commission / VAT | OFFICIAL SOURCE OBSERVATION | 0.157% and VAT 7%; transaction CSV does not retain fee fields, so bridge calculations are derived from fills. |
| Slippage | OFFICIAL SOURCE OBSERVATION | Market execution applies the price-bucket increment; limit execution does not use that market slippage calculation. |
| Research next-session open fills | RESEARCH ONLY | Official fills occur on supplied intraday ticks and use simulator matching rules. |
| SETTRADE or Yahoo features | RESEARCH ONLY | Not inputs to official tick data. |

## Simulator and task-rule discrepancies

The bundled example calls market orders, while the repository competition rules
allow only Limit and Market-to-Limit IOC. The inspected StrategyHandler exposes
Limit and Market order methods but no IOC validity. The competition briefing PDFs
were not present locally, so these discrepancies are documented rather than
resolved against older material. The newest 08/10/2026 official workshop must
decide the competition rule.

TradeSim's portfolio source keeps multiple stock lots per symbol and closes them
FIFO. This supports accounting for simultaneous lots but does not prove the
organizer permits adding to a position. `ADD_TO_POSITION_RULE = UNCONFIRMED`.

Research and official metrics are not treated as interchangeable. Official result
normalization preserves engine identity, daily rows, fills, errors, fees where
derivable, holdings, and raw artifact references. Metrics absent from simulator
outputs remain null/UNKNOWN. Exact Competition Performance PDF formulas need
confirmation from the missing local PDF before the report is treated as final.

## Current verification boundary

The repository contains neither `KGI AlgoTrading 2026 ALGO workshop_08102026.pdf`
nor `KGI_ALGO26_Performance_TH.pdf`. The local archive is `tradeSim0.2.5.zip`
with SHA-256
`9f9e972f9df082bcd0739588f241a318243db06f5d0837290d4bc8593bfb5ed7`.
The exact Python 3.13.0 runtime is also absent (`py -3.13` resolves to 3.13.16),
so import, dependency, one-day, and multi-day runtime checks are BLOCKED. Do not
substitute 3.13.16 or use the research Python to import the simulator.

TradeSim source checks confirm 100-share order increments, SET50 symbol-list
validation, Limit and Market APIs, full-quantity fills, no exposed IOC or
Market-to-Limit order argument, price-bucket market slippage, and 0.157%
commission plus 7% VAT. These are source observations, not verified competition
rules. The October 16 Settrade production transition is intentionally a
partial-day cutover and is unrelated to completeness of these practice ticks.

The inspected `Order.validate_order` path has no explicit positive-quantity
guard (its board-lot check only applies when volume is positive). The portable
competition `OrderIntent` therefore rejects zero/negative quantities before an
engine adapter can receive them. This is a local safety boundary; TradeSim
internals remain unchanged.

## TradeSim 0.2.6 organizer compatibility update (2026-10-22)

See [TradeSim 0.2.6 final readiness](TRADESIM_026_READINESS.md) for evidence
labels, archive identity, source comparison, and the full readiness decision.

| Behavior | 0.2.6 evidence | Status |
|---|---|---|
| Resting limit touch | Does not fill; price must be traded through | CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED; runtime unobserved |
| Tick quantity cap | Fill is no more than tick volume, floored to 100-share lots | CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED; runtime unobserved |
| Residual quantity | Rests intraday; remainder is canceled at EOD | CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED; runtime unobserved |
| Immediate limit fill | Prior immediate behavior and price improvement retained; tick cap applies | CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED; runtime unobserved |
| Market order | Changelog says unchanged; price-bucket slippage and fees unchanged in source | CHANGELOG DOCUMENTED + SOURCE REVIEW; runtime unobserved |
| `create_order_to_limit` | Same four-argument signature; fill expectations change with tick caps | CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED; runtime unobserved |
| Same-symbol buys | Different orders remain distinct lots; a single order's pieces combine as one lot | SOURCE IMPLEMENTED; competition rule unconfirmed |
| Fees | 0.157% commission plus 7% VAT | SOURCE REVIEW; runtime unobserved |
| Competition order types | Simulator exposes Limit and Market, not Market-to-Limit IOC | SOURCE REVIEW; conflicts with local competition constraints, organizer rule confirmation pending |

The 0.2.5 ZIP is absent, so changed-file inventory compares the preserved
unversioned 0.2.5 extraction with the 0.2.6 archive. The 0.2.5 compatibility
extraction was not overwritten. No 0.2.6 runtime regression was run because
only Python 3.13.16 is currently registered, not exact 3.13.0.

### 0.2.6 execution matrix with evidence layers

| Semantics | Team competition rules in `AGENTS.md` | 0.2.6 changelog | 0.2.6 source | Runtime |
|---|---|---|---|---|
| Limit orders | Allowed | Matching changes documented | Limit API and matching present | NOT OBSERVED |
| Market orders | Prohibited | Behavior unchanged | Market API remains, with price-bucket slippage | NOT OBSERVED |
| Market-to-Limit + IOC | Allowed | Not addressed | No such order type/IOC parameter found | NOT OBSERVED |
| Resting limit partial fills | Tick slippage/rule costs apply | Documented | Tick-volume cap, 100-share floor, residual book state | NOT OBSERVED |
| Immediate limit fill | Limit is allowed | Prior behavior retained, now volume capped | Immediate quote path present | NOT OBSERVED |
| EOD residual | No overnight pending state in team model | Cancel remainder at close | New daily simulator has empty in-memory book | NOT OBSERVED |
| Same-symbol buys | No explicit organizer permission identified | A single order's pieces merge into one lot | Separate orders create separate lots | NOT OBSERVED; permission unconfirmed |
| Board lot | Competition execution follows exchange rules | Tick quantities rounded to 100 for partial fills | Order validation requires multiples of 100 | NOT OBSERVED |
| Long-only / sell-only-held | Required | Not a new 0.2.6 change | Sell validation checks holdings; no explicit positive-quantity guard identified | NOT OBSERVED |
| Commission / VAT | 0.157% + 7% VAT on commission | Unchanged | Constants unchanged | NOT OBSERVED |
| Slippage | One tick by team rules | Market-order behavior unchanged | Market price-bucket increment remains; limit matching uses separate limit logic | NOT OBSERVED |

The competition briefing PDFs are not present in this workspace. `AGENTS.md`
records the team's supplied rule summary, while the simulator API mismatch is a
source observation. Do not treat Market order smoke results as competition
compliant.

## Current runtime and official-data verification (2026-10-22)

Older runtime-blocked statements above are historical and superseded. Exact Python 3.13.0 and the TradeSim 0.2.6 requirements/import checks pass. Official `Daily_Ticks.zip` is inventoried and integrated as an explicitly selected source. One-day and multi-day no-order simulations, a multi-fill limit order, and EOD cancellation were observed in the isolated official simulator. The official example strategy's Market orders are not competition-compliant; the smoke fixtures use valid limit orders and make no external broker calls.

The official tick and history inventories, and quantified Settrade comparisons, are in `reports/tradesim_official_tick_inventory.json`, `reports/tradesim_official_history_inventory.json`, and `reports/tradesim_vs_settrade_data_comparison.json`. Practice data and official data have disjoint dates (practice through 2026-09-30, official ticks from 2026-10-01), classified as extended history. Source roles and the no-cross-source-fill policy are recorded in the comparison report.

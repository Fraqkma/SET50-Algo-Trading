# Backtest Execution Assumptions Requiring Approval

AGENTS.md fixes the competition-compatible order vocabulary (`LIMIT` and `MARKET_TO_LIMIT` with `IOC`), commission `0.157%`, VAT `7%` of commission, and one-tick slippage. It does not specify the historical bar fill model or the SET price-to-tick-size mapping. The Backtest harness therefore makes these items explicit instead of hiding them.

## Current harness policy

`src.backtest.engine.ExecutionPolicy` is an explicit policy object. The engine also records `SelectionEvent`, `OrderEvent`, and `PortfolioSnapshot` records for audit; snapshots expose valuation gaps rather than forward-filling a held symbol:

`BacktestEngine` defaults to Design A (the reference benchmark). Pass `design="C"` explicitly to use the approved Top N = 10 cross-sectional selector.

- order type: `LIMIT`
- validity: `IOC`
- signal at `t`: execution is scheduled at the next observed trading row
- requested buy price: next-session `Open + one tick`
- requested sell price: next-session `Open - one tick`
- fill: requested price must lie inside that session's observed `[Low, High]`
- otherwise: record `NON_FILL` with a reason and leave the portfolio unchanged for that order
- `tick_size` must be supplied by the caller; no mapping is guessed

This is conservative and competition-compatible as a research model, but the fill rule and tick mapping are still assumptions, not claims about actual exchange execution.

## Human approval still required

Choose one:

1. Approve the current LIMIT/IOC next-open adverse-tick and bar-range fill model.
2. Approve a documented `MARKET_TO_LIMIT`/IOC model with explicit requested-price and non-fill rules.
3. Provide an official competition fill and tick-size specification to replace the research assumption.

Until this is approved, the harness can be tested with an injected deterministic policy but production-data Backtest results should not be treated as final evidence.

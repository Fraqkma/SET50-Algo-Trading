# Strategy Implementation Decisions Still Requiring Approval

Design A is the simple reference: apply `momentum_20 > 0` and `Close > sma_20` per stock. Design C is limited to ranking only those passing symbols by `momentum_20`. The implementation now has a deterministic three-observed-trading-row schedule and a strict next-session helper, but the following backtest decisions remain open.

## Exact Top N — approved

- **Fixed small N** (for example 3 or 5): simple and predictable; may concentrate risk and can be arbitrary.
- **Larger fixed N**: more diversified; may dilute the strongest signals and increase orders.
- **Percentile/variable count**: adapts to the number of candidates; makes exposure and turnover less predictable.

Approved value: fixed `Top N = 10` for Design C.

## Fewer than N candidates — approved

- **Hold all available candidates**: preserves the approved signal and avoids inventing assets; exposure varies.
- **Hold cash for unused slots**: conservative and auditable; may leave substantial capital idle.
- **Reject the rebalance**: keeps the previous portfolio; introduces path dependence and requires holding rules.

Approved behavior: hold all available qualifying candidates and leave unused allocation as cash.

## Position sizing — approved

- **Equal weight**: easiest to audit; ignores volatility and price/liquidity differences.
- **Fixed share quantity**: simple operationally; produces unequal risk and value exposure.
- **Volatility-scaled sizing**: can balance risk; adds assumptions and depends on the quality of `volatility_20`.

Approved rule: equal weight across selected candidates. The Backtest must also enforce cash, long-only, position limits, commission, VAT, and tick slippage.

## Holding and rebalance behavior — approved

Approved schedule: every 3 observed trading rows, anchored at the first row of the research calendar. Approved holding behavior is full replacement: exit symbols no longer selected, enter newly selected symbols, and rebalance weights for selected symbols. The first observation does not trade; normal signal-to-next-session timing applies.

Options considered at each rebalance:

- **Full replacement**: exit names no longer selected and enter the new Top N; clear but potentially high turnover.
- **Hold-until-exit**: keep existing positions unless their Design A filter fails; lower turnover but portfolio can differ from current ranking.
- **Hybrid persistence rule**: require a name to remain outside selection for a specified number of rebalances; lower churn but adds a parameter.

These options are retained as research context; the approved rule is full replacement and no immediate initial trade.

## Execution/order assumptions

- **Next observed session at an allowed limit order**: respects signal timing; requires a documented limit/fill rule.
- **Next observed session using Market-to-Limit IOC**: competition-compatible; requires explicit non-fill handling.
- **Close-to-next-close simulation**: easy to calculate but must not imply execution at a price known only after the signal.

The only fixed policy is that a signal at `t` cannot execute before the next observed trading row. Order type, requested price, fill, and non-fill behavior remain open.

## Evaluation metrics

At minimum, the Backtest should report gross/net return, final equity, volatility, drawdown, turnover, commission, VAT, total fees, trade count, and `unique_symbols_traded`. Human approval is still required for the primary comparison metric, research date range, and minimum acceptance criteria. Performance must not be judged on return alone.

## Current implementation boundary

`BaselineStrategy`, `rank_time_series_candidates`, `rebalance_dates`, and `next_trading_session` remain reusable signal/schedule components. `BacktestEngine` now provides the first event-ordered harness with equal-weight accounting and explicit `ExecutionPolicy`; it does not claim that the historical fill/tick assumptions are official until `docs/BACKTEST_EXECUTION_DECISIONS.md` is approved. Raw data and eligibility policies are unchanged.

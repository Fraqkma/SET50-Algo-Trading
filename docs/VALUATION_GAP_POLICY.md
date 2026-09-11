# Backtest Valuation-Gap Policy (Option A)

The research backtest does not repair incomplete market data. When a held symbol
has no valid OHLC row on an observation date, the engine records an
`INCOMPLETE` valuation snapshot. The missing symbol and the deterministic reason
`NO_VALID_VALUATION_ROW` are retained; the position and cash are not deleted,
forward-filled, or otherwise changed.

On an incomplete snapshot, `market_value` is only the sum of holdings that can be
valued from an exact valid row. It is not a total portfolio value, and `equity`,
returns, and drawdown are reported as unavailable (`null`/`None`). Therefore an
incomplete observation cannot create an artificial price or an artificial jump
in performance.

For the first Design A run, performance metrics that require a complete equity
series (final equity/returns, volatility, and maximum drawdown) are unavailable
when the run contains incomplete snapshots. Accounting metrics derived directly
from executed fills—cash, positions, fees, slippage, turnover, and trade counts—
remain auditable. The final cash balance and unvalued position quantities are
reported separately.

BGRIM and CENTEL demonstrate the policy: their raw files have coverage, but
historical SET50 membership ends before the later research dates. A next-session
exit can therefore be rejected by the eligibility gate. The engine preserves the
position and exposes the resulting incomplete valuation instead of inventing a
post-membership price.

Downstream research must check `valuation_complete` (and each snapshot's
`valuation_status`) before comparing performance. A run with incomplete
valuation is not a complete return series and must not be used as if its final
equity were known.

## Historical-universe boundary exits

The engine now checks the active membership end date for every held position on
each observed date. On that final eligible session it creates an explicit
`UNIVERSE_BOUNDARY_EXIT` SELL using the same LIMIT/IOC, one-tick adverse price,
and `[Low, High]` fill rule as ordinary execution. The event records the
membership end date and may be `FILLED` or an explicit
`UNIVERSE_BOUNDARY_EXIT_IOC_LIMIT_NOT_FILLED`.

This is not a normal strategy signal: the historical membership boundary is an
approved universe constraint already present in the research data. It does not
use a future market price or post-membership observation. A failed IOC attempt
is recorded once and the position is not silently retried or replaced; any
remaining quantity stays explicitly auditable and cannot be valued after the
boundary.

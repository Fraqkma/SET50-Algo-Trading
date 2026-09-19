# Settrade Research Integration

Settrade expands diagnostics, but does not justify a new alpha strategy or a
survivorship-safe pre-2023 backtest.

Safe future experiments:

1. Compare hypothetical next-session orders with best bid/ask and ten-level
   depth.
2. Estimate spread cost and plausible LIMIT/IOC fill probability by symbol,
   session phase, and order size.
3. Test whether the one-tick adverse assumption is conservative for liquid
   names and insufficient for wide-spread names.
4. Compare daily/bar-based fills with quote-path fills without changing the
   production backtester.
5. Measure opening, midday, and closing liquidity and volume timing.
6. Validate recent Settrade/Yahoo discrepancies before source promotion.

These remain diagnostic experiments. They must preserve chronology, avoid
lookahead, retain source adjustment policies, and stay outside the approved
manifest until reviewed.

Remaining blockers:

- Historical SET50 membership and effective dates are not exposed by the SDK.
- Delisted/renamed identity and corporate-action coverage are not established.
- Settrade history before the bounded December 2023 observation is not
  established.
- A quote/depth event is not an order fill; execution validation needs a
  designed event-path study.
- Continuous collection requires a human licensing/retention decision.

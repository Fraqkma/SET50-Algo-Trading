# Settrade execution research framework

The research-only package under `src/research/execution/` implements diagnostics for spread, midpoint, one-tick cost, depth totals, depth-weighted book-sweep VWAP, IOC fill plausibility, and daily-vs-book classification. It does not alter `src/backtest/engine.py`, submit orders, or promote observations into production assumptions.

`MODEL_V1` remains the current backtest model: next-session LIMIT/IOC behavior, one adverse tick, daily High/Low fill condition, competition fees, and cash constraints. The observed-book model is diagnostic only. It cannot model queue priority, hidden liquidity, latency, cancellations, timestamp mismatch, or auction matching.

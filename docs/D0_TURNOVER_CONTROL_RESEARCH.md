# D0 Turnover-Control Diagnostic

This is an isolated diagnostic of a fixed persistence rule. Design A, Design C,
the production backtest engine, approved manifest, and raw data are unchanged.

## Rules

- Design-A qualification: `momentum_20 > 0` and `close > SMA20`.
- Entry requires two consecutive observed qualifying rows.
- Exit requires two consecutive observed failing rows.
- Existing holdings are retained; there is no ranking replacement or resizing.
- Maximum ten positions; equal slot sizing and deterministic symbol tie-break.
- The replay evaluates every observed row and never fabricates sessions.

## Result status

The runner completed a deterministic qualification-state replay over the
approved 2023-01-03–2026-09-04 data (13,500 symbol/date observations). It writes
signal-churn and diagnostic files under `reports/`.

The repository's production `BacktestEngine` deliberately accepts only Design A
and Design C. No D0 adapter was added to that engine, so a fee/slippage-aware
execution comparison and fold-level D0 walk-forward result are **not reported**.
The walk-forward output is marked `NOT_RUN`, and this diagnostic must not be
interpreted as evidence that D0 improves performance.

## Decision

Classification: `DIAGNOSTIC_ONLY`. A human must approve a dedicated, separately
tested D0 execution adapter before any A-vs-D0 cost or performance conclusion.

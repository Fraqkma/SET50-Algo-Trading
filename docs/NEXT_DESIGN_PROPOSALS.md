# Next design proposals (approval required)

These are hypotheses only. They have not been implemented, backtested, or
selected from a parameter search. Existing Design A and Design C remain
unchanged.

## D1 — fixed trend-confirmed momentum

Use the existing candidate universe and execution rules, but require the
already-defined long/short moving-average trend confirmation before ranking by
the pre-specified momentum feature. Any exact feature window and schedule must
be approved before implementation. Purpose: test whether the observed losses
are associated with momentum signals operating against trend.

## D2 — fixed volatility/liquidity diagnostic design

Use one pre-specified volatility/liquidity eligibility rule and the existing
selection/execution mechanics. No threshold may be chosen from realized return.
Purpose: test whether turnover, fills, and costs explain the A/C gap.

## Evidence update (diagnostics only)

The approved-data diagnostics found a large cost burden: Design A gross return
is -58.94% versus net -71.19%; Design C's corresponding values are -58.87%
and -72.05%. Fees plus slippage account for roughly 59.9% of starting capital
in A and 60.1% in C. C has fewer fills (1,299 vs 1,363) but slightly higher
turnover (731.0m vs 729.0m), so lower fill count did not reduce costs.

Pooled descriptive feature correlations with same-day returns were positive for
momentum_20 (about 0.21), momentum_60 (0.12), and momentum_120 (0.09), while
SMA20>SMA50 was near zero and volume ratio was near zero. Five-day forward means
were negative in aggregate. These are not causal or out-of-sample evidence.

Human approval is required for one design, its parameters, and an OOS protocol
before any implementation. No design is promoted by this document.

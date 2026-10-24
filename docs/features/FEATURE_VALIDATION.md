# SET50 Feature Layer Validation

**Status:** `READY_FOR_NEXT_PHASE`  
**Phase:** 5.5 Feature Validation  
**Protocol gate:** `LOCKED`  
**Scope:** Correctness and research-governance validation of the implemented
feature layer  
**Boundary:** No alpha research, signal, strategy, backtest, optimization, ML,
portfolio construction, or execution logic was performed.

## Validation Scope

The validation covered the eight specified features:

- `daily_return`
- `momentum_20`
- `sma_20`
- `sma_50`
- `trend_20_50`
- `volatility_20`
- `volume_sma_20`
- `volume_ratio_20`

Deterministic synthetic fixtures were used only to validate implementation
behavior, not alpha performance.

## Validation Results

| Area | Result | Evidence |
|---|---|---|
| Mathematical definitions | PASS | Formula, rolling length, alignment, and `ddof=0` volatility checks pass. |
| Adjusted Close | PASS | Price features use `Adjusted Close`; fixtures with `Close != Adj Close` detect the selected representation. |
| Raw Volume | PASS | Volume features use reported/raw `Volume` without adjustment. |
| PIT membership | PASS | `FeatureContext` is required; missing or ineligible context fails closed or produces unavailable values. |
| Identity | PASS | Missing identity fails; unresolved and unsupported predecessor/successor relationships produce unavailable values. |
| Timestamps | PASS | `data_timestamp <= feature_timestamp <= information_cutoff` is enforced. |
| Lookahead | PASS | Future-row mutation, future-column rejection, trailing-window, and no-future-fill checks pass. |
| Dataset status | PASS | `USE`, `USE_WITH_FLAG`, `SOURCE_NEEDED`, and `NEEDS_REVIEW` behavior is preserved explicitly. |
| Corporate actions | PASS | Raw action columns are preserved; unavailable action metadata is reported as `UNAVAILABLE`. |
| Target/label separation | PASS | Target, future-return, label, signal, and execution columns are rejected. |
| Warm-up / NaN | PASS | Required initial unavailable periods remain `NaN`; no backfill is performed. |
| Determinism | PASS | Identical inputs produce identical values, metadata, and ordering. |
| Raw-data immutability | PASS | Input DataFrames remain unchanged after feature construction. |
| Feature contract | PASS | Security, PIT, status, timestamp, source, representation, validity, and action metadata are emitted. |

## Test Results

Validation-specific tests:

```text
18 passed, 0 failed
```

Relevant dependent suite:

```text
36 passed, 1 skipped, 0 failed
```

The skipped test is pre-existing. Some broader eligibility/constituent tests
could not start because the environment denied access to
`C:\Users\server\AppData\Local\Temp\pytest-of-server`. This is recorded as
an environmental limitation and was not worked around in production code.

## Governance Check

Validation did not:

- select or modify a strategy or signal;
- run a backtest or evaluate profitability;
- optimize, sweep, or rank parameters;
- perform ML or rank alpha families;
- use future outcomes to change implementation;
- modify the locked Research Protocol;
- modify raw OHLCV, historical universe data, or ticker mappings.

The values `20` and `50` remain implementation defaults only.

## Final Validation Status

```text
READY_FOR_NEXT_PHASE
```

Next phase: Alpha Research / Signal Design according to the repository's
documented research sequence.

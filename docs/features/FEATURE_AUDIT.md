# Existing Feature Implementation Audit

**Status:** `READY_FOR_FEATURE_SPECIFICATION`  
**Phase:** 5.2 Existing Feature Audit  
**Protocol gate:** `LOCKED`  
**Audit boundary:** Read-only audit. Existing implementation was not modified;
no new feature, signal, strategy, backtest, optimization, ML model, portfolio,
or execution logic was created.

## 1. Scope

This audit compares the existing feature implementation with:

- `docs/research_foundation/SET50_RESEARCH_PROTOCOL.md`;
- `docs/features/FEATURE_ARCHITECTURE.md`;
- `docs/research_foundation/SET50_ALPHA_RESEARCH.md`;
- `docs/set50_parameter_research.md`.

Inspected source and tests:

- `src/data/features.py`;
- `src/data/research.py`;
- `src/data/eligibility.py`;
- `src/data/validator.py`;
- `src/data/constituents.py`;
- `tests/test_features.py`.

`src/data/features.py` imports only pandas and has no hidden feature-related
module dependency. The approved-data and eligibility modules were inspected to
determine whether the existing feature function itself consumes their controls.

## 2. Protocol Gate

The Research Protocol is `LOCKED`. The audit may record gaps and proposed
remediation, but it must not silently change the protocol or implementation.

## 3. Existing Feature Inventory

The existing function is `src.data.features.build_features`. It accepts one
DataFrame for one symbol and returns a copy containing the original columns plus
the following eight calculated feature columns:

| Feature | Alpha family | Inputs | Concept | Warm-up | Output |
|---|---|---|---|---|---|
| `daily_return` | Momentum / Trend; descriptive input for other families | `close` or `adj_close` | `close[t] / close[t-1] - 1` | First row `NaN` | Float series |
| `momentum_20` | Momentum / Trend | selected close column | `close[t] / close[t-20] - 1` | 20 prior observations | Float series |
| `sma_20` | Momentum / Trend | selected close column | Trailing 20-observation mean including `t` | 20 observations | Float series |
| `sma_50` | Momentum / Trend | selected close column | Trailing 50-observation mean including `t` | 50 observations | Float series |
| `trend_20_50` | Momentum / Trend | `sma_20`, `sma_50` | `sma_20 / sma_50 - 1` | 50 observations | Float series |
| `volatility_20` | Volatility-related | `daily_return` | Population std. dev. (`ddof=0`) over trailing 20 returns | First 20 returns | Float series |
| `volume_sma_20` | Volume / Liquidity | `volume` when present | Trailing 20-observation volume mean | 20 observations | Float series |
| `volume_ratio_20` | Volume / Liquidity | `volume`, `volume_sma_20` | `volume[t] / volume_sma_20[t]` | 20 observations | Float series |

No implementation was found for a mean-reversion-specific feature or an
industry/relative-strength feature. The existing function does not perform
cross-sectional ranking, normalization, percentile calculation, sector joins,
or PIT-universe comparison.

## 4. Protocol Alignment

Statuses are alignment findings, not performance rankings.

| Feature group | Status | Reason |
|---|---|---|
| `daily_return`, `momentum_20`, `sma_20`, `sma_50`, `trend_20_50` | `PARTIALLY_ALIGNED` | Causal trailing calculations are consistent with descriptive momentum/trend concepts, but PIT context, metadata, price representation, and protocol parameter declaration are not carried by the function. |
| `volatility_20` | `PARTIALLY_ALIGNED` | Uses a trailing return dispersion measure without an evident future window, but adjustment semantics, PIT context, status propagation, and metadata are unspecified. |
| `volume_sma_20`, `volume_ratio_20` | `PARTIALLY_ALIGNED` | Uses observed volume and does not fabricate missing volume, but does not establish trading-value provenance, source status, PIT context, or execution interpretation. |
| Mean Reversion / Reversal | `UNSUPPORTED` | No dedicated implemented feature was found. Existing return/trend columns must not be interpreted as a reversal feature without a specification. |
| Industry / Relative Strength | `UNSUPPORTED` | No sector/industry input or cross-sectional implementation was found. |

No existing feature is marked `ALIGNED` because the function-level contract does
not establish all locked requirements, particularly PIT membership, identity,
source status, timestamp metadata, and price representation.

## 5. Lookahead Audit

### Findings from actual implementation

- No `shift` toward future observations is used.
- No centered rolling window is used.
- `pct_change`, `rolling(...).mean()`, and `rolling(...).std()` operate on the
  current row and prior rows after chronological sorting.
- The future-row mutation test in `tests/test_features.py` confirms that earlier
  feature rows do not change when the final close is changed.
- No future join, future membership lookup, future sector classification, or
  target/label column is referenced by `build_features`.
- No forward-fill or interpolation is explicitly requested by the function.
- Missing close/volume values raise an error rather than being fabricated.

### Remaining lookahead limitations

- The function accepts a generic DataFrame and does not require an explicit
  `information_cutoff` or source publication timestamp.
- It sorts an unsorted index rather than rejecting it, so chronological
  availability semantics are not independently asserted at the feature API.
- It does not reject arbitrary extra input columns that could include a target;
  calculations do not reference them, but the contract does not explicitly
  prohibit target-bearing frames.

**Lookahead finding:** `PARTIALLY_ALIGNED`; the arithmetic is causal for the
selected columns, but the feature API does not encode the complete timestamp
contract.

## 6. Timestamp Audit

| Timestamp requirement | Existing behavior | Status |
|---|---|---|
| `data_timestamp` | Derived from a Date column or DataFrame index; not returned as metadata. | `NEEDS_REVIEW` |
| `feature_timestamp` | Implicitly the sorted index row `t`; not declared in output metadata. | `NEEDS_REVIEW` |
| `information_cutoff` | Not accepted or recorded. | `NEEDS_REVIEW` |
| Signal/execution/label timestamps | Not used by the feature function, which is appropriate for separation. | `PARTIALLY_ALIGNED` |

The arithmetic can answer “which rows were used?” for simple trailing columns,
but the returned frame cannot independently document the source timestamp,
information cutoff, adjustment status, or historical availability at `t`.

## 7. PIT Audit

`build_features` receives only a single DataFrame and has no membership,
effective-from/effective-to, eligibility, suspension, source-gap, or identity
argument. It does not call `load_approved_market_data` or
`MarketDataEligibilityGate`.

The repository has those controls in `src/data/research.py` and
`src/data/eligibility.py`, but their existence does not prove that every caller
of `build_features` used them. The feature function itself therefore cannot
establish:

- historical additions and removals;
- suspension handling;
- unresolved source periods;
- predecessor/successor identity boundaries;
- point-in-time SET50 membership.

**PIT status:** `NEEDS_REVIEW`. The existing function must only be used after an
approved, date-filtered input has been established by the research-data path.
No current-constituent assumption was found inside the function itself.

## 8. Cross-sectional Audit

No ranking, normalization, percentile, z-score, relative comparison, or sector
join exists in `build_features`. Therefore there is no implemented
cross-sectional future-universe calculation to validate.

Cross-sectional protocol requirements remain unimplemented and must be handled
in a future feature specification using the PIT universe at a common timestamp.

**Status:** `UNSUPPORTED` for cross-sectional and industry/relative-strength
features; no conclusion about their research validity is made.

## 9. Data-Quality Audit

Observed behavior:

- `None` input raises `ValueError`.
- Duplicate dates raise `ValueError`.
- Close missing/non-numeric values raise `ValueError`.
- Volume missing/non-numeric values raise `ValueError` when volume is present.
- Warm-up periods remain `NaN`; they are not filled or interpolated.
- Input is deep-copied before transformation.
- No explicit finite-value, OHLC consistency, source status, or identity-status
  validation is performed in `build_features`.
- The function does not understand `USE`, `USE_WITH_FLAG`, `SOURCE_NEEDED`, or
  `NEEDS_REVIEW` statuses.
- It does not itself detect source gaps, suspensions, or price-limit conditions.

**Status:** `PARTIALLY_ALIGNED`. The no-fabrication behavior is positive, but
status propagation and non-finite/source-quality handling require a future
specification.

## 10. Raw Data Immutability

The implementation creates `dataframe.copy(deep=True)` and writes calculated
columns to that copy. Existing tests verify that the input frame is not changed
by the tested operations and that missing/duplicate input is not silently
repaired.

The function does not write files or modify historical universe/ticker mapping
artifacts. This audit found no raw-data mutation in the inspected feature code.

**Status:** `ALIGNED` for local input immutability, subject to callers not
passing a previously mutated shared object and subject to future tests covering
all supported input dtypes.

## 11. Corporate Action Audit

The function chooses `close`, then `adj_close`, then `adjusted_close` after
lower-casing column names. It does not record which representation was selected,
whether it came from Yahoo adjustment semantics, or whether OHLC fields are
consistent with that representation.

Consequences:

- raw versus adjusted price use is implicit rather than declared;
- the same feature name can represent different price semantics across inputs;
- no corporate-action-aware identity metadata is carried forward.

**Status:** `NEEDS_REVIEW`. A future feature specification must declare the
required price representation and adjustment provenance per feature family.

## 12. Test Coverage

`tests/test_features.py` currently covers:

- causal behavior when the final future row is changed;
- rolling warm-up `NaN` behavior;
- missing close rejection;
- duplicate-date rejection;
- volume feature calculation without filling;
- deterministic baseline-signal behavior using the existing strategy layer;
- rejection of unfeatured baseline input.

Current test gaps:

- explicit `data_timestamp`, `feature_timestamp`, and `information_cutoff`;
- PIT membership additions/removals and future-membership rejection;
- suspension and source-gap status handling;
- `USE_WITH_FLAG`, `SOURCE_NEEDED`, and `NEEDS_REVIEW` propagation;
- identity boundaries and predecessor/successor non-merging;
- infinite values and non-finite output;
- cross-sectional PIT behavior;
- raw/adjusted/corporate-action representation metadata;
- target/label-column rejection or explicit input schema;
- deterministic behavior across the full feature contract.

No tests were added in this audit phase.

## 13. Parameter Audit

Current defaults are:

```text
momentum_window = 20
short_window = 20
long_window = 50
volatility_window = 20
volume_window = 20
```

The 20/50 trend and 20-day momentum/volatility values overlap candidate ranges
in `docs/set50_parameter_research.md`, but that document defines candidate
ranges, not a pre-registered best value. The volume lookback is not established
there as an optimal value.

Because the existing function does not record a research experiment ID,
pre-registration reference, or parameter selection provenance, all current
lookbacks are marked:

`PARAMETER_REVIEW_REQUIRED`

This is an audit finding, not a recommendation to change them and not an
optimization result.

## 14. Findings

1. The existing implementation provides eight single-symbol descriptive
   columns and has no mean-reversion or industry feature implementation.
2. The arithmetic is trailing and causal for the columns it reads; no direct
   future shift, centered rolling window, or future join was found.
3. PIT membership, identity, source status, suspension, and information-cutoff
   metadata are not enforced by `build_features` itself.
4. Price representation and corporate-action semantics are inferred from input
   column names and are not recorded in feature metadata.
5. The existing tests provide useful causal, warm-up, duplicate, missing-input,
   and immutability evidence, but do not cover the locked PIT/identity/status
   contract.
6. Current lookbacks require provenance review before being treated as
   pre-registered research choices.

## 15. Required Changes Before Feature Specification / Implementation

No remediation was applied in Phase 5.2. Before implementation, the next
specification should decide and document:

- how the feature entry point receives approved PIT data and identity context;
- how `data_timestamp`, `feature_timestamp`, and `information_cutoff` are
  represented and validated;
- how source statuses and missingness propagate to feature outputs;
- which raw/adjusted/corporate-action representation each feature requires;
- how non-finite values, source gaps, suspensions, and identity boundaries are
  handled;
- how current parameter choices are declared or labeled research-derived;
- which tests will enforce PIT, timestamp, status, identity, and metadata rules.

These are proposed remediation items only. They must not be implemented by
silently changing this audit or the locked protocol.

## 16. Explicit Non-Claims

This audit does not claim that any existing feature:

- has predictive power;
- has positive alpha;
- is profitable;
- is a strategy;
- passed a backtest;
- is robust;
- is production-ready.

## Audit Boundary Statement

Existing features were audited only. No source implementation, raw data,
historical universe, ticker mapping, Research Protocol, signal, strategy,
backtest, optimization, ML model, portfolio construction, or execution logic
was modified or created.

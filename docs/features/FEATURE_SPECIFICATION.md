# SET50 Feature Specification

**Status:** `READY_FOR_FEATURE_IMPLEMENTATION`  
**Phase:** 5.3 Feature Specification  
**Protocol gate:** `LOCKED`  
**Feature audit gate:** `READY_FOR_FEATURE_SPECIFICATION`  
**Boundary:** Specification only. No feature calculation, feature values,
signal, strategy, backtest, optimization, ML, portfolio construction, or
execution logic is created or changed here.

## 1. Purpose

This document defines the contract for a future feature layer:

```text
Research Data
    -> PIT Context
    -> Feature Calculation
    -> Validated Feature Output
```

It documents the eight existing feature columns and the requirements that a
future implementation must satisfy. It does not claim predictive power,
positive alpha, profitability, or strategy readiness.

## 2. Gates and Evidence

- Research Protocol: `LOCKED`.
- Existing Feature Audit: `READY_FOR_FEATURE_SPECIFICATION`.
- Current implementation audited: `src/data/features.py`.
- Approved research-data boundary: `src/data/research.py` and
  `src/data/eligibility.py`.
- Validation authority: `src/data/validator.py`.
- Parameter reference: `docs/set50_parameter_research.md`, which defines
  candidate ranges only and does not define optimal values.

The audit found causal arithmetic for the existing single-symbol features, but
also found unresolved PIT, timestamp metadata, source-status, identity, and
price-representation requirements. Those issues remain explicit below.

## 3. Existing Feature Specification

The following table is the complete current feature inventory. It does not
include original input columns returned unchanged by the existing function.

| Feature | Alpha family | Conceptual definition | Input data | Required history | Parameter status | Feature status |
|---|---|---|---|---|---|---|
| `daily_return` | Momentum / Trend; descriptive input | `adjusted_close[t] / adjusted_close[t-1] - 1` | Adjusted Close | One prior observation | No research parameter; representation is resolved | `SPECIFIED` |
| `momentum_20` | Momentum / Trend | `adjusted_close[t] / adjusted_close[t-20] - 1` | Adjusted Close | 20 prior observations | Implementation default only; not optimal or validated | `SPECIFIED` |
| `sma_20` | Momentum / Trend | Mean of Adjusted Close over 20 observations including `t` | Adjusted Close | 20 observations including `t` | Implementation default only; not optimal or validated | `SPECIFIED` |
| `sma_50` | Momentum / Trend | Mean of Adjusted Close over 50 observations including `t` | Adjusted Close | 50 observations including `t` | Implementation default only; not optimal or validated | `SPECIFIED` |
| `trend_20_50` | Momentum / Trend | `sma_20[t] / sma_50[t] - 1` | Adjusted Close | 50 observations | Implementation defaults only; pair is not optimized or endorsed | `SPECIFIED` |
| `volatility_20` | Volatility-related Effects | Population standard deviation (`ddof=0`) of trailing Adjusted-Close returns | Adjusted Close | 20 prior daily returns | Implementation default only; not optimal or validated | `SPECIFIED` |
| `volume_sma_20` | Volume / Liquidity | Mean of reported/raw Volume over 20 observations including `t` | Reported/raw Volume | 20 observations including `t` | Implementation default only; not optimal or validated | `SPECIFIED` |
| `volume_ratio_20` | Volume / Liquidity | `volume[t] / volume_sma_20[t]` | Reported/raw Volume | 20 observations including `t` | Implementation default only; not optimal or validated | `SPECIFIED` |

The statuses identify specification work that must be resolved before feature
implementation. They are not quality or performance rankings.

## 4. Alpha Family Mapping

The current mapping is deliberately limited:

| Family | Existing mapping |
|---|---|
| Momentum / Trend | `daily_return`, `momentum_20`, `sma_20`, `sma_50`, `trend_20_50` |
| Volatility | `volatility_20` |
| Volume / Liquidity | `volume_sma_20`, `volume_ratio_20` |
| Mean Reversion / Short-term Reversal | `UNSPECIFIED / NOT CURRENTLY IMPLEMENTED` |
| Industry / Relative Strength | `UNSPECIFIED / NOT CURRENTLY IMPLEMENTED` |

The mapping describes possible research use. It does not label any feature as
alpha, signal, ranking, or trading decision.

## 5. Common Feature Contract

Every future output record must expose, directly or through immutable metadata:

| Field | Contract |
|---|---|
| `security_id` | Security identity used for the observation; ticker resemblance is insufficient. |
| `timestamp` | Observation timestamp for the feature row. |
| `feature_name` | Stable descriptive feature name; no buy/sell or strategy wording. |
| `feature_value` | Numeric value or explicit missing value. |
| `data_timestamp` | Source observation timestamp(s) used in the calculation. |
| `feature_timestamp` | Time at which the feature becomes available. |
| `information_cutoff` | Latest information permitted for the feature. |
| `pit_membership` | Membership/eligibility context effective at the feature timestamp. |
| `data_status` | `USE`, `USE_WITH_FLAG`, `SOURCE_NEEDED`, `NEEDS_REVIEW`, or documented equivalent. |
| `validity_status` | Result of schema, numeric, timestamp, and identity validation. |
| `identity_status` | Security identity and boundary status from the audit. |
| `source_data` | Input columns, source file/version, and representation provenance. |

The contract must answer: “At time `t`, what data and status were used to create
this value?” The current `build_features()` return frame does not yet carry all
of this metadata; that is an implementation requirement, not a change made here.

## 6. PIT Universe and Eligibility Contract

Feature calculation must receive an explicit point-in-time SET50 universe or an
approved eligibility context. Current constituents must not be used as a
historical default.

Required behavior:

- **Historical additions:** eligible only from the evidenced effective date.
- **Historical removals:** eligible only through the evidenced effective date.
- **Suspensions/price limits:** preserve supported status and do not infer a
  tradable fill from a daily bar.
- **Identity boundaries:** keep predecessor and successor securities separate
  unless an explicit evidence-based policy exists.
- **Source gaps:** exclude, flag, or retain descriptive only according to a
  declared experiment rule; never fabricate history.

The approved research path must be established before calculation. A feature
function must receive or be preceded by an explicit PIT eligibility and identity
context; it must not reconstruct membership, merge identities, or silently
bypass `MarketDataEligibilityGate`.

**Human decision recorded:** historical membership is never reconstructed from
current constituents, and identity mapping remains governed by the Dataset Gate
and identity audit. The existing `build_features()` function does not enforce
this by itself; implementation must add the contract without changing those
authorities.

## 7. Data-Status Contract

| Status | Calculate? | Required output behavior |
|---|---|---|
| `USE` | Yes, if all other contracts pass | Emit value with normal validity metadata. |
| `USE_WITH_FLAG` | Only when the future experiment explicitly permits flagged data | Emit value with the original flag preserved; do not silently treat it as clean. |
| `SOURCE_NEEDED` | No | Emit no usable feature value; retain an explicit source-needed/unavailable status. |
| `NEEDS_REVIEW` | No until resolved or explicitly approved for a declared descriptive use | Retain review status or exclude; never silently promote. |

Missing data, source gaps, and identity uncertainty cannot be repaired by
forward-fill, interpolation, future backfill, or guessed values. An absent
volume field must not be converted into a liquidity feature.

## 8. Timestamp Specification

The required relationship is:

```text
data_timestamp
    -> feature_timestamp
    -> information_cutoff
    -> later signal/execution consumer
    -> future label
```

For daily OHLCV, the default rule is to use a completed bar at `t`, make the
feature available only after the declared information cutoff for that bar, and
leave execution and future labels to later layers. The repository does not
provide a more precise universal publication/fill timestamp, so no such detail
is assumed here.

The following are prohibited:

- future return, high, low, or close;
- centered rolling windows or future-directed shifts;
- future membership or sector classification;
- future source status or corporate-action knowledge;
- target/label columns as feature inputs;
- full-period normalization using future observations.

**Human decision recorded:** use completed daily bars and preserve
`data_timestamp -> feature_timestamp -> information_cutoff -> future
label_timestamp`. A future implementation must validate these fields before
emitting a usable feature record. No exact exchange publication/fill clock is
assumed; this limitation is explicit and does not block the daily contract.

## 9. Feature-specific Missing and Warm-up Rules

Insufficient history produces `NaN`/not-ready status rather than a fabricated
value. The required minimums are:

| Feature | Warm-up rule | Validation behavior |
|---|---|---|
| `daily_return` | First observation has no prior close and remains `NaN`. | Confirm no fill and correct prior-row dependency. |
| `momentum_20` | First valid value requires 20 prior closes. | Confirm row `t` never uses a close after `t`. |
| `sma_20` | First valid value requires 20 closes including `t`. | Confirm trailing, right-aligned window. |
| `sma_50` | First valid value requires 50 closes including `t`. | Confirm trailing, right-aligned window. |
| `trend_20_50` | First valid value requires both moving averages; currently 50 closes. | Confirm no division by unavailable warm-up values. |
| `volatility_20` | First valid value requires 20 prior daily returns. | Confirm return warm-up and `ddof=0` concept. |
| `volume_sma_20` | First valid value requires 20 volumes including `t`. | Confirm missing volume is not filled. |
| `volume_ratio_20` | First valid value requires valid `volume_sma_20` and current volume. | Confirm no divide-by-missing or fabricated denominator. |

Non-finite values must be marked invalid or missing under the future validation
contract. Rows must not be dropped solely to make output look complete.

## 10. Price Representation and Corporate Actions

Price-consuming features must declare whether they require raw price, adjusted
price, or another corporate-action-aware representation. The current repository
implementation selects a close-like column by input name but does not record the
representation or adjustment provenance.

**Human decision recorded:** all price-based return/trend/volatility features
use Adjusted Close as the research price representation. Raw OHLCV remains
immutable and must not be repaired or overwritten. Raw Close and Adjusted Close
must not be silently mixed within one feature definition.

Repository evidence does establish the current input behavior: the acquisition
path requests yfinance with `auto_adjust=False`, preserves raw OHLCV and
`Adj Close`, and `src/data/features.py` prefers `Close` before adjusted-close
column names. This describes the existing implementation; it is not evidence
that raw close is the approved research representation for every feature.

This is a governance representation choice, not a claim that Adjusted Close is
universally superior or more predictive.

Downstream impact:

- return, moving-average, trend, and volatility values can change with price
  adjustment semantics;
- corporate actions can create discontinuities or alter comparability;
- feature metadata must preserve source and adjustment status;
- identity continuity is not solved by an adjusted price series alone.

## 11. Volume / Liquidity Contract

For `volume_sma_20` and `volume_ratio_20`:

- input is reported/raw `volume` only;
- window is the existing implementation default of 20 observations; it is not
  an optimal or validated research parameter;
- calculation uses data available by the information cutoff;
- missing/non-numeric volume is not fabricated or forward-filled;
- `USE_WITH_FLAG` status is preserved;
- `SOURCE_NEEDED` and `NEEDS_REVIEW` do not produce a clean feature value;
- PIT membership and identity context remain mandatory;
- no bid/ask spread, depth, queue, fill probability, or trading value may be
  invented from volume alone.

These features are descriptive volume measures, not liquidity or execution
proof and not trading signals. Volume is not manually adjusted and no spread,
depth, queue, or fill data may be fabricated.

**Human decision recorded:** `USE` calculates normally; `USE_WITH_FLAG`
calculates with the original flag preserved; `SOURCE_NEEDED` and
`NEEDS_REVIEW` remain unavailable/`NaN` until explicitly resolved. The
implementation must map repository gate/readiness statuses explicitly rather
than treating different status vocabularies as interchangeable.

## 12. Cross-sectional Contract

No cross-sectional feature is currently implemented. If a future specification
adds one, it must require:

- the PIT SET50 universe at one common timestamp;
- only eligible securities and available observations;
- no future membership, sector, or normalization statistics;
- same information cutoff for all compared rows;
- explicit missing/flagged/identity handling;
- no conversion of ranking into a trade or portfolio decision.

No ranking, normalization, alpha score, or signal is created in this phase.

## 13. Validation Contract

Future implementation tests must cover every existing feature for:

1. deterministic calculation;
2. exact warm-up behavior;
3. timestamp and information-cutoff metadata;
4. causal behavior and no future data;
5. PIT membership and eligibility;
6. identity boundaries and non-merging;
7. missing/status behavior;
8. raw-data immutability;
9. corporate-action representation semantics;
10. parameter provenance and declared selection status.

Additional leakage tests must explicitly reject future returns/highs/lows/closes,
centered windows, future membership/sector/status, future corporate-action
knowledge, and target/label inputs. Tests are specified here but not written in
Phase 5.3.

## 14. Parameter Governance

The values `20` and `50` are current implementation defaults only. They are not
best parameters, recommendations, optimization results, or locked research
choices.

The parameter categories are:

- **Conceptual parameter:** the lookback idea required by a feature definition.
- **Candidate range:** a range documented in `docs/set50_parameter_research.md`.
- **Pre-registered parameter:** an exact value declared before the relevant
  outcome evaluation.
- **Exploratory parameter:** a value selected or changed after inspecting
  results.

Current exact lookbacks are implementation defaults. They are not declared
optimal, validated research parameters, or optimization results. Future alpha
experiments must declare exact values before outcome evaluation under the locked
Research Protocol. No optimization, grid search, or best-value choice is
permitted in this phase.

Evidence classification for current values:

- `20` and `50` are implementation defaults in `src/data/features.py`;
- they overlap candidate ranges in the parameter research document;
- they are not recorded there as exact pre-registered values;
- no value is classified as best or optimal;
- the defaults may remain for the existing implementation where required, while
  future research parameters require explicit pre-registration.

## 15. Feature Status Vocabulary

Permitted specification statuses include:

- `SPECIFIED` — contract is complete for the intended implementation scope;
- `NEEDS_PARAMETER_REVIEW` — exact lookback provenance is unresolved;
- `NEEDS_TIMESTAMP_REVIEW` — timestamp metadata/cutoff contract is unresolved;
- `NEEDS_PIT_REVIEW` — PIT eligibility is not enforced or evidenced;
- `NEEDS_PRICE_SEMANTICS_REVIEW` — raw/adjusted/action-aware representation is
  unresolved.

The following statuses are prohibited because they make unsupported claims:
`PROFITABLE`, `BEST`, `VALIDATED_ALPHA`, and `WINNER`.

## 16. Open Issues and Recorded Decisions

The human research decisions in Phase 5.3B resolve the governance blockers
without changing the locked Research Protocol:

1. PIT eligibility and identity context are mandatory inputs/context.
2. Completed daily bars and the declared timestamp ordering are mandatory.
3. Adjusted Close is the research representation for price-based features.
4. Reported/raw Volume is the representation for volume features.
5. Dataset statuses are preserved according to the data-status contract.
6. Raw OHLCV remains immutable; unsupported corporate-action corrections and
   predecessor/successor inference are prohibited.
7. Targets and future labels remain outside the Feature Layer.
8. Exact exchange publication/fill time is an explicit limitation, not an
   invented assumption.
9. Existing 20/50 values remain implementation defaults only; future research
   values require pre-registration.

The remaining items are implementation requirements rather than unresolved
governance decisions: carrying the metadata/status fields, enforcing the input
allowlist, and preserving corporate-action/identity metadata in output. They
must be implemented and tested without weakening the protocol.

## Decision Matrix

| Issue | Evidence | Current State | Decision | Status |
|---|---|---|---|---|
| PIT enforcement | Locked protocol, architecture, `src/data/research.py`, and `src/data/eligibility.py` require date-aware approved eligibility; `build_features()` itself accepts only a generic frame. | PIT authority exists upstream, but the feature entry point does not enforce/contextualize it. | Feature Layer must receive or be preceded by explicit PIT eligibility and identity context; implementation remains separate. | `RESOLVED` |
| Timestamp metadata | Locked protocol and architecture define `data_timestamp`, `feature_timestamp`, `information_cutoff`, and completed-bar-to-later-session ordering. | Required fields are not yet emitted by current feature output. | Enforce the fields; exact exchange publication/fill time remains an explicit limitation. | `RESOLVED` |
| Raw vs adjusted price | Acquisition uses `auto_adjust=False`, preserves `Close` and `Adj Close`; existing feature code prefers `Close`. | Existing behavior differs from the new research representation decision. | Use Adjusted Close for price-based features; preserve raw OHLCV unchanged. | `RESOLVED` |
| Source status | Dataset Gate defines `USE`, `USE_WITH_FLAG`, `SOURCE_NEEDED`; readiness code has additional approval statuses. | Mapping is not yet implemented in feature output. | Preserve gate/readiness provenance; only USE/flagged rows can calculate, unresolved rows remain unavailable. | `RESOLVED` |
| Parameter provenance | Parameter research documents candidate ranges only; source defaults are 20/50. | Exact values are not pre-registered research parameters. | Retain defaults only as implementation defaults; declare future experiment values before evaluation. | `RESOLVED` |
| Target/label protection | Current calculation reads close/volume only but accepts a generic DataFrame and returns original columns. | Input allowlist/schema enforcement is not yet implemented. | Keep targets/labels outside the Feature Layer and enforce an allowlist/input contract. | `RESOLVED` |
| Corporate-action metadata | Raw and adjusted fields are preserved by acquisition; feature output currently lacks metadata. | Metadata propagation is not yet implemented. | Preserve available action/identity metadata and expose limitations; never fabricate corrections. | `RESOLVED` |

`RESOLVED` means the human governance decision is recorded in the
specification. It does not mean the source implementation has been changed,
tested, or shown to have predictive or economic value.

## 17. Implementation Boundary

```text
Existing features: SPECIFIED
New features: NOT CREATED
Existing implementation: NOT MODIFIED
Signals: NOT CREATED
Strategies: NOT CREATED
Backtests: NOT RUN
Optimization: NOT PERFORMED
ML: NOT CREATED
Portfolio construction: NOT CREATED
Execution logic: NOT CREATED
```

## Specification Boundary Statement

This document specifies the existing feature contract and records unresolved
implementation decisions. It does not claim predictive power, economic value,
profitability, robustness, production readiness, or human-audit approval.

# SET50 Feature Layer Architecture

**Status:** `READY_FOR_REVIEW`  
**Phase:** 5.1 Feature Architecture Design  
**Protocol gate:** `LOCKED`  
**Boundary:** Design only. No feature calculation, feature dataset, signal,
strategy, backtest, optimization, ML, portfolio construction, or execution
logic is created by this document.

## 1. Purpose

This document defines the architecture and contracts for a future SET50 feature
layer. It provides a controlled boundary between approved research data and
future descriptive feature calculations while preserving the locked Research
Protocol's timing, point-in-time, identity, and data-quality rules.

It does not select an alpha family, rank features, choose parameters, or claim
that any feature is predictive or profitable.

## 2. Repository Findings

The repository already contains relevant components:

| Component | Existing responsibility | Architecture decision |
|---|---|---|
| `src/data/loader.py` | Read CSV/Parquet/Feather or copy an in-memory frame | Reuse as low-level loading utility; it is not the PIT policy boundary. |
| `src/data/research.py` | Read approved market data and apply date-aware eligibility | Use as the research-data entry boundary before future feature work. |
| `src/data/eligibility.py` | Apply membership, mapping, approval, date-range, identity, and known-gap checks | Treat as the PIT/data-eligibility authority; do not bypass it. |
| `src/data/validator.py` | Diagnose OHLCV structure and data-quality issues | Reuse for validation; do not repair or silently fill records. |
| `src/data/constituents.py` | Historical constituent discovery utilities | Use only with an explicitly evidenced historical universe; current constituents are not a default. |
| `src/data/features.py` | Existing pure single-symbol feature transformation | Treat as existing implementation to audit/reconcile later; do not duplicate or expand it in this design phase. |
| `data/features/` | Currently only a placeholder | Reserved for a future validated feature output, subject to a separate implementation decision. |
| `tests/test_features.py` | Existing causal/warm-up/immutability tests | Reuse the testing intent; future architecture tests must also cover PIT and identity boundaries. |

The repository also contains legacy strategy and backtest code. Those layers are
outside this design and must not be imported as feature-layer dependencies.

## 3. Scope and Family Coverage

The architecture must be able to represent descriptive inputs for all five
locked-protocol families without ranking them:

1. Momentum / Trend
2. Mean Reversion / Short-term Reversal
3. Volatility-related Effects
4. Volume / Liquidity
5. Industry / Relative Strength

Family support means that a future feature specification can declare its inputs,
history, timing, identity policy, and status. It does not mean that every family
is currently data-ready. Volume/trading-value and point-in-time sector data may
remain `SOURCE_NEEDED` or `NOT_AVAILABLE`.

## 4. Data Flow

The intended dependency direction is:

```text
Raw source data (read-only)
        |
        v
Validated / approved research data
        |
        v
Point-in-time universe and identity context
        |
        v
Feature layer
        |
        v
Signal layer       (future, separate)
        |
        v
Strategy layer     (future, separate)
        |
        v
Backtest / evaluation (future, separate)
```

The Feature Layer may consume validated data and PIT context. It must not call
brokers, create orders, allocate capital, generate buy/sell decisions, or depend
on future labels.

## 5. Feature Layer Boundary

The future feature layer should have four conceptual responsibilities:

1. **Input contract:** accept an approved, timestamped research frame and its
   PIT/security context.
2. **Descriptive transformation:** calculate only declared values available at
   the feature timestamp.
3. **Quality/status propagation:** preserve missingness, source status, identity
   status, and validation flags rather than hiding them.
4. **Metadata output:** record what the feature means, what data it used, and
   which limitations apply.

It must not contain signal thresholds, ranking-to-trade rules, position sizing,
portfolio weights, stop-loss/take-profit rules, or execution assumptions that
turn a measurement into a trading decision.

## 6. Common Feature Contract

Every future feature record or feature-frame schema must make the following
fields available, either as columns or as an attached immutable metadata object:

| Field | Meaning |
|---|---|
| `feature_name` | Stable descriptive name; never a trading decision name. |
| `security_id` | Security identity used for the observation, not merely a similar ticker. |
| `timestamp` | Feature observation timestamp. |
| `value` | Numeric or explicitly typed descriptive value; missingness remains observable. |
| `source_data` | Source columns/files and provenance used by the calculation. |
| `required_history` | Minimum lookback and the unit of observation. |
| `data_timestamp` | Timestamp(s) of source observations used. |
| `feature_timestamp` | Timestamp at which the feature is available. |
| `information_cutoff` | Latest information permitted for the feature. |
| `pit_membership` | Membership version/effective interval used. |
| `missing_data_status` | Explicit status for NaN, gap, unavailable source, or excluded input. |
| `validity_status` | Validation result such as valid, flagged, source-needed, or needs-review. |
| `identity_status` | Identity continuity/uncertainty status from the audit. |
| `alpha_family` | Related research family, without implying alpha or profitability. |

The contract must answer: “At time `t`, exactly which observations and metadata
were used to calculate this feature?”

## 7. Timestamp Model and Lookahead Protection

The architecture separates:

```text
data_timestamp
feature_timestamp
information_cutoff
signal_timestamp       (future consumer, not a feature input)
execution_timestamp    (future consumer, not a feature input)
label_timestamp        (future outcome, never a feature input)
```

The default daily convention is:

```text
completed bar at t
    -> feature available after the declared cutoff at t
    -> later consumer may create a signal
    -> later permitted session may execute
    -> future label is evaluated afterward
```

Rolling calculations must be trailing and right-aligned. No centered rolling
window, future shift, full-period normalization, future rank, future high/low/
close, or target/label column may enter a feature calculation. Cross-sectional
operations must use only rows eligible at the same point-in-time timestamp.

## 8. Point-in-time Universe and Identity Context

Feature inputs must be restricted to the SET50 membership effective at the
feature timestamp. The context layer must preserve:

- historical additions and removals;
- suspensions and price-limit flags when evidenced;
- unresolved source periods;
- security identity boundaries and predecessor/successor separation;
- source and validation status for each observation.

The current SET50 constituent list must never be the historical default. Ticker
resemblance is not continuity evidence. A future implementation must consume
the existing eligibility and identity authorities rather than reconstructing
membership or merging securities inside a feature function.

## 9. Data-Quality Handling

Feature computation must use explicit statuses rather than silent repair:

| Condition | Required behavior |
|---|---|
| Warm-up history incomplete | Return `NaN`/not-ready with metadata; do not forward-fill. |
| Missing OHLCV input | Preserve/exclude according to the declared feature contract; never fabricate. |
| `USE` | Eligible subject to the approved scope and other checks. |
| `USE_WITH_FLAG` | Carry the flag into feature metadata and reporting. |
| `SOURCE_NEEDED` | Do not calculate a production research feature; mark unavailable/source-needed. |
| `NEEDS_REVIEW` | Do not silently promote; keep flagged or exclude as pre-declared. |
| Infinite/non-finite result | Mark invalid; do not coerce into a usable value without a declared rule. |
| Duplicate timestamp/security key | Fail validation; do not silently deduplicate. |
| Suspension/price limit | Preserve the status; do not infer tradability from OHLCV alone. |
| Identity uncertainty | Preserve separate identity or exclude under the approved policy. |

Automatic forward-fill, interpolation, backfill from future rows, and hidden
row dropping are prohibited when they change historical information.

## 10. Raw Data Protection

Raw source data, canonical historical-universe files, ticker mappings, and audit
artifacts are read-only inputs to the future feature layer. Feature computation
must operate on a copy or immutable read interface and must never:

- overwrite raw OHLCV;
- repair or rewrite raw prices;
- rewrite historical membership;
- rewrite Yahoo/security mappings;
- promote source-needed data by changing the source artifact.

Output should be written only to an explicitly approved feature location after a
separate implementation gate. This design creates no feature values or output
dataset.

## 11. Price and Corporate-action Representations

Feature specifications must declare the required representation rather than
forcing one representation on every family:

- raw price;
- adjusted price;
- corporate-action-aware representation.

The chosen representation, source semantics, adjustment status, and identity
policy must be recorded in feature metadata. The feature layer must not rewrite
raw data to make representations agree. A feature based on adjusted history does
not by itself solve PIT membership or security continuity.

## 12. Cross-sectional Feature Rules

If a future feature compares securities, ranking/normalization/comparison must
be performed only within the PIT SET50 universe at that timestamp. It must use
only values available by the information cutoff and must preserve missing,
flagged, and identity-excluded rows according to the declared contract.

Cross-sectional comparison is descriptive and does not imply a portfolio rank,
selection rule, alpha score, or trade. No current constituents, future weights,
future sectors, or later-known universe membership may enter the comparison.

## 13. Family-to-Architecture Mapping

| Family | Future feature inputs | Main architecture guard |
|---|---|---|
| Momentum / Trend | Trailing price returns, trend measurements, relative returns | Trailing windows and PIT comparison universe. |
| Mean Reversion / Reversal | Recent return, deviation, range/movement measurements | No signal threshold; conservative timing and identity flags. |
| Volatility | Trailing return, OHLC, or range measurements where supported | No future normalization; declare price representation. |
| Volume / Liquidity | Volume or evidenced trading value/illiquidity inputs | No fabricated spread, depth, queue, or fill fields. |
| Industry / Relative Strength | PIT sector classification and cross-sectional returns | Do not use current or future sector classifications. |

These are architectural input categories, not an implementation list or a
recommendation of which family to test.

## 14. Test Architecture

Tests should be added only in a later implementation phase. The planned test
structure must cover:

- timestamp correctness and information-cutoff enforcement;
- no future-data leakage;
- trailing rolling-window correctness and warm-up behavior;
- PIT membership additions/removals and future-membership rejection;
- missing, flagged, source-needed, and needs-review behavior;
- security-identity boundaries and non-merging;
- deterministic output for identical inputs;
- duplicate timestamps/security keys and non-finite values;
- cross-sectional operations restricted to the PIT universe;
- raw-input immutability and no output-side mutation.

Synthetic toy cases with known expected values are preferred for causal and
rolling-window checks. Tests must not use future information merely to make an
expected result convenient.

## 15. Future Implementation Boundary

Phase 5.1 ends at this design. A separate implementation request must first
declare the feature catalog, source schemas, parameter choices, output schema,
status policy, and test plan. It must not modify the locked Research Protocol
to make implementation easier.

The following remain outside this document:

- feature calculation code or feature values;
- signals, entry/exit logic, or ranking-to-trade rules;
- strategy, portfolio construction, or position sizing;
- backtests, optimization, robustness runs, or ML;
- order generation, execution, or broker integration.

## 16. Design Status

```text
Protocol Gate:
LOCKED

Architecture Status:
READY_FOR_REVIEW

Next Implementation Gate:
Separate approved feature-layer implementation request
```

This document is an architecture proposal for review. It does not claim that
any feature has predictive power, economic value, or live-trading readiness.

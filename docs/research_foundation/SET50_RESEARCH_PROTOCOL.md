# SET50 Research Protocol / Pre-registration

**Status:** `LOCKED`  
**Date:** 2026-09-23  
**Scope:** Governance rules for future SET50 alpha research  
**Boundary:** Research documentation only. No features, signals, strategies,
backtests, optimization, machine learning, portfolio construction, or execution
logic is created here.

## 1. Purpose

This protocol defines rules before a future experiment is run. It is intended to
prevent lookahead bias, survivorship bias, label leakage, security-identity
errors, data-mining, and retrospective changes to a research question.

Two questions must remain separate:

1. **Predictive/statistical validity:** does a pre-specified variable have a
   relationship with a future outcome under the declared information set,
   universe, controls, and out-of-sample design?
2. **Economic viability:** does an observed return difference remain meaningful
   after the project's costs, turnover, liquidity, and execution assumptions?

This document answers neither question and does not rank candidate families.

## 2. Research Scope and Evidence Boundary

The approved scope is the Research Dataset Gate's `2022_H2` through `2026_H2`
window. `2026_H2` is a current/incomplete observation period and must not be
treated as a completed historical test period without a later gate decision.

The research population is the **point-in-time SET50 universe** applicable at
the decision date. Repository evidence from the Research Dataset Gate,
historical-universe audit, security-identity audit, research-data readiness
records, and source/mapping audits governs the population.

Research must not:

- apply today's constituents to historical dates;
- add a security retrospectively because it later entered the index;
- remove a security merely because it later left the index or was delisted;
- use future observations, future labels, or later-known status as inputs;
- treat ticker similarity as proof of security continuity;
- merge predecessor and successor securities without explicit evidence;
- repair raw OHLCV or manufacture missing observations.

Status handling is explicit: `USE` may be used subject to scope;
`USE_WITH_FLAG` may be used only with its limitation preserved;
`SOURCE_NEEDED`, `NEEDS_REVIEW`, and other unresolved rows must be excluded,
separately flagged, or kept descriptive until evidence is available. No status
may be silently upgraded after inspecting an outcome.

## 3. Candidate Alpha Families

All five Phase 4 families are candidates only. Inclusion does not imply
profitability, priority, or permission to implement them.

### 3.1 Momentum / Trend

- **Research question:** Do past eligible-security returns or a pre-declared
  trend measure contain information about later relative or own returns?
- **Falsifiable hypothesis:** A declared past-return/trend measure has a stable,
  directionally specified association with future returns after market,
  cross-sectional, identity, data-quality, and timing controls.
- **Required data:** PIT membership, daily prices, adjustment semantics, identity
  status, and an appropriate benchmark.
- **Timing/leakage:** The lookback ends at the information cutoff. Future ranks,
  current-universe substitution, revised prices, and future bars are prohibited.
- **Data limitations:** Membership and identity evidence is incomplete in some
  periods; daily prices do not establish execution quality.
- **Predictive validity:** Require persistence after PIT, timing, baseline,
  identity, and out-of-sample controls; costs are not statistical controls.
- **Economic viability:** Separately assess commission, VAT, slippage, turnover,
  liquidity, and permitted execution assumptions.
- **Failure condition:** No stable OOS relationship, disappearance under PIT or
  timing controls, or full explanation by the declared baseline.

### 3.2 Mean Reversion / Short-term Reversal

- **Research question:** Do unusually large recent moves or ranges predict a
  pre-declared opposite-direction future return?
- **Falsifiable hypothesis:** Extreme recent movement has a stable opposite-
  direction association after market, identity, suspension, and timing controls.
- **Required data:** PIT prices/OHLC, identity status, suspension/price-limit
  information where available, and a benchmark.
- **Timing/leakage:** The extreme must be observable by the cutoff and the label
  must follow later permitted execution. Future extremes, future halts, revised
  corporate actions, and same-bar hindsight are prohibited.
- **Data limitations:** OHLCV does not identify spread, queue, depth, or exact
  fill sequencing; short-horizon effects are especially exposed.
- **Predictive validity:** Test the statistical association with conservative
  timing and controls independently of post-cost results.
- **Economic viability:** Separately evaluate spread uncertainty, turnover,
  fees, one-tick slippage, and permitted execution.
- **Failure condition:** The association disappears under controls/OOS or cannot
  be distinguished from data-quality or microstructure artifacts.

### 3.3 Volatility-related Effects

- **Research question:** Does a pre-declared volatility measure relate to future
  returns beyond market and risk baselines?
- **Falsifiable hypothesis:** The measure has a stable, directionally declared
  association with future eligible-security returns after declared controls.
- **Required data:** OHLC or returns, adjustment semantics, PIT membership,
  identity status, and an appropriate benchmark.
- **Timing/leakage:** Use only observations known by the cutoff; no full-period
  statistic, future regime label, or later-revised history.
- **Data limitations:** Price limits, suspensions, identity boundaries, sector,
  and liquidity exposure can distort the observed measure.
- **Predictive validity:** Assess association after market/risk, universe,
  identity, and timing controls; costs are not a statistical baseline.
- **Economic viability:** Separately assess turnover, concentration, fees, tick
  slippage, liquidity, and execution feasibility.
- **Failure condition:** Unstable sign, post-result threshold dependence,
  disappearance under controls, or insufficient reliable OHLC history.

### 3.4 Volume / Liquidity

- **Research question:** Does a pre-declared volume or illiquidity measure add
  information about future returns or continuation/reversal?
- **Falsifiable hypothesis:** The measure has an incremental association after
  price, market, eligibility, and data-quality controls and is available at the
  declared cutoff.
- **Required data:** Volume and preferably trading value, prices, PIT membership,
  suspension/limit status, and declared execution assumptions.
- **Timing/leakage:** Later revised/end-of-day information used before it is
  available, future halts, and selective missing-value treatment are prohibited.
- **Data limitations:** Complete historical trading value, spread, depth, queue,
  and fill history are not established for the full scope.
- **Predictive validity:** Test only where the measure is historically available
  and distinguish it from suspension/data-quality flags; costs do not determine
  statistical validity.
- **Economic viability:** Separately test costs, turnover, liquidity, and fill
  assumptions.
- **Failure condition:** Required data are unavailable, the result is only a
  data-quality proxy, or it fails OOS and execution-feasibility review.

### 3.5 Industry / Relative Strength

- **Research question:** Does point-in-time sector-relative performance add
  information beyond individual momentum and market exposure?
- **Falsifiable hypothesis:** A declared sector measure has a stable association
  with future eligible returns after composition, market, momentum, identity,
  and timing controls.
- **Required data:** PIT sector classifications, PIT membership, returns, identity
  status, and a benchmark.
- **Timing/leakage:** Use labels and composition available at the decision date;
  future sector assignments and reconstituted labels are prohibited.
- **Data limitations:** Complete historical classifications are source-needed or
  limited; small changing sectors create concentration risk.
- **Predictive validity:** Compare against declared market and individual-
  security baselines without calling cost survival a statistical result.
- **Economic viability:** Separately assess turnover, concentration, fees,
  slippage, liquidity, and long-only constraints.
- **Failure condition:** Labels cannot be verified, the relationship disappears
  after composition/identity controls, or it lacks OOS robustness.

No family may be described as a winner or recommended strategy from this
protocol.

## 4. Information-Timing Convention

Every future experiment must record:

```text
data_timestamp
feature_timestamp
signal_timestamp
execution_timestamp
label_timestamp
information_cutoff
```

At `signal_timestamp`, only information available by `information_cutoff` may
be used. The conservative daily convention is:

```text
completed bar at t
    -> signal after the declared information cutoff
    -> execution at a later permitted session
    -> future return label after execution
```

The label and observations created after the signal cannot be inputs. A
different convention must be declared before the relevant experiment and logged
as a protocol decision.

## 5. Point-in-time Universe Rule

Each observation must use SET50 membership effective at its decision date.
Additions, removals, delistings, suspensions, unresolved identities, and source
gaps remain visible.

- **Addition/removal:** eligible only during the evidenced membership interval.
- **Suspension/price limit:** retain and flag when status is supported; do not
  infer a tradable fill from a daily bar.
- **Unresolved identity:** keep separate or exclude according to the existing
  identity audit; never merge by ticker resemblance.
- **Source gap:** exclude, flag, or keep descriptive only; never invent history.

Later knowledge that an instrument entered, left, or changed identity cannot be
applied backwards. The current constituent list is not a historical universe.

## 6. Baselines

Each future family test must declare which are available and appropriate:

- simple market exposure or buy-and-hold;
- point-in-time SET50 price-index baseline;
- point-in-time SET50 total-return baseline, only if authoritative aligned data
  exist;
- cash/no-signal baseline for a long-only design that may remain uninvested;
- neutral long-only cross-sectional comparison without an impermissible short leg.

These are statistical comparison baselines, separate from economic viability.
Price-index and total-return series must not be mixed. A baseline cannot be
claimed as available without historical provenance and timing evidence.

## 7. Predictive Validity

Predictive validity is supported only if a pre-declared relationship remains
after relevant PIT universe, timestamp, identity/data-quality, market/risk, and
out-of-sample controls. The population, direction, horizon, baseline, and
rejection condition must be declared.

Transaction costs are not statistical baseline controls. A relationship may be
statistically present but economically unusable; execution assumptions cannot be
used to claim that the statistical relationship does not exist. No predictive
test is run by this document.

## 8. Economic Viability and Fixed Constraints

Economic viability is assessed separately after a statistical relationship is
defined. Future evaluation must preserve:

```text
initial capital = THB 10,000,000
long-only = true
commission = order value × 0.00157
VAT = commission × 0.07
slippage = one applicable SET price tick
allowed order types = Limit; Market-to-Limit IOC
minimum distinct symbols for a future strategy evaluation = 5
```

A relationship can be statistically detectable and still fail economic
viability after commission, VAT, slippage, turnover, liquidity, or execution
assumptions. Report that as statistically supported but economically non-viable
under the declared evaluation, not as a contradiction of the statistical result.

## 9. Data Limitations and Status Handling

Binding limitations include incomplete historical membership; flagged,
source-needed, needs-review, and unresolved rows; daily OHLCV without spread,
queue, depth, or exact-fill information; suspension and price-limit effects;
security-identity uncertainty; and incomplete point-in-time sector
classifications. Yahoo/source availability is not proof of security continuity.

No limitation may be solved by synthetic observations, raw-OHLCV repair,
unsupported security merging, or future-knowledge backfill.

## 10. Multiple Testing and Research Bias

Future work must log all families, definitions, parameter values, horizons,
exclusions, missing-data rules, universe versions, and failed tests. A parameter
or design chosen after seeing historical performance is a research-derived or
exploratory choice, not a pre-registered choice. This also applies to changed
timing, costs, universe, identity rules, exclusions, thresholds, and repeated
experiments on the same outcome sample.

## 11. Parameter Policy

`docs/set50_parameter_research.md` is a reference of candidate ranges and
evidence strength only. It does not establish a best parameter. This protocol
does not authorize optimization, grid search, parameter ranking, or selection
from historical performance. Exact future values must be declared before
outcome evaluation; post-result values remain exploratory.

## 12. Validation Design

Future testing must preserve chronological order and distinguish:

- **In-sample:** a declared exploratory or training purpose only.
- **Out-of-sample:** held out from parameter/design selection and evaluated under
  the registered rules.
- **Walk-forward:** sequential selection windows followed by later evaluation.
- **Robustness:** pre-declared sensitivity to periods, data status, identity
  exclusions, timing, and documented assumptions.

The test period must not select a strategy, parameter, threshold, universe rule,
or interpretation. Any numerical threshold not fixed by repository evidence is
**to be specified before the relevant experiment**.

```text
Research Protocol
    -> feature implementation
    -> signal design
    -> strategy
    -> backtest
    -> out-of-sample evaluation
    -> robustness analysis
```

This protocol defines the sequence but does not execute it.

## 13. Failure and Rejection Rules

A future hypothesis may be rejected when the relationship does not persist OOS,
disappears under PIT/timing/identity controls, is fully explained by a declared
baseline, lacks sufficient correctly timed data, fails economic viability under
declared costs/execution, is sensitive to small undocumented parameter changes,
or is not robust across declared periods/status subsets.

Unsupported numerical thresholds, minimum samples, and parameter-specific
acceptance criteria are **to be specified before the relevant experiment**.

## 14. Research Log

Every future experiment must record:

```text
experiment_id
date
hypothesis
dataset_version
universe_version
parameter_specification
baseline
cost_assumptions
train_period
test_period
result
interpretation
deviations_from_protocol
```

Deviations are logged as deviations; the protocol must not be edited after an
outcome to make the experiment appear pre-registered.

## 15. No Implementation in This Phase

This document does not create or modify features, signals, strategies,
portfolio construction, backtests, optimization, parameter sweeps, ML models,
execution engines, raw OHLCV, historical-universe files, or ticker mappings.
This is documentation and research governance only.

## 16. Final Gate

```text
Protocol Status:
LOCKED

Next Gate:
Feature Implementation
```

This protocol was locked after Human Audit. The lock does not claim that any
alpha, feature, strategy, or performance result is validated or proven.

## Research Boundary Statement

The Research Protocol is a pre-registration draft. It defines future research
controls and evidence boundaries but does not execute research, validate an
alpha, select a strategy, or modify production code or data.

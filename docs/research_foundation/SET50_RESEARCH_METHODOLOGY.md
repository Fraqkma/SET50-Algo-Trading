# SET50 Research Foundation: Phase 1 Research Methodology

**Status:** Research-only methodology
**Date:** 2026-09-22
**Scope:** Quantitative research design for a daily, long-only SET50 project

This document defines how future research should be designed and reported. It is
not a strategy, feature specification, signal specification, backtest, optimizer,
or performance result.

## 1. Research objective

The central question is:

> How should quantitative research for SET50 be designed so that future alpha
> discovery and strategy testing are credible, while reducing lookahead bias,
> survivorship bias, data snooping, and overfitting?

The project constraints remain fixed:

- SET50 historical point-in-time universe only.
- Long-only; no short leg and no market-neutral construction requiring shorting.
- Initial capital: THB 10,000,000.
- Commission: 0.157% of order value.
- VAT: 7% of commission.
- Slippage: one applicable price tick.
- Allowed orders: Limit and Market-to-Limit IOC.
- At least five distinct symbols traded when a future strategy is eventually evaluated.

These are project constraints, not empirical findings. They must not be changed to
make a result look better.

## 2. Repository context and evidence boundary

The repository already contains separate work on historical SET50 membership,
historical data availability, Yahoo ticker auditing, security identity, source
audits, the Research Dataset Gate, and parameter research. This methodology should
be read together with:

- [Historical SET50 universe audit](../../reports/pilot/historical_universe_2016_2022/historical_universe_2016_2022_audit.md)
- [Security identity audit](../HISTORICAL_SECURITY_IDENTITY_AUDIT.md)
- [Research Dataset Gate](../../reports/pilot/research_dataset_gate.md)
- [SET50 parameter research](../set50_parameter_research.md)
- [Research data readiness](../RESEARCH_DATA_READINESS.md)

The historical-universe audit currently has complete cited tables for only five
2016--2022 half-year periods. Other periods are partial or unresolved. Therefore,
future results must report the exact membership coverage used; a current SET50 list
must never silently stand in for historical membership.

## 3. Information set

The information set at time `t`, written `I(t)`, is the collection of information
that was actually available and usable at the decision time. A signal at `t` may
use only `I(t)`.

```text
t-2 --------> t-1 --------> t --------> t+1 --------> t+2
 known data       known data    decision       future data
```

For a daily example, after the close at date `t`, `I(t)` may contain the published
OHLCV for `t`, historical membership effective by `t`, and mappings or corporate
action information that was publicly available by the declared cutoff. It does not
contain the close, volume, membership revision, or event that becomes known at
`t+1`.

The research record must state:

```text
feature_timestamp
signal_timestamp
execution_timestamp
label_timestamp
information_cutoff
```

An information timestamp is not automatically the same as a market timestamp. A
historical file may carry a date while the value was published or revised later.
When availability time cannot be established, the result should be flagged rather
than treated as unquestionably point-in-time.

## 4. Lookahead bias

Lookahead bias occurs when a calculation uses information that was not available at
the time of the decision.

### Incorrect daily example

```text
Close(t+1) -> Feature(t) -> Signal(t)
```

`Close(t+1)` is future information relative to a decision made at `t`. It makes the
historical result unrealistically informed.

### Correct causal sequence

```text
Data available by t
        -> Feature(t)
        -> Signal(t)
        -> Order after signal
        -> Execution at a permitted later time
```

The following timestamps must remain distinct:

- **Data timestamp:** when the market observation belongs to, such as the close of
  trading date `t`.
- **Signal time:** when the rule is evaluated.
- **Execution time:** when an order could actually be submitted and filled.
- **Label time:** the future interval used to evaluate an outcome, such as
  `t+1` through `t+5`.

### Daily execution conventions

The research specification must choose one convention before testing:

1. **Daily close signal, next-day execution:** use the completed bar at `t`, then
   submit the order at the next permitted session. This is the conservative default
   when only daily OHLCV is available.
2. **Same-day execution:** only valid if the rule uses information available before
   the assumed execution point. A completed close cannot be used to claim an earlier
   same-day fill.
3. **Close execution:** requires an explicit operational assumption about when the
   close is known and how the allowed order is filled; it must not be assumed merely
   because a daily bar exists.

Indicator calculations must use only rows whose timestamps are no later than the
declared information cutoff. Rolling functions must be checked for accidental
forward filling, centered windows, or use of future-ranked data.

## 5. Survivorship bias and point-in-time universe

Survivorship bias occurs when a historical test uses only securities that survived
into the present.

### Incorrect SET50 design

```text
2026 SET50 constituents
        -> test them as if they were the 2018 universe
```

### Correct SET50 design

```text
SET50 constituents effective during period t
        -> apply eligibility at t
        -> use only data available for those securities at t
```

The universe model must represent:

- point-in-time membership;
- membership effective-from and effective-to dates;
- additions and removals;
- delistings and suspensions;
- security replacements;
- unresolved periods and evidence quality.

The index archive and methodology describe a periodically reviewed SET50 universe;
the repository's historical audit records which periods currently have complete,
partial, or unresolved evidence. A missing historical snapshot is an evidence gap,
not permission to copy the next or current period.

If a membership period cannot be verified, future research must either exclude that
period explicitly or label the result as conditional. It must not silently fill the
membership from memory or from today's constituents.

## 6. Corporate action and security identity

Corporate actions change rights, capital structure, listing status, or trading
terms. Security identity answers which tradable security a price observation belongs
to. They are related but not interchangeable.

```text
Ticker continuity != Security continuity
```

A ticker can change while the security remains the same, or a new security can
appear with a related company name. Concatenating prices without evidence can create
a synthetic series that never existed.

The repository audit identifies cases requiring separate treatment, including:

- `TMB -> TTB`: a ticker/company change requiring an effective-date mapping review;
- `TRUEE / DTAC -> TRUE`: predecessor and successor securities remain separate;
- `NTL -> TIDLOR`: replacement boundary must be respected;
- `SCBB -> SCB / SCBX`: corporate restructuring does not itself prove OHLCV
  continuity;
- `BANPU / BANPUU`: period-specific identity and listing boundaries;
- `GULF / INTUCH / GULFI`: event, suspension, and successor boundaries.

Until a separate, approved identity policy resolves a case, the raw series and
historical membership should preserve the published symbol exactly. No identity
continuity should be inferred from similar names, ticker suffixes, or a convenient
Yahoo series.

## 7. Adjusted versus unadjusted prices

The following concepts must be kept separate:

- **Raw price:** the observed OHLC value as supplied by the source for that security
  and trading date.
- **Adjusted price:** a transformed series intended to make selected corporate
  actions or distributions comparable across time.
- **Corporate-action adjustment:** a documented transformation for a split, dividend,
  rights issue, merger, or other event.
- **Split:** a change in share count and quoted price that may require a split factor
  for return analysis.
- **Dividend:** a cash distribution that affects total-return interpretation but is
  not the same event as a split.
- **Rights or other action:** an event that may affect price, entitlement, quantity,
  or tradability and requires its own evidence.

For return, momentum, and volatility research, the specification must state whether
it uses raw close, adjusted close, or an independently reconstructed series. It must
also record the source's adjustment semantics and whether the adjustment was known
at the historical decision time.

Adjusted price is **not** the same thing as point-in-time data. An adjusted series
may revise historical values using a later corporate action, while point-in-time
research asks what data and universe were knowable at the decision date. Adjusted
prices can be useful for economic return measurement, but they do not resolve
membership timing, security identity, availability timing, or execution realism.

Raw and adjusted series must not be mixed in one feature without an explicit rule.
If a corporate action cannot be explained, preserve the raw observation and flag the
period rather than silently repairing it.

## 8. Data snooping

Data snooping is the discovery of an apparently attractive pattern after examining
many possible patterns. For example:

```text
Momentum lookbacks: 5D, 10D, 15D, 20D, ... 200D
        -> choose the best historical result
```

The selected result is conditional on the entire search. Its apparent confidence is
too high if the search process is not acknowledged. The same issue applies to
universe definitions, holding periods, thresholds, rebalance dates, feature
combinations, and exclusions.

Before any future experiment, record the hypothesis, candidate range, selection
rule, data window, cost assumptions, and intended evaluation set. Changes after
seeing results must be logged as a new research decision, not silently folded into
the original test.

## 9. Multiple testing and research degrees of freedom

Testing many hypotheses creates a multiple-comparisons problem. A nominally
interesting result can occur by chance when enough alternatives are tried.

For example:

```text
10 momentum windows
 x 10 moving-average windows
 x 10 volatility windows
 x 5 holding periods
 = 5,000 combinations before other choices
```

The research log must record:

- every tested family and candidate value;
- the order in which decisions were made;
- data windows and universe versions;
- exclusions, missing-data rules, and failed runs;
- whether a result was exploratory or confirmatory;
- which data were used to make any subsequent design choice.

Research degrees of freedom include more than numeric parameters. They include
signal timing, rebalance frequency, top-N selection, volatility estimator,
corporate-action treatment, membership handling, and cost assumptions.

This methodology does not propose changing parameters to improve a backtest. The
purpose of the log is to make the search visible and to prevent an exploratory
finding from being presented as independent confirmation.

## 10. Parameter overfitting

Parameter overfitting occurs when a rule is tuned too closely to historical noise.

```text
20D -> good
21D -> very good
22D -> best
23D -> good
        -> select 22D because it is best
```

An isolated peak can be a noise feature of one sample. A broad, stable region is
more informative than a single highly tuned value, but even a broad region still
requires out-of-sample confirmation.

The ranges in [SET50 Parameter Research](../set50_parameter_research.md) are
**candidate research ranges**, not proven optimal parameters. They are intended to
bound a future pre-specified experiment. They must not be described as “the best
20D” or as a validated live configuration before testing.

## 11. Hypothesis, evidence, result, interpretation, conclusion

These statements must not be collapsed into one sentence:

| Label | Meaning | Example |
|---|---|---|
| Hypothesis | A testable proposition stated before the result | “Momentum may contain predictive information within the eligible SET50 universe.” |
| Evidence | External literature, source data, or a documented observation | “A published study reports momentum over a stated horizon in a different market.” |
| Result | Output of a pre-declared experiment | “Under the declared split and costs, the measured outcome was ...” |
| Interpretation | A bounded explanation of the result | “The result is consistent with, but does not prove, the hypothesis.” |
| Conclusion | What can responsibly be carried forward | “Retain this as a candidate for an independent test.” |

Do not write “Momentum works” before a defined experiment. A literature result is
not a result for this repository, and a result in one sample is not a universal
law.

## 12. Training, validation, and out-of-sample data

For future research:

- **Training/development set:** used to formulate or implement the hypothesis and
  make design decisions.
- **Validation set:** used to check whether the design generalizes during research
  development. Repeated use still creates selection pressure and must be logged.
- **Out-of-sample set:** kept untouched during development and used for the final
  pre-declared assessment of the frozen design.

OOS data matter because they provide evidence on data not used to choose the
research design. OOS data must not be used to select the parameter, change the
signal, choose the universe, or revise the cost model. If OOS results lead to a
change, the changed design begins a new research cycle and requires a new OOS set.

Splits must be chronological. Random shuffling can place future market conditions
in the training set and past conditions in the test set, obscuring the information
available at each historical decision.

## 13. Walk-forward analysis

Walk-forward analysis moves development and evaluation windows through time:

```text
Train        Test
2018-2020 -> 2021
2019-2021 -> 2022
2020-2022 -> 2023
2021-2023 -> 2024
```

It is appropriate for time-series research because it preserves chronology and
tests whether a design remains useful as the market changes. Each training window
must use the point-in-time universe and information rules for its dates.

Walk-forward analysis is not permission to repeatedly tune until the latest test
looks good. The window plan, refit rule, candidate ranges, and evaluation metrics
must be declared before the relevant result is inspected. This phase defines the
method only; it does not implement or run walk-forward analysis.

## 14. Time alignment

The minimum timing model is:

```text
Data available through t
        ↓
Feature timestamp: t
        ↓
Signal timestamp: t
        ↓
Order timestamp: after signal
        ↓
Execution timestamp: permitted fill time
```

For a next-day daily convention:

```text
Close(t) -> calculate signal after t close -> order on next session
```

`Close(t+1)` cannot be used to create a signal at `t`. A future return label may be
defined as `Return(t+1:t+5)`, but it must remain a label and must never enter a
feature or eligibility decision.

Every future experiment should be able to answer:

- What was known at feature time?
- When did the signal become actionable?
- What execution assumption was used?
- Which price and volume observations belong to the label interval?
- Were membership and mapping facts available by the decision cutoff?

## 15. Label and target leakage

Target leakage occurs when information derived from the future target enters the
feature or selection process.

Valid conceptual separation:

```text
Feature(t) = data available by t
Target(t)  = future return after the decision, for example t+1 through t+5
```

Invalid examples include:

- using future return to normalize today's momentum;
- using the maximum future price to define a breakout threshold;
- filling today's missing value from a later observation;
- using a final full-sample ranking or scaler before a chronological split;
- using a later membership revision to decide historical eligibility.

The label may be calculated for evaluation, but it must be kept outside the
information set used to generate the decision.

## 16. Transaction cost and slippage

The cost model must remain tied to the competition constraints:

```text
initial_capital = 10,000,000 THB
commission      = order_value * 0.00157
VAT             = commission * 0.07
slippage        = 1 applicable tick
direction       = long-only
orders          = LIMIT or MARKET_TO_LIMIT with IOC validity
```

The research record must keep commission and VAT separate and must distinguish:

```text
signal price
requested order price
executed price
slippage
commission
VAT
total fees
```

Shorter holding periods may create more turnover and therefore greater cost and
execution sensitivity, but this is a mechanism-based hypothesis until measured.
No future result should be reported using gross return alone when the design is
intended to reflect competition execution.

Daily OHLCV is sufficient for a first daily descriptive study, but it cannot by
itself establish intraday queue position, bid/ask spread, IOC fill probability, or
the exact path of a limit order.

## 17. Research record and decision gate

Every future quantitative experiment should preserve a research record containing:

```text
experiment_id
research_question
hypothesis
universe_version
security_identity_policy_version
data_source_and_version
data_cutoff_and_availability_rule
feature_definitions
signal_timing
execution_assumptions
candidate_parameter_ranges
train_validation_oos_windows
cost_and_slippage_model
missing_data_policy
corporate_action_policy
pre_declared_metrics
results_location
interpretation
limitations
decision
```

The Research Dataset Gate must remain a prerequisite for feature engineering and
strategy evaluation. Unresolved historical membership, security identity, or data
quality should appear as an explicit status, not be silently repaired.

## 18. Methodology checklist

Before any future strategy or parameter experiment, confirm:

- [ ] The point-in-time SET50 universe is identified for each date.
- [ ] Membership effective dates and unresolved periods are recorded.
- [ ] Security identity and corporate-action assumptions are explicit.
- [ ] Raw versus adjusted price semantics are documented.
- [ ] Feature, signal, execution, and label timestamps are separated.
- [ ] No calculation uses data after the information cutoff.
- [ ] Candidate parameters were declared before result inspection.
- [ ] All tested variants and research decisions are logged.
- [ ] Training, validation, and OOS windows are chronological.
- [ ] OOS data are not used to choose parameters.
- [ ] Commission, VAT, slippage, order type, and long-only constraints are applied.
- [ ] Daily-data limitations are disclosed.
- [ ] No missing historical data were invented or silently repaired.
- [ ] Results distinguish hypothesis, evidence, result, interpretation, and conclusion.

## 19. Scope boundary

This document is research methodology only. It does not create or modify source
code, feature code, strategy code, backtest code, data pipelines, historical
universes, Yahoo mappings, production data, research datasets, or the Research
Dataset Gate. It does not download data, run backtests, run optimization, select a
best parameter, or merge securities.

## References

- [SET50 profile and methodology - Stock Exchange of Thailand](https://www.set.or.th/en/market/index/set50/profile)
- [Historical SET50 Universe Audit in this repository](../../reports/pilot/historical_universe_2016_2022/historical_universe_2016_2022_audit.md)
- [Historical Security-Identity Audit in this repository](../HISTORICAL_SECURITY_IDENTITY_AUDIT.md)
- [Research Dataset Gate in this repository](../../reports/pilot/research_dataset_gate.md)
- [SET50 Parameter Research in this repository](../set50_parameter_research.md)
- [Jegadeesh & Titman (1993), Returns to Buying Winners and Selling Losers](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)
- [Moskowitz, Ooi & Pedersen (2012), Time Series Momentum](https://research.cbs.dk/en/publications/time-series-momentum)
- [Brock, Lakonishok & LeBaron (1992), Simple Technical Trading Rules](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04681.x)
- [Garman & Klass (1980), On the Estimation of Security Price Volatilities](https://econpapers.repec.org/article/ucpjnlbus/v_3a53_3ay_3a1980_3ai_3a1_p_3a67-78.htm)
- [Thailand SET50 technical trading study](https://so01.tci-thaijo.org/index.php/buacademicreview/article/view/240412)

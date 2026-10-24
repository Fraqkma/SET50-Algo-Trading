# SET50 Alpha Research Foundation

**Status:** `READY_FOR_AUDIT`  
**Date:** 2026-09-22  
**Scope:** Research-only review of candidate alpha families for the historical, point-in-time SET50 universe  
**Boundary:** No feature implementation, signal, strategy, backtest, optimization, ML model, portfolio construction, or execution logic is created here.

## 1. Research Objective

This document asks:

> Which alpha hypotheses are sufficiently motivated and supported by prior
> evidence to justify formal testing on the historical SET50 research dataset?

The purpose is to define candidates and their evidence requirements, not to prove
that any candidate works. No candidate is selected as a winner, and no parameter
is optimized.

## 2. Repository Research Boundary

The Phase 1 methodology, Phase 2 microstructure foundation, Phase 3 Thailand
market-regime foundation, parameter research, and data audits are the governing
context for this document.

The current repository constraints are:

- historical point-in-time SET50 membership only;
- long-only research;
- initial capital of THB 10,000,000 for any later competition evaluation;
- commission of 0.157% plus 7% VAT on commission;
- one applicable price tick of slippage;
- permitted order types of Limit and Market-to-Limit IOC;
- at least five distinct symbols for a future strategy evaluation.

These are project constraints, not empirical evidence for any alpha hypothesis.

The Research Dataset Gate currently covers `2022_H2` through `2026_H2` and
contains rows with different readiness statuses. The historical-universe audit
also has incomplete or unresolved evidence for several earlier 2016–2022
half-year periods. Therefore, an alpha result must disclose the exact universe
and data subset used; it must not silently expand the approved period or replace
historical membership with today's constituents.

## 3. What “Alpha” Means Here

In this project, alpha is not synonymous with a positive return.

| Concept | Meaning |
|---|---|
| Market return | Return attributable to broad SET/SET50 market movement. |
| Market-trend exposure | Sensitivity to a broad upward or downward market condition. |
| Systematic risk premium | Compensation associated with a declared risk exposure, such as liquidity or volatility risk. |
| Cross-sectional return difference | A difference in future returns between eligible securities, conditional on a point-in-time universe and baseline. |
| Predictive information | An observable variable available at the decision time that is associated with a future outcome under a pre-declared test. |
| Incremental alpha (predictive concept) | Predictive information that remains after declared market, risk, universe, and other relevant statistical baseline controls. It is not a post-cost viability conclusion. |
| Economic viability | Whether an observed return difference remains economically meaningful after the project's commission, VAT, slippage, turnover, liquidity, and execution assumptions. |

A pattern is not called genuine alpha merely because it is profitable before
costs, correlated with a later return, or present in an external market. A
statistically predictive relationship and its economic viability after costs are
separate questions. Each
candidate below is explicitly labeled as evidence, interpretation, hypothesis,
or future test design.

## 4. Evidence Classification

- **Documented empirical evidence:** a cited study or official source reports an
  observation for a stated market, sample, and method.
- **Economic interpretation:** a possible explanation proposed by literature or
  inferred cautiously from market structure; it is not a causal finding here.
- **Research hypothesis:** a proposition that can be rejected by a declared test.
- **Future test design:** a protocol decision that must be pre-registered before
  implementation and outcome inspection.

External evidence is not SET50 evidence. A study in U.S. equities, futures, or
another emerging market can motivate research, but cannot establish that the
same effect exists in Thailand.

## 5. Candidate Alpha Families

### 5.1 Momentum and trend continuation

**What it represents:** Past relative or own-security returns may contain
information about subsequent returns. Cross-sectional momentum compares eligible
SET50 securities; time-series momentum evaluates an instrument's own prior return.

**Documented evidence:** Jegadeesh and Titman (1993) reported positive returns
from buying past winners and selling past losers over three- to twelve-month
holding periods in U.S. equities. Moskowitz, Ooi, and Pedersen (2012) reported
time-series momentum across 58 liquid futures with persistence over one to twelve
months and partial reversal at longer horizons. A Thailand SET50 study examined
technical rules, including moving averages, under different asset conditions.
The study analyzed 19 stocks that were listed consistently from 2007 to 2017.
This is direct Thailand/SET50-related evidence that can motivate conditional
investigation, but the fixed-stock sample is not equivalent to the repository's
point-in-time SET50 universe and may carry sample-selection or survivorship
limitations. It does not validate the repository's point-in-time implementation
or prove that an effect survives its universe controls.

**Possible mechanism:** Prior literature proposes delayed information
incorporation, underreaction, institutional trading, and gradual repositioning as
possible mechanisms. These mechanisms are not established for this repository.

**SET50 applicability:** Large-cap concentration, sector concentration,
periodic membership review, price limits, suspensions, identity boundaries, and
daily-data execution constraints can all change the observed persistence. A
cross-sectional result may also reflect sector or market exposure rather than
security-specific information.

**Falsifiable hypothesis:** Among securities that were eligible at the decision
date, a pre-declared past-return ranking or own-return direction contains a
positive association with a later declared-horizon return after comparison with
the relevant market and cross-sectional baseline. The statistical hypothesis is
unsupported if the relationship disappears under point-in-time membership,
identity-aware data, and pre-specified out-of-sample evaluation, or if it is
fully explained by the baseline exposure. Economic viability is a separate
question: any observed return difference must later be evaluated against the
project's declared costs, turnover, liquidity, and execution assumptions.

### 5.2 Mean reversion and short-term reversal

**What it represents:** Extreme recent movements may be followed by returns in
the opposite direction. This is distinct from medium-term momentum and must not
be combined with it silently.

**Documented evidence:** De Bondt and Thaler (1985) reported evidence consistent
with long-horizon overreaction and subsequent reversal in U.S. CRSP monthly
returns. This is external evidence with a long formation and holding context; it
does not establish short-term reversal in SET50.

**Possible mechanism:** Literature proposes behavioral overreaction, temporary
price pressure, liquidity provision, and limits to arbitrage. In a daily Thai
market setting, the same apparent pattern could instead reflect bid/ask effects,
price limits, stale prices, suspensions, or unmodeled execution costs.

**SET50 applicability:** Daily OHLCV does not identify spread or queue position.
A reversal measured from closing prices can therefore be contaminated by
microstructure and corporate-action effects. The long-only constraint also means
that a symmetric long/short reversal construction is not directly compatible
with the competition.

**Falsifiable hypothesis:** Conditional on point-in-time eligibility, unusually
large recent returns or range movements are followed by a pre-declared opposite-
direction return over a short, literature-motivated horizon, after controlling
for market movement and excluding or flagging identity and suspension cases.
The statistical hypothesis is unsupported if the relationship is removed by
conservative timing, appropriate controls, or execution-quality sensitivity
analysis. Economic viability is separate and requires later evaluation after
commission, VAT, slippage, turnover, liquidity, and execution assumptions.

### 5.3 Volatility-related effects

**What it represents:** Volatility may persist over time, and cross-sectional
volatility exposure or realized volatility may be associated with future returns.
This family includes volatility persistence and cross-sectional volatility
hypotheses; it does not imply that high volatility is automatically good or bad.

**Documented evidence:** French, Schwert, and Stambaugh (1987) reported a
positive relation between predictable market volatility and expected market risk
premium in their U.S. market study. Ang, Hodrick, Xing, and Zhang (2006)
reported that stocks with high sensitivities to aggregate volatility
innovations, and stocks with high idiosyncratic volatility in their sample, had
low average returns. Garman and Klass (1980) support the separate research
question of how OHLC data can estimate volatility; they do not establish a
return anomaly.

**Possible mechanism:** Volatility may proxy for changing risk, uncertainty,
limits to arbitrage, or investor demand for lottery-like payoffs. These are
possible mechanisms, not causal conclusions for SET50.

**SET50 applicability:** Daily OHLCV can support descriptive realized-volatility
measures, but the source's adjustment semantics, suspensions, price limits, and
security identity boundaries matter. A volatility effect can be confounded with
size, liquidity, sector, or market-regime exposure. No formal volatility regime
or threshold is selected in this document.

**Falsifiable hypothesis:** A pre-declared volatility measure available at the
decision timestamp has a stable, directionally declared association with the
future return of eligible securities beyond the market and relevant risk
baselines. It is unsupported if the sign or association is unstable across
declared periods, disappears after controls, or depends on a threshold selected
after inspecting performance. Economic viability is a separate later question:
the observed return difference must be evaluated after the project's declared
cost and execution assumptions rather than treating costs as a statistical
baseline control.

### 5.4 Volume and liquidity-related effects

**What it represents:** Trading activity or illiquidity may be related to future
returns, turnover, or the persistence of price movements.

**Documented evidence:** Amihud (2002) proposed and tested an illiquidity proxy
based on the daily ratio of absolute return to dollar volume, reporting a
positive relation between expected illiquidity and expected excess return in his
sample. Lee and Swaminathan (2000) studied the relation between price momentum
and trading volume in U.S. equities. These findings motivate investigation but
are not evidence that the same relationship is statistically present in SET50
or economically viable under the project's costs and long-only restrictions.

**Possible mechanism:** A liquidity premium, temporary price pressure, investor
segmentation, or limits to arbitrage may produce a relationship. The same
variables can also measure implementation difficulty rather than predictive
information.

**SET50 applicability:** The repository has daily market-data artifacts with
known readiness and source limitations, but a consistent point-in-time trading-
value history and historical spread/depth history are not established for all
periods. Volume-based observations must not be treated as a fill model. A high
illiquidity reading may be a reason to reject an order rather than an alpha.

**Falsifiable hypothesis:** A pre-declared volume or illiquidity measure has an
incremental association with future returns or continuation/reversal after
controlling for market, price movement, and eligibility, and is available at the
declared information cutoff. The statistical hypothesis is unsupported if it
relies on unavailable trading value or is only a proxy for a data-quality or
suspension flag. Economic viability is separate and requires later evaluation
after realistic commission, VAT, slippage, turnover, liquidity, and execution
assumptions.

### 5.5 Industry and cross-sectional relative strength

**What it represents:** Relative performance across sectors or industries may
contain information distinct from individual-security return ranking.

**Documented evidence:** Moskowitz and Grinblatt (1999) reported industry
momentum in U.S. equities and found that controlling for industry momentum
reduced individual-stock momentum profitability in their sample. The result is
important for decomposition, but it does not prove an industry effect in SET50.

**Possible mechanism:** Sector-level information diffusion, common cash-flow or
discount-rate shocks, institutional herding, and gradual capital reallocation
are possible explanations. The evidence does not establish which mechanism
would operate in Thailand.

**SET50 applicability:** SET50 has a small, concentrated, time-varying universe.
Sector labels, classification revisions, mergers, and membership turnover can
make sector comparisons unstable. With few constituents in a sector, apparent
relative strength may be a single-security effect or a market beta effect.

**Falsifiable hypothesis:** After assigning only point-in-time sector
classifications, sector-relative returns or dispersion contain information about
future eligible-security returns beyond the market and individual-security
momentum baselines. The statistical hypothesis is unsupported if it disappears
after sector composition, membership, and identity controls, or cannot be tested
with historical classifications available at the time. Economic viability is a
separate later question requiring evaluation after the project's declared costs,
turnover, liquidity, and execution assumptions.

## 6. Prior Evidence Register

| Source | Market / sample | Method and documented finding | Limitation for SET50 |
|---|---|---|---|
| Jegadeesh & Titman (1993), *Returns to Buying Winners and Selling Losers* | U.S. equities, 1965–1989 | Portfolio sorts; positive winner-minus-loser returns over three to twelve months | External market; long/short construction; not SET50 or long-only |
| De Bondt & Thaler (1985), *Does the Stock Market Overreact?* | U.S. CRSP monthly returns | Long-horizon loser portfolios subsequently outperformed winners; evidence consistent with overreaction | External market; long horizon; reversal may differ from daily SET50 behavior |
| Moskowitz, Ooi & Pedersen (2012), *Time Series Momentum* | 58 liquid futures across asset classes | Own-past-return persistence over one to twelve months, with longer-horizon reversal | Futures and long/short implementation; not individual SET50 equities |
| French, Schwert & Stambaugh (1987), *Expected Stock Returns and Volatility* | U.S. market | Predictable volatility related positively to expected market risk premium | Market-level risk relation, not a SET50 cross-sectional anomaly |
| Ang, Hodrick, Xing & Zhang (2006), *The Cross-Section of Volatility and Expected Returns* | U.S. equities | High volatility exposure/idiosyncratic volatility associated with lower average returns in the sample | External market and factor specification; sensitive to measurement and controls |
| Amihud (2002), *Illiquidity and Stock Returns* | U.S. stock-market data | Return-to-dollar-volume illiquidity measure; expected illiquidity related to expected excess return | Requires consistent dollar volume; not proof of Thai liquidity premium |
| Lee & Swaminathan (2000), *Price Momentum and Trading Volume* | U.S. equities | Examined the interaction of prior price momentum and trading volume | External market; exact implementation and costs differ |
| Moskowitz & Grinblatt (1999), *Do Industries Explain Momentum?* | U.S. industry portfolios and stocks | Industry momentum accounted for much of individual-stock momentum in their sample | Sector definitions and market structure differ from SET50 |
| Chaysiri et al. (2020), *Tests of Technical Trading Strategies with Different Asset Conditions in the Emerging Markets: Case Study of Thailand SET50 Index* | 19 stocks listed consistently in Thailand SET50 from 2007–2017 | Technical rules varied across asset conditions, including volatility/volume/trading-period conditions | Direct Thailand/SET50-related evidence that motivates research; the fixed-stock sample is not the repository's point-in-time universe and may carry sample-selection/survivorship limitations. It does not validate the repository implementation or prove effects survive universe controls. |

The sources above justify research questions. None establishes that a candidate
is profitable after this project's data, cost, identity, and long-only controls.

## 7. SET50 Applicability and Data Feasibility

The following table distinguishes documented repository characteristics from
possible implications. The implication is a test concern, not a finding.

| Documented characteristic | Possible implication for future alpha research |
|---|---|
| SET50 membership is periodically reviewed and historical evidence is incomplete for several periods | Current constituents could create survivorship bias; every test needs point-in-time eligibility and an explicit unresolved-period policy. |
| Security identity audit records TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI, TIDLOR/NTL, BANPU/BANPUU, SCB/SCBB, TMB/TTB, and MRDIYT boundaries | Momentum, reversal, volatility, and volume measures can be fabricated by concatenating non-continuous securities. Use the identity audit; do not merge by name or ticker resemblance. |
| Research Dataset Gate covers `2022_H2–2026_H2` with mixed readiness statuses | Results may be conditional on the approved subset and cannot be generalized to all 2016 onward without a separate gate decision. |
| Daily OHLCV does not provide historical spread, queue position, or exact fill sequence | Short-horizon reversal, volume, and high-turnover hypotheses are especially sensitive to unobserved execution effects. |
| Project is long-only with fixed commission, VAT, and one-tick slippage assumptions | Long/short literature cannot be transferred mechanically; a future test must report gross and net outcomes under the fixed assumptions. |
| Sector classifications and point-in-time trading-value histories are not established as complete in the current gate | Industry and liquidity hypotheses may be data-limited until historical sources and availability dates are verified. |

## 8. Data Requirements and Readiness

Statuses mean `AVAILABLE`, `AVAILABLE_WITH_LIMITATIONS`, `FLAGGED`, `MISSING`,
`SOURCE_NEEDED`, or `NOT_REQUIRED`. These are feasibility labels, not quality
scores.

| Candidate family | Minimum data required | Current repository status | Consequence |
|---|---|---|---|
| Momentum / trend | Point-in-time membership; security-level daily prices; corporate-action semantics; identity mapping; benchmark | Prices and existing mappings available with limitations; membership and identity have documented gaps | Candidate is researchable only on an explicitly gated subset with exclusions/flags. |
| Mean reversion | Same as momentum, plus reliable short-horizon price continuity and suspension/limit handling | Available with limitations; execution/spread history missing | Daily reversal must be treated as data- and implementation-sensitive. |
| Volatility | OHLC or returns; adjustment policy; identity mapping; point-in-time membership; benchmark | OHLC available with limitations; adjustment and identity cases flagged | Descriptive volatility is feasible; return-effect testing remains conditional. |
| Volume / liquidity | Volume and preferably trading value; price; membership; suspension/limit status; execution assumptions | Daily volume may be available with limitations; complete historical trading value and spread/depth are source-needed | Cannot claim a complete liquidity test from OHLCV alone. |
| Industry / relative strength | Point-in-time sector classification; membership; security returns; benchmark | Historical sector classification is source-needed or limited for the full research window | Test must be deferred or explicitly restricted until classification provenance is verified. |
| Total-return comparison | Authoritative benchmark TRI and documented dividend/corporate-action semantics | Source-needed for a fully aligned security-level implementation | Do not mix price and total-return series. |

No missing item is silently substituted. If a required field is unavailable at
the correct historical timestamp, the candidate must be excluded, flagged, or
reframed as descriptive rather than promoted to a valid predictive test.

## 9. Information-Timing and Leakage Risks

Every future test must declare an information set `I(t)` containing only data
that were available and usable at the decision timestamp. At minimum, the record
must distinguish:

```text
data_timestamp
feature_timestamp
signal_timestamp
execution_timestamp
label_timestamp
information_cutoff
```

Family-specific risks include:

- **Momentum/trend:** using a future close, future ranking, or a completed bar
  for an earlier execution; ranking the universe before applying membership at
  that date.
- **Mean reversion:** using the eventual extreme, a future suspension status, or
  a corporate-action-adjusted history that was revised after the decision.
- **Volatility:** using a full-period volatility estimate, future range, or a
  revised adjusted series; using future regime labels to define the sample.
- **Volume/liquidity:** using end-of-day trading value before the assumed order
  time; treating a later-known halt or liquidity event as known earlier.
- **Industry/relative strength:** using a later sector classification,
  reconstituted index membership, or future constituent weights.

The conservative daily convention is to use a completed bar at `t` and evaluate
execution only at a later permitted session, unless a different convention is
pre-registered and operationally justified.

## 10. Survivorship and Security-Identity Controls

The future test must:

1. apply membership effective at the decision date;
2. preserve additions, removals, delistings, suspensions, and unresolved periods;
3. use the existing security-identity audit as the authority;
4. keep predecessor and successor securities separate until an explicit,
   evidenced policy is approved;
5. document source gaps instead of filling them from current constituents;
6. report results separately for approved, flagged, and excluded data statuses.

A ticker match is not evidence of security continuity. An adjusted price series
also does not solve membership timing, publication timing, or identity continuity.

## 11. Transaction Costs and Implementability Boundary

No profitability or post-cost survival claim is made here. For any later test,
the established assumptions remain:

```text
commission = order_value × 0.00157
VAT        = commission × 0.07
slippage   = one applicable SET price tick
```

The likely sensitivity differs by family:

- momentum/trend: turnover and holding horizon determine cost exposure;
- mean reversion: short holding periods and spread uncertainty may dominate;
- volatility: risk sorting can alter turnover and concentration;
- volume/liquidity: the signal variable may also be an implementation constraint;
- industry/relative strength: sector rotation may create turnover and
  concentration even when the cross-sectional signal is slower.

These are implementation concerns, not evidence that any family survives costs.

## 12. Candidate Alpha Matrix

The status describes evidence and data readiness, not expected profitability and
is not a ranking.

| Alpha family | Hypothesis | Prior evidence | Economic rationale | SET50 relevance | Required data | Main leakage risk | Cost sensitivity | Research status |
|---|---|---|---|---|---|---|---|---|
| Momentum / trend | Past eligible-security returns may predict future relative or own returns | External evidence is substantial; direct Thailand evidence is conditional | Underreaction and gradual information incorporation are proposed mechanisms | Membership, sectors, identity, and long-only constraints matter | PIT membership, daily prices, identity, adjustment policy, benchmark | Future ranking, current-universe substitution, revised prices | Medium to high, depending on turnover | `SUPPORTED_FOR_FURTHER_RESEARCH` |
| Mean reversion / short-term reversal | Extreme recent moves may reverse over a declared horizon | Long-horizon external evidence; short-term SET50 evidence insufficient | Overreaction, price pressure, liquidity provision are proposed mechanisms | Daily OHLCV cannot separate reversal from spread, limits, halts, or actions | PIT prices, OHLC, identity, suspension/limit flags, execution assumptions | Future extreme, future halt, revised corporate actions | High | `MIXED_EVIDENCE` |
| Volatility-related | Observable volatility may relate to future returns beyond market exposure | External evidence is mixed across market-level and cross-sectional settings | Risk compensation, uncertainty, and demand effects are possible mechanisms | Price limits, sectors, and identity can distort volatility estimates | OHLC/returns, adjustment policy, PIT universe, benchmark | Full-sample volatility, future regime labels | Medium | `MIXED_EVIDENCE` |
| Volume / liquidity | Volume or illiquidity may contain incremental information or explain persistence | External evidence exists; SET50 applicability and data completeness limited | Liquidity premium and temporary price pressure are possible mechanisms | Trading value, spread, and execution history are incomplete | Volume, trading value, prices, PIT universe, suspension/limit data | End-of-day information timing, missing-value selection | High | `DATA_LIMITED` |
| Industry / relative strength | Point-in-time sector relative performance may explain future cross-sectional differences | External industry-momentum evidence; no complete SET50 validation | Sector information diffusion and institutional reallocation are possible mechanisms | Small and changing sector membership creates concentration risk | PIT sector classification, membership, prices, benchmark | Future sector labels and reconstituted classifications | Medium | `DATA_LIMITED` |

No row is a recommendation to trade and no row is a winner.

## 13. Falsifiable Future Research Questions

Before any implementation, a separate protocol should state the population,
information set, target horizon, direction, baseline, and rejection conditions.
The following are intentionally conceptual:

1. **Momentum/trend:** Within the point-in-time eligible universe, does a
   pre-declared past-return measure predict future relative returns after market
   and identity-aware controls? Reject if the relationship is not stable across
   declared time splits or is fully explained by market/sector exposure.
2. **Mean reversion:** Do extreme recent moves predict opposite-direction future
   returns after conservative daily timing and execution-quality exclusions?
   Reject the statistical hypothesis if the relationship disappears under the
   declared timing, controls, or out-of-sample evaluation. Evaluate economic
   viability separately under the project's cost and liquidity assumptions.
3. **Volatility:** Does a pre-declared volatility measure retain a directional
   association with future returns after controlling for market and liquidity
   exposure? Reject if it depends on a post-result threshold or unstable sign.
4. **Volume/liquidity:** Does a pre-declared liquidity measure add information
   beyond price movement and market exposure when trading value is available at
   the correct timestamp? Reject if it is only a data-quality or suspension
   proxy.
5. **Industry/relative strength:** Does point-in-time sector relative strength
   explain future returns beyond individual momentum and market exposure? Reject
   if historical sector labels cannot be verified or the effect vanishes after
   composition controls.

These are not parameter grids and do not select a preferred horizon.

## 14. Baselines Required Before Testing

At minimum, a future study should declare:

- a buy-and-hold or simple market-exposure benchmark appropriate to the question;
- a point-in-time SET50 benchmark, keeping price and total-return versions
  separate;
- a cash/no-signal baseline where long-only exposure can be absent;
- for cross-sectional tests, a clearly defined neutral comparison that does not
  introduce an impermissible short leg;
- market, sector, volatility, liquidity, and universe controls where relevant.

Baselines distinguish broad market return from cross-sectional predictive
information and help reveal when a candidate is only a risk or market exposure.
No baseline test is run in this phase.

## 15. Multiple Testing and Research Bias

Future alpha research must record every candidate family, horizon, definition,
universe version, exclusion, missing-data rule, and failed test. The main risks
are:

- trying many families and retaining only successful ones;
- changing lookbacks, holding periods, or thresholds after seeing outcomes;
- repeatedly backtesting the same data until a result appears;
- changing membership, identity, adjustment, or cost rules to improve a result;
- treating external evidence as confirmation of a SET50 effect;
- reporting gross returns while hiding turnover, fees, or execution limitations.

The research protocol must be pre-declared before feature implementation or
backtesting. Exploratory findings must be labeled exploratory and cannot be
presented as independent confirmation.

## 16. What This Phase Does Not Do

This phase does not:

- create Python features or feature columns;
- create signals, entry/exit rules, or strategies;
- run backtests, parameter sweeps, or optimizations;
- train ML models or calculate strategy performance metrics;
- select or rank a winning alpha;
- modify raw OHLCV, historical constituent data, or ticker mappings;
- fabricate missing historical data.

## 17. Phase 4 to Research Protocol Boundary

The required sequence is:

```text
Alpha Research Foundation
        ↓
Candidate Hypotheses
        ↓
Evidence Review
        ↓
Data Feasibility
        ↓
Leakage / Bias Review
        ↓
Research Protocol / Pre-registration
        ↓
Feature Implementation
        ↓
Backtest
```

No feature implementation should begin until a separate protocol declares the
information cutoff, point-in-time universe, security-identity policy, data
exclusions, timing convention, cost model, baselines, evaluation split,
multiple-testing controls, and reporting requirements.

## 18. References

1. [Jegadeesh & Titman (1993), Returns to Buying Winners and Selling Losers](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)
2. [De Bondt & Thaler (1985), Does the Stock Market Overreact?](https://doi.org/10.1111/j.1540-6261.1985.tb05004.x)
3. [Moskowitz, Ooi & Pedersen (2012), Time Series Momentum](https://research.cbs.dk/en/publications/time-series-momentum)
4. [French, Schwert & Stambaugh (1987), Expected Stock Returns and Volatility](https://www.nber.org/system/files/working_papers/w4520/w4520.pdf)
5. [Ang, Hodrick, Xing & Zhang (2006), The Cross-Section of Volatility and Expected Returns](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.2006.00836.x)
6. [Amihud (2002), Illiquidity and Stock Returns](https://doi.org/10.1016/S1386-4181(01)00024-6)
7. [Lee & Swaminathan (2000), Price Momentum and Trading Volume](https://www.lsvasset.com/pdf/research-papers/Price-Momentum-Trad-Vol-2000.pdf)
8. [Moskowitz & Grinblatt (1999), Do Industries Explain Momentum?](https://doi.org/10.1111/0022-1082.00146)
9. [Garman & Klass (1980), On the Estimation of Security Price Volatilities from Historical Data](https://econpapers.repec.org/article/ucpjnlbus/v_3a53_3ay_3a1980_3ai_3a1_p_3a67-78.htm)
10. [Chaysiri et al. (2020), Tests of Technical Trading Strategies with Different Asset Conditions in Thailand SET50](https://so01.tci-thaijo.org/index.php/buacademicreview/article/view/240412)
11. [SET50 profile and methodology](https://www.set.or.th/en/market/index/set50/profile)
12. [SET price bands and tick sizes](https://www.set.or.th/en/market/information/trading-procedure/price-bands-and-tick-sizes)

## Research Boundary Statement

This file is a research foundation only. It contains evidence review,
applicability analysis, data-feasibility notes, and falsifiable hypotheses. It
does not modify source code, production data, raw OHLCV, historical constituent
files, Yahoo mappings, features, signals, strategies, backtests, optimizers,
portfolio construction, or execution logic.

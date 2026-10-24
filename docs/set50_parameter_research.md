# SET50 Parameter Research

**Status:** Research-only documentation
**Date:** 2026-09-22
**Scope:** Long-only SET50 research under the repository's stated competition constraints

## 1. Executive Summary

This document defines **research-supported candidate parameter ranges** for daily SET50 research. It does not select a winning parameter, create a strategy, run a backtest, optimize a parameter, or rank performance.

The evidence supports studying momentum, moving-average/trend rules, volatility measures, and trading-range breakouts. Direct SET50 research exists for moving averages, CCI, and Bollinger Bands under different volatility, volume, and trading-period conditions, but it does not establish a universal best lookback for this project. General finance research provides broader support for momentum persistence over approximately one to twelve months and for studying moving-average and trading-range rules.

The ranges below are therefore hypotheses for a later, pre-registered research design:

| Parameter | Low Risk | Medium Risk | High Risk | Rationale | Evidence |
|---|---:|---:|---:|---|---|
| Momentum lookback | 60–120D | 20–60D | 5–20D | Longer windows are smoother; shorter windows are more responsive and more exposed to noise and turnover. | MEDIUM for broad momentum; LOW for these exact SET50 bands |
| Trend MA | 100–200D | 50–100D | 20–50D | Separates slow, intermediate, and fast trend hypotheses. | MEDIUM for technical-rule relevance; LOW for exact bands |
| Volatility lookback | 20–60D | 10–30D | 5–10D | Longer windows stabilize estimates; shorter windows detect regime changes sooner. | MEDIUM for volatility measurement; LOW for exact bands |
| Breakout lookback | 60–120D | 20–60D | 10–20D | Longer channels reduce false breaks; shorter channels increase responsiveness and false-break risk. | MEDIUM for trading-range rules; LOW for exact bands |
| Holding period | 10–30D or longer | 5–15D | 1–5D | Holding period controls signal decay, turnover, execution burden, and cost exposure. | MEDIUM for momentum horizon; LOW for project-specific bands |

These are **candidate research ranges**, not recommendations that one risk class is superior. “High risk” means shorter horizon, higher turnover, higher volatility exposure, and higher execution sensitivity; it does not mean short selling.

## 2. Research Question

The research question is:

> What parameter ranges are defensible starting points for daily, long-only SET50 research across low-, medium-, and high-volatility/risk operating profiles?

The question is deliberately about ranges and research design. It is not a request to identify the best-performing parameter.

Constraints carried into every future hypothesis:

- Universe: historical SET50 constituents only.
- Position direction: long-only; no short leg or market-neutral construction requiring shorting.
- Initial capital: THB 10,000,000.
- Commission: 0.157% plus 7% VAT on commission.
- Slippage: one tick.
- Allowed order types: Limit and Market-to-Limit IOC.
- Minimum distinct symbols traded: 5.

The constraints above are project requirements supplied in the research brief, not findings from the literature.

## 3. SET50 Market Characteristics

### Sourced facts

SET describes SET50 as a periodically reviewed index universe. The project should therefore treat membership as time-varying and use the constituent set effective at the relevant date, rather than today's constituents for all historical dates. See the [SET50 profile and methodology page](https://www.set.or.th/en/market/index/set50/profile).

A Thailand SET50 study examined 19 stocks that were continuously listed in SET50 from 2007–2017 and evaluated moving averages, CCI, and Bollinger Bands under combinations of volume, volatility, and trading-period conditions. Its abstract explicitly reports that results varied by asset condition and indicator; that is evidence for conditional research, not a universal parameter choice. [Chaysiri et al., 2020](https://so01.tci-thaijo.org/index.php/buacademicreview/article/view/240412)

### Research interpretation

SET50 research should be expected to contain multiple regimes rather than one stable volatility level. Candidate regimes should be defined using observable, rolling information and should be evaluated separately from the parameter definition.

### What remains unknown

This repository does not yet have a complete, canonical, fully verified SET50 membership history for every requested 2016–2022 half-year. Any future SET50-specific parameter result must disclose the universe coverage and unresolved membership periods.

## 4. Parameter Families

The families are intentionally kept separate:

1. **Momentum:** past return over a lookback, either cross-sectional ranking within SET50 or time-series direction for an individual security.
2. **Trend / moving average:** price relative to a moving average, or fast/slow average relationship.
3. **Volatility:** realized dispersion estimated from close-to-close or OHLC data, optionally normalized to annualized units.
4. **Breakout:** price relative to a prior rolling high/low or trading range.
5. **Holding period:** planned minimum or review interval before a position is reconsidered.

The families should not be silently combined into one score during this research phase. A later experiment should state which family is being tested and which other inputs are held constant.

## 5. Momentum Parameter Research

### What it measures

Momentum lookback measures the return accumulated over a prior window. A cross-sectional version ranks SET50 stocks relative to each other; a time-series version asks whether the security's own prior return is positive or negative.

### Evidence

Jegadeesh and Titman documented positive returns from buying past winners and selling past losers over 3–12-month holding periods in U.S. equities. This is broad evidence for studying medium-horizon momentum, not direct evidence that the same windows work in SET50 or under long-only constraints. [Jegadeesh & Titman, 1993](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)

Moskowitz, Ooi, and Pedersen documented time-series momentum across 58 liquid futures and reported persistence over one to twelve months, with partial reversal at longer horizons. This is useful supporting evidence, but the instruments, implementation, and short leg are not identical to daily long-only SET50 stocks. [Moskowitz, Ooi & Pedersen, 2012](https://research.cbs.dk/en/publications/time-series-momentum)

Thailand-specific trade-based research has studied momentum behavior using SET50 stocks and transaction data, but it is not a direct validation of the candidate ranges in this document. [Apiwattanporn, Chulalongkorn University thesis](https://digital.car.chula.ac.th/chulaetd/18922/)

### Candidate ranges

- Low-risk hypothesis: 60–120 trading days.
- Medium-risk hypothesis: 20–60 trading days.
- High-risk hypothesis: 5–20 trading days.

The 5D and 10D cases are intentionally exploratory. They may capture very short-term continuation, reversal, or noise and should not be treated as established momentum evidence.

## 6. Trend / Moving-Average Research

### What it measures

Moving-average rules compare price with a smoothed reference or compare fast and slow averages. The lookback controls lag versus noise sensitivity.

### Evidence

Brock, Lakonishok, and LeBaron tested moving-average and trading-range-break rules on the Dow Jones Index from 1897–1986. Their findings support studying these rule families, but the market, period, and implementation differ from SET50. [Brock, Lakonishok & LeBaron, 1992](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04681.x)

The direct SET50 study cited above found that moving-average results varied across volatility and volume conditions. This supports testing conditional behavior rather than assuming one fixed moving average.

### Candidate ranges

- Short trend: 20–50D.
- Medium trend: 50–100D.
- Long trend: 100–200D.

The risk-level mapping is a research convention: low-risk profiles emphasize the slower part of the range, high-risk profiles the faster part. It is not an empirical ranking.

## 7. Volatility Parameter Research

### What it measures

Volatility lookback estimates recent price variability. Close-to-close volatility is simple and reproducible; OHLC estimators can use more information within each daily bar.

Garman and Klass studied security-price volatility estimation from historical open, high, low, and close data and proposed improved estimators over close-only approaches under their assumptions. This supports comparing estimator choice and lookback separately. [Garman & Klass, 1980](https://econpapers.repec.org/article/ucpjnlbus/v_3a53_3ay_3a1980_3ai_3a1_p_3a67-78.htm)

### Candidate ranges

- Low-risk hypothesis: 20–60D.
- Medium-risk hypothesis: 10–30D.
- High-risk hypothesis: 5–10D.

### Regime definition hypothesis

Do not hard-code a THB or percentage threshold before inspecting the distribution. A defensible initial design is rolling cross-sectional or time-series percentile bands, for example low / medium / high as lower / middle / upper distribution regions. The percentile cutoffs themselves are hypotheses and must not be tuned to historical performance.

## 8. Breakout Parameter Research

### What it measures

A breakout lookback compares current price with a prior rolling high or low. It expresses trend continuation through a trading-range boundary.

Brock, Lakonishok, and LeBaron provide broad evidence that trading-range-break rules are a legitimate research family. The evidence does not establish that a particular 20D, 55D, or 120D channel is optimal for SET50.

### Candidate ranges

- Low-risk hypothesis: 60–120D.
- Medium-risk hypothesis: 20–60D.
- High-risk hypothesis: 10–20D.

Short channels are expected to react earlier but may produce more false breaks. Long channels are expected to react later but may filter more short-lived moves. These are mechanism-based hypotheses, not performance findings.

## 9. Holding Period Research

Holding period is not only a return parameter. It also determines the frequency with which signals are reconsidered and positions are replaced.

The 3–12-month horizon in the classic cross-sectional momentum study supports studying medium-horizon persistence, while the one-to-twelve-month persistence in time-series momentum supports a broad monthly-to-yearly research horizon. Neither source validates a 1–3 day holding period for SET50.

Candidate implementation ranges for this project:

- Low risk: 10–30 trading days or longer.
- Medium risk: 5–15 trading days.
- High risk: 1–5 trading days.

The high-risk range is included because the research brief asks for it, not because the literature establishes it as profitable. Daily OHLCV data can support this level of measurement, but cannot model intraday fill sequencing or bid/ask behavior precisely.

## 10. Transaction Cost Sensitivity

Shorter holding periods generally create more opportunities for turnover, and turnover compounds commission, VAT, spread, market impact, and slippage exposure. The exact relationship must be measured by executed notional turnover in a later experiment rather than assumed from a parameter label.

Research on momentum and transaction costs shows that implementation costs can materially affect post-cost results and that turnover control is an explicit research problem. [Li, Brooks & Miffre, Transaction Costs, Trading Volume and Momentum Strategies](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1406475)

For this project, the later research design must model the fixed competition assumptions exactly:

```text
commission = order_value × 0.00157
VAT        = commission × 0.07
slippage   = one applicable price tick
```

No conclusion about a range should be based only on gross returns. This document does not calculate net performance.

## 11. Long-only Constraint

Many momentum and time-series studies use a long/short construction. Those results can support the existence of a research phenomenon, but the short leg is not directly compatible with this competition.

The appropriate translation for this project is a long-only rule such as:

- rank eligible SET50 securities and hold selected positive candidates;
- hold cash when a signal does not justify a long position;
- never create a synthetic short leg or market-neutral hedge requiring shorting.

This translation is a research design hypothesis, not evidence that a long-only implementation will preserve the published result.

## 12. Three Risk / Volatility Levels

“High risk” here means a long-only profile with shorter horizon, faster reaction, more turnover, greater volatility exposure, and higher execution sensitivity. It does not mean short selling.

| Level | Operating interpretation | Typical research emphasis |
|---|---|---|
| Low | Lower turnover, smoother signals, longer holding horizon, lower cost sensitivity | 60–120D momentum; 100–200D trend; 20–60D volatility; 60–120D breakout; 10–30D+ holding |
| Medium | Balance between responsiveness and turnover | 20–60D momentum; 50–100D trend; 10–30D volatility; 20–60D breakout; 5–15D holding |
| High | Shorter horizon, higher turnover, greater noise and execution sensitivity | 5–20D momentum; 20–50D trend; 5–10D volatility; 10–20D breakout; 1–5D holding |

The labels organize hypotheses. They are not risk scores and are not a ranking of strategies.

## 13. Recommended Research Ranges

“Recommended” here means recommended for the **next research design**, not recommended for live trading.

The ranges in the Executive Summary should be used as a bounded, explainable starting grid. A later study should pre-register which values inside each range are examined, define signal timing, and report all tested values without selecting one based on the same sample's outcome.

Do not expand the ranges merely because an initial result is weak. Do not narrow them merely because one value looks attractive.

## 14. Evidence Strength

Evidence ratings in this document mean:

- **HIGH:** direct SET50-specific evidence from multiple strong sources. No parameter family in this document reaches this level for an exact numerical range.
- **MEDIUM:** credible Thailand/emerging-market or broad academic evidence supporting the research family or approximate horizon.
- **LOW:** hypothesis or operational translation requiring direct SET50 validation.

The direct SET50 technical-analysis source is **MEDIUM** for studying indicator behavior under different asset conditions, but **LOW** for the exact ranges proposed here. The classic momentum and technical-rule papers are **MEDIUM** supporting evidence for research direction, not direct SET50 proof.

## 15. Limitations

1. The evidence is not a backtest of this repository's implementation.
2. The historical SET50 constituent audit is incomplete for 2016–2022; some periods remain unresolved.
3. Daily OHLCV cannot establish intraday execution quality, queue position, bid/ask spread, or IOC fill probability.
4. The cited long/short literature is not directly compatible with the competition's long-only rule.
5. Different papers use different universes, markets, data cleaning, rebalance timing, and cost assumptions.
6. Technical indicators can be sensitive to data snooping, parameter selection, and survivorship bias.
7. The proposed risk bands are labels for research scenarios, not measured volatility classes for SET50.
8. No company/security identity continuity was solved here.

## 16. Research Gaps

- Complete and authoritative SET50 membership for every requested historical half-year.
- A clean historical price dataset aligned to membership effective dates.
- Direct SET50 evidence comparing the proposed lookback ranges.
- Long-only implementation evidence after the required fees and one-tick slippage.
- A reproducible rule for missing prices, suspensions, corporate actions, and ticker changes.
- Empirical volatility-regime definitions using only information available at each decision date.
- Execution-quality evidence for the actual order types allowed by the competition.
- Robustness checks across time splits and membership revisions.

## 17. Next Research Steps

1. Finish the historical SET50 universe evidence audit; do not promote unresolved periods into the canonical file.
2. Validate the daily OHLCV source and security identity mapping for the verified research universe.
3. Write a pre-registration for signal timing, universe timing, cost model, and evaluation windows.
4. Perform descriptive, non-performance analysis first: distributions, turnover implications, missingness, volatility regimes, and signal frequency.
5. Only after the data gate is passed, run separately documented long-only experiments across the predefined ranges.
6. Report all range members, costs, turnover, drawdowns, and failure cases; do not optimize silently.

## 18. References

1. [Stock Exchange of Thailand — SET50 profile and methodology](https://www.set.or.th/en/market/index/set50/profile)
2. [Chaysiri, Jeenanunta & Senanayake Ihala Gamage (2020), Tests of Technical Trading Strategies with Different Asset Conditions in the Emerging Markets: Case Study of Thailand SET50 Index](https://so01.tci-thaijo.org/index.php/buacademicreview/article/view/240412)
3. [Chaysiri et al. (2019), The Profitability of Moving Average Trading Strategies in the Thailand SET50 Index: Past and Future](https://sc01.tci-thaijo.org/index.php/tureview/article/view/186840)
4. [Jegadeesh & Titman (1993), Returns to Buying Winners and Selling Losers](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1993.tb04702.x)
5. [Moskowitz, Ooi & Pedersen (2012), Time Series Momentum](https://research.cbs.dk/en/publications/time-series-momentum)
6. [Brock, Lakonishok & LeBaron (1992), Simple Technical Trading Rules and the Stochastic Properties of Stock Returns](https://onlinelibrary.wiley.com/doi/10.1111/j.1540-6261.1992.tb04681.x)
7. [Garman & Klass (1980), On the Estimation of Security Price Volatilities from Historical Data](https://econpapers.repec.org/article/ucpjnlbus/v_3a53_3ay_3a1980_3ai_3a1_p_3a67-78.htm)
8. [Apiwattanporn, Trade-based analysis of momentum: evidence from Thailand](https://digital.car.chula.ac.th/chulaetd/18922/)
9. [Li, Brooks & Miffre, Transaction Costs, Trading Volume and Momentum Strategies](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1406475)

## Research Boundary Statement

This file contains sourced evidence, explicit limitations, and research hypotheses only. It does not modify source code, strategy code, feature code, backtests, optimizers, production data, historical universe files, Yahoo mappings, or the Research Dataset Gate.

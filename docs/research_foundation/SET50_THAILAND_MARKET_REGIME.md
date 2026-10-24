# Thailand Market Regime Research Foundation

**Status:** `READY_FOR_AUDIT`  
**Date:** 2026-09-22  
**Scope:** Thailand equity-market and SET50 regime context for the repository research window, `2022_H2`–`2026_H2`  
**Boundary:** Research foundation only. This document does not create features, signals, strategies, backtests, optimizations, or trading rules.

## 1. Research Objective

This phase documents observable Thailand equity-market conditions that may affect
later SET50 research. It establishes a reproducible vocabulary for describing
market context and records what is known, what is an interpretation, and what
remains a hypothesis.

The objective is not to identify a profitable regime rule or to claim that a
regime predicts returns. Any later use of regimes must be declared before the
relevant experiment and must use information available at the decision time.

## 2. Research Scope

The repository's current research-data scope is `2022_H2` through `2026_H2`.
It does not include `2022_H1` in the Research Dataset Gate. The historical SET50
universe is time-varying, and the repository records material gaps in earlier
membership evidence and security identity continuity.

This phase therefore covers:

- Thailand listed-equity context, with SET and SET50 index evidence where
  available;
- the half-year research periods already used by the repository;
- descriptive market dimensions: direction, drawdown, volatility, liquidity,
  breadth/leadership, and macro or policy context;
- limitations caused by incomplete historical membership, identity, and daily
  data coverage.

It does not cover intraday execution, security-level feature construction,
portfolio construction, or performance attribution.

## 3. Definitions

The following terms are descriptive labels, not trading signals:

| Term | Meaning in this document |
|---|---|
| Uptrend | Sustained positive movement or recovery in the selected index observation window. |
| Downtrend | Sustained negative movement or loss from a prior reference peak. |
| High-volatility period | A period whose observed return dispersion or range is high relative to the declared comparison sample. No threshold is selected here. |
| Low-volatility period | A period whose observed dispersion or range is low relative to the declared comparison sample. No threshold is selected here. |
| Drawdown | Decline from a prior observed peak, measured separately for price and total-return series where available. |
| Liquidity stress | Reduced turnover, wider execution uncertainty, or impaired tradability; daily index value alone is not sufficient to measure all components. |
| Recovery | A rebound after a drawdown. Recovery does not imply that the prior peak was regained. |
| Regime | A descriptive combination of market dimensions over a declared period, not a hidden state inferred from future data. |

## 4. Thailand Equity Market Structure

The SET Index is a market-capitalization-weighted price index of common stocks
on the SET main board, with adjustments intended to remove effects unrelated to
price movement. SET50 is a reviewed, liquid large-cap subset rather than a
permanent list of securities. SET index methodology describes periodic reviews,
eligibility, constituent selection, and changes between reviews.

For research, this has three consequences:

1. SET and SET50 price indices are not interchangeable.
2. Price indices and total-return indices must not be mixed in one return series.
3. A market regime label is not enough to resolve constituent membership or
   security identity.

## 5. SET50 Structure and Historical Membership

The repository's canonical later-period constituent file is
`data/processed/constituents/historical_set50.csv`, covering `2023_H1` through
`2026_H2`. The historical-universe audit contains five complete cited tables for
2017_H1, 2020_H2, 2021_H2, 2022_H1, and 2022_H2; other 2016–2022 periods are
partial or unresolved.

The repository separately documents identity discontinuities including
TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI, TIDLOR/NTL, BANPU/BANPUU, SCB/SCBB,
TMB/TTB, and MRDIYT. These are not silently merged in this phase.

Accordingly, this document may describe broad market context for the research
window, but it does not assert that every historical SET50 security is available
or continuously represented in the price data.

## 6. Research Data and Sources

### Repository evidence

- [Research Dataset Gate](../../reports/pilot/research_dataset_gate.md): current
  scope and row-level readiness status.
- [Historical universe audit](../../reports/pilot/historical_universe_2016_2022/historical_universe_2016_2022_audit.md): provenance and gaps in historical membership.
- [Historical security identity audit](HISTORICAL_SECURITY_IDENTITY_AUDIT.md):
  predecessor/successor and ticker-boundary risks.
- [Research data readiness](RESEARCH_DATA_READINESS.md): approved, flagged,
  review, and rejected data status.
- [SET50 research methodology](SET50_RESEARCH_METHODOLOGY.md): information-set,
  timing, bias, and governance controls.
- [Market microstructure foundation](SET50_MARKET_MICROSTRUCTURE.md): daily-data
  and execution limitations.

### External authoritative sources

- [SET50 profile and methodology](https://www.set.or.th/en/market/index/set50/profile)
- [SET Index profile](https://www.set.or.th/en/market/index/set/profile)
- [SET Index methodology](https://media.set.or.th/set/Documents/2022/Nov/SET-Index-Methodology_EN_Nov2022.pdf)
- [SET full-year 2023 market report](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=85535400&symbol=SET)
- [SET Annual Report 2024](https://media.set.or.th/set/Documents/2025/May/SET_Annual_Report_2024_ENG.pdf)
- [SET full-year 2025 market report](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=100717700)
- [SET One Report 2025](https://media.set.or.th/set/Documents/2026/May/SET_56-1_OneReport_2025_EN.pdf)
- [BOT Financial Stability Report 2024](https://www.bot.or.th/content/dam/bot/documents/en/research-and-publications/reports/financial-stability-report/FSR2024e.pdf)
- [BOT Financial Stability Review 2025](https://www.bot.or.th/content/dam/bot/documents/en/research-and-publications/reports/financial-stability-report/FS_Review_2025e.pdf)
- [Thai Economic Indicators 2025](https://www.nso.go.th/public/e-book/Indicators-Economic/Thai_Economic_Indicators_2025/187/)
- [BOT Monetary Policy Report archive](https://www.bot.or.th/en/our-roles/monetary-policy/mpc-publication/Monetary-Policy-Report.html)

The external sources are used for market/index context only. They do not
replace the repository's universe, mapping, or data-gate artifacts.

## 7. Regime Identification Methodology

This phase uses an ex-post descriptive protocol. It does not fit a predictive
regime model.

### 7.1 Required observations

For each declared period, later analysis should keep separate columns for:

- SET50 price-index close, high, and low;
- SET50 total-return index, if available from the same authoritative source;
- period return and peak-to-trough drawdown;
- return dispersion or range, with the lookback and annualization declared;
- SET and SET50 trading value or turnover proxies, where consistently available;
- sector or constituent leadership summaries, only after point-in-time universe
  and identity gates are satisfied;
- relevant macro, policy, or market-structure context.

### 7.2 Labeling rule

Regime descriptions should be based on declared observations and comparison
windows, not on later strategy performance. If a period has mixed dimensions,
use a compound description such as “downtrend with late recovery” rather than
forcing one scalar label.

Thresholds for “high” and “low” volatility or liquidity stress are deliberately
not fixed in this foundation document. They must be pre-declared before Phase 4,
kept constant for the registered experiment, and not selected by maximizing
historical results.

### 7.3 Information timing

An ex-post report may use the complete period to describe what happened. A
future real-time regime input may use only an expanding or rolling history ending
before the decision timestamp. It must not use the period's eventual close,
future drawdown, future constituent membership, or future sector leadership.

## 8. Historical Market Regimes

The following are evidence-backed descriptive episodes, not strategy regimes.

### 8.1 2022_H2–2023: broad index weakness and declining year-end levels

**Observed:** The SET Index closed 2022 at 1,668.66 and 2023 at 1,415.85;
SET reported the 2023 year-end level as 15.2% below year-end 2022. The official
Thai Economic Indicators table reports SET50 closes of 1,005.2 in 2022 and
875.3 in 2023, with a 2023 high of 1,018.0 and low of 841.2.

**Research period:** This section discusses the repository's combined
`2022_H2–2023` context. **Evidence resolution:** The supporting index evidence
is annual; it does not establish a precise half-year regime boundary.

**Interpretation:** The available annual evidence supports describing 2023 as
broad index weakness relative to the 2022 year-end level. This is a broad index
description, not evidence that every SET50 constituent behaved similarly or a
formally measured risk-off regime.

**Context:** SET attributed the 2023 environment to factors including global
rate expectations, inflation developments, and changing recession expectations;
these are contextual explanations reported by SET, not a causal identification
performed by this repository.

### 8.2 2024: weak / drawdown-prone period with a late recovery

**Observed:** SET closed 2024 at 1,400.21, versus 1,415.85 at end-2023. BOT
reported a 2024 low of 1,274.01 and described a temporary Q4 rebound. The Thai
Economic Indicators table reports SET50 close 906.2, high 956.5, and low 800.1
for 2024. SET's 2024 average daily trading value across SET and mai was THB
46.55 billion, down 12.7% year over year.

**Interpretation:** 2024 is reasonably described as a weak, drawdown-prone
period with a late recovery attempt, not as a sustained bull market. Any
qualitative impression of range-like movement is not a formal range-bound metric
because no such metric was calculated here. The price-index and SET50 evidence
should remain separate from total-return interpretation.

**Context:** BOT and SET reported political, economic, governance, foreign-asset
return, and market-confidence factors around this period. These reports provide
context; they do not prove which factor caused each daily movement.

### 8.3 2025: first-half decline followed by partial recovery

**Observed:** SET reported a 2025 close of 1,259.67, down 10.0% from end-2024.
SET's 2025 report states that the index recovered 18.5% from its June low by
year-end, while BOT's 2025 review described a first-half decline and a third-
quarter recovery. SET and mai average daily trading value in 2025 was reported
at approximately THB 41.41 billion, below 2024.

**Interpretation:** The evidence supports “first-half decline followed by
partial recovery” for 2025. “Stress” may be used only as a qualitative
description of the observed decline; it is not a formally measured volatility
or dispersion regime. The evidence does not support labeling the whole year as
a single low-volatility or high-volatility state.

**Context:** Official sources mention earthquake effects, trade-policy
uncertainty, domestic political and economic concerns, and later policy and
political clarity. These are recorded as contemporaneous explanations, not
future information used in a live signal.

### 8.4 2026_H1–2026_H2: current and incomplete observation window

**Observed:** The repository includes 2026_H1 and 2026_H2 in its current gate
scope, but 2026_H2 is not a completed calendar half-year as of 2026-09-22.
The BOT statistical series and SET current pages are useful for monitoring, but
the current period has not been converted here into a validated historical
regime table.

**Interpretation:** This period must remain `CURRENT_INCOMPLETE` for this
foundation. No completed-period regime conclusion should be used for it until
the observation window closes and the underlying data are audited.

## 9. Evidence Table

| Period | SET / SET50 evidence | Liquidity evidence | Regime description | Evidence status |
|---|---|---|---|---|
| 2022_H2–2023 | SET 1,668.66 at end-2022 to 1,415.85 at end-2023; SET50 1,005.2 to 875.3 | Annual liquidity comparison requires a consistent period series | Broad index weakness and declining year-end levels; annual evidence does not establish a precise half-year boundary | `OBSERVED_WITH_LIMITATIONS` |
| 2024 | SET 1,400.21 at year-end; low 1,274.01; SET50 906.2 with 800.1 low | SET+mai ADV THB 46.55bn, -12.7% YoY | Weak / drawdown-prone period with a late recovery | `OBSERVED_WITH_LIMITATIONS` |
| 2025 | SET 1,259.67; -10.0% YoY; +18.5% from June low by year-end | SET+mai ADV approximately THB 41.41bn | First-half decline followed by partial recovery | `OBSERVED_WITH_LIMITATIONS` |
| 2026_H1 | Repository gate scope exists; full source audit for regime metrics not completed here | Not classified | Current transition; no final label | `INCOMPLETE` |
| 2026_H2 | Half-year is incomplete as of 2026-09-22 | Not classified | Current/incomplete observation window | `INCOMPLETE` |

## 10. Regime Summary Table

| Regime label | Approximate period | Direction | Volatility / drawdown | Liquidity / participation | Confidence |
|---|---|---|---|---|---|
| Broad index weakness and declining year-end levels | 2022_H2–2023 | Negative by year-end 2023 relative to year-end 2022 | Annual evidence only; full dispersion not calculated here | Not fully harmonized | Medium |
| Weak / drawdown-prone with late recovery | 2024 | Flat-to-negative year-end with Q4 recovery | Material index low; no formal range-bound metric calculated | Trading value lower YoY | Medium |
| First-half decline followed by partial recovery | 2025 | Negative year-end, rebound from June low | Qualitative decline/recovery description; full dispersion not calculated here | Trading value lower than 2024 | Medium |
| Current incomplete | 2026_H1–2026_H2 | Not finalized | Not finalized | Not finalized | Low |

Confidence expresses evidence completeness and classification ambiguity; it is
not confidence that a regime label predicts returns.

## 11. Structural Changes and Important Events

Important structural considerations for later research include:

- SET50 periodic review and constituent changes mean membership is point-in-time,
  not a static list.
- Corporate actions, ticker changes, and predecessor/successor securities can
  break naive price continuity. The repository's identity audit must be used
  before any continuity assumption.
- SET methodology and eligibility changes can alter the composition or
  comparability of the index universe. Methodology notices and review documents
  should be archived with any future dataset revision.
- Market-wide measures such as tax-incentive funds, buybacks, foreign flows,
  and policy changes may affect liquidity or participation, but their effects
  should not be coded as causal features without a separate design.
- Daily OHLCV cannot reveal queue position, bid/ask spread, intraday liquidity,
  or order-fill probability. A daily regime label cannot solve that limitation.

## 12. Research Interpretation

The evidence supports treating the research window as heterogeneous rather than
assuming one stable Thailand market condition. The documented sequence contains
a broad decline in 2023, weak and drawdown-prone conditions with a late recovery
in 2024, and a 2025 first-half decline followed by partial recovery. The
supporting 2022–2023 evidence is annual and does not establish a precise
half-year regime boundary. The current 2026 window is not yet complete.

This foundation supports stratified descriptive analysis later, but it does not
establish that any factor, signal, or parameter works better in any label. A
future result must report the exact period definitions, constituent coverage,
identity policy, source availability, and whether the label was available at the
decision time.

## 13. Hypotheses for Phase 4 Alpha Research

These are research questions only; none is implemented or validated here:

1. Does a long-only SET50 research result differ between broad downtrend,
   drawdown/rebound, and recovery periods after applying the fixed cost model?
2. Are missingness, security identity uncertainty, and constituent turnover
   concentrated in particular market episodes?
3. Does a volatility or range descriptor add information beyond a simple
   price-trend descriptor when both are defined without lookahead?
4. Are apparent period differences robust when the analysis uses SET50 price
   index and total-return index separately?
5. Do conclusions survive exclusion of periods or securities with unresolved
   identity or source-quality status?

These questions must not be turned into feature code or backtest rules until a
separate research protocol declares the data, timing, split, costs, metrics,
and multiple-testing controls.

## 14. Bias and Leakage Controls

- Use point-in-time SET50 membership; never use the current constituent list for
  past periods.
- Keep predecessor/successor securities separate unless an explicit, evidenced
  identity policy is approved.
- Do not use future index levels, future drawdowns, future volatility, future
  sector leadership, or later reports when constructing a historical decision
  input.
- Separate price-index and total-return calculations and document dividends or
  corporate-action treatment.
- Declare regime thresholds and lookbacks before evaluating Phase 4 outcomes;
  do not optimize labels on the same sample.
- Report incomplete periods rather than carrying end-of-period knowledge
  backwards.
- Preserve source provenance, retrieval date, revision state, and the exact
  observation window for every external series.
- Treat Yahoo/source availability as an availability observation, not proof of
  historical security continuity.
- Report results by data-quality status and run sensitivity checks excluding
  flagged rows; do not silently impute unresolved history.

## 15. Limitations

1. The repository's historical SET50 membership evidence is incomplete for
   several 2016–2022 periods; this Phase 3 scope inherits the documented later
   gate rather than repairing that gap.
2. The current research gate begins at 2022_H2 and therefore does not support a
   complete 2016-onward regime history.
3. This document records official annual and contextual evidence but does not
   calculate a new monthly/quarterly volatility or drawdown dataset.
4. 2026_H2 is incomplete as of the document date.
5. Index-level observations can conceal large cross-sectional differences among
   SET50 securities.
6. Reported explanations from SET or BOT are contextual narratives, not causal
   estimates.
7. Daily OHLCV cannot establish intraday execution quality, spread, queue, or
   fill probability.
8. Historical source revisions, corporate actions, suspensions, and identity
   boundaries may change comparability.
9. The regime labels are descriptive hypotheses and have no demonstrated
   predictive value.

## 16. Audit Checklist

Before this foundation is treated as audited, a reviewer should confirm:

- [ ] The repository scope is correctly stated as `2022_H2`–`2026_H2`.
- [ ] SET and SET50 price-index figures are traceable to official sources.
- [ ] SET50 price and total-return series are not mixed.
- [ ] 2026_H2 is marked incomplete as of 2026-09-22.
- [ ] Historical membership and identity limitations are linked to repository
      evidence.
- [ ] Every regime row distinguishes observation from interpretation.
- [ ] No regime threshold was selected from strategy performance.
- [ ] No feature, signal, strategy, backtest, or optimization was created in
      this phase.
- [ ] External source dates and URLs remain reproducible.
- [ ] A future Phase 4 protocol declares timing, splits, costs, and metrics
      before outcome evaluation.

## 17. References

1. [SET50 profile and methodology](https://www.set.or.th/en/market/index/set50/profile)
2. [SET Index profile](https://www.set.or.th/en/market/index/set/profile)
3. [SET Index methodology](https://media.set.or.th/set/Documents/2022/Nov/SET-Index-Methodology_EN_Nov2022.pdf)
4. [SET full-year 2023 market report](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=85535400&symbol=SET)
5. [SET Annual Report 2024](https://media.set.or.th/set/Documents/2025/May/SET_Annual_Report_2024_ENG.pdf)
6. [SET full-year 2025 market report](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=100717700)
7. [SET One Report 2025](https://media.set.or.th/set/Documents/2026/May/SET_56-1_OneReport_2025_EN.pdf)
8. [BOT Financial Stability Report 2024](https://www.bot.or.th/content/dam/bot/documents/en/research-and-publications/reports/financial-stability-report/FSR2024e.pdf)
9. [BOT Financial Stability Review 2025](https://www.bot.or.th/content/dam/bot/documents/en/research-and-publications/reports/financial-stability-report/FS_Review_2025e.pdf)
10. [Thai Economic Indicators 2025](https://www.nso.go.th/public/e-book/Indicators-Economic/Thai_Economic_Indicators_2025/187/)
11. [BOT Monetary Policy Report archive](https://www.bot.or.th/en/our-roles/monetary-policy/mpc-publication/Monetary-Policy-Report.html)

## Research Boundary Statement

This file is a research foundation and audit draft. It does not modify source
code, production data, raw OHLCV, historical constituent files, Yahoo mappings,
features, signals, strategies, backtests, optimizers, or trading execution.

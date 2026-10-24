# Research Candidate Discovery Status

Run `20261023T154742Z_candidate_discovery` completed on 2026-10-23. This is an exploratory research record, not a strategy selection or execution authorization.

## Data and method

- Approved daily research loader and point-in-time eligibility gate; 20 symbols were available at some point, with 18 spanning the core 2023-01-03 to 2026-09-04 period and two later-start series. There are 898 union observation dates. Coverage is partial and per-symbol dates differ.
- Historical membership/approved-data support before 2023 is unavailable. Results are not presented as survivorship-safe pre-2023 evidence.
- Features use adjusted close for returns, raw daily OHLC for bar fields, and reported volume only as a coarse activity proxy. No historical spread, depth, or BBO was synthesized.
- Signal decisions occur at an observed close and execution is attempted at the next observed session open. The unchanged `RESEARCH_EXECUTION_V1` model requests one tick of adverse price impact and fills only when that request falls inside the next observed bar range. This is a research assumption, not an organizer-confirmed fill rule.
- Commission 0.157%, VAT 7% of commission, one tick, LIMIT/IOC, equal weight up to 10 names, and a three-observation rebalance cadence. Capital resets nowhere within the full period. All positions are long-only and cash constrained by the existing research engine.
- No investable equal-weight buy-and-hold comparator was constructed because the approved universe and observation coverage change by date; using a static cohort would introduce survivorship/coverage distortion. Existing A/C/D0 research runs are retained as systematic references.
- Feature windows are causal. The breakout compares the current close against the prior 20 observed highs; mean reversion uses the current five-observation adjusted-close return and current SMA50. Signals are read only as of each rebalance timestamp.
- Explicit checks are recorded in [`no_lookahead_candidate_audit.json`](../reports/no_lookahead_candidate_audit.json): no future rows, centered windows, future-normalized ranks, or same-bar fills were identified. Survivorship status is partial because pre-2023 historical membership evidence is insufficient.

## Hypotheses and candidates

Machine-readable specifications are in [`research_hypothesis_specs.json`](../reports/research_hypothesis_specs.json). The four fixed candidates were tested once; no grid search or OOS tuning was performed.

| Candidate | Hypothesis | Entry / ranking | Net return | Gross return | Max drawdown | Turnover | Fills / non-fills | Evidence |
|---|---|---|---:|---:|---:|---:|---:|---|
| CANDIDATE_TREND20 | H1 proxy | Positive 20-session momentum, close above SMA20; rank momentum | -69.80% | -59.04% | -74.68% | 64.02x | 1,523 / 696 | REJECTED_STAGE_1 |
| CANDIDATE_BREAKOUT20 | H2 partial | Close above prior 20 observed highs and volume ratio >= 1; rank breakout excess | -43.98% | -33.95% | -48.25% | 59.69x | 148 / 66 | REJECTED_STAGE_1 |
| CANDIDATE_MEANREV5 | H5 partial | Five-observation return below -5%, close above SMA50; rank pullback size | -4.37% | +11.26% | -39.33% | 93.07x | 205 / 83 | REJECTED_STAGE_1 |
| CANDIDATE_REL_STRENGTH | H3 partial | Positive 20-session momentum; rank momentum | -68.41% | -57.52% | -74.05% | 64.82x | 1,544 / 704 | REJECTED_STAGE_1 |

All four candidates failed the predefined Stage 1 net-return gate. The two largest turnover candidates lost about THB 1.08m in fees and THB 4.26–4.31m in modeled slippage. Breakout lost about THB 1.00m in fees and THB 3.70m in modeled slippage. MeanRev5 generated positive gross return but lost about THB 1.56m in fees and THB 6.46m in modeled slippage, ending down THB 0.44m net with a 39.33% maximum drawdown. A positive gross result did not survive costs.

Prior fixed-parameter baselines are also weak: the existing five-fold A and C studies report mean OOS net returns of -3.56% and -3.39%, compounded independent-fold returns of -20.07% and -19.12%, and 2/5 positive folds each. Prior D0 turnover control reports fold returns of -3.02%, -11.06%, +11.82%, -3.47%, and -1.70% (1/5 positive). The final A/C fold has only 18 observations and is low confidence. These are preserved prior experiments, not newly repeated candidates.

`gross_return` includes the price effect of modeled slippage but excludes separately reported commission/VAT. `slippage` is the engine's one-tick modeled cost. Turnover is filled notional divided by starting capital. FIFO attribution and annual equity changes are available in the machine-readable summary; realized symbol attribution excludes open lots and should not be mistaken for total mark-to-market symbol contribution.

## Walk-forward, robustness, and official simulator gate

No candidate passed Stage 1, so walk-forward folds, cost perturbations, delay tests, and regime robustness were deliberately not run. There are therefore no new OOS folds or robustness survivors. Existing Design A/C/D0 walk-forward evidence remains separately registered as historical prior research and is not conflated with these candidates.

Promotion result: `NO_CANDIDATE_PASSED_PROMOTION_GATE`. No candidate was promoted to official TradeSim 0.2.6, and no candidate-level one-day or multi-day simulator validation was run. The current local official TradeSim 0.2.6 environment check is READY on the exact Python 3.13.0 venv; this is runtime availability, not candidate performance validation. Earlier engine smoke artifacts are simulator smoke only.

Competition qualification and award thresholds remain `RULE_CONFIRMATION_REQUIRED`; this research does not infer them. Order legality has an unresolved discrepancy between the project competition briefing and TradeSim's exposed order behavior; see `docs/STRATEGY_IMPLEMENTATION_DECISIONS.md` and the final human decisions.

## Evidence limits and rejection reasons

- Candidate results use partial approved daily coverage and a small, date-varying universe. Missing symbols/dates are not imputed.
- Historical BBO/spread/depth and a defensible historical liquidity condition are unavailable. H1/H4 are `NEEDS_MORE_DATA`; H2 and H5 were only partially tested; H3 breadth conditioning was not tested.
- Bar-based LIMIT/IOC fills are not official TradeSim fills. Results are highly sensitive to the documented fill/slippage assumptions.
- Candidate rejects: all had negative net full-period return. MeanRev5 is closest to breakeven but its drawdown and turnover remain large and it has no OOS validation.
- Four candidates from five hypotheses is a small search, but prior Design A/C/D0 work plus this set adds multiple-testing exposure. No p-value or proof-of-edge claim is made.
- Regime attribution and formal symbol/date bootstrap intervals were not run after Stage 1 rejection. Annual equity changes and FIFO distribution are descriptive diagnostics only.

## CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW

`NO_CANDIDATE_PASSED_PROMOTION_GATE`; no candidate is recommended for selection. MeanRev5 is listed only as the least negative exploratory diagnostic, not as a surviving or promotable candidate. It needs a new, predeclared hypothesis, lower-turnover portfolio design, and independent walk-forward validation before reconsideration.

## HUMAN_DECISIONS_REQUIRED

1. Confirm the authoritative competition order types and validity; the local briefing permits LIMIT and MARKET_TO_LIMIT IOC, while the simulator/report evidence shows a rule/API discrepancy.
2. Provide the authoritative competition qualification and award criteria, or confirm that these remain unknown.
3. Decide whether the team wants to invest in a lower-turnover research redesign after reviewing the negative candidate funnel; no further search should silently tune to this same historical period.
4. Confirm the acceptable research execution model or provide approved historical execution data. `RESEARCH_EXECUTION_V1` is only a diagnostic approximation.

## Readiness

| Area | Status |
|---|---|
| Approved data / PIT gate | PARTIAL; useful daily history, limited universe and dates |
| Candidate specifications / registry | COMPLETE for this bounded experiment |
| First-pass backtests and cost audit | COMPLETE; 4/4 rejected |
| Walk-forward / robustness | NOT RUN AFTER STAGE-1 REJECTION |
| Candidate-level official TradeSim | NOT RUN; no promotion candidate |
| TradeSim 0.2.6 runtime | READY; exact Python 3.13.0 and imports verified |
| Human strategy selection | NOT READY; no candidate passed |
| Real-order readiness | NOT AUTHORIZED; zero orders placed |

## Validation

- Focused candidate/backtest/feature tests: 18 passed.
- Full suite: 271 passed, 1 skipped in 87.90s using the approved elevated rerun after workspace-local pytest cleanup failed with Windows `WinError 5`.
- `compileall` passed for `src`, `scripts`, `ui`, and `tests`.
- `git diff --check` passed; Git emitted line-ending warnings and could not inspect several pre-existing ACL-restricted temp directories. No whitespace error was reported.
- Secret-pattern scan of task-created code and report files found no credential-like literals.

Next work should resolve the order-rule authority, acquire approved PIT historical liquidity/execution observations if available, and develop a separately pre-registered lower-turnover hypothesis. Do not select a competition strategy from this report.

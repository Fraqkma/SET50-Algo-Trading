# SET50 Research Progress

**Status vocabulary:** `NOT_STARTED`, `IN_PROGRESS`, `COMPLETE`,
`COMPLETE_WITH_LIMITATIONS`, `BLOCKED`, `DEFERRED`, `LOCKED`

This document is a status index, not a duplicate of the underlying research. A
status is based on files and evidence currently present in the repository; it does
not imply that a legacy implementation is validated for the current research path.

## 1. Project Overview

The repository is a Python SET50 long-only trading project with separate data,
research, strategy, risk, execution, and evaluation areas. The current research
priority remains data validity, point-in-time universe integrity, security identity,
and execution realism before new strategy claims.

## 2. Research Pipeline

```text
DATA FOUNDATION
├── Historical Universe
├── Source Audit
├── Yahoo Ticker Audit
├── Security Identity
├── Market Data
└── Data Validation

RESEARCH FOUNDATION
├── Methodology
├── Market Microstructure
├── Thailand Market Regime
└── Alpha Research

RESEARCH DESIGN
├── Parameter Research
└── Research Protocol

IMPLEMENTATION
├── Features
├── Signals
├── Strategy
└── Backtest

EVALUATION
├── OOS
├── Optimization
└── Robustness

DEPLOYMENT
└── Paper Trading
```

## 3. Data Foundation

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Historical SET50 Universe | COMPLETE_WITH_LIMITATIONS | [Historical universe audit](../reports/pilot/historical_universe_2016_2022/historical_universe_2016_2022_audit.md) | Five 2016–2022 periods have complete cited tables; remaining periods are partial or unresolved. |
| SET Data Audit | COMPLETE_WITH_LIMITATIONS | [Constituent audit](CONSTITUENT_AUDIT.md) | Official later-period snapshots exist; historical gaps and symbol issues remain. |
| Yahoo Ticker Audit | COMPLETE_WITH_LIMITATIONS | [Yahoo ticker audit](../reports/yahoo_ticker_audit.md) | Existing mapping is available, but historical identity limitations remain. |
| Security Identity | COMPLETE_WITH_LIMITATIONS | [Security identity audit](HISTORICAL_SECURITY_IDENTITY_AUDIT.md) | Several predecessor/successor cases remain separate or require explicit mapping policy. |
| Historical Data Availability | COMPLETE_WITH_LIMITATIONS | [Availability report](../reports/pilot/historical_set50_data_availability.md) | Source depth was measured; coverage does not resolve universe or identity gaps. |
| Research Dataset Gate | COMPLETE_WITH_LIMITATIONS | [Research Dataset Gate](../reports/pilot/research_dataset_gate.md) | Gate artifacts exist, with rows requiring source or review flags. |
| Market Data Validation | COMPLETE_WITH_LIMITATIONS | [Research data readiness](RESEARCH_DATA_READINESS.md) | Approved and flagged subsets exist; broad historical readiness is not complete. |

## 4. Research Foundation

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Research Methodology | COMPLETE | [Phase 1 methodology](research_foundation/SET50_RESEARCH_METHODOLOGY.md) | Defines information sets, bias controls, time alignment, OOS, and research governance. |
| Market Microstructure | COMPLETE | [Phase 2 microstructure](research_foundation/SET50_MARKET_MICROSTRUCTURE.md) | Documents order interaction, fills, tick sizes, costs, and daily-data limitations. |
| Thailand Market Regime | IN_PROGRESS | [Thailand market regime foundation](research_foundation/SET50_THAILAND_MARKET_REGIME.md) | Research foundation drafted; marked `READY_FOR_AUDIT`, not complete. |
| Alpha Research | IN_PROGRESS | [Alpha research foundation](research_foundation/SET50_ALPHA_RESEARCH.md) | Candidate hypotheses and evidence review drafted; no implementation or testing performed. |

## 5. Parameter Research

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Parameter Research | COMPLETE_WITH_LIMITATIONS | [SET50 parameter research](set50_parameter_research.md) | Candidate ranges only; no optimal parameter was selected and no performance ranking is implied. |

## 6. Research Protocol

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Research Protocol | LOCKED | [Research Protocol / pre-registration](research_foundation/SET50_RESEARCH_PROTOCOL.md) | Locked after Human Audit; defines timing, PIT universe, baselines, costs, validation, and rejection rules. Next gate: Feature Implementation. |

## 7. Strategy Research

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Features | IN_PROGRESS | [Feature baseline](FEATURE_ENGINEERING_BASELINE.md) | Existing feature code/docs are present; current research gate and validation limitations remain. |
| Signals | IN_PROGRESS | [Strategy research](STRATEGY_RESEARCH.md) | Existing signal-related implementation is not a validated final strategy. |
| Strategy | IN_PROGRESS | [Strategy research decision](STRATEGY_RESEARCH_DECISION.md) | Existing and legacy strategy material exists; no final validated strategy is declared here. |

## 8. Backtesting

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Backtest | COMPLETE_WITH_LIMITATIONS | [Backtest report](BACKTEST_REPORT.md) | Existing runs/reports exist; this status does not override data, identity, or execution limitations. |

## 9. OOS / Robustness

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| OOS | COMPLETE_WITH_LIMITATIONS | [Larger OOS research](LARGER_OOS_RESEARCH.md) | OOS artifacts exist, but they remain bounded by the documented dataset and methodology limitations. |
| Walk-forward | COMPLETE_WITH_LIMITATIONS | [Walk-forward research](WALK_FORWARD_RESEARCH.md) | Existing walk-forward material exists; it is not evidence that all future research is OOS-safe. |
| Optimization | DEFERRED | No current research approval | Parameter optimization is deferred until data and protocol gates are stronger. |
| Robustness | IN_PROGRESS | [D0 walk-forward evaluation](D0_WALK_FORWARD_EVALUATION.md) | Existing diagnostics are not a complete robustness program for the full historical universe. |

## 10. Paper Trading

| Area | Status | Primary document / evidence | Notes |
|---|---|---|---|
| Paper Trading | IN_PROGRESS | [Settrade research integration](SETTRADE_RESEARCH_INTEGRATION.md) | Collector and paper-trading infrastructure exist; this is not a validated live strategy result. |

## 11. Known Limitations

- Historical SET50 membership is incomplete for several 2016–2022 periods.
- Daily OHLCV does not reveal historical bid/ask, depth, queue, or exact fills.
- Security identity cases must not be merged without evidence.
- Yahoo availability is not equivalent to point-in-time security continuity.
- Existing backtest and strategy artifacts may be legacy or bounded by incomplete data.
- Phase 3 Thailand Market Regime has a research foundation draft awaiting human audit; Phase 4 Alpha Research has a research-only foundation draft and no implementation.

## 12. Research Gaps

- Complete authoritative historical SET50 constituent evidence.
- A complete identity-aware historical price dataset aligned to membership periods.
- A dedicated research protocol with pre-declared splits, timing, costs, and metrics.
- Direct SET50 evidence for parameter ranges rather than broad supporting literature.
- Execution evidence beyond daily OHLCV.
- A documented Thailand market-regime research phase.

## 13. Important Documents

- [Documentation map](README.md)
- [Research Foundation index](research_foundation/README.md)
- [Phase 1 methodology](research_foundation/SET50_RESEARCH_METHODOLOGY.md)
- [Phase 2 market microstructure](research_foundation/SET50_MARKET_MICROSTRUCTURE.md)
- [Phase 3 Thailand market regime](research_foundation/SET50_THAILAND_MARKET_REGIME.md)
- [Phase 4 alpha research](research_foundation/SET50_ALPHA_RESEARCH.md)
- [Parameter research](set50_parameter_research.md)
- [Historical universe audit](../reports/pilot/historical_universe_2016_2022/historical_universe_2016_2022_audit.md)
- [Historical security identity audit](HISTORICAL_SECURITY_IDENTITY_AUDIT.md)
- [Research Dataset Gate](../reports/pilot/research_dataset_gate.md)
- [Research data readiness](RESEARCH_DATA_READINESS.md)

## 14. Change Governance

- Research documents must not silently modify datasets.
- Research documents must not silently modify trading logic.
- Parameter research must not be treated as validated strategy parameters.
- OOS results must not be used retroactively to rewrite hypotheses without a new
  documented research decision.
- Historical universe changes require evidence and provenance.
- Security identity changes require evidence and an explicit policy decision.
- Execution assumptions must be documented and separated from observed data.
- Major methodology changes must be recorded as a new research decision.
- Legacy files must not be deleted merely to make the repository appear complete.
- Statuses must use the controlled vocabulary at the top of this document.

## 15. Current change record

This organization pass creates navigation and status documents only. It does not
move or rename existing files because no move was necessary to make the research
structure auditable. Phase 3 and Phase 4 placeholders were intentionally not
created.

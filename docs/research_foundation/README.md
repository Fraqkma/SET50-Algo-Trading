# SET50 Research Foundation

## Purpose

Research Foundation documents define the methodological and market understanding
required before feature engineering, signal design, strategy implementation, or
backtesting. They are explanatory and governance documents; they do not by
themselves validate a strategy or select optimal parameters.

## Phases

| Phase | Topic | Status | Document |
|---:|---|---|---|
| 1 | Research Methodology | COMPLETE | [SET50_RESEARCH_METHODOLOGY.md](SET50_RESEARCH_METHODOLOGY.md) |
| 2 | Market Microstructure | COMPLETE | [SET50_MARKET_MICROSTRUCTURE.md](SET50_MARKET_MICROSTRUCTURE.md) |
| 3 | Thailand Market Regime | IN_PROGRESS | [Thailand market regime foundation](SET50_THAILAND_MARKET_REGIME.md); research draft is ready for human audit |
| 4 | Alpha Research | IN_PROGRESS | [Alpha research foundation](SET50_ALPHA_RESEARCH.md); candidate families and data-feasibility review drafted, no implementation |

## Research boundary

The current Phase 4 research-design document is the [Research Protocol /
pre-registration](SET50_RESEARCH_PROTOCOL.md), currently `LOCKED` after Human
Audit. The next gate is Feature Implementation. This is a governance gate, not
a new research phase.

Research Foundation must not silently modify datasets, historical universes,
security mappings, trading logic, or production behavior. Parameter ranges remain
hypotheses until independently tested. Existing implementation or legacy reports
must not be presented as current research evidence without an explicit status.

## Dependency flow

```text
Research Foundation
        ↓
Research Protocol
        ↓
Features
        ↓
Signals
        ↓
Strategy
        ↓
Backtest
        ↓
OOS / Robustness
        ↓
Paper Trading
```

## Related navigation

- [Master research progress](../RESEARCH_PROGRESS.md)
- [Documentation map](../README.md)
- [SET50 parameter research](../set50_parameter_research.md)

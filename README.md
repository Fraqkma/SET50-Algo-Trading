# SET50 Algo Trading Competition

Skeleton repository for a SET50 long-only algorithmic trading project.

## Competition Constraints

- Universe: SET50 stocks only.
- Initial capital: THB 10,000,000.
- No additional capital.
- Long-only; no short selling.
- Minimum coverage target: at least 5 distinct stock symbols traded by the end of the competition.
- Allowed order types: Limit Order and Market-to-Limit Order with IOC validity.
- Commission: 0.157% of order value.
- VAT: 7% of commission.
- Slippage: 1 tick size.

## Architecture

```text
src/
├── data/         market data loading, cleaning, features
├── strategies/   strategy interfaces and signal generation
├── backtest/     simulation, costs, and metrics
├── risk/         sizing and risk checks
├── execution/    order models and execution interfaces
└── utils/        shared helpers and logging
```

## Setup

1. Create a Python 3.13+ environment.
2. Install dependencies from `requirements.txt`.  pip install -r requirements.txt
3. Review `config/config.yaml` and `config/trading_hours.yaml`.
4. Run `python main.py` to confirm the skeleton initializes.

## Results

This repository currently contains only the project skeleton. Backtest outputs, reports, and figures will be written under `results/` once implementation work begins.

No performance claims are made at this stage.

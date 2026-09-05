# SET50 Algo Trading Competition

This repository contains a Python-only algorithmic trading system for a SET50 stock trading competition.

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
├── data/         market data loading, cleaning, validation, and research data
├── strategies/   strategy interfaces and signal generation
├── backtest/     simulation, costs, and metrics
├── risk/         sizing and risk checks
├── execution/    order models and execution interfaces
└── utils/        shared helpers and logging
```

## Data Pipeline

The project now includes a historical SET50 data pipeline designed to avoid survivorship bias and unnecessary downloads.

1. Historical SET50 constituent data is stored as date-aware membership records, not as a single static list.
2. The pipeline reads historical membership from the CSV files under `data/raw/constituents/` and resolves the eligible universe for the requested period.
3. Required symbols are discovered automatically from the union of historical constituent membership in the requested date range, then normalized to Yahoo Finance tickers.
4. Yahoo Finance is used only as a research data source during development. The market-data provider is isolated behind the data module boundary so it can later be replaced with official SET or competition data without changing downstream logic.
5. Raw downloaded files remain in `data/raw/prices/` and are never modified during cleaning.
6. Processed/cleaned data is stored separately under `data/processed/prices/`.
7. Data validation is performed before a file is treated as usable for downstream research or backtesting.

### Constituent CSV schema

The expected CSV schema is:

```csv
effective_from,effective_to,symbol
2025-01-01,2025-06-30,AOT
2025-01-01,2025-06-30,ADVANC
2025-07-01,2025-12-31,ADVANC
2025-07-01,2025-12-31,CPALL
```

The pipeline expects this file to be supplied locally. If no historical constituent data is available, the code raises a clear error explaining which file is required, rather than silently inventing membership.

## Setup

1. Create a Python 3.13+ environment.
2. Install dependencies from `requirements.txt` with `pip install -r requirements.txt`.
3. Add historical SET50 constituent CSV files under `data/raw/constituents/`.
4. Run `python main.py data download --start 2020-01-01 --end 2026-09-01` to download the required Yahoo Finance data for the historical period.
5. Run `python main.py data validate` to validate the raw price files.

## Results

The project keeps raw downloaded data, cleaned/processed data, and validation reports under the repository's `data/` and `results/` directories. No trading strategy or backtest claims are made at this stage.

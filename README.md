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

## Official KGI TradeSim

The organizer-designated TradeSim 0.2.6 runtime and official `Daily_Ticks.zip`
data workflow are documented in [the integration guide](docs/OFFICIAL_TRADESIM_INTEGRATION.md).
Research backtests remain separate. Use `python scripts/run_official_tradesim.py
--check` to inspect runtime readiness, `--list-official-data` to inspect official
coverage, and pass `--data-source official` explicitly to run against an isolated
copy of the official ticks/history. Practice remains the default source.

## Data Exploration UI

The repository includes a read-only Streamlit UI for current-SET50 visual
research, historical membership, Yahoo ticker audit, acquisition reports, raw
OHLCV, Settrade pilot evidence, and data-quality warnings. The current SET50
Market Overview is explicitly an exploratory display universe, not a historical
membership series or survivorship-safe backtest input. The derived daily view
preserves per-row provenance, rejects conflicting symbol-dates, and does not
fill prices or volume. See [the market research terminal guide](docs/MARKET_RESEARCH_TERMINAL.md)
for source precedence, identity boundaries, return/correlation methodology, and
catalog refresh instructions.

Settrade production is isolated from the older sandbox pilot under
`data/pilot/settrade/production`. The connection and collector are market-data
only; account/private endpoints require an account number and any trading SDK
methods remain unused. See [the production cutover and capability audit](docs/SETTRADE_PRODUCTION_CUTOVER.md)
for verified API behavior, provenance, readiness commands, and current limits.

Install dependencies and start it from the repository root:

```powershell
python -m pip install -r requirements.txt
python -m streamlit run ui/app.py
```

The research-result sections are placeholders only. No strategy, feature,
backtest, optimization, or paper-trading logic is implemented by the UI.

For bounded recovery, reconnect evidence, and the local TradeSim archive upgrade
procedure, see [operational recovery and TradeSim readiness](docs/FULL_OPERATIONAL_TRADESIM_READINESS.md).

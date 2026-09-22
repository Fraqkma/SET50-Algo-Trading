# Historical Depth Experiment

## Objective
Measure how far the current project Yahoo/yfinance source retrieves daily OHLCV; no missing data was repaired or merged.

## Repository universe discovery
- Requested research range: `2016_H1 -> 2026_H2`.
- Available canonical periods: `2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2`.
- Available period rows: `400`; unique symbols: `63`.
- Repository lacks constituent snapshots for: `2016_H1, 2016_H2, 2017_H1, 2017_H2, 2018_H1, 2018_H2, 2019_H1, 2019_H2, 2020_H1, 2020_H2, 2021_H1, 2021_H2, 2022_H1, 2022_H2`.
- Those absent memberships were not invented or inferred.

## Request semantics
- Requested range: `2016-01-01` through `2026-09-19` inclusive; yfinance end-exclusive parameter: `2026-09-20`.
- `interval=1d`, `auto_adjust=False`, `actions=True`, `threads=False`.
- Unique verified Yahoo tickers requested once: `62`.
- Non-verified mapping symbols not requested: `1`.
- Outputs are isolated under `data/pilot/historical_depth_experiment/` and `reports/pilot/`.

## Results
- `MAPPING_NOT_FOUND`: `1`
- `PARTIAL`: `62`

### Historical depth classification
- `NOT_REQUESTED`: `1`
- `REACHES_2016_START`: `49`
- `START_AFTER_2016_START`: `13`

Availability is reported separately from validation. `REACHES_2016_START` means the first returned row was on or before the first expected SET trading date in 2016 (2016-01-04); `START_AFTER_2016_START` identifies a shorter Yahoo history. The requested end was 2026-09-19, while the latest observed Yahoo row was 2026-09-18.

## Reused project utilities
- `normalize_download_frame`
- `validate_raw_frame`
- `coverage_issues`

## Reproducibility
- Branch: `research/historical-depth`
- Commit: `9b49b7e021896dcaabfbe387dc8483b391d4b524`
- yfinance: `1.7.0`
- Timestamp UTC: `2026-09-19T16:39:21.707069+00:00`
- Production/raw files modified: `False`
- Canonical constituent file modified: `False`
- Yahoo ticker mapping modified: `False`
- Research Dataset Gate modified: `False`

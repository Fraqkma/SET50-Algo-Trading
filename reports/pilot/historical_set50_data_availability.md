# Historical SET50 Data Availability Experiment

## 1. Objective
Measure Yahoo/yfinance daily OHLCV availability without modifying production data.

## 2. Scope
- Periods: `2022_H2, 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1, 2025_H2, 2026_H1, 2026_H2`
- Requested range: `2022-07-01` through `2026-09-18` inclusive
- Period rows: `450`; periods: `9`; unique symbols: `66`
- 2022_H1 was intentionally excluded.

## 3. Universe
2022_H2 was supplied from the official SET H2 2022 PDF as an experiment-only input; 2023_H1 onward was read from the canonical processed universe.

## 4. Yahoo Mapping Coverage
- Verified mappings: `62`
- Unmapped/non-verified: `3`
- No ticker was guessed or written back to the production audit.

## 5. Download Method
- Yahoo Finance via yfinance; interval `1d`; `auto_adjust=False`; `actions=True`.
- Pilot CSVs are stored under `data/pilot/historical_set50_availability/`.
- Production acquisition was not called.

## 6. Validation Method
Reused `normalize_download_frame`, `validate_raw_frame`, and `coverage_issues` from `src/data/market_data_acquisition.py`. No filling, repairing, row deletion, or tolerance changes were performed.

## 7. Availability Results
- `FULL`: `18`
- `PARTIAL`: `44`
- `PARTIAL_KNOWN_GAP`: `0`
- `NO_DATA`: `1`
- `ERROR`: `0`
- `UNMAPPED`: `3`

## 8. Missing / Partial Symbols
- `ADVANC` `PARTIAL`: High below Open/Close by 1.00 (0.44%)
- `AOT` `PARTIAL`: Low above Open/Close by 0.25 (0.36%)
- `AWC` `PARTIAL`: Low above Open/Close by 0.02 (0.49%)
- `BANPU` `PARTIAL`: missing values in Open; missing values in High; missing values in Low; missing values in Close; High below Open/Close by 0.10 (0.69%); large calendar date gap (>10 days): 2026-08-11 -> 2026-09-11 (30 calendar days)
- `BBL` `PARTIAL`: High below Open/Close by 0.50 (0.31%); Low above Open/Close by 0.50 (0.32%)
- `BCP` `PARTIAL`: High below Open/Close by 0.50 (1.56%)
- `BEM` `PARTIAL`: High below Open/Close by 0.05 (0.56%); Low above Open/Close by 0.05 (0.58%)
- `BH` `PARTIAL`: High below Open/Close by 2.00 (0.77%); Low above Open/Close by 1.00 (0.37%)
- `BJC` `PARTIAL`: High below Open/Close by 0.25 (0.72%); Low above Open/Close by 0.25 (0.68%)
- `BLA` `UNMAPPED`: Yahoo mapping status=UNMAPPED; no ticker guessed.
- `BTS` `PARTIAL`: High below Open/Close by 0.05 (0.68%)
- `CBG` `PARTIAL`: High below Open/Close by 1.00 (1.19%); Low above Open/Close by 0.50 (0.62%)
- `CCET` `PARTIAL`: Low above Open/Close by 0.04 (2.16%)
- `CPALL` `PARTIAL`: High below Open/Close by 0.25 (0.39%)
- `CPF` `PARTIAL`: High below Open/Close by 0.10 (0.49%); Low above Open/Close by 0.10 (0.51%)
- `CPN` `PARTIAL`: High below Open/Close by 0.25 (0.37%); Low above Open/Close by 0.25 (0.38%)
- `CRC` `PARTIAL`: Low above Open/Close by 0.25 (0.66%)
- `DELTA` `PARTIAL`: High below Open/Close by 2.25 (2.27%)
- `DTAC` `UNMAPPED`: Yahoo mapping status=UNMAPPED; no ticker guessed.
- `EA` `PARTIAL`: Low above Open/Close by 0.25 (0.43%)
- `EGCO` `PARTIAL`: High below Open/Close by 2.50 (1.73%); Low above Open/Close by 0.50 (0.42%)
- `GPSC` `PARTIAL`: High below Open/Close by 0.25 (0.38%); Low above Open/Close by 0.25 (0.54%)
- `GULF` `PARTIAL`: coverage starts after requested start: 2025-04-03 > 2022-07-01
- `INTUCH` `NO_DATA`: Yahoo mapping status=NOT_FOUND; no ticker guessed.
- `IRPC` `UNMAPPED`: Yahoo mapping status=UNMAPPED; no ticker guessed.
- `ITC` `PARTIAL`: High below Open/Close by 0.30 (1.36%); Low above Open/Close by 0.10 (0.54%)
- `JMART` `PARTIAL`: Low above Open/Close by 0.10 (0.52%)
- `JMT` `PARTIAL`: Low above Open/Close by 0.25 (0.66%)
- `KBANK` `PARTIAL`: High below Open/Close by 0.50 (0.39%); Low above Open/Close by 0.50 (0.39%)
- `KCE` `PARTIAL`: High below Open/Close by 0.25 (0.54%); Low above Open/Close by 0.25 (0.60%)
- `KTC` `PARTIAL`: Low above Open/Close by 0.75 (1.47%)
- `MINT` `PARTIAL`: High below Open/Close by 0.25 (0.72%)
- `OR` `PARTIAL`: High below Open/Close by 0.10 (0.44%); Low above Open/Close by 0.10 (0.45%)
- `PTT` `PARTIAL`: High below Open/Close by 0.25 (0.79%); Low above Open/Close by 0.25 (0.79%)
- `PTTEP` `PARTIAL`: Low above Open/Close by 0.50 (0.34%)
- `SAWAD` `PARTIAL`: High below Open/Close by 0.21 (0.43%); Low above Open/Close by 0.21 (0.55%)
- `SCB` `PARTIAL`: Low above Open/Close by 0.50 (0.50%)
- `SCC` `PARTIAL`: High below Open/Close by 2.00 (0.59%); Low above Open/Close by 1.00 (0.31%)
- `TCAP` `PARTIAL`: High below Open/Close by 0.50 (1.00%)
- `TFG` `PARTIAL`: High below Open/Close by 0.02 (0.50%); Low above Open/Close by 0.06 (1.57%)
- `TIDLOR` `PARTIAL`: coverage starts after requested start: 2025-05-16 > 2022-07-01
- `TISCO` `PARTIAL`: High below Open/Close by 0.25 (0.26%)
- `TLI` `PARTIAL`: High below Open/Close by 0.10 (0.77%)
- `TRUE` `PARTIAL`: High below Open/Close by 0.05 (0.70%); Low above Open/Close by 0.05 (0.76%)
- `TTB` `PARTIAL`: High below Open/Close by 0.01 (0.58%); Low above Open/Close by 0.01 (0.58%)
- `TU` `PARTIAL`: Low above Open/Close by 0.10 (0.68%)
- `VGI` `PARTIAL`: Low above Open/Close by 0.02 (0.74%)
- `WHA` `PARTIAL`: High below Open/Close by 0.05 (0.98%)

## 9. Corporate Action Flags
- `BANPU`: BANPU/BANPUU corporate-action context requires identity review.; existing pilot file reused; production overlap dates=880; production file read-only
- `GULF`: INTUCH/GULF combination effective 2025-04-01 requires identity review.; existing pilot file reused; production overlap dates=348; production file read-only
- `INTUCH`: INTUCH/GULF combination effective 2025-04-01 requires identity review.
- `SCB`: SCB X / SCBB restructuring boundary requires identity review.; existing pilot file reused; production overlap dates=898; production file read-only
- `TIDLOR`: 2021 listing and 2025 holding-company transition require identity review.; existing pilot file reused; production overlap dates=323; production file read-only
- `TRUE`: TRUE/TRUEE/DTAC corporate-action history requires identity review.; existing pilot file reused; production overlap dates=898; production file read-only
- `TTB`: TMB to TTB historical identity transition requires date-effective review.; existing pilot file reused; production overlap dates=898; production file read-only

## 10. Source/Data Issues
Availability and validity are reported separately. A returned series with OHLC or coverage issues remains an observed source result and is not repaired.

## 11. Key Findings
See the CSV/JSON records for per-symbol actual dates, row counts, gap measurements, validation status, and production overlap notes.

## 12. Limitations
- The experiment uses observed dates, not an official Thailand trading-calendar utility.
- A date gap is not classified as a market closure without independent evidence.
- Corporate-action flags are not resolved in this step.

## 13. Recommended Next Step
Review partial histories and corporate-action flags before any research approval or backtest use.

## Reproducibility
- Branch: `research/historical-data`
- Commit: `9b49b7e021896dcaabfbe387dc8483b391d4b524`
- yfinance: `1.7.0`
- Experiment timestamp UTC: `2026-09-19T14:30:53.328193+00:00`
- Production files modified: `False`

# Market Data Acquisition Report

- Total historical symbols: 63
- Verified Yahoo tickers: 62
- Unresolved symbols: 1
- Requested inclusive date range: 2023-01-01 to 2026-12-31
- Source: Yahoo Finance via yfinance with `auto_adjust=False`, `actions=True`.
- Raw data is preserved under `data/raw/market_data/`; validation issues are reported, not cleaned in place.

## Status breakdown
- SUCCESS: 19
- PARTIAL: 42
- PARTIAL_KNOWN_GAP: 1
- FAILED: 0
- NO_DATA: 1

## Issues
- `INTUCH` / `INTUCH.BK` — NO_DATA: Gate 1 status NOT_FOUND; no ticker was guessed or downloaded. INTUCH was combined into Gulf Development Public Company Limited (GULF) effective 2025-04-01. Yahoo metadata returned HTTP 404 for INTUCH.BK; retain INTUCH for pre-merger historical review without rewriting history.
- `ADVANC` / `ADVANC.BK` — PARTIAL: High below Open/Close by 1.00 (0.44%)
- `AOT` / `AOT.BK` — PARTIAL: Low above Open/Close by 0.25 (0.36%)
- `AWC` / `AWC.BK` — PARTIAL: Low above Open/Close by 0.02 (0.49%)
- `BANPU` / `BANPU.BK` — PARTIAL: High below Open/Close by 0.10 (0.69%); large calendar date gap (>10 days)
- `BBL` / `BBL.BK` — PARTIAL: High below Open/Close by 0.50 (0.31%); Low above Open/Close by 0.50 (0.32%)
- `BCP` / `BCP.BK` — PARTIAL: High below Open/Close by 0.50 (1.56%)
- `BEM` / `BEM.BK` — PARTIAL: High below Open/Close by 0.05 (0.56%); Low above Open/Close by 0.05 (0.58%)
- `BH` / `BH.BK` — PARTIAL: High below Open/Close by 2.00 (0.77%); Low above Open/Close by 1.00 (0.37%)
- `BJC` / `BJC.BK` — PARTIAL: High below Open/Close by 0.25 (0.72%); Low above Open/Close by 0.25 (0.68%)
- `BTS` / `BTS.BK` — PARTIAL: High below Open/Close by 0.05 (0.68%)
- `CBG` / `CBG.BK` — PARTIAL: High below Open/Close by 1.00 (1.19%); Low above Open/Close by 0.50 (0.62%)
- `CCET` / `CCET.BK` — PARTIAL: Low above Open/Close by 0.04 (2.16%)
- `CPALL` / `CPALL.BK` — PARTIAL: High below Open/Close by 0.25 (0.39%)
- `CPF` / `CPF.BK` — PARTIAL: High below Open/Close by 0.10 (0.47%); Low above Open/Close by 0.10 (0.51%)
- `CPN` / `CPN.BK` — PARTIAL: High below Open/Close by 0.25 (0.37%); Low above Open/Close by 0.25 (0.38%)
- `CRC` / `CRC.BK` — PARTIAL: Low above Open/Close by 0.25 (0.66%)
- `DELTA` / `DELTA.BK` — PARTIAL: High below Open/Close by 2.25 (2.27%)
- `EA` / `EA.BK` — PARTIAL: Low above Open/Close by 0.25 (0.43%)
- `EGCO` / `EGCO.BK` — PARTIAL: High below Open/Close by 2.50 (1.73%); Low above Open/Close by 0.50 (0.42%)
- `GPSC` / `GPSC.BK` — PARTIAL: High below Open/Close by 0.25 (0.38%); Low above Open/Close by 0.25 (0.54%)
- `ITC` / `ITC.BK` — PARTIAL: High below Open/Close by 0.30 (1.36%); Low above Open/Close by 0.10 (0.43%)
- `JMART` / `JMART.BK` — PARTIAL: Low above Open/Close by 0.10 (0.52%)
- `JMT` / `JMT.BK` — PARTIAL: Low above Open/Close by 0.25 (0.66%)
- `KBANK` / `KBANK.BK` — PARTIAL: High below Open/Close by 0.50 (0.39%); Low above Open/Close by 0.50 (0.39%)
- `KCE` / `KCE.BK` — PARTIAL: High below Open/Close by 0.25 (0.54%); Low above Open/Close by 0.25 (0.60%)
- `KTC` / `KTC.BK` — PARTIAL: Low above Open/Close by 0.75 (1.47%)
- `MINT` / `MINT.BK` — PARTIAL: High below Open/Close by 0.25 (0.72%)
- `OR` / `OR.BK` — PARTIAL: High below Open/Close by 0.10 (0.44%); Low above Open/Close by 0.10 (0.45%)
- `PTT` / `PTT.BK` — PARTIAL: High below Open/Close by 0.25 (0.79%); Low above Open/Close by 0.25 (0.79%)
- `PTTEP` / `PTTEP.BK` — PARTIAL: Low above Open/Close by 0.50 (0.34%)
- `SAWAD` / `SAWAD.BK` — PARTIAL: High below Open/Close by 0.21 (0.43%); Low above Open/Close by 0.21 (0.55%)
- `SCB` / `SCB.BK` — PARTIAL: Low above Open/Close by 0.50 (0.50%)
- `SCC` / `SCC.BK` — PARTIAL: High below Open/Close by 2.00 (0.59%); Low above Open/Close by 1.00 (0.31%)
- `TCAP` / `TCAP.BK` — PARTIAL: High below Open/Close by 0.50 (1.00%)
- `TFG` / `TFG.BK` — PARTIAL: High below Open/Close by 0.02 (0.50%); Low above Open/Close by 0.06 (1.57%)
- `TIDLOR` / `TIDLOR.BK` — PARTIAL_KNOWN_GAP: Skipped valid existing raw file (resume). Ngern Tid Lor PCL, listed 2021-05-10, was delisted 2025-05-15 and replaced by Tidlor Holdings PCL under the same ticker via a 1:1 share swap. Yahoo Finance TIDLOR.BK provides the new holding-company entity from 2025-05-15 onward; pre-merger history is not available under this ticker.
- `TISCO` / `TISCO.BK` — PARTIAL: High below Open/Close by 0.25 (0.26%)
- `TLI` / `TLI.BK` — PARTIAL: High below Open/Close by 0.10 (0.77%)
- `TRUE` / `TRUE.BK` — PARTIAL: High below Open/Close by 0.05 (0.70%); Low above Open/Close by 0.05 (0.76%)
- `TTB` / `TTB.BK` — PARTIAL: High below Open/Close by 0.01 (0.58%); Low above Open/Close by 0.01 (0.58%)
- `TU` / `TU.BK` — PARTIAL: Low above Open/Close by 0.10 (0.68%)
- `VGI` / `VGI.BK` — PARTIAL: Low above Open/Close by 0.02 (0.74%)
- `WHA` / `WHA.BK` — PARTIAL: High below Open/Close by 0.05 (0.98%)
- None

No strategy, feature engineering, backtest, or optimization was performed.

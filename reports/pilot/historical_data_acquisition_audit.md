# Step 2D — Historical Data Acquisition & Validation

## 1. Executive Summary

- SOURCE_NEEDED rows at start: `22`
- Successfully acquired: `0`
- Full coverage: `0`
- Partial coverage: `0`
- Still SOURCE_NEEDED: `22`
- UNRESOLVED: `0`
- USE: `0`
- USE_WITH_FLAG: `0`

The rows were read directly from the current Step 2C CSV. No data source was bypassed. SET/SETSMART requires authenticated or licensed access, and EODHD requires an API key/paid historical access; no authorized credentials were available locally. Therefore no OHLCV acquisition was attempted or claimed.

## 2. Acquisition Table

| Period | Security | Historical security | Source | Coverage | Validation | Decision |
|---|---|---|---|---|---|---|
| 2026_H2 | BANPU | BANPUU / BANPU | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | BLA | BLA | EODHD BLA.BK candidate; official SET historical request/SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | DTAC | DTAC | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H1 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H2 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2024_H1 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2024_H2 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2025_H1 | GULF | GULF | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H1 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H2 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2024_H1 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2024_H2 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2025_H1 | INTUCH | INTUCH | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | IRPC | IRPC | EODHD IRPC.BK candidate; official SET historical request/SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | TIDLOR | NTL | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H1 | TIDLOR | NTL | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H2 | TIDLOR | NTL | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2024_H2 | TIDLOR | NTL | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2022_H2 | TRUE | TRUEE | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |
| 2023_H1 | TRUE | TRUEE | Official SET Historical Data Request / SETSMART | NOT_ACQUIRED | NOT_RUN_NO_DATA | SOURCE_NEEDED |

## 3. Security-by-Security Findings

### BANPU

- Required periods: `2026_H2`.
- Historical security: `BANPUU / BANPU`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### BLA

- Required periods: `2022_H2`.
- Historical security: `BLA`.
- Source candidate: EODHD BLA.BK candidate; official SET historical request/SETSMART.
- Access status: API key and paid historical plan required; no authorized key available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### DTAC

- Required periods: `2022_H2`.
- Historical security: `DTAC`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### GULF

- Required periods: `2022_H2, 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1`.
- Historical security: `GULF`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### INTUCH

- Required periods: `2022_H2, 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1`.
- Historical security: `INTUCH`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### IRPC

- Required periods: `2022_H2`.
- Historical security: `IRPC`.
- Source candidate: EODHD IRPC.BK candidate; official SET historical request/SETSMART.
- Access status: API key and paid historical plan required; no authorized key available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### TIDLOR

- Required periods: `2022_H2, 2023_H1, 2023_H2, 2024_H2`.
- Historical security: `NTL`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

### TRUE

- Required periods: `2022_H2, 2023_H1`.
- Historical security: `TRUEE`.
- Source candidate: Official SET Historical Data Request / SETSMART.
- Access status: Authenticated/licensed SET or SETSMART access required; no authorized access available locally.
- Acquisition result: no data acquired; coverage and OHLCV validation remain unverified.
- Decision: `SOURCE_NEEDED`.

## 4. Data Quality Findings

No datasets were acquired, so no date, duplicate, missing-value, OHLC, or gap validation was run. These fields are recorded as `UNKNOWN`, not zero or passing.

## 5. Research Readiness

### READY FOR RESEARCH

None of the Step 2D SOURCE_NEEDED rows moved to research-ready status.

### READY WITH FLAGS

None.

### STILL NEEDS DATA

All `22` processed rows remain SOURCE_NEEDED. The principal gaps are pre-event GULF and INTUCH, NTL, TRUEE/DTAC, the BANPUU/new-BANPU boundary, and BLA/IRPC.

### UNRESOLVED

None were forced into UNRESOLVED; access blockage is documented as SOURCE_NEEDED.

## Safety and Validation

Only new Step 2D artifacts were created. Existing raw Yahoo files, Step 2C files, mappings, processed data, and prior pilot artifacts were not modified. No securities were merged, no prices were synthesized or repaired, no missing values were filled, no bulk OHLCV was downloaded, and Step 3 was not started.

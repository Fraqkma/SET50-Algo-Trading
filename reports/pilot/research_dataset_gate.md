# Step 2C — Research Dataset Gate

## 1. Executive Summary

- Scope: `2022_H2` through `2026_H2` (no `2022_H1`).
- Total security-period rows: `450`
- `USE`: `133`
- `USE_WITH_FLAG`: `295`
- `SOURCE_NEEDED`: `22`
- `EXCLUDE_FROM_PERIOD`: `0`
- `UNRESOLVED`: `0`

Historically required securities remain represented even when data is unavailable. No security histories were merged.

## 2. Decision Matrix

The complete period-level matrix is in the CSV. Summary by membership period:

| Period | USE | USE_WITH_FLAG | SOURCE_NEEDED | EXCLUDE | UNRESOLVED |
|---|---:|---:|---:|---:|---:|
| 2022_H2 | 12 | 31 | 7 | 0 | 0 |
| 2023_H1 | 15 | 31 | 4 | 0 | 0 |
| 2023_H2 | 15 | 32 | 3 | 0 | 0 |
| 2024_H1 | 15 | 33 | 2 | 0 | 0 |
| 2024_H2 | 14 | 33 | 3 | 0 | 0 |
| 2025_H1 | 14 | 34 | 2 | 0 | 0 |
| 2025_H2 | 15 | 35 | 0 | 0 | 0 |
| 2026_H1 | 16 | 34 | 0 | 0 | 0 |
| 2026_H2 | 17 | 32 | 1 | 0 | 0 |

## 3. Security Identity Cases

- **BANPUU → BANPU:** 2026_H2 is `SOURCE_NEEDED` because the period crosses the BANPUU/new-BANPU boundary.
- **GULF:** pre-2025_H2 periods are `SOURCE_NEEDED`; post-event periods can use complete Yahoo coverage.
- **INTUCH:** all membership periods are `SOURCE_NEEDED`; do not replace INTUCH with GULF.
- **SCBB → SCBX:** current scope is post-restructuring SCB and remains `USE_WITH_FLAG`; no merge is made.
- **NTL → TIDLOR:** pre-2025_H2 periods are `SOURCE_NEEDED`; post-replacement periods can use Yahoo.
- **TRUEE / DTAC → TRUE:** 2022_H2 and 2023_H1 TRUE periods are `SOURCE_NEEDED`; later periods are flagged.
- **TMB → TTB:** current scope is post-ticker-change and remains `USE_WITH_FLAG`.
- **BLA / IRPC:** 2022_H2 is `SOURCE_NEEDED`; EODHD candidates are not yet verified.

## 4. Research Dataset Readiness

### Ready now

`USE` rows have verified Yahoo daily OHLCV without a reported Step 1C validation issue. `USE_WITH_FLAG` rows remain usable only with their documented limitation preserved.

### Needs source acquisition

`SOURCE_NEEDED` rows: `22`. These include missing mappings/data and predecessor or replacement periods requiring exact security-period OHLCV.

### Still unresolved

`UNRESOLVED` rows: `0`.

## Safety and Validation

Only the new research-dataset-gate CSV/JSON/Markdown artifacts were created. No alternative OHLCV was downloaded, no raw or processed data was changed, no securities were merged, no survivorship deletion was performed, and Step 3 was not started.

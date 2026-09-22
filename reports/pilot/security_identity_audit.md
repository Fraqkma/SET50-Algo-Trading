# Step 2A — Corporate Action / Security Identity Audit

## 1. Objective

Audit whether Step 1C availability gaps reflect ticker changes, security replacement, corporate restructuring, mergers, or Yahoo mapping limitations. No ticker mapping or OHLCV data was changed.

## 2. Scope

The ten requested cases are `BANPU`, `GULF`, `INTUCH`, `SCB`, `TIDLOR`, `TRUE`, `TTB`, `BLA`, `DTAC`, and `IRPC`. Step 1C covered `2022_H2` through `2026_H2`; `2022_H1` remains outside this audit.

## 3. Method and evidence boundary

The existing repository identity audit and Step 1C reports were inspected first. Official SET notices were preferred for event dates and security status. Yahoo was used only as market-data evidence; no historical ticker was guessed.

## 4. Source hierarchy

- Official SET listing, delisting, index, and corporate-action notices.
- Existing repository audit: `reports/historical_security_identity_audit.*`.
- Existing Step 1C results: `reports/pilot/historical_set50_data_availability.*`.

## 5. Case-by-case findings

### BANPU

SET records BANPU temporarily becoming `BANPUU` during the BANPU/BPP amalgamation, followed by delisting of BANPUU/BPP and listing of BANPU traded from 2026-08-04. Classification: `SECURITY_REPLACED`, confidence `HIGH`. The Step 1C 30-day gap is consistent with the suspension/amalgamation boundary, but raw BANPU, BANPUU, and post-event BANPU must remain separate.

Sources: [SET suspension notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105437300&symbol=SET), [SET delisting/listing notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105587000&symbol=BPP).

### GULF

The GULF/INTUCH amalgamation created a post-event GULF security. Yahoo `GULF.BK` begins on 2025-04-03, so the missing earlier history is not proof that historical GULF market history did not exist. Classification: `SECURITY_REPLACED`, confidence `HIGH`.

Source: [SET GULF/INTUCH amalgamation index notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=94859900&symbol=INTUCH).

### INTUCH

INTUCH ceased as a separately traded security after the GULF/INTUCH amalgamation. The existing Yahoo audit marks `INTUCH.BK` `NOT_FOUND`; replacing INTUCH with GULF would fabricate security continuity. Classification: `SECURITY_REPLACED`, confidence `HIGH`.

Source: [SET GULF/INTUCH notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=94859900&symbol=INTUCH).

### SCB

SET describes SCBX replacing SCB/SCBB through a holding-company restructuring and share exchange, effective around 2022-04-27. The last SCBB price used for trading limits is not evidence that OHLCV is continuous. Classification: `SECURITY_REPLACED`, confidence `HIGH`.

Source: [SET SCB restructuring notice](https://www.set.or.th/th/market/news-and-alert/newsdetails?id=16486816997531).

### TIDLOR

SET listed TIDLOR Holdings in place of NTL on 2025-05-15 after a corporate shareholding restructuring and 1:1 share swap. Yahoo `TIDLOR.BK` begins on 2025-05-16. Classification: `SECURITY_REPLACED`, confidence `HIGH`; do not backfill TIDLOR into NTL history.

Sources: [SET TIDLOR listing notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=96648700&symbol=SET), [SET NTL delisting notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=96649800&symbol=NTL).

### TRUE

SET states that TRUEE and DTAC were delisted after amalgamation and that new TRUE traded from 2023-03-03. Classification: `SECURITY_REPLACED`, confidence `HIGH`. The Step 1C `TRUE.BK` series must not be treated as old TRUEE or DTAC history.

Sources: [SET delisting notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256332430), [SET index replacement notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2023027510&symbol=SET).

### TTB

SET records the effective company-name and ticker change from TMB to TTB on 2021-05-12. Classification: `TICKER_CHANGED`, confidence `HIGH`. This is materially different from the replacement cases, but a date-effective TMB/TTB mapping still needs source-specific verification before extending the Step 1C window backward.

Source: [SET TMB/TTB change notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2021051542&symbol=TTB).

### BLA

SET confirms BLA as an active listed security. No identity transition was established, but the existing Yahoo audit has no verified mapping. Classification: `CONTINUOUS_IDENTITY` for the security, with an unresolved Yahoo/source-data problem; confidence `HIGH` for SET identity and `LOW` for source availability.

Source: [SET BLA factsheet](https://www.set.or.th/en/market/product/stock/quote/bla/factsheet).

### DTAC

DTAC was delisted after the TRUE/DTAC amalgamation and replaced by new TRUE trading from 2023-03-03. Classification: `SECURITY_REPLACED`, confidence `HIGH`. DTAC history must remain separate and must not be replaced automatically with TRUE.

Sources: [SET DTAC/TRUEE delisting notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256332430), [SET index replacement notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2023027510&symbol=SET).

### IRPC

SET constituent material identifies IRPC as a listed security, and no relevant 2022-onward identity transition was established. The existing Yahoo audit has no verified mapping. Classification: `CONTINUOUS_IDENTITY` for the security but `UNRESOLVED` for Yahoo/source availability, confidence `MEDIUM`.

Source: [SET H1 2023 constituent document](https://media.set.or.th/set/Documents/2023/Mar/SET50SET100_H1_2023_revise.pdf).

## 6. Classification summary

| Classification | Cases |
|---|---|
| `SECURITY_REPLACED` | BANPU, DTAC, GULF, INTUCH, SCB, TIDLOR, TRUE |
| `TICKER_CHANGED` | TTB |
| `CONTINUOUS_IDENTITY` with source/mapping unresolved | BLA, IRPC |

No case is safely classified as “Yahoo mapping issue only.” BLA and IRPC are unresolved source/mapping cases; the remaining gaps involve security identity boundaries.

## 7. Impact on Step 1C

- Explained or materially explained: BANPU’s internal gap; GULF’s 2025 start; INTUCH’s no-data result; TIDLOR’s 2025 start; TRUE/DTAC replacement; SCB’s restructuring boundary.
- Not an identity failure: TTB is a ticker transition, not a merger replacement.
- Still requiring another source: pre-event GULF, INTUCH, SCBB, NTL, TRUEE, DTAC, and BANPU/BANPUU boundary-separated history; BLA and IRPC data.
- OHLC validation anomalies remain a separate data-quality issue from identity.

## 8. Unresolved questions

- Which source can provide historical OHLCV for BLA and IRPC under verified security identity?
- Which source provides separate pre-event series for GULF, INTUCH, SCBB, NTL, TRUEE, DTAC, and BANPUU?
- What explicit corporate-action adjustment policy, if any, is acceptable for research returns?

## 9. Recommended data-research next step

Acquire or inspect a second historical market-data source using an explicit security-period manifest. Keep each listed security separate at raw-data level; do not silently combine related tickers.

## Safety confirmation

Only new files under `data/pilot/security_identity/` and `reports/pilot/` were created. Production/raw data, Step 1C pilot files, Yahoo mappings, canonical constituents, configuration, strategies, and backtests were not modified. No bulk OHLCV acquisition was performed.

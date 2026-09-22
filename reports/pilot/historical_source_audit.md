# Step 2B — Historical Data Source Audit

## 1. Executive Summary

Nine security cases were investigated, represented by 15 distinct historical security periods. The audit found:

- 9 cases with primary-source evidence that an official SET historical-data route exists.
- 8 secondary instrument/API candidates, mainly EODHD current or surviving symbols.
- 7 security-period rows classified `PARTIAL_PRIMARY`.
- 8 rows classified `PARTIAL_SECONDARY`.
- 0 rows classified `AVAILABLE_PRIMARY` or `AVAILABLE_SECONDARY`.
- 0 rows classified `NOT_FOUND` or `UNRESOLVED` at the source-route level.

The zero “available” count is deliberate: exact coverage for each historical security period was not independently verified without authenticated/licensed access or a controlled data request.

## 2. Source Hierarchy

### Primary: SET / SETSMART / SMART Marketplace

SET’s documentation confirms historical daily security price/statistics through SETSMART, with date-range selection and authenticated Excel/API access. [SETSMART FAQ](https://media.set.or.th/set/Documents/2022/Jul/SETSMART_web_FAQs.pdf) records historical daily security price/statistics and API access. SET’s [SMART Marketplace](https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace) explicitly lists equity EOD trading price/statistics and corporate-action/reference data. The repository’s existing audit identifies the [SET Historical Data Request](https://www.set.or.th/en/services/connectivity-and-data/data/historical) as the official request/licensed-delivery route.

These sources are the preferred acquisition path because exchange identity and corporate-action context can be requested together with the price data. Public documentation does not prove exact coverage for every predecessor security, field schema, or licensing term.

### Secondary: EOD Historical Data (EODHD)

EODHD documents a daily EOD API returning Open, High, Low, Close, adjusted close, and Volume. [Thailand Exchange BK](https://eodhd.com/exchange/BK) is identified as Thailand/XBKK. Public instrument pages were found for several surviving symbols, including [BLA.BK](https://eodhd.com/financial-summary/BLA.BK), [IRPC.BK](https://eodhd.com/financial-summary/IRPC.BK), [INTUCH.BK](https://eodhd.com/financial-summary/INTUCH.BK), [GULF.BK](https://eodhd.com/financial-summary/GULF.BK), and [SCB.BK](https://eodhd.com/financial-summary/SCB.BK).

EODHD is not primary exchange evidence. Its public pages do not independently establish the earliest available date for each required security period, and predecessor pages for TRUEE, DTAC, NTL, SCBB, and BANPUU were not verified.

## 3. Security-by-Security Findings

### GULF

- Historical security: pre-amalgamation GULF, required through 2025-03-20.
- Yahoo: Step 1C begins 2025-04-03, after the relevant boundary.
- Alternatives: official SET historical EOD request/SETSMART; EODHD GULF.BK candidate.
- OHLCV: the official route is a credible candidate; EODHD documents OHLCV fields, but exact pre-event coverage is unverified.
- Status: `PARTIAL_PRIMARY` / `PARTIAL_SECONDARY`.
- Identity confidence: `HIGH`.
- Use: potentially usable only after security-period extraction; never fill pre-event GULF with post-event GULF.

### INTUCH

- Historical security: separately traded INTUCH through its last trading period.
- Yahoo: `INTUCH.BK` was `NOT_FOUND`.
- Alternatives: official SET route; EODHD has an INTUCH.BK instrument page showing a quote dated 2025-02-19 and paid EOD access.
- OHLCV: secondary candidate exists, but earliest date and full 2022–2025 coverage were not verified.
- Status: `PARTIAL_PRIMARY` / `PARTIAL_SECONDARY`.
- Identity confidence: `HIGH`.
- Use: potentially usable through the separate-security period; do not substitute GULF.

### SCBB / SCBX

- Historical securities: SCBB before 2022-04-27 and SCBX/SCB after the restructuring.
- Yahoo: current `SCB.BK` does not prove SCBB continuity.
- Alternatives: official SET route for both periods; EODHD SCB.BK candidate only for the surviving/current security.
- OHLCV: primary route is credible but exact SCBB coverage and schema require confirmation.
- Status: `PARTIAL_PRIMARY` for SCBB and `PARTIAL_SECONDARY` for SCBX.
- Identity confidence: `HIGH`.
- Use: acquire and validate SCBB and SCBX as separate securities.

### NTL / TIDLOR

- Historical securities: NTL through 2025-05-14; TIDLOR from 2025-05-15.
- Yahoo: TIDLOR begins after the replacement and cannot cover NTL.
- Alternatives: official SET route; EODHD TIDLOR.BK candidate for the replacement security.
- OHLCV: NTL predecessor coverage remains unverified; TIDLOR has a secondary candidate.
- Status: `PARTIAL_PRIMARY` for NTL and `PARTIAL_SECONDARY` for TIDLOR.
- Identity confidence: `HIGH`.
- Use: keep NTL and TIDLOR separate; no backfill.

### TRUEE / DTAC / TRUE

- Historical securities: TRUEE and DTAC before the 2023 amalgamation; new TRUE from 2023-03-03.
- Yahoo: current TRUE data cannot prove coverage for TRUEE or DTAC.
- Alternatives: official SET route; EODHD current TRUE.BK candidate.
- OHLCV: predecessor coverage is unverified; new TRUE has a secondary candidate.
- Status: `PARTIAL_PRIMARY` for TRUEE/DTAC and `PARTIAL_SECONDARY` for new TRUE.
- Identity confidence: `HIGH`.
- Use: three separate security periods; no concatenation.

### BANPUU / BANPU

- Historical securities: temporary BANPUU during the 2026 amalgamation boundary; new BANPU from 2026-08-04.
- Yahoo: BANPU.BK contains a boundary gap and does not establish BANPUU coverage.
- Alternatives: official SET route; EODHD BANPU.BK candidate for the new/current security.
- OHLCV: BANPUU coverage was not independently found; new BANPU has a secondary candidate.
- Status: `PARTIAL_PRIMARY` for BANPUU and `PARTIAL_SECONDARY` for new BANPU.
- Identity confidence: `HIGH`.
- Use: preserve BANPUU and new BANPU as separate securities.

### TMB / TTB

- Historical securities: TMB through 2021-05-11; TTB from 2021-05-12.
- Yahoo: TTB.BK is available in the current mapping, but the old period was not tested here.
- Alternatives: official SET route; EODHD TTB.BK candidate.
- OHLCV: historical TMB coverage and continuity require controlled comparison; no assumption is made.
- Status: `PARTIAL_PRIMARY` for TMB and `PARTIAL_SECONDARY` for TTB.
- Identity confidence: `HIGH`.
- Use: a date-effective mapping may be possible, but preserve original symbols and validate before treating returns as continuous.

### BLA

- Historical security: BLA, no identity transition identified; required 2016 onward.
- Yahoo: unresolved mapping.
- Alternatives: official SET route; EODHD BLA.BK instrument page and paid EOD package.
- OHLCV: strongest candidate for a mapping-only failure, but exact earliest date and full coverage were not independently verified.
- Status: `PARTIAL_SECONDARY`.
- Identity confidence: `HIGH`.
- Use: candidate for controlled validation; do not add it to the verified mapping yet.

### IRPC

- Historical security: IRPC, no relevant identity transition identified; required 2016 onward.
- Yahoo: unresolved mapping.
- Alternatives: official SET route; EODHD IRPC.BK instrument page and paid EOD package.
- OHLCV: strongest candidate for a mapping-only failure, but exact earliest date and full coverage were not independently verified.
- Status: `PARTIAL_SECONDARY`.
- Identity confidence: `HIGH`.
- Use: candidate for controlled validation; do not add it to the verified mapping yet.

## 4. Coverage Matrix

| Security | Required period | Best source | Quality | Coverage | OHLCV | Identity confidence | Status |
|---|---|---|---|---|---|---|---|
| GULF | 2022-07-01–2025-03-20 | SET Historical/SETSMART | PRIMARY | Unknown | Product-level EOD confirmed; fields require confirmation | HIGH | PARTIAL_PRIMARY |
| INTUCH | 2022-07-01–2025-03-20 | SET Historical/SETSMART; EODHD | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| SCBB | 2016-01-01–2022-04-26 | SET Historical/SETSMART | PRIMARY | Unknown | Product-level EOD confirmed; fields require confirmation | HIGH | PARTIAL_PRIMARY |
| SCBX | 2022-04-27–2026-09-18 | SETSMART; EODHD SCB.BK | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| NTL | 2016-01-01–2025-05-14 | SET Historical/SETSMART | PRIMARY | Unknown | Product-level EOD confirmed; fields require confirmation | HIGH | PARTIAL_PRIMARY |
| TIDLOR | 2025-05-15–2026-09-18 | SETSMART; EODHD | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| TRUEE / DTAC | 2016-01-01–2023-03-01 | SET Historical/SETSMART | PRIMARY | Unknown | Product-level EOD confirmed; fields require confirmation | HIGH | PARTIAL_PRIMARY |
| TRUE | 2023-03-03–2026-09-18 | SETSMART; EODHD | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| BANPUU | 2026-07-17–2026-07-31 | SET Historical/SETSMART | PRIMARY | Unknown | Product-level EOD confirmed; fields require confirmation | HIGH | PARTIAL_PRIMARY |
| BANPU | 2026-08-04–2026-09-18 | SETSMART; EODHD | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| TMB / TTB | 2016-01-01–2026-09-18 | SET Historical/SETSMART; EODHD TTB.BK | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| BLA | 2016-01-01–2026-09-18 | SETSMART; EODHD BLA.BK | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |
| IRPC | 2016-01-01–2026-09-18 | SETSMART; EODHD IRPC.BK | PRIMARY/SECONDARY | Unknown | EODHD fields documented | HIGH | PARTIAL_SECONDARY |

## 5. Backtest Implications

No security is approved for backtest use by this audit. The usable candidates are:

- Official SET historical data request/SETSMART for all periods, subject to authenticated extraction and security-identity fields.
- EODHD for BLA and IRPC as likely mapping-resolution candidates, subject to exact coverage, licensing, and identity validation.
- EODHD for surviving/current GULF, INTUCH, SCBX, TIDLOR, TRUE, BANPU, and TTB symbols, but not as evidence of predecessor-security coverage.

Predecessor periods for GULF, INTUCH, SCBB, NTL, TRUEE, DTAC, and BANPUU remain the principal unresolved acquisition need.

## 6. Recommended Next Research Step

Prepare a small, authenticated source-validation request for SET/SETSMART covering one representative date range per security period. Require raw daily fields, exact security identifier, symbol/name history, corporate-action references, date coverage, licensing, and revision metadata. Separately validate only the BLA.BK and IRPC.BK EODHD candidates before considering any mapping update.

## Safety and validation

Only new files under `data/pilot/historical_source_audit/` and `reports/pilot/` were created. No bulk OHLCV was downloaded, no historical securities were merged, no synthetic OHLCV was created, and no production/raw, canonical, Step 1C, Step 2A, mapping, strategy, feature, configuration, or backtest files were modified. Step 3 was not started.

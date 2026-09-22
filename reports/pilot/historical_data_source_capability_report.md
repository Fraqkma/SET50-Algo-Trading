# Historical Data Source Capability Report

## 1. Executive Summary

The current Step 2C gate has 22 missing historical SET50 period rows, covering
eight symbols: BANPU, BLA, DTAC, GULF, INTUCH, IRPC, TIDLOR, and TRUE. The
missing periods are not proven unrecoverable. The strongest theoretical recovery
route is an authenticated/licensed SET Historical Data or SETSMART/SMART
Marketplace request, because SET documents historical trading/statistics data
from 30 April 1975. The practical blocker is access and exact security-period
delivery, not a demonstrated exchange-level absence.

EODHD is a secondary candidate for BLA and IRPC and possibly other surviving or
predecessor symbols, but Thailand-specific earliest dates and predecessor
coverage were not verified. Yahoo is not a verified recovery route for the
current gaps. No API calls, downloads, or production-data changes were made.

## 2. Current 22 Missing Periods

The gap CSV is generated from the current gate rather than a hardcoded universe:

`reports/pilot/historical_data_source_capability_by_gap.csv`

It contains 22 rows, 8 unique symbols, and the following periods by symbol:

| Symbol | Missing periods |
|---|---|
| BANPU | 2026_H2 |
| BLA | 2022_H2 |
| DTAC | 2022_H2 |
| GULF | 2022_H2, 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 |
| INTUCH | 2022_H2, 2023_H1, 2023_H2, 2024_H1, 2024_H2, 2025_H1 |
| IRPC | 2022_H2 |
| TIDLOR | 2022_H2, 2023_H1, 2023_H2, 2024_H2 |
| TRUE | 2022_H2, 2023_H1 |

## 3. SET / SETSMART Limitations

SET's public Historical Data page is the most promising route and states that
historical trading and statistics data cover all securities from 30 April 1975.
It also describes a one-time request and a per-year fee. SETSMART documentation
describes historical daily security price/statistics and authenticated
Excel/API retrieval, but its public material does not prove the exact start date,
security-identity treatment, or delivery schema for each missing row.

SET tick data is a separate product/request. Therefore, “SET can provide
historical data” must not be interpreted as proof that the exact required daily
OHLCV columns, volume definition, predecessor security, and date range will be
delivered under the currently available account.

## 4. EODHD Limitations

EODHD documents daily OHLCV fields, a BK/XBKK exchange, and a delisted-security
query option. It also documents shallow free access and deeper paid historical
access. These are provider-level facts. The exact earliest date for the required
Thai instruments, the symbols for predecessor securities, and the completeness
of their history remain unverified without an authorized token and a controlled
metadata/query test.

The public EODHD documentation also warns that renamed tickers do not
automatically preserve history. That makes a security-master check mandatory;
successor ticker data cannot be silently substituted for a historical constituent.

## 5. Yahoo Limitations

The existing verified project mapping remains authoritative. This investigation
does not regenerate it. The prior audit observed mapped daily coverage beginning
2022-07-01, but that observation does not establish predecessor coverage.

yfinance documents daily and intraday intervals and intraday retention limits;
Yahoo's generic help says history is usually not earlier than 1970 and is
instrument-dependent. Neither source establishes Thai predecessor/delisted
coverage for these 22 rows. Yahoo therefore cannot be used to declare the gaps
recoverable or unrecoverable without a row-level historical-identity test.

## 6. Alternative Sources

Bloomberg, LSEG/Refinitiv, and FactSet are plausible institutional routes, but
exact SET coverage and earliest dates for these securities require authenticated
entitlements. LSEG documents broad interday/intraday/tick products and Tick
History documentation states global history back to January 1996; that is not
proof of SET coverage. TradingView lists SET coverage and permits chart-data
export, but historical depth and predecessor identity are not established.

Alpha Vantage documents a global daily endpoint with a long history, but no
SET-specific evidence was found. Stooq has no authoritative SET capability
evidence in this investigation.

## 7. Source Capability Matrix

See [historical_data_source_capability_matrix.md](historical_data_source_capability_matrix.md).

## 8. Missing-Period Recovery Matrix

| Gap group | Official SET route | EODHD route | Yahoo route | Assessment |
|---|---|---|---|---|
| BANPU 2026_H2 | Theoretically possible if historical security-period data is delivered | Predecessor/period coverage unverified | No verified coverage | Requires security identity and access confirmation |
| BLA 2022_H2 | Theoretically possible | BLA.BK is a candidate; period still unverified | No verified coverage | Candidate for controlled EODHD test after credentials |
| DTAC 2022_H2 | Theoretically possible | Predecessor coverage unverified | No verified coverage | Official route preferred |
| GULF 2022_H2–2025_H1 | Theoretically possible | Current-symbol candidate only; required historical periods unverified | No verified coverage | Need exact period and identifier test |
| INTUCH 2022_H2–2025_H1 | Theoretically possible | Predecessor/period coverage unverified | No verified coverage | Do not substitute successor security |
| IRPC 2022_H2 | Theoretically possible | IRPC.BK is a candidate; period still unverified | No verified coverage | Candidate for controlled EODHD test after credentials |
| TIDLOR 2022_H2–2024_H2 | Theoretically possible | Historical NTL/predecessor coverage unverified | No verified coverage | Official route preferred |
| TRUE 2022_H2–2023_H1 | Theoretically possible | Predecessor/period coverage unverified | No verified coverage | Official route preferred |

“Theoretically possible” is not an acquisition result. It means the source's
documented product could plausibly cover the row; actual recovery requires an
authorized request and row-level validation.

## 9. Actual Blocking Constraints

1. No SET/SETSMART authenticated subscription or delivered historical extract is
   available in the current workspace.
2. No EODHD API token is present, and no paid historical-plan entitlement is
   available for testing.
3. Public documentation does not establish the exact security identifiers,
   predecessor symbols, OHLCV schema, and earliest date for every missing row.
4. The verified Yahoo mapping cannot be guessed, regenerated, or extended by
   treating successor tickers as historical identities.

## 10. Earliest Realistic Historical Coverage

| Source | Earliest defensible statement |
|---|---|
| SET Historical Data | The public page states historical trading/statistics data from 1975-04-30; exact requested fields and security-period delivery remain to be confirmed. |
| SETSMART investor web | Public comparison material advertises 5 years; API/package history is entitlement-dependent. |
| EODHD | BK-specific earliest date unknown; provider-wide claims cannot be transferred to these symbols. |
| Yahoo | Generic help says usually not earlier than 1970, but Thai ticker-specific availability is unknown; project-observed mapped coverage begins 2022-07-01. |
| LSEG Tick History | Global documentation says back to January 1996; SET-specific coverage unknown. |
| Bloomberg, FactSet, TradingView, Alpha Vantage, Stooq | Earliest exact coverage for these Thai securities is unknown or not verified. |

For intraday, SET tick data is a separate request; EODHD retention is
instrument/product dependent; Yahoo documents a recent intraday window rather
than a long historical tick archive; and institutional tick products require
entitlements.

## 11. Recommended Data-Access Options

1. Request a small, non-production SET Historical Data/SETSMART sample covering
   one row from each identity class, with symbol/security ID, date, OHLCV fields,
   and corporate-action/security-master metadata.
2. If EODHD is being evaluated, obtain an authorized token and test only BLA.BK
   and IRPC.BK first, plus explicitly searched predecessor symbols. Record
   provider responses without merging them into raw production data.
3. Treat Bloomberg/LSEG/FactSet as paid institutional alternatives if official
   SET delivery is unavailable or incomplete; obtain written confirmation of SET
   coverage and predecessor security identity before purchase.
4. Keep Yahoo as a comparison source, not as the authority for unresolved
   historical identities.

## 12. What Can and Cannot Be Verified

Verified from public documentation: SET's historical-data product and stated
1975-04-30 trading/statistics start; SETSMART/API product existence; EODHD daily
fields, BK exchange, delisted query mechanism, and access tiers; yfinance interval
and intraday constraints; and the existence of institutional historical products.

Not verified: actual row-level recovery for any of the 22 gaps; exact Thai
predecessor symbols in EODHD or institutional feeds; exact delivered OHLCV
schema/adjustment policy; exact earliest date per security; completeness of
delisted Thai history; or any source's ability to recover every row.

No Step 3 acquisition was started, and no production/raw dataset, existing OHLCV
CSV, ticker mapping, or gate file was modified.

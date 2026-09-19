# Market-Data Coverage and Historical Extension Audit

Status: read-only research audit. No data was downloaded, changed, repaired, or
added to the approved research path.

## Executive summary

The approved research path currently covers 3 January 2023 through 4 September
2026 (898 observed union rows). Seventeen symbols have a complete raw file for
that full window; MRDIYT is approved but only begins in 2025, while GULF and
TIDLOR are explicitly approved with known gaps and corporate-action boundaries.
The historical SET50 membership file covers eight official
half-year snapshots from 2023 H1 through 2026 H2, but no pre-2023 membership
snapshots.

Extending price history to 10–20 years is technically plausible, but extending
the *approved research dataset* also requires historical SET50 membership,
security-identity mappings, corporate-action treatment, and source validation for
every symbol and date. The official SET historical-data service is the strongest
candidate for provenance but is a data-request/service route rather than an
assumed free bulk source. Free aggregators may provide useful candidates, but
none should enter the approved path without a new audit.

## Current coverage

The manifest has 20 rows: 18 `APPROVED` (including the shorter-history MRDIYT)
and 2 `APPROVED_WITH_KNOWN_GAP`.
All currently represented raw files end on 2026-09-04. Coverage by file is:

| Symbol | First raw date | Last raw date | Rows | Status / limitation |
|---|---:|---:|---:|---|
| BDMS, BGRIM, CENTEL, COM7, GLOBAL, HMPRO, IVL, KKP, KTB, LH, MTC, OSP, PTTGC, RATCH, SCGP, THAI, TOP | 2023-01-03 | 2026-09-04 | 898 each | Fully approved window |
| GULF | 2025-04-03 | 2026-09-04 | 348 | Known pre-merger coverage gap; boundary policy applies |
| TIDLOR | 2025-05-16 | 2026-09-04 | 323 | Known issuer/corporate-action continuity gap |
| MRDIYT | 2025-11-05 | 2026-09-04 | 208 | Newer listing; no earlier price history expected under this identity |

The apparent differences from 898 are not repaired by interpolation. The gate
also enforces exact raw-date presence and the existing continuity rules. The
current source pipeline is Yahoo Finance/yfinance, with explicit mapping audit,
raw validation, remediation, and manifest approval before `MarketDataEligibilityGate`
can admit a row.

### Membership coverage

`historical_set50.csv` contains 8 periods × 50 rows, from 2023 H1 through 2026
H2 (effective dates 2023-01-01 through 2026-12-31). It represents 63 distinct
symbols across those snapshots. The audit records changes such as TRUEE/BANPUU
temporary symbols, MRDIYT, the GULF/INTUCH merger boundary, and the TIDLOR
identity issue. There is no verified SET50 constituent history before 2023 H1
in the current repository. This is the main universe-integrity gap for a
10–20-year study.

## What would be needed for an extension

To reach approximately 10 years (roughly back to 2016), the project would need
about seven additional years of daily prices and approximately 14 additional
half-year SET50 snapshots. Fifteen years implies roughly 2009–2010 and about 24
additional snapshots; twenty years implies roughly 2006–2007 and about 34
additional snapshots. These counts are planning estimates, not evidence that
the documents exist or that every symbol was listed then.

The price universe must include historical constituents, not only today’s 20
manifest symbols. Former constituents, delisted issuers, renamed securities,
merger predecessors, and symbols with no current Yahoo mapping may be required
for an unbiased historical universe. Current constituents cannot be substituted
for missing historical members.

## Candidate free or low-cost sources

| Source | Potential depth / fields | Coverage and quality assessment | Access / licensing assessment | Research disposition |
|---|---|---|---|---|
| SET Information Services / SETSMART | Official SET end-of-day and historical equity data; corporate/reference services are available through SET information products. | Best provenance and likely strongest corporate-action/security-master support; exact historical depth and bulk availability must be requested per product. | Official page describes historical-data requests and SMART Marketplace services, not an unrestricted free bulk archive. | Preferred validation/reference source; obtain terms and a historical membership extract before acquisition. |
| Yahoo Finance (`.BK`) / yfinance | Daily OHLCV and actions where Yahoo has a symbol; existing pipeline already uses it. Yahoo says historical viewing is broad, but CSV download requires Gold and availability varies by instrument. | Convenient but ticker history, delistings, mergers, adjusted-vs-raw semantics, and old SET coverage are uneven. | Public chart access/yfinance is not equivalent to a guaranteed free redistribution license; official Yahoo help documents subscription/licensing limits. | Candidate acquisition source only; every extension needs the same mapping, raw validation, and remediation gates. |
| Twelve Data | Daily OHLCV with volume; documentation states daily history is typically 10+ years and supports date ranges, with a 5,000-record request limit. | Thailand is listed as a supported market, but symbol-by-symbol depth, adjusted history, and corporate-action completeness must be verified. | Free tier has limited credits; historical availability and usage rights vary by plan/instrument. | Plausible 10-year cross-check/source; not yet approved and not assumed free for bulk research. |
| Alpha Vantage | Daily raw OHLCV; documentation describes 25+ years and adjusted endpoints. | Documentation does not establish complete SET/SET50 coverage; ticker support and Thai corporate actions need direct verification. | Full history (`outputsize=full`) is premium; free access is limited to compact history/API quotas. | Useful feasibility probe if coverage is confirmed; not a guaranteed free 10–20-year source. |
| Stooq | Third-party daily CSV/API may have long history for some instruments. | SET/Thai symbol coverage and corporate-action treatment are not established by this audit; ticker discovery and history must be tested. | Access/API requirements and redistribution terms need confirmation; third-party coverage is not an approval basis. | Do not rely on it until a symbol-level coverage and license audit passes. |
| Kaggle/GitHub/scraped pages | May contain prebuilt CSVs or chart data. | Provenance, survivorship, timestamp, adjustment, and completeness are usually unclear. | Dataset licenses and redistribution rights vary. | Exploration only; unsuitable as an approved source without primary-source reconstruction. |

SET describes historical-data requests, end-of-day data, reference data, and
corporate-action services through its information-services products. [SET
Information Services](https://www.set.or.th/en/services/connectivity-and-data/data/main)
is therefore the strongest provenance candidate, although this audit does not
assume it is free.

Yahoo's own help says historical CSV download is a Gold feature and that some
instruments lack download availability because of licensing restrictions.
[Yahoo historical-data help](https://help.yahoo.com/kb/sln2311.html)

Twelve Data documents Thailand as a supported market, daily history typically
over 10 years, date filtering, and a 5,000-record request limit; it also warns
that availability and rights vary by instrument and plan. [Twelve Data market
coverage](https://twelvedata.com/stocks), [historical-data limits](https://support.twelvedata.com/en/articles/5214728-getting-historical-data),
and [data-rights/availability notes](https://support.twelvedata.com/en/articles/5609168-introduction-to-twelve-data)
support treating it as a candidate rather than pre-approved data.

Alpha Vantage documents 25+ years for its daily endpoint, but full history is
premium and the documentation examples do not prove SET coverage. [Alpha
Vantage API documentation](https://www.alphavantage.co/documentation/)

## Walk-forward impact estimate

Using the existing comparable-block reference (250 observed research rows,
80-row OOS blocks, equal capital reset, and no short terminal block), a rough
252-observed-session-per-year planning estimate is:

| Total history | Approx. observed rows | Approx. full usable OOS blocks after 250-row history | Approx. terminal remainder |
|---:|---:|---:|---:|
| Current 3.7 years | 898 | 8 | 8 rows |
| 10 years | 2,520 | 28 | 30 rows |
| 15 years | 3,780 | 44 | 10 rows |
| 20 years | 5,040 | 59 | 70 rows |

These are planning estimates only. Actual SET holidays, suspensions, listing
dates, per-symbol gaps, and the historical-universe gate determine usable rows.
More blocks do not make expanding research windows statistically independent.

## Historical-universe and identity risks

- The index is reconstituted semiannually; older official snapshots are needed
  to avoid survivorship bias.
- Ticker changes and temporary symbols must remain date-specific; TRUEE/BANPUU
  cannot be silently mapped to current symbols.
- GULF/INTUCH and TIDLOR involve merger, replacement, or issuer-identity
  boundaries; joining their prices would create fabricated continuity unless a
  separately approved security-master policy exists.
- Delistings, suspensions, relistings, rights issues, splits, dividends, and
  adjusted/raw-price differences can change both OHLCV and tradability.
- A current ticker may represent a different legal issuer than an older ticker.
- Historical SET50 membership and historical price coverage are separate gates;
  having a price file does not make a symbol eligible.

## Validation required before approval

For every candidate source and symbol:

1. Preserve the downloaded source artifact read-only with provenance, query
   parameters, retrieval date, license, and checksum.
2. Validate schema, timezone/date normalization, duplicate dates, monotonicity,
   OHLC relationships, positive volume, and exact-session coverage against an
   independently sourced SET trading calendar.
3. Reconcile corporate actions and adjusted/raw semantics; never mix adjusted
   closes with raw execution OHLC without an explicit policy.
4. Audit ticker-to-security identity, issuer name, ISIN if available, listing,
   delisting, merger, and suspension intervals.
5. Extend official historical SET50 membership snapshots and source URLs; audit
   every effective boundary and symbol mapping.
6. Run `validate_raw_frame` and coverage checks, then create acquisition,
   remediation, and manifest records. Only an explicit approved decision may
   expose a row through `MarketDataEligibilityGate`.
7. Re-run continuity, no-lookahead, valuation, and historical-universe tests
   before any backtest or walk-forward run.

## Recommendation for human decision

Extension is worthwhile if the research goal is stronger regime coverage and a
larger descriptive OOS sample. It is not a quick Yahoo backfill: the limiting
work is historical SET50 membership and security identity, not merely obtaining
more candles. The recommended sequence is to request/verify official SET
historical membership and data availability first, then run a small, read-only
coverage pilot against one official source and one cross-check source. Do not
approve or merge any new data until the validation and remediation gates pass.

No final source, cost, or acquisition decision is made by this audit.

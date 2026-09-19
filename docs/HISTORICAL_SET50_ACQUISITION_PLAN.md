# Historical SET50 Acquisition Plan: 2016-2026

Status: planning and verification only. This document does not acquire data,
modify approved raw files, change the manifest or eligibility gate, or run a
backtest.

## Decision summary

The minimum target requires **22 canonical SET50 snapshots**: 2016 H1 through
2026 H2. The repository currently exposes 63 symbols from the audited
2023-2026 snapshots. Adding the known predecessor/temporary identity aliases
TRUEE, DTAC, GULFI, and BANPUU produces **67 distinct planning symbols**. This
is a provisional planning universe, not a claim that all 67 symbols occur in
the missing 2016-2022 snapshots. The complete historical union can only be
finalized after legitimate access to the official pre-2023 files.

The best legitimate acquisition route is an official SET or SETSMART licensed
historical-data and constituent extract. The public SET archive lists the
required periods, but its download controls route through member authentication.
Yahoo/yfinance remains a technical candidate or cross-check only; it is not a
source approval or licensing decision.

## 1. Required official membership snapshots

The exact canonical periods are:

```text
2016 H1, 2016 H2, 2017 H1, 2017 H2, 2018 H1, 2018 H2,
2019 H1, 2019 H2, 2020 H1, 2020 H2, 2021 H1, 2021 H2,
2022 H1, 2022 H2, 2023 H1, 2023 H2, 2024 H1, 2024 H2,
2025 H1, 2025 H2, 2026 H1, 2026 H2.
```

Effective dates are January 1-June 30 and July 1-December 31, except that
2024 H1 starts January 2. The 2026 H2 revised file is the current repository's
primary version. SET also lists occasional “between periodic review update”
files; those are revision candidates and must not replace a canonical snapshot
without explicit effective-date and revision review.

Source: [SET50/SET100 constituent archive](https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100).
The archive is publicly discoverable, but downloads route to
`member.set.or.th`; no authentication or access control should be bypassed.

| Period range | Official listing | Repository verification | Acquisition status |
|---|---|---|---|
| 2016 H1-2022 H2 (14 periods) | Listed in SET archive | No pre-2023 file in repository | Requires legitimate SET access |
| 2023 H1-2026 H2 (8 periods) | Listed in SET archive | Audited repository PDFs/CSV | Existing current path only |

## 2. Security identity review

The identity table is deliberately conservative. A modern ticker is not treated
as proof of price continuity with a predecessor.

| Historical symbol | Modern symbol | Issue | Continuity decision | Human approval |
|---|---|---|---|---|
| TRUE / TRUEE / DTAC | TRUE | 2023 amalgamation, predecessor delisting, new listing | No unapproved splice | Required |
| GULF / GULFI / INTUCH | GULF | 2025 amalgamation and trading suspension | Explicit boundary required | Required |
| TIDLOR | TIDLOR | Ngern Tid Lor to TIDLOR Holdings transition | Explicit boundary required | Required |
| BANPU / BANPUU | BANPU/BANPUU | Temporary/revised symbol and amalgamation context | Unresolved | Required |
| MRDIYT | MRDIYT | Newer listing; no pre-listing history | No pre-listing fabrication | Required |
| SCB | SCB | SCB X / Siam Commercial Bank corporate transition | Verify issuer continuity and corporate-action treatment | Required |
| TTB | TTB | TMB/Thanachart bank combination and rename | Verify issuer continuity and corporate-action treatment | Required |

Other historical constituents require the same review for renames, mergers,
delistings, suspensions, rights issues, splits, and relistings. The matrix in
`reports/historical_set50_symbol_matrix.csv` marks every symbol as unreviewed
or review-required; none is approved for acquisition.

## 3. Provisional historical universe

The 67 planning symbols are the union of all symbols currently present in the
audited repository membership file plus the four known aliases needed to avoid
silently losing identity boundaries. Categories are:

- Directly observed current-path symbols: 63.
- Explicit identity-review aliases: TRUEE, DTAC, GULFI, BANPUU.
- Unresolved historical identities: all symbols until issuer, listing interval,
  and corporate-action evidence is reconciled for the target period.
- Delisted/former constituents: must be added if the official 2016-2022 files
  show them; they cannot be replaced by current constituents.

Because pre-2023 snapshots have not been retrieved, the complete historical
union is intentionally not asserted. The generated count is a planning lower
bound plus known aliases.

The existing 2023-2026 CSV also contains several company-name strings with
embedded PDF footer or neighboring-row text (for example WHA, SCC, KBANK,
GLOBAL, and SCGP). These are extraction-quality flags, not evidence of ticker
changes. They must be corrected from the source layout during membership
acquisition rather than copied into a historical security master.

## 4. Price-data acquisition matrix

The machine-readable matrix provides, for each of the 67 planning symbols:

- required dates `2016-01-01` through `2026-09-04`;
- preferred source order (official SET/licensed, legitimate secondary, then
  Yahoo/yfinance cross-check);
- source and licensing limitations;
- adjusted/raw status, corporate-action concerns;
- acquisition and validation status, both `NOT_STARTED`;
- identity status and human-approval requirement.

No row is marked available merely because a provider advertises historical
depth. A symbol becomes an acquisition target only after it appears in an
official snapshot and its identity is resolved.

## 5. Independent validation plan

Before any file can enter the approved research path:

1. Preserve source artifacts, request parameters, retrieval timestamp, license,
   and checksums.
2. Reconcile dates to an independently sourced SET trading calendar; do not
   infer missing sessions from another symbol.
3. Check schema, timezone normalization, monotonic dates, duplicate dates,
   OHLC envelope (`High >= Open/Close`, `Low <= Open/Close`), and positive
   volume.
4. Separate raw execution OHLC from adjusted close. Corporate actions must be
   represented as events, not hidden by rewriting prices.
5. Audit issuer/security identity, ISIN where available, listing and delisting
   intervals, ticker changes, suspensions, mergers, and successors.
6. Reconcile source discrepancies without automatically choosing a winner;
   unresolved discrepancies remain unapproved.
7. Run the existing validation/remediation/readiness process and obtain an
   explicit approval before any manifest or gate exposure.

## 6. Cost and access classification

| Source class | Technical status | Cost/access status | Planning use |
|---|---|---|---|
| SET/SETSMART official history | Strongest provenance; exact product access unverified | Authentication and/or paid/licensed service likely | Preferred acquisition and reference source |
| Legitimate licensed secondary vendor | Symbol-level coverage unverified | May require paid plan and redistribution review | Independent cross-check or fallback |
| Yahoo/yfinance | Demonstrated partial technical retrieval in pilot | Licensing and availability vary; not assumed free redistribution | Candidate/cross-check only |
| Public archives, Kaggle, GitHub, scraped pages | Technically variable | Provenance and licensing unclear | Exploration only; not approval basis |

Technical accessibility is not legal permission. No paywall, authentication,
or licensing restriction may be bypassed.

## 7. Readiness and required human decision

The project is **not ready to begin full historical price acquisition**. The
remaining blockers are:

- legitimate access to all 14 missing 2016-2022 official snapshots;
- confirmation of authoritative versus revised files and effective dates;
- completion of the historical security master and human decisions for the
  identity cases above;
- a licensed price source and independent SET session calendar;
- explicit approval of the final historical symbol universe and raw-data
  validation protocol.

The next human decision is whether to authorize a membership-only acquisition
through a legitimate SET/SETSMART access route. No price acquisition, manifest
change, eligibility-gate change, backtest, or optimization should follow until
that decision is made.

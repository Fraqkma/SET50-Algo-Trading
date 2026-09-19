# Historical SET50 Membership Access Audit

Status: read-only source and acquisition-readiness audit. No constituent file,
price file, manifest, eligibility rule, strategy, or backtest was changed. No
synthetic membership list was constructed.

## Executive conclusion

The official SET archive publicly exposes the period index for all 14 missing
half-year snapshots (2016 H1 through 2022 H2), but each constituent download is
behind member authentication. Thus the archive establishes that the periods
exist, not that their constituent rows have been independently verified. All 14
snapshots are `ACCESS_REQUIRED`; none is currently research-ready.

A licensed SET/SETSMART extract would resolve the membership blocker if it
contains the official rows, effective dates, revisions, and security identifiers.
The project is **not ready for full historical price acquisition** until that
extract is obtained and audited, and identity policies are approved.

## A. Officially verified membership

None of the 14 missing *constituent lists* is verified in this repository. The
official archive page is publicly viewable and lists 2016 H1, 2016 H2, through
2022 H2 with the conventional Jan–Jun and Jul–Dec effective periods. Its file
links display “Login to download file” and route to SET member access.

Official archive: [SET50 and SET100 constituents](https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100).

## B. Official source identified but access-restricted

All 14 rows in the companion JSON/CSV report are in this category. The archive
period metadata is public (`publicly_accessible=true`), while the file bytes are
not (`file_bytes_publicly_accessible=false`, `authentication_required=true`).
No request was made and no authentication was bypassed.

Legitimate routes identified by SET are:

- [SET Information Services](https://www.set.or.th/en/services/connectivity-and-data/data/main), which catalogues historical data, SETSMART, and reference/corporate-action services.
- [Historical Data Request](https://www.set.or.th/en/services/connectivity-and-data/data/historical) and the [request service](https://www.set.or.th/en/services/connectivity-and-data/data/data-request), which provide a legitimate one-time/request route; the exact constituent-file product must be confirmed with SET.
- [SETSMART web-based services](https://www.set.or.th/en/services/connectivity-and-data/data/web-based), whose historical depth and access depend on the subscribed product.
- [SMART Marketplace](https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace), which includes authenticated reference-data and corporate-action APIs.
- [SET end-of-day services](https://www.set.or.th/en/services/connectivity-and-data/data/end-of-day), which may provide official index/constituent reference files subject to product access.

The five-year SETSMART investor product alone does not establish coverage for
2016–2022; an enterprise/advance product or a direct licensed historical request
would be needed.

## C. Secondary evidence only

No third-party list, search snippet, GitHub/Kaggle dataset, or reconstructed
membership table is admitted as evidence. Such material may be used later only
as a cross-check after the official extract is obtained and explicitly approved.

## D. Unverified

Period metadata is not unverified: all 14 periods are identified in the official
archive. However, all 14 constituent contents remain unverified. This distinction
is deliberate; it prevents a visible archive index from being mistaken for an
audited historical universe.

## Snapshot access matrix

The generated CSV has one row for each exact period, effective date, archive URL,
access status, verification status, identity status, price readiness, blocker,
and human-approval requirement. The statuses are deterministic and are not
derived from a performance result.

| Periods | Official source | Public file access | Authentication | Acquisition status | Price readiness |
|---|---|---|---|---|---|
| 2016 H1–2022 H2 (14) | SET archive period listed | Metadata only | Required | ACCESS_REQUIRED | NOT_READY |

## Identity cross-reference

The prior security-identity audit remains controlling. The missing membership
rows must preserve historical symbols and effective dates for TRUE/TRUEE/DTAC,
GULF/INTUCH/GULFI, TIDLOR, BANPU/BANPUU, SCB/SCBB, TMB/TTB, and MRDIYT. The
first five contain verified non-continuity or mapping boundaries; TMB/TTB is a
date-effective ticker change; MRDIYT has a listing boundary. None may be joined
merely because tickers look similar. The archive extract must be reviewed against
these cases before any price acquisition.

## Acquisition-readiness matrix

| Required period | Official status | Identity status | Price-data readiness | Remaining blocker | Human approval |
|---|---|---|---|---|---|
| Each of 2016 H1–2022 H2 | Archive identified; file access restricted | Review required against identity audit | Not ready | Obtain and validate licensed official rows | Yes |

No historical symbol is certified safe for the future price-acquisition stage
from this audit alone. Unambiguous symbols can be nominated only after the
official snapshot rows and security identifiers are received.

## Final counts and decision

- Missing snapshots with an identified official source: **14**.
- Accessible without authentication: **0** constituent files (period metadata is public).
- Requiring legitimate SET/member access: **14**.
- Periods completely unverified at the metadata level: **0**; constituent lists unverified: **14**.
- A licensed SET/SETSMART extract would resolve the membership blocker **provided** it includes official half-year rows, effective dates, revisions/provenance, and identifiers.
- Ready for full historical price acquisition: **No**.

The next human decision is whether to request or license the official extract and
approve its scope, cost, licensing, identity mapping, and validation plan. No
statistical or strategy work should proceed on a reconstructed membership list.

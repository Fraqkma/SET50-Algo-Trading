# Historical SET50 Data-Access Decision Package

Status: pre-acquisition planning only. No historical price data was downloaded,
merged, or exposed to the approved research path.

## A. Exact data to request

Request a licensed official extract covering **all 22 canonical half-year SET50
periods from 2016 H1 through 2026 H2**, plus any between-period revision. The
extract should contain the fields listed below.

| Field | Priority |
|---|---|
| Index name | REQUIRED |
| Effective start and end dates | REQUIRED |
| Historical symbol | REQUIRED |
| Security identifier / exchange code | REQUIRED |
| Issuer/security name | REQUIRED |
| Membership status | REQUIRED |
| Revision or boundary date | REQUIRED |
| Source provenance, version and correction history | REQUIRED |
| ISIN or equivalent independent identifier | HIGHLY_DESIRABLE |
| Listing/delisting dates | HIGHLY_DESIRABLE |
| Corporate-action reference ID | HIGHLY_DESIRABLE |
| Corporate-action adjustment factors | OPTIONAL |

The request must explicitly cover ticker changes, mergers/amalgamations,
successors, delistings, relistings, corrections, and research-use licensing.

## B. Route comparison

The official routes were compared using SET documentation:

- [SET Historical Data Request](https://www.set.or.th/en/services/connectivity-and-data/data/historical): best initial route because it supports a tailored, one-time official request. The exact availability of constituent and security-master fields must be confirmed.
- [Historical Data Request Service](https://www.set.or.th/en/services/connectivity-and-data/data/data-request): complementary request/contact route for defining the required package.
- [SETSMART services](https://www.set.or.th/en/services/connectivity-and-data/data/web-based): potentially useful for historical securities, issuer information, announcements and statistics, but depth depends on the subscribed product.
- [SMART Marketplace](https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace): possible authenticated API route for reference data and corporate actions; exact membership endpoint and history must be confirmed.
- [SET End-of-Day service](https://www.set.or.th/en/services/connectivity-and-data/data/end-of-day): useful official cross-check for index/weight files, but not assumed sufficient for complete historical membership.

The recommendation is to begin with a SET Historical Data Request for a combined
membership and security-reference bundle, then use SETSMART or SMART Marketplace
only if their product scope is confirmed to meet the schema.

## C. Still unknown until SET responds

The public service descriptions do not establish whether a delivered product
will include every required field, all between-period revisions, historical
security identifiers, correction history, or redistribution rights. They also do
not prove that an EOD/index file alone contains the complete 2016–2022 member
history. These questions are included verbatim in the generated request
checklist.

## D. Acceptance criteria

Do not admit a delivery unless:

1. All 22 canonical periods are present.
2. Effective dates and index name are explicit.
3. Each member is identified by an authoritative security identifier or a
   resolvable official mapping.
4. Revisions, replacements, corrections and boundary events are documented.
5. Provenance, versioning, checksums and licensing are preserved.
6. The prior identity audit cases—TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI, TIDLOR,
   BANPU/BANPUU, SCB/SCBB, TMB/TTB and MRDIYT—reconcile without synthetic
   continuity.

## E. Rejection criteria

Reject a delivery with missing periods, implicit dates, ticker-only identity,
unexplained revisions, unverifiable provenance, unsuitable licensing, or any
requirement to infer historical membership from current constituents.

## F. If SET supplies membership lists only

Membership lists alone are not sufficient to begin price acquisition. A separate
official security-master/reference extract would still be required, covering
identifiers, issuer/security names, ticker history, listing/delisting dates,
successor/predecessor relationships, mergers, suspensions, and corporate-action
references. Historical prices must remain separate at identity boundaries until
an explicit mapping policy is approved.

## Decision

The project is **not ready** to acquire historical prices immediately after a
membership-only delivery. It can proceed to the price-acquisition stage only
after the membership and security-reference data pass the acceptance criteria,
licensing is confirmed, and a human approves the identity mapping policy.

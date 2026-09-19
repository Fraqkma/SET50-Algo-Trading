# SET50 Historical Data Request Specification

Status: pre-acquisition request package. This document does not authorize
downloading, transforming, merging, approving, or backtesting any historical
data.

## Scope

Request a licensed extract covering the 22 canonical half-year periods from
2016 H1 through 2026 H2:

`2016 H1 ... 2026 H2`, with effective dates of 1 January–30 June and 1 July–31
December for each year, plus any between-review revisions.

The request must include membership rows and the related historical
security-master/reference information. The machine-readable field priorities
and checklist are in [historical_set50_data_request_spec.json](../reports/historical_set50_data_request_spec.json) and [historical_set50_data_request_checklist.csv](../reports/historical_set50_data_request_checklist.csv).

## Required membership and reference data

Required fields are: index name, effective start/end dates, historical symbol,
authoritative security identifier, issuer/security name, membership status,
revision or boundary date, and source provenance/version. Highly desirable
fields are ISIN or exchange code, listing/delisting dates, ticker/name-change
history, and corporate-action references. Corporate-action factors are
optional unless SET documents their semantics.

The extract must explicitly address TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI,
TIDLOR, BANPU/BANPUU, SCB/SCBB, TMB/TTB, and MRDIYT. No identity may be joined
solely because tickers are similar.

## Price-data clarification questions

If price data are offered with the reference extract, SET must state:

1. Whether OHLCV is raw, adjusted, or supplied in both forms.
2. Whether splits, rights, dividends, bonus issues, and other corporate actions
   are reflected in each field.
3. Whether the series is suitable for OHLC execution backtesting, including
   whether raw execution prices remain available.
4. Whether a complete corporate-action record, adjustment factors, and effective
   dates accompany the prices.
5. Whether suspended, delisted, successor, and predecessor securities retain
   separate identities and files.

Adjusted analytical prices must not be substituted for raw execution OHLC.

## Licensing and commercial questions

Please provide one-time and recurring cost, permitted internal research use,
retention period, derived-report rights, API/download limits, redistribution
restrictions, and the applicable licence or terms of use. Cost and permitted
research usage remain unresolved until SET responds; the project assumes the
data are not free.

## Acceptance criteria

Data may enter the acquisition/validation workflow only if all 22 periods are
present, dates and identities are explicit, revisions are documented, corporate
actions and listing boundaries are preserved, provenance/versioning/checksums
are retained, and the audited identity cases reconcile without synthetic
continuity. Raw versus adjusted semantics and licensing must be explicit.

## Rejection criteria

Reject deliveries with missing periods, implicit boundaries, ticker-only
identity, current-constituent substitution, unexplained corrections, unclear
raw/adjusted semantics, missing corporate-action evidence, unverifiable
provenance, or licensing that does not permit the intended research use.

## Ready-to-send English request

> Subject: Request for licensed historical SET50 constituent and security-reference data (2016–2026)
>
> Dear SET Information Products / SETSMART team,
>
> We are conducting internal quantitative research on the SET50 index and would
> like a quotation and availability confirmation for an official, licensed
> historical extract covering all canonical SET50 half-year periods from 2016 H1
> through 2026 H2 (22 periods). Please include the effective start and end date
> for each period and all between-period additions, removals, replacements,
> corrections, and superseded versions.
>
> For every membership row, please provide the index name, historical ticker,
> authoritative security identifier/exchange code, issuer or security name,
> membership status, revision/boundary date, provenance, product/file version,
> and correction history. Where available, please include ISIN, listing and
> delisting dates, ticker/name changes, merger or amalgamation boundaries,
> successor/predecessor references, and corporate-action identifiers.
>
> Please also clarify whether historical OHLCV can be supplied. For each price
> field, state whether it is raw or adjusted, how splits, rights, dividends and
> other corporate actions are handled, whether raw OHLC is suitable for execution
> backtesting, and whether a complete corporate-action file and adjustment
> factors are included. Please keep predecessor, successor, suspended and
> delisted securities separately identifiable.
>
> Please provide pricing, delivery format, API or download limits, licence terms,
> permitted internal research and derived-report use, retention rights, and any
> redistribution restrictions. We will preserve the delivered files and
> provenance and will not redistribute the source data.
>
> Please confirm whether this request is best fulfilled through SET Historical
> Data Request, SETSMART, SMART Marketplace, or another official product, and
> identify any required account, authentication, or subscription.
>
> Kind regards,
> [Researcher / Organisation]

No request has been sent by this repository. Human approval and a SET response
are required before any acquisition begins.

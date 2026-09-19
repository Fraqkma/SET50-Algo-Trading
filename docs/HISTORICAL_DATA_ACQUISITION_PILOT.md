# Historical Data Acquisition and Validation Pilot

Status: **UNAPPROVED feasibility pilot only**. Existing raw market data,
approved manifest, eligibility gate, strategies, backtest, and walk-forward
artifacts were not modified.

## A. Scope and isolation

The pilot tested four representative symbols over the requested range
2010-01-01 through 2022-12-31:

- PTT — long-lived constituent and validation anomaly case;
- ADVANC — long-lived constituent;
- TRUE — issuer/merger identity case;
- BANPU — long-lived issuer with historical symbol/corporate-action questions.

Files were written only under
`data/pilot/historical_acquisition/`. Every price file is explicitly
`UNAPPROVED_ACQUIRED` unless a validation issue is recorded. No pilot file is
visible to `MarketDataEligibilityGate`.

## B. Historical SET50 membership investigation

The official SET constituent page exposes archive periods from 2005 onward,
including 2010–2022 semiannual periods, but every archive download link tested
redirects to SET member login. The pilot saved the archive landing page as
`set_constituents_archive_landing.html`; it is not a constituent snapshot.

Result: official historical membership appears obtainable in principle, with
the earliest listed archive in 2005, but no pre-2023 membership snapshot was
acquired in this pilot. Therefore membership status for the four price samples
during 2010–2022 remains unresolved. Current 2023+ membership rows are not
used as a substitute for pre-2023 history.

## C. Successfully acquired data (still unapproved)

| Symbol | Provider ticker | Returned period | Rows | Status |
|---|---|---|---:|---|
| ADVANC | ADVANC.BK | 2010-01-04 – 2022-12-30 | 3,167 | Acquired; validation checks passed |
| TRUE | TRUE.BK | 2010-01-04 – 2022-12-30 | 3,167 | Acquired; identity/membership unresolved |
| BANPU | BANPU.BK | 2016-10-28 – 2022-12-30 | 1,500 | Acquired; requested early coverage unavailable |
| PTT | PTT.BK | 2010-01-04 – 2022-12-30 | 3,167 | Acquired; OHLC validation issue |

The Yahoo/yfinance files contain daily OHLCV plus adjusted close and action
columns. The existing `validate_raw_frame` tooling was used without repairing
any rows.

## D. Validation findings

### ADVANC and TRUE

Schema, ordering, duplicate-date, OHLC, and volume checks passed. Their dates
match the ADVANC pilot calendar exactly. This means the files are technically
usable candidates, not approved research data. TRUE still requires a historical
security-master decision because a current ticker can represent a changed legal
issuer or merger lineage.

### BANPU

Schema and row-level checks passed for the returned range, but Yahoo returned no
rows before 2016-10-28 despite the 2010 request. It cannot support a full
2010–2022 pilot window without another source. Any temporary BANPU/BANPUU symbol
period must remain date-specific.

### PTT

One existing validation issue was detected: on 2018-12-18, `High=47.75` while
`Close=48.00`, so High is below Close. The row was preserved unchanged and the
file remains unapproved. No large (>50%) close discontinuity was automatically
treated as a corporate action.

### Calendar coverage

ADVANC, TRUE, and PTT share the same 3,167 returned dates. BANPU begins later
and is missing 1,667 dates relative to that pilot calendar. No official
pre-2023 SET trading calendar was acquired, so this is a cross-file coverage
comparison, not proof that every missing date was a trading session.

## E. Cross-source comparison

The attempted independent Stooq CSV endpoints returned HTTP 404/no usable data
for all four tested Thai ticker forms. Consequently, no overlapping OHLCV
comparison could be performed. This is a source-coverage failure, not evidence
that Yahoo is correct.

## F. Provenance

Machine-readable provenance is in
`reports/historical_data_acquisition_pilot.json` and `.csv`. For each acquired
file it records source, provider ticker, requested and returned dates, UTC
retrieval time, row count, relative artifact path, SHA-256 checksum, validation
issues, and apparent discontinuities. The official SET landing-page artifact is
recorded similarly. No Stooq response was retained because it contained no
usable data.

## G. Data that appears usable but is not approved

ADVANC and TRUE are technically clean candidates for further review. They are
not eligible for features or backtests because pre-2023 membership, identity,
corporate actions, source licensing, and independent calendar reconciliation are
incomplete. BANPU is also incomplete in the requested period. PTT has a direct
OHLC anomaly requiring source reconciliation.

## H. Sources rejected for this pilot

- Stooq: rejected as a cross-check for this pilot because tested Thai ticker
  forms returned no usable data.
- Current constituent lists: rejected as a historical-universe substitute.
- Any inferred ticker/merger stitching: rejected; no continuity was fabricated.

Yahoo was used only as an isolated feasibility source, not as an approval
decision. The official SET archive remains the preferred membership source, but
member-login access is a blocker for automated acquisition here.

## I. Remaining blockers

1. Obtain official pre-2023 SET50 snapshots, ideally 2010–2022, with effective
   dates and source PDFs/files.
2. Obtain an independent historical SET trading calendar and a second price
   source with Thai coverage.
3. Reconcile PTT's OHLC anomaly and all corporate-action/adjusted-price
   semantics.
4. Build a historical security master for TRUE, BANPU/BANPUU, delistings,
   mergers, and predecessor identities.
5. Run source-license review, exact-session coverage checks, and the existing
   acquisition/remediation workflow before any manifest change.

## Final recommendation

**PROCEED WITH CAUTION.** The pilot demonstrates that long daily files can be
retrieved from Yahoo for some symbols, but it does not yet establish a
survivorship-safe historical SET50 dataset. Official membership access,
independent price/calendar cross-checks, and identity/corporate-action work
remain necessary before a 10–20-year acquisition. Stop here and wait for human
approval; do not merge pilot files or run a strategy evaluation.

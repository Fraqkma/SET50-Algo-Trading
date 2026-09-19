# Historical SET50 Membership Feasibility

Status: research-only feasibility study. No historical price dataset was
downloaded or merged, and no approved data, manifest, gate, strategy, or
backtest behavior was changed.

## Executive conclusion

**PROCEED WITH CAUTION.** The public SET archive is a credible route to the
membership history needed for extension: it lists canonical half-year periods
from 2005 H1 through 2026 H2. However, the archive page routes downloads to
SET member authentication, so archive listing is not evidence that the files
are freely retrievable or licensed for this project. No pre-2023 constituent
snapshot is approved in this repository.

The realistic minimum extension is 2016-2026, conditional on obtaining the
official 2016-2022 files through legitimate SET access and completing a
security-master audit. A 2010-2026 extension is technically possible but has
substantially more identity and delisting risk. A 2006-2026 extension should
not be planned until official access, historical security identities, and
price coverage are demonstrated for the older constituents.

## A. Verified official evidence

The SET constituent page displays archive years 2005 through 2025 and current
2026 entries. Its canonical periods are:

- January 1-June 30 and July 1-December 31 for most years;
- January 2-June 30 for 2024 H1 because of the trading calendar;
- 2026 H2 is shown as July 1-December 31, with an additional December 30
  revision entry;
- the page also lists separate “between the periodic review update” files for
  selected periods. These must not be silently substituted for the canonical
  snapshot; the authoritative version must be selected using the PDF revision
  and effective-date evidence.

The canonical half-year period inventory is:

```text
2005 H1, 2005 H2, 2006 H1, 2006 H2, 2007 H1, 2007 H2,
2008 H1, 2008 H2, 2009 H1, 2009 H2, 2010 H1, 2010 H2,
2011 H1, 2011 H2, 2012 H1, 2012 H2, 2013 H1, 2013 H2,
2014 H1, 2014 H2, 2015 H1, 2015 H2, 2016 H1, 2016 H2,
2017 H1, 2017 H2, 2018 H1, 2018 H2, 2019 H1, 2019 H2,
2020 H1, 2020 H2, 2021 H1, 2021 H2, 2022 H1, 2022 H2,
2023 H1, 2023 H2, 2024 H1, 2024 H2, 2025 H1, 2025 H2,
2026 H1, 2026 H2.
```

The current repository has verified and audited files only for 2023 H1 through
2026 H2. The public page's download controls point to `member.set.or.th`; this
study did not bypass that authentication. SET's information-services offering
also describes historical, reference, and corporate-action data as services,
not as an unrestricted public bulk archive.

Sources: [SET constituent archive](https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100),
[SET information services](https://www.set.or.th/en/services/connectivity-and-data/data/main).

## B. Acquisition feasibility by target

| Target | Membership periods required | Feasibility assessment | Main blocker | Readiness today |
|---|---|---|---|---|
| 2016-2026 | 2016 H1 through 2026 H2, 22 canonical periods | Realistic if SET member access or a licensed SET extract is obtained | Authentication, licensing, PDF revision control, security master | Not ready |
| 2010-2026 | 2010 H1 through 2026 H2, 34 canonical periods | Technically plausible, but requires more predecessor/delisting mapping | Identity continuity and complete historical prices | Not ready |
| 2006-2026 | 2006 H1 through 2026 H2, 42 canonical periods | Archive is listed, but practical feasibility is unproven | Old constituents, delistings, corporate actions, source depth | Not ready |

These counts exclude 2005 H1-H2, which are listed by SET but are outside the
2006-2026 target. “Not ready” means no approved membership dataset exists, not
that the periods are absent from the public index.

## C. Security identity mapping requiring human approval

The following are evidence-backed boundary cases, not automatic mappings:

| Case | Verified issue | Required policy |
|---|---|---|
| TRUE / TRUEE / DTAC | SET records TRUEE and DTAC as predecessors in the 2023 amalgamation; a new TRUE was listed and added to SET50 effective March 2, 2023 | Keep predecessor and successor securities separate; do not splice prices without an approved corporate-action model |
| GULF / INTUCH / GULFI | SET records suspension for the amalgamation and inclusion of the resulting GULF effective April 2, 2025 | Preserve pre-event identities and the trading suspension; treat post-event GULF as a new boundary |
| TIDLOR | SET records TIDLOR Holdings as a new listed security traded May 15, 2025; older Ngern Tid Lor evidence exists under the same ticker lineage | Require issuer/security-master evidence before joining old and new instruments |
| BANPU / BANPUU | Existing repository audit identifies BANPUU as a temporary/revised symbol around the BANPU/BPP amalgamation; the pilot did not verify a complete price history | Store symbol events separately from index membership; do not map BANPUU to BANPU automatically |
| MRDIYT | Existing approved history begins in 2025 and the issuer is a newer listing | No pre-listing history should be manufactured |
| Other historical constituents | Renames, mergers, delistings, suspensions, rights issues, splits, and relistings are expected in 2005-2022 | Build a date-effective security master keyed by issuer/security identity, not ticker text alone |

Evidence: [TRUE/DTAC amalgamation](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256345950&symbol=SET),
[new TRUE listing](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256332630&symbol=TRUE),
[GULF/INTUCH amalgamation](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=95454300&symbol=GULF),
[TIDLOR new listing](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=96648700&symbol=SET).

## D. Price-data implications

The membership archive determines which prices are needed; it does not prove
that those prices exist in the current pipeline. The pilot showed long Yahoo
files for ADVANC, TRUE, and PTT, an incomplete BANPU file, and no independent
Stooq cross-check. Therefore each historical membership row must be classified
as:

1. accessible price history with verified identity;
2. accessible price history requiring corporate-action or ticker mapping;
3. unavailable or incomplete price history requiring another source; or
4. historical member whose identity or listing interval is unresolved.

Current 20-symbol files cannot represent older SET50 membership without
survivorship bias. Former constituents, delisted securities, and predecessor
issuers must be acquired or explicitly documented as unavailable.

## E. Planning coverage matrix

| Period | SET50 membership available? | Source | Access status | Price-data feasibility | Identity issues | Research readiness |
|---|---|---|---|---|---|---|
| 2005 H1-H2 | Listed by SET | SET archive | Member login required; not acquired | Unknown; broad constituent set not tested | High | Not ready |
| 2006-2009 H1/H2 | Listed by SET | SET archive | Member login required; not acquired | Unknown; delisted/renamed issuers likely | High | Not ready |
| 2010-2015 H1/H2 | Listed by SET | SET archive | Member login required; not acquired | Partial pilot evidence only | Medium-high | Not ready |
| 2016-2022 H1/H2 | Listed by SET | SET archive | Member login required; not acquired | Plausible, but symbol-by-symbol acquisition required | Medium | Not ready |
| 2023 H1-H2 | Verified in repository | SET PDFs | Audited and recorded | Existing approved prices for applicable symbols | Known TRUEE boundary | Approved current path only |
| 2024 H1-H2 | Verified in repository | SET PDFs | Audited and recorded | Existing approved prices for applicable symbols | GULF/INTUCH boundary developing | Approved current path only |
| 2025 H1-H2 | Verified in repository | SET PDFs | Audited and recorded | Existing approved prices for applicable symbols | GULF/INTUCH, TIDLOR | Approved current path only |
| 2026 H1-H2 | Verified in repository | SET PDFs, revised H2 | Audited/revision-aware | Existing approved prices for applicable symbols | BANPUU, MRDIYT, revised H2 | Approved current path only |

## F. Required controls before any acquisition

- Obtain the historical PDFs or licensed extract through legitimate SET access;
  retain source URL, effective date, revision state, retrieval timestamp, and
  checksum.
- Verify every PDF visually and by text extraction; distinguish SET50 rows from
  reserve, inclusion, and exclusion sections.
- Build a date-effective security master with issuer name, ISIN where available,
  ticker, listing interval, delisting/merger dates, and predecessor/successor
  links. Ambiguities require human approval.
- Acquire an independent SET trading calendar and reconcile exact observed
  sessions; do not infer missing sessions from another symbol.
- Acquire prices for every historical constituent needed by the selected target,
  preserving raw versus adjusted semantics and corporate-action events.
- Run the existing raw validation, remediation, readiness, and eligibility gates
  only after explicit approval. No reconstructed membership may enter the gate.

## G. Minimum viable extension

The 2016-2026 target is the minimum credible extension because it requires 22
canonical snapshots and is within the period where the repository's pilot has
already demonstrated some long-history price retrieval. It is still not ready:
official membership access and identity/security-master work are prerequisites.

The 2010-2026 target could provide stronger regime coverage, but it should be a
second phase after the 2016-2026 chain is complete and audited. The 2006-2026
target is not justified as an initial commitment because the marginal history
adds the largest identity and delisting burden while access and price coverage
remain unverified.

## H. Final recommendation

**PROCEED WITH CAUTION.** The SET archive makes historical membership
obtainable in principle, but authentication, licensing, constituent-file
retrieval, and security identity mapping remain unresolved. Seek legitimate
SET access or a licensed historical extract first, then acquire only the
membership snapshots for the 2016-2026 minimum target. Stop and obtain human
approval before any full historical price acquisition or manifest change.

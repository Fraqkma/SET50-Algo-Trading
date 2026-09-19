# Historical SET50 Security-Identity Audit

Status: read-only audit. No bulk price data was downloaded, no raw or approved
research data was changed, and no strategy, backtest, or eligibility behavior
was modified.

Audit date: 2026-09-12.

## Executive conclusion

Official SET notices resolve the legal listing boundaries for all seven cases,
but legal replacement is not the same as OHLCV continuity. The conservative
raw-data rule is to keep predecessor and successor securities separate unless a
separately approved mapping policy says otherwise.

The project may proceed with historical-price planning for unambiguous symbols,
and with date-effective ticker mapping for TMB -> TTB after explicit data-review
approval. TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI, TIDLOR, BANPU/BANPUU, and SCB/SCBB
must remain separate at the raw-series level. MRDIYT is usable only from its
first listing/trading date.

The official SET constituent archive establishes the existence and effective
period structure of historical snapshots, but archive access alone does not
resolve every security identity; the underlying historical files and corporate
action records are still required.

## Decision table

| Case | Historical identity | Transition | Continuity status | Price treatment | Membership treatment | Confidence | Human approval |
|---|---|---|---|---|---|---|---|
| TRUE / TRUEE / DTAC | TRUEE and DTAC predecessors; new TRUE Corporation security | Amalgamation registered 2023-03-01; index boundary 2023-03-02; TRUE traded 2023-03-03 | Verified non-continuity | Separate raw series; no synthetic splice | Old symbols before boundary, TRUE after | VERIFIED | Yes |
| GULF / INTUCH / GULFI | GULF Energy and INTUCH predecessors; temporary GULFI; GULF Development successor | Suspension 2025-03-21 to 2025-04-02; post-event GULF inclusion 2025-04-02 | Verified non-continuity | Separate series and explicit suspension boundary | Use symbol in each effective snapshot | VERIFIED | Yes |
| TIDLOR | Ngern Tid Lor predecessor; TIDLOR Holdings replacement under ticker TIDLOR | Replacement effective 2025-05-15 | Verified non-continuity | Keep NTL and TIDLOR separate | NTL before boundary, TIDLOR after | VERIFIED | Yes |
| BANPU / BANPUU | Banpu security before and during temporary BANPUU period; BANPU relisted after amalgamation | BANPUU effective during July 2026 suspension; BANPUU/BPP delisted 2026-07-31; BANPU traded 2026-08-04 | Verified non-continuity | Separate raw series; adjustment policy still required | Exact published symbol only | VERIFIED | Yes |
| MRDIYT | MR. D.I.Y. Holding (Thailand) | First listed/traded 2025-11-05 | Verified boundary | Use from listing date; no pre-listing data | Membership only after listing | VERIFIED | Boundary only |
| SCB / SCBB | SCB X holding company replaced The Siam Commercial Bank security SCBB | SCB listed and SCBB delisted 2022-04-27 | Requires mapping policy | Separate raw series; limit-price carryover is not OHLCV proof | SCBB before, SCB after unless official snapshot says otherwise | VERIFIED | Yes |
| TTB / TMB | Same bank lineage with company and ticker change | TMB -> TTB effective 2021-05-12 | Verified continuity with ticker change | Date-effective mapping; no adjustment inferred from rename alone | TMB before, TTB after | VERIFIED | Data-mapping approval |

## A. Verified continuity

Only TMB -> TTB is supported as a direct ticker/name continuity event by the
official notice. The notice records a company-name and security-symbol change,
not a new replacement security. Even here, the raw files should retain the
original ticker and use an explicit effective-date mapping. Corporate actions
must still be checked independently.

MRDIYT is also unambiguous as a single security from its first listing date,
but it has no valid pre-listing price interval.

## B. Verified non-continuity

SET explicitly describes TRUEE and DTAC as deleted and TRUE as the new company;
it describes the GULF/INTUCH event as an amalgamation with a suspension and new
GULF Development inclusion; it describes TIDLOR as listed in place of NTL; and
it describes BANPUU/BPP delisting followed by BANPU listing. These are legal and
index boundaries, not permission to concatenate OHLCV.

Official notices:

- [TRUE/DTAC amalgamation](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256345950&symbol=SET)
  and [new TRUE listing](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256332630&symbol=TRUE)
- [GULF/INTUCH suspension](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=94876500&symbol=INTUCH)
  and [post-event GULF inclusion](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=95454300&symbol=GULF)
- [TIDLOR replacement listing](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=96648700&symbol=SET)
- [BANPU/BPP suspension](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105437300&symbol=BANPUU)
  and [BANPUU/BPP delisting](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105587000&symbol=BPP)

## C. Requires explicit mapping policy

SCB is a particularly important case. SET states that SCB X was listed in
place of SCBB after restructuring and that SCBB was delisted on 2022-04-27. SET
also used the last SCBB price as the underlying price for trading limits, but
that operational rule does not establish identical issuer economics or permit
raw OHLCV joining. [SCB/SCBB SET notice](https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2022049146&symbol=SCB)

The required policy decision is whether research wants (a) legal-security
series only, or (b) an explicitly modeled economic-continuity series. The
second option would require corporate-action ratios, holdings, and valuation
rules not present in this audit.

## D. Insufficient evidence and archive limits

The public [SET constituent archive](https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100)
lists the historical periods and routes downloads through member authentication.
It is enough to establish period structure, but not enough by itself to prove
membership for a symbol before or after an identity transition. The underlying
official snapshot and effective-date evidence must be retained for every row.

No secondary source was used to override an official SET fact. No restricted
archive content was accessed.

## Source register

The machine-readable report records source name, URL, retrieval date, official
status, and the fact supported. All sources used for case conclusions are
official SET pages retrieved on 2026-09-12.

## Practical decisions

### Safe to proceed with

- Historical price planning for symbols with no identity transition, subject to
  the separate membership and price-source gates.
- MRDIYT from 2025-11-05 onward only.
- TMB/TTB only after recording the 2021-05-12 date-effective ticker mapping and
  obtaining data-review approval.

### Must remain separate

TRUEE, DTAC, and TRUE; pre-event GULF, GULFI/INTUCH, and post-event GULF; NTL
and TIDLOR; BANPU, BANPUU, and post-event BANPU; and SCBB and SCB.

### Bias risks

Joining these series can create survivorship bias, lookahead bias, false
continuity, duplicated returns, or membership leakage. In particular, using a
successor ticker in a predecessor's historical SET50 interval would let future
corporate information influence the past.

## Remaining blockers before full 2016-2026 acquisition

1. Obtain the official 2016-2022 constituent snapshots through legitimate SET
   access.
2. Decide and document legal-security versus economic-continuity treatment for
   SCB/SCBB and all amalgamation cases.
3. Build a date-effective security master with listing, delisting, issuer, and
   corporate-action identifiers.
4. Acquire raw prices for each historical identity from a licensed source and
   validate session coverage, OHLCV, actions, and boundaries independently.
5. Obtain human approval before any manifest or eligibility-gate exposure.

The project is **not yet ready for full historical price acquisition**, but it
can begin a membership-only and source-coverage review for unambiguous symbols.

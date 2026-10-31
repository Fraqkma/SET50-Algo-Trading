# Phase 4 Source and Coverage Audit

**Audit date:** 2026-10-31. Source archives and raw market files were read only.

## Why the Phase 3 PIT panel has 18 names

`reports/market_data_remediation.csv` lists 63 date-effective SET50 candidates. The raw Yahoo-mapped panel exists for 62; 42 are `NEEDS_REVIEW` because the remediation records unresolved OHLC range anomalies, known gaps/suspensions, or insufficient coverage with no authoritative daily comparison. INTUCH is `REJECTED` because Yahoo history/mapping is unavailable and its separate pre-merger identity cannot be silently mapped to GULF. The manifest has 18 rows with `APPROVED` status and 2 bounded post-transition approvals (GULF/TIDLOR); however, two approved names (THAI and MRDIYT) have no PIT membership overlap inside the Phase 3 sample ending 2026-09-04. The frozen Phase 3 event universe is therefore 18 names: the intersection of approved-source dates and actual sample-era PIT membership, including two bounded histories. These distinctions and per-symbol membership intervals are explicit in the matrix.

The detailed matrix enumerates every remediation row, published PIT membership interval, source-specific date span and file count, approval/identity reason, and present tick-archive evidence in [phase4_pit_universe_eligibility.json](../reports/phase4_pit_universe_eligibility.json). Pipeline filter counts are in that file. Membership evidence exists for intervals through 2026H2, but later dates within that interval are prospective and not observed at this audit date.

**Safe expansion:** no reviewed `NEEDS_REVIEW` name can be promoted from present evidence alone. The separate baseline panel safely includes all 20 manifest-approved records, while Phase 3's event engine has 18 names because THAI and MRDIYT each have only 48 gate-approved PIT observations through 2026-09-04, below its 55-row feature warmup. Both are now included in the non-promotional randomized feasibility baseline, with date-effective membership and approved source bounds. They were not added to prior signal results or called holdout data. The official TradeSim daily history is preserved as a distinct provenance candidate panel (48 stock files plus the index, 2023-09-21–2026-10-21), but adjustment/action semantics and exact issuer continuity have not been adjudicated across every symbol. Settrade production daily history is a current production feed (50 current symbols, normalized through Oct 28; separate Oct 29 daily recovery is 50/50 with adjustment status unknown); it does not prove historical PIT eligibility or adjustment semantics. Organizer tick data cover only 13 sessions, 2026-10-01–2026-10-21, and are execution diagnostics rather than a historical daily panel. These sources were not unioned.

## Source roles and limitations

| Source | Observed scope | Legitimate use now | Not established |
|---|---|---|---|
| Approved Yahoo PIT | 18 Phase 3 event names, 2023-01-03–2026-09-04 sample boundary; 16 approved-status names overlap sample PIT membership and 2 are bounded GULF/TIDLOR histories | Retrospective PIT signal diagnostics and single-source baselines | Full SET50 breadth; independent OOS; exchange-verified adjustments |
| TradeSim official history | Daily stock series and SET50 benchmark, 2023-09-21–2026-10-21 | Separate source-specific descriptive/regime research; benchmark cross-check | Exact future scoring feed/revision; universal stock adjustment/action identity |
| Settrade production | Normalized production daily feed has 50 current symbols through Oct 28; separate Oct 29 historical recovery persisted 50/50 daily rows with adjustment status unknown. Intraday/BBO coverage varies by date. | Current collection quality, live accumulation, source-specific diagnostics | Historical PIT membership; authenticated back-adjustment; historical BBO recovery |
| Organizer ticks | 13 sessions in Oct 2026 archive through Oct 21 | Local 0.2.7 mechanics and date-limited execution diagnostics | General fill rate, price-time queue model, adequate OOS strategy validation |

`reports/settrade_source_comparison.csv` contains only five matched comparison rows; all five classify as `MATERIAL_DIFFERENCE`. Recorded OHLC differences are zero on these rows, while volume differs materially. This small diagnostic is not a full-history equivalence test. No cross-source merged series was created. For each feed, availability is not the same as PIT admissibility, and daily OHLCV is not a TradeSim fill record.

## Panel decision

The Phase 3 18-name panel remains unchanged. An expanded candidate universe is recorded for future review, but an expanded return panel was not admitted because (1) 42 raw Yahoo cases fail source/quality adjudication, (2) TradeSim adjustment and corporate-action continuity are not certified per security, (3) Settrade represents a different production source/current universe, and (4) tick scope is too short for daily breadth research. Resolving this requires primary-source security-period OHLCV plus corporate-action/adjustment metadata and a dated issuer/security mapping for each PIT interval.

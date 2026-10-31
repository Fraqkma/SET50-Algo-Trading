# Phase 4 Research Triage and Plan

**As of 2026-10-31; holding-distribution addendum run 2026-10-31.** The new report is a retrospective descriptive reanalysis, not a new signal batch or strategy selection.

## Current gate state

- Phase 3 remains `NO_SIGNAL_PASSED_PROMOTION_GATE`: all four final hypotheses failed G1; portfolio construction remains gated off.
- The final report enabled S3-B using the official TradeSim-history SET50 series. That series is suitable as a research regime/price-index proxy with provenance caveats, not yet proven to be the organizer's exact future scoring feed.
- The research panel is an 18-name partial PIT panel. Existing results are seen data, not untouched OOS.
- Competition calendar currently contains 21 expected sessions, subject to SET amendments.
- No signal is promoted. 6–7% return remains aspirational and was not used to tune a baseline.
- Research direction is user-confirmed: Best Alpha primary, Best Risk Control secondary; additional data spend is 0 THB; 1–5 sessions are preferred starting horizons, while longer horizons remain in the distribution comparison. These choices do not waive qualification or evidence gates.
- Fixed H=1/2/3/4/5/7/10/15 net outcome, matched-control, uncertainty, and first-passage distributions are recorded in [RESEARCH_HOLDING_PERIOD_DISTRIBUTIONS.md](RESEARCH_HOLDING_PERIOD_DISTRIBUTIONS.md) and the two JSON artifacts. They reuse the already-seen Phase 3 panel and do not reopen rejected signals.
- Random 3/5/8-name and cash-only baselines are explicitly non-promotional; methodology and limitations are in [PHASE4_NONPROMOTIONAL_BASELINES.md](PHASE4_NONPROMOTIONAL_BASELINES.md).

## Reconciliation and PIT finding

See [phase3_run_reconciliation.json](../reports/phase3_run_reconciliation.json) for artifact IDs, hashes, run methods, and hypothesis-specific comparability. The initial screen, final addendum, and decision document are not three independent experiments: the decision document restates the earlier run and the later addendum. S3-B's initial `POSTPONED` is an absence of a test, not a zero result. S3-C's control changed from same-date cross-section to same-symbol/same-year non-gap observations; its matched count and estimate therefore cannot be interpreted as a performance reversal under identical controls. S3-D changed by one event and the source evidence does not identify a single-row cause. S3-A uses the same event counts but the interval differs; resampling implementation is not established as identical, so compare point estimate and gate outcome, not interval width.

There are 63 date-effective candidates, 62 raw Yahoo files, 18 `APPROVED` remediation rows, 2 bounded post-transition approvals (GULF/TIDLOR), 42 unresolved quality/coverage cases, and one rejected INTUCH identity. Phase 3's event engine admits 18 names after its 55-row feature warmup; THAI and MRDIYT are PIT-active and manifest-approved but have only 48 admissible rows by the Sep 4 cutoff. They are included only in a distinct 20-name randomized baseline. Exact per-symbol reasons are in [phase4_pit_universe_eligibility.json](../reports/phase4_pit_universe_eligibility.json). Existing evidence cannot clear the remaining 42 because primary-source OHLC/action reconciliation is absent. No current-membership backfill or provider union was made.

## Work sequence

1. Keep source provenance separate and resolve the identity, action, adjustment, and quality audit before a new hypothesis study.
2. Confirm the exact scoring benchmark/revision and competition boundary valuation/FIFO treatment with the organizer.
3. Preserve upcoming Settrade collection data from Nov/Dec as prospective, untouched evidence; use the read-only Nov 2 checklist and do not label it OOS until its data and process provenance pass.
4. Only after coverage and power gates pass, freeze at most 2–3 economically distinct, cost-aware hypotheses and an untouched evaluation interval. No broad parameter grid.
5. Promote nothing unless a pre-registered G1 test passes and later stages support the claim with date/symbol dependence, overlap purging, realistic costs, and source-compatible execution evidence.

## Genuine unresolved questions

Only organizer decisions already documented in `docs/QUESTIONS_FOR_ORGANIZER.md` remain: exact scoring benchmark/revision, start/end NAV cutoff and boundary-day fill treatment, and pre-period / post-period FIFO lot eligibility. There is no unresolved user strategy decision because no candidate is ready for selection.

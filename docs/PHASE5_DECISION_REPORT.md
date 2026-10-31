# Phase 5 Decision Report

## Decision

Phase 3/4 conclusions remain unchanged: `NO_SIGNAL_PASSED_PROMOTION_GATE`; `CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW = []`. Phase 5 added no PIT-approved observations and found no genuinely untouched historical outcome block. `NEW_ALPHA_SCREEN_DEFERRED`. No strategy selected.

## Evidence

- PIT: 18 Phase 3 event symbols and 20 approved manifest rows; 42 candidate identities remain individually `NEEDS_REVIEW`, one INTUCH identity is rejected. Net Phase 5 approvals: zero symbols and zero symbol-date observations.
- Holdout: all historical outcomes through the observed Oct 30 evidence window are previously seen diagnostics; Oct 31 onward is prospective. Independent OOS does not exist. Effective power/MDE for a new screen is therefore not estimable.
- Reproducibility: incompatible S3-A/B/C/D definitions remain separately labeled. Existing Phase 3/4 rejection status is preserved.
- TradeSim 0.2.7: exact Python 3.13.0 runtime is validated; existing fixtures cover IOC/volume/FIFO/ladder mechanics. A one-order official-tick probe was rejected by the local simulator's cumulative-volume constraint and created zero fills. Neither this probe nor the fixtures estimate fill rates or alpha.
- KGI scoring PDF: all 18 pages were extracted and read directly. SHA-256: `e2a7d549dfffd9691e077a09ba3e51d94a3da11da3da9433ba717039721d79f1`. Verified Common Criteria are Portfolio MDD `< 1.5×` benchmark MDD, at least 5 FIFO-completed round trips, average daily close exposure `≥ 50%`, and expected payoff `> 0`. Best Alpha adds nonnegative portfolio return and excess return; ranks by excess return, Calmar, portfolio return. Best Risk Control ranks by Calmar, excess return, then lowest MDD.
- Competition feasibility: Phase 4 non-promotional 21-session rolling baseline remains the only feasibility baseline. 5 FIFO round trips and 50% exposure cannot be confirmed from daily bars or assumed fills. Common Criteria stay `CONDITIONAL_OR_UNKNOWN`. Best Alpha remains primary, Best Risk Control secondary.
- Collector: Oct 30 cycles persisted data but failed after repeated 60-second health subprocess timeouts. The bounded default is increased to 180 seconds, with failure propagation preserved. Logged-out execution remains configuration-only; Nov 2 is not yet observable.

## Human decisions and organizer questions

`HUMAN_DECISIONS_REQUIRED: NONE`. The only outstanding policy questions remain in [QUESTIONS_FOR_ORGANIZER.md](QUESTIONS_FOR_ORGANIZER.md): official benchmark/revision, boundary NAV/fill cutoff, and cross-boundary FIFO lot eligibility.

## Next actions

1. Preserve new prospective PIT evidence and resolve each source/identity case only with dated primary provenance.
2. Run the read-only Nov 2 collector check after its scheduled time and validate persisted market-time coverage.
3. Keep TradeSim mechanics and signal research separate until a signal has newly qualified PIT coverage and an untouched chronological evaluation block.

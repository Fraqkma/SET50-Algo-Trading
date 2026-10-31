# Signal-first discovery

Classification: `SIGNAL_DIAGNOSTIC_ONLY`; no portfolio candidate passed promotion.

## Tested hypothesis

One pre-registered family was studied: H6, a 5-session pullback between -8% and -3% while close is above SMA50, SMA50 is at least SMA100, 10-session directional efficiency is at most 0.35, and SET50 is above SMA50 with 20-session return at least -1%. Decisions use close data and reference entry at the next observed open. The partial approved dataset contains 20 symbols through 2026-09-04; the H6 event set has 137 events across 17 names. This is not PIT-complete and is exposed to survivorship and repeated-history bias.

## Forward returns and controls

The 137 events produced means of +0.31% (next open to same-session close), +0.42% (+2 sessions), +0.52% (+3), +0.33% (+5), and +1.06% (+10). Approximate 95% mean intervals cross zero at every horizon. The event hit rate ranges from 43.1% to 53.3%. The largest symbol contributes 13.1% of events; the busiest year, 2026, contributes 45.3%.

Deterministic seed 2701 controls include unconditional eligible symbol-dates, same-symbol random eligible dates, same-regime eligible dates, and daily equal-weight cross-sectional returns. The event mean is positive while matched control means are mostly negative, but control intervals are approximate and do not address serial dependence, overlapping events, universe selection, or parameter multiplicity. These controls do not establish an edge; the event confidence intervals remain consistent with zero.

Horizon definitions: next-open entry, then same-session close or close after the labeled number of observed sessions. All rates use approved rows, never fill missing bars, and require symbol eligibility on the signal date. The current report preserves event dates and control counts.

## Promotion gate and multiplicity

Only H6 was evaluated in this control run from the six small hypothesis families listed in the pre-existing hypothesis registry; five were not run here. Existing Trend20, Breakout20, RelativeStrength, and MeanRev5 strategy attempts remain preserved as earlier Stage 1 rejections. The H6 event sample meets the minimum event/symbol count but fails promotion because uncertainty crosses zero at every horizon, event periods overlap, 2026 concentration is high, and the separate H6 portfolio had net return -3.49%, average exposure 21.94%, max drawdown 27.42%, and only 23 completed round-trips. `NO_SIGNAL_PASSED_PROMOTION_GATE`.

No parameter sweep, automatic strategy promotion, walk-forward rerun, or official TradeSim candidate run was performed. A later signal must be independently registered, use complete PIT eligibility, and pass an uncertainty/concentration/stability gate before any portfolio prototype.

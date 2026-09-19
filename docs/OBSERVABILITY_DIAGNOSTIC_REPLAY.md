# Observability diagnostic replay

This replay uses only approved 2023–2026 data and reproduces the existing
qualification rule (positive momentum_20 and Close above SMA20) and Design C
ranking. Future returns are labels only. No official backtest reports or
strategy logic were changed.

The replay persisted 13,500 qualification rows and 1,624 candidate rows. There
were 657 qualification ENTER events; all were one-row streak starts in the
persisted state, but a true persistence-2 order simulation is not performed.

For selected versus qualified-not-selected candidates, selected five-day mean
forward return was approximately 0.0002%, while the qualified-not-selected
group was approximately 0.338%. At 10 days the corresponding means were
approximately -0.230% and 0.531%. This descriptive result does not establish
that Design C is inferior because the groups are small, overlapping, and the
selection process is not randomized.

Exact observed-row holding durations and a persistence-2 turnover comparison
require an engine replay that emits observed-row indices and signal-to-order
mapping. The current artifacts therefore mark those conclusions as
INSUFFICIENT_EVIDENCE rather than inferring them from calendar dates.

# Historical daily OHLCV acquisition (staging only)

This phase prepares a reproducible, opt-in acquisition path for the planned
2010-01-01 through 2026-09-04 window. The runner uses the planning symbol matrix
and writes only to `data/pilot/historical_daily/`; it never changes `data/raw`,
the approved manifest, eligibility rules, or strategy code. Without `--download`
it produces a plan and no network request. All downloaded files remain
`UNAPPROVED` until separate membership, identity, licensing, and quality gates
pass. Existing four-symbol pilot artifacts are audited but not repaired.

The current historical membership blocker remains: prices alone cannot establish
a survivorship-safe SET50 universe. No backtest or optimization is run here.

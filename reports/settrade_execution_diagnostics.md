# Settrade execution diagnostics

Descriptive analysis of genuine persisted BBO snapshots. Hypothetical sweeps use only displayed depth and must not be read as actual fills.

- Dataset date range: 2026-09-22 to 2026-10-01
- BBO readiness: READY_FOR_EXPLORATORY_RESEARCH
- Raw callback events: 18321; normalized event candidates: 18,321; valid two-sided, positive, uncrossed snapshots: 12,110; excluded from spread metrics: 6,211
- Symbols: 50
- Quoted spread median: 0.2500 THB / 1.000 ticks / 62.31 bps
- Spread <=1 tick: 56.47%; >1 tick: 43.53%
- Best-level median depth: bid 7800; ask 8400 shares

Cumulative visible depth medians:
- Top 3: bid 28700; ask 27900 shares
- Top 5: bid 48500; ask 41800 shares
- Top 10: bid 52800; ask 45900 shares

Hypothetical visible-book sweeps:
- Buy 100,000 THB: 11,125/12,110 snapshots visibly fillable; insufficient depth 985; median visible quantity 2220 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.0 ticks / 0.0 bps; displayed-depth impact for available shares 0.0 ticks / 0.0 bps.
- Sell 100,000 THB: 11,355/12,110 snapshots visibly fillable; insufficient depth 755; median visible quantity 2272 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.0 ticks / 0.0 bps; displayed-depth impact for available shares 0.0 ticks / 0.0 bps.
- Buy 500,000 THB: 9,391/12,110 snapshots visibly fillable; insufficient depth 2,719; median visible quantity 10638 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.375 ticks / 19.542293134397013 bps; displayed-depth impact for available shares 0.5799488781596137 ticks / 24.744514685905465 bps.
- Sell 500,000 THB: 9,417/12,110 snapshots visibly fillable; insufficient depth 2,693; median visible quantity 10893 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.4851226726987993 ticks / 21.95261467321085 bps; displayed-depth impact for available shares 0.6075070629550543 ticks / 27.932960893854748 bps.
- Buy 1,000,000 THB: 7,535/12,110 snapshots visibly fillable; insufficient depth 4,575; median visible quantity 19801 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.5168172690763052 ticks / 25.041602662570405 bps; displayed-depth impact for available shares 0.9615975422427036 ticks / 46.65585146928931 bps.
- Sell 1,000,000 THB: 7,410/12,110 snapshots visibly fillable; insufficient depth 4,700; median visible quantity 20000 shares; median per-snapshot visible/requested fraction 100.0%; full-request slippage on fillable snapshots 0.5291692919456042 ticks / 24.177398283874865 bps; displayed-depth impact for available shares 0.9798994974874372 ticks / 44.34492237438538 bps.

Time-of-day, per-day, per-symbol, and symbol-session medians and sweep coverage are in the JSON `by_group` sections. These are descriptive profiles, not rankings or recommendations.
Spread tick conversion uses the explicit repository research tick-size helper. Sweep slippage is measured from the opposite best quote, excludes the cost to cross from a separate reference price, and represents visible-depth impact only.

Limitations: snapshots cannot establish queue priority, hidden liquidity, latency, actual IOC fill probability, or executed trade ticks. The one-adverse-tick MODEL_V1 assumption is unchanged; this evidence is insufficient to establish realized fill cost.

MODEL_V1_UNCHANGED_INSUFFICIENT_EVIDENCE

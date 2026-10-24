# Current SET50 market research terminal

The Streamlit app (`python -m streamlit run ui/app.py`) opens on **Market Overview**. It is a read-only visual research terminal for the 50 names in `reports/current_set50_universe.csv` (current H2 2026 display list). It is not a historical constituent simulation. Old prices for current names must not be interpreted as evidence that the name was a SET50 member at that time, and the exploratory view is not survivorship-safe backtest input.

## Daily source and derived view

`src/data/exploratory_market.py` reads, without changing source files:

- manifest-bounded approved Yahoo files in `data/raw/market_data/`;
- longer Yahoo staging histories in `data/pilot/historical_daily/`;
- later Yahoo staging bars in `data/pilot/historical_set50_availability/` and `data/pilot/historical_depth_experiment/`;
- the four older Yahoo staging files in `data/pilot/historical_acquisition/`.

The date-aware manifest source is preferred only inside its recorded approval dates; outside those dates it is exploratory. Other raw acquisition rows come next, followed by full-history daily staging, the later availability staging, the depth experiment, and legacy staging. Overlap checks found identical OHLCV values across these Yahoo vintages for the observed common symbol-dates; the derived view still checks all overlaps and excludes any disagreement. The merger key is the exact symbol plus date. Identical duplicate observations collapse to one row. Source path and approval-scope provenance are retained. No rows, prices, returns, or volume are imputed. Invalid OHLC rows keep their observed close for close-only views but are flagged; invalid candles are omitted from the candlestick trace and reported on the detail page. Long date gaps are only a >4-calendar-day heuristic, not a Thai exchange-calendar estimate of missing sessions. The view is computed in memory and cached by source file size/mtime; it is reproducible and is not a second persistent market-data authority.

The explicit ticker/security caveats in `reports/historical_security_identity_audit.json` are enforced as display boundaries: TRUE from 2023-03-03, GULF from 2025-04-03, SCB from 2022-04-27, TIDLOR from 2025-05-16, MRDIYT from 2025-11-05 and post-amalgamation BANPU from 2026-08-04. TRUEE/DTAC, GULFI/INTUCH, SCBB, NTL and BANPUU are not spliced into those symbols. TMB/TTB is the audit-approved ticker continuity; raw prices are not adjusted. Other symbols also retain exact source identity. Review the identity audit and the detail-page caveat before drawing conclusions.

Refresh the machine-readable inventory and conflict report after source changes with:

```powershell
python scripts/build_exploratory_market_catalog.py
```

The script writes only exploratory reports under `reports/`: `exploratory_market_source_catalog.csv`, `exploratory_market_source_conflicts.csv`, and `exploratory_market_view_summary.json`. It does not modify approved files or source data. The catalog includes intraday Settrade 1m/5m/15m artifacts as inventory-only rows. Settrade candles/BBO remain separate pilot data; BBO is event-driven and no synthetic events or daily candles are created.

## Visual calculations

- **Raw close** shows the source close in THB.
- **Normalized performance** sets each symbol to 100 at its first actual close inside the selected range. Unequal starts remain visible as blank space.
- **Cumulative return** is close-to-close percentage return compounded from observed returns, with the first unavailable return left missing.
- **Relative performance** is each security’s compounded return less the compounded equal-weight basket of the current 50-name display universe. Each basket date uses only non-missing returns that exist; it is not the official SET Index.
- Presets use the latest available source date and select calendar ranges (1M, 3M, 6M, YTD, 1Y, 2Y, 3Y, Max, or custom). No prices are resampled for the multi-chart views.
- Correlations are Pearson correlations of daily close-to-close percentage returns, never raw price levels. Dates are joined by exact observed date; returns are not forward-filled. The matrix reports pairwise N and suppresses coefficients below 60% of the selected 20/60/120/252-observation window (at least 10 observations). The scatter reports its own N. Rolling correlation requires a full 20/60 pairwise window.
- SMA breadth denominators include only securities with 20/50 actual closes; return breadth denominators include only observations with the required lookback. Advance/decline breadth uses the latest date with at least 80% current-universe return coverage.
- Daily volume is the Yahoo-reported field and is shown with its source label only. Settrade volume semantics are not mixed into the daily matrix.

Market Overview and Multi-Stock Trends show four columns with seven rows (the last row has one symbol) and lightweight WebGL lines. This gives each panel more width at typical 1080p desktop sizes; the two groups are exactly current-universe positions 1–25 and 26–50. Candlesticks are lazy and available only on Stock Detail. Correlation clustering is deterministic hierarchical average-linkage ordering on distance `(1 - r) / 2`; it is not a sector classification.

All pages are descriptive and read-only. No UI action initializes the broker, submits an order, changes MODEL_V1, or alters formal strategy/backtest behavior. The research display must not be used to claim historical SET50 membership or survivorship-safe performance.

## Official TradeSim and Settrade source boundary

Organizer-provided TradeSim ticks/history are stored separately under `data/official/tradesim/` and are the source for official simulator validation and competition replay. Settrade production remains the source for live/current monitoring. They are not merged: comparisons in `reports/tradesim_vs_settrade_data_comparison.json` show differences in candles, volume, and session coverage, and the history documentation describes corporate-action-adjusted prices while Settrade adjustment status is unknown. No source fills another source's missing rows. Official raw ticks retain repeated rows and source order. See [the official TradeSim integration guide](OFFICIAL_TRADESIM_INTEGRATION.md).

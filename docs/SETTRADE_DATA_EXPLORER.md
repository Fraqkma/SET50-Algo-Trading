# Settrade Data Explorer

The Streamlit explorer is read-only and operates on normalized pilot artifacts.
It never creates candles from BBO or price-info events, fills missing intervals,
rewrites source timestamps, or changes production strategy data.

## Timeline modes

- **Compact trading timeline** is the default intraday view. It assigns positions
  only to observed rows within each Bangkok trading day, compressing overnight,
  weekend, and midday gaps for visual inspection. The original UTC timestamp,
  Asia/Bangkok timestamp, OHLC values, and volume remain unchanged and are shown
  in hover text and the source-row table.
- **Real clock time** uses the actual Asia/Bangkok timestamp spacing. This is the
  preferred mode for diagnosing collector timing and source gaps.
- **Multiple trading days** adds clear day separators in compact mode. The
  default scope remains one observed trading day for intraday inspection.

## Coverage diagnostics

The candle panel reports duplicates, invalid OHLC relationships, missing values,
observed trading days, gaps longer than the requested timeframe, an estimated
coverage percentage, and the largest observed gap. Coverage is diagnostic only;
no missing candle rows are synthesized. Settrade source volume is displayed as
persisted and is not inferred or used to manufacture candles.

The current pilot may be sparse when the collector starts after the session opens
or when the Settrade candle endpoint returns incomplete data. That sparsity is
shown explicitly rather than hidden by chart interpolation.

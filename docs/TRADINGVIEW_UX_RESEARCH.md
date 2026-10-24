# TradingView public UI/UX observations

Research date: 2026-10-21. The public chart page was opened at [TradingView Chart](https://www.tradingview.com/chart/) using the configured read-only Playwright browser connector. REA MCP was available, but its `list_browser_targets` request to `http://127.0.0.1:9222` failed because no CDP target was reachable. The page was therefore inspected through the available browser connector instead. No authentication, paywall bypass, proprietary source, or asset extraction was used. The captured public page exposed an anonymous chart workspace with AAPL as its initial symbol.

## Observed patterns and adaptation

| Public pattern | Why it helps | Streamlit fit / effort | Project decision |
|---|---|---|---|
| Symbol and timeframe controls sit in a compact chart toolbar | Keeps chart context visible and reduces navigation | Strong fit; low effort with columns and controls | Keep symbol/timeframe/date/source controls together above the candle view |
| Candlestick chart is the central work surface | Makes price structure the primary focus | Strong fit with existing Plotly chart; medium effort for overlays and gaps | Use Plotly dark template, OHLC hover, volume, and true timestamp gaps |
| Chart type and indicator actions are grouped near timeframe controls | Makes chart changes discoverable | Moderate fit; low effort for SMA/VWAP toggles | Adapt only simple transparent research overlays; VWAP only when valid intraday volume exists |
| Watchlist and details occupy a persistent side panel | Makes symbol switching and cross-sectional scanning quick | Partial fit; Streamlit sidebar/columns are rerun-based and less flexible | Provide a compact sortable table and symbol selector; do not imply live values when stale |
| Right-side icon rail organizes alerts, object/data panels, screeners, and calendars | Keeps secondary tools available without crowding the chart | Moderate fit; low effort as a labeled research navigation menu | Keep existing pages in the Workspace menu and group operational/data-quality tools clearly |
| Alerts, object tree/data window, screeners, calendars, and community are separate panels | Separates chart work from supporting context | Good fit as non-empty Streamlit pages; medium effort | Preserve working breadth, correlation, liquidity/BBO, source, quality, and collector views; avoid placeholders |
| Dark canvas uses muted gray surfaces with restrained accent colors | Supports long sessions and differentiates state without visual noise | Strong fit; low effort via Streamlit theme plus shared CSS | Adopt dark navy/charcoal surfaces, teal selection, muted text, and conventional warning/error colors |
| Dense charts keep OHLC values and symbol context close to the plot | Reduces context switching when inspecting candles | Strong fit with hover templates and freshness captions | Show source, environment, market timestamp, collection timestamp, and quality state beside charts |
| Bottom status/panel area separates secondary workspaces from the chart | Allows chart focus while retaining access to other tasks | Limited in Streamlit's page layout | Use tabs and expandable sections instead of simulating a draggable/dockable terminal |
| Crosshair and hover expose exact time/price values | Supports point inspection | Plotly supports unified hover, but cross-panel synchronized cursor behavior is limited | Use unified hover and synchronized subplot axes where available; no custom crosshair clone |

## What not to copy

- TradingView name, logos, icons, visual assets, proprietary code, exact toolbar artwork, or branded wording.
- Paid, logged-in, broker-connected, or account-specific behavior.
- Trading buttons, broker order panels, alerts that send external messages, or any order workflow. This application remains research-only.
- A fake impression of live data, smooth charts from forward-filled bars, or synthetic quotes.

## Streamlit limits

Streamlit reruns the script when controls change. It does not provide TradingView's continuously interactive canvas, draggable/resizable dock panels, persistent crosshair, or full mobile chart gestures without custom components. The project uses native Streamlit controls and Plotly interactions, keeps source rows unmodified, and treats auto-refresh as a view refresh rather than a collector/API action.

## Implementation priority

1. Dark theme, readable tables, clear freshness and connectivity state.
2. A compact symbol/timeframe/date/source toolbar and source-faithful candles with volume and missing-data gaps.
3. Sortable SET50 watchlist, metric heatmap, and quick symbol selection.
4. Gap/session timeline and provenance inspector backed by persisted operational reports.
5. Add simple indicators only where source columns support them; keep unsupported indicators unavailable rather than substituting fabricated values.

Screenshot reference: the public chart viewport was captured by the browser connector at `.playwright-mcp/page-2026-10-21T13-57-18-095Z.png`. It is local inspection evidence only and is not shipped as a UI asset.

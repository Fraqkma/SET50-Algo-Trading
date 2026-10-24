"""Current-SET50 historical visualization pages (read-only and exploratory)."""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.data.exploratory_market import (  # noqa: E402
    IDENTITY_NOTES,
    build_exploratory_view,
    breadth_summary,
    daily_returns,
    inventory_sources,
    normalize_closes,
    return_correlation,
    rolling_pair_correlation,
)

RANGES = ("1M", "3M", "6M", "YTD", "1Y", "2Y", "3Y", "Max available", "Custom")
MODES = ("Raw close", "Normalized performance", "Cumulative return", "Relative performance")


def display_universe(root: str | Path = ROOT) -> list[str]:
    """Read the official current-set display list; never infer it from data."""
    path = Path(root) / "reports/current_set50_universe.csv"
    if not path.exists():
        return []
    frame = pd.read_csv(path, dtype=str)
    return frame["symbol"].str.upper().tolist() if "symbol" in frame else []


def split_universe(symbols: list[str], group: str) -> list[str]:
    """Return deterministic 25 + 25 navigation groups."""
    index = 0 if group == "Stocks 1–25" else 25
    return symbols[index:index + 25]


def date_window(bars: pd.DataFrame, preset: str, custom: tuple[date, date] | None = None) -> tuple[pd.Timestamp, pd.Timestamp]:
    """Apply a calendar preset to the actual available latest observation."""
    if bars.empty:
        today = pd.Timestamp.today().normalize()
        return today, today
    end = pd.Timestamp(bars["Date"].max()).normalize()
    if preset == "Custom" and custom:
        start, selected_end = map(pd.Timestamp, custom)
        return max(start.normalize(), pd.Timestamp(bars["Date"].min())), min(selected_end.normalize(), end)
    offsets = {"1M": pd.DateOffset(months=1), "3M": pd.DateOffset(months=3),
               "6M": pd.DateOffset(months=6), "1Y": pd.DateOffset(years=1),
               "2Y": pd.DateOffset(years=2), "3Y": pd.DateOffset(years=3)}
    if preset == "YTD":
        start = pd.Timestamp(year=end.year, month=1, day=1)
    elif preset == "Max available":
        start = pd.Timestamp(bars["Date"].min()).normalize()
    else:
        start = end - offsets.get(preset, pd.DateOffset(months=6))
    return max(start, pd.Timestamp(bars["Date"].min()).normalize()), end


def series_for_mode(bars: pd.DataFrame, symbols: list[str], mode: str,
                    basket_symbols: list[str] | None = None) -> pd.DataFrame:
    """Create visual values from true closes; no price/return forward filling."""
    calculation_symbols = list(dict.fromkeys((basket_symbols or symbols) + symbols)) if mode == "Relative performance" else symbols
    subset = bars[bars["symbol"].isin(calculation_symbols)]
    closes = subset.pivot(index="Date", columns="symbol", values="Close").sort_index()
    closes = closes.reindex(columns=calculation_symbols)
    if mode == "Raw close":
        return closes.reindex(columns=symbols)
    normalized = normalize_closes(closes)
    if mode == "Normalized performance":
        return normalized.reindex(columns=symbols)
    returns = closes.pct_change(fill_method=None)
    if mode == "Cumulative return":
        return (1 + returns).cumprod().sub(1).mul(100).reindex(columns=symbols)
    # Basket return for each date is the arithmetic mean of valid returns from
    # the current display universe; missing securities are not imputed.
    basket_return = returns.mean(axis=1, skipna=True)
    basket = (1 + basket_return).cumprod().mul(100)
    asset = (1 + returns).cumprod().mul(100)
    return asset.sub(basket, axis=0).reindex(columns=symbols)


def source_signature(root: Path) -> tuple[tuple[str, int, int], ...]:
    """Cheap cache key that changes when any read source is replaced or edited."""
    paths = list((root / "data/raw/market_data").glob("*.csv"))
    paths += list((root / "data/pilot/historical_daily").glob("*.csv"))
    paths += list((root / "data/pilot/historical_set50_availability").glob("*.csv"))
    paths += list((root / "data/pilot/historical_depth_experiment").glob("*.csv"))
    paths += list((root / "data/pilot/historical_acquisition").glob("*.csv"))
    paths += [root / "data/processed/approved_market_data_manifest.csv", root / "reports/current_set50_universe.csv"]
    return tuple(sorted((str(p), p.stat().st_size, p.stat().st_mtime_ns) for p in paths if p.exists()))


def _open_stock_detail(symbol: str) -> None:
    """Route from the overview quick picker to one security's read-only detail."""
    st.session_state["detail_symbol"] = symbol
    st.session_state["workspace_navigation"] = "Stock Detail"


@st.cache_data(max_entries=2, show_spinner="Loading source-faithful historical bars…")
def _cached_view(root: str, signature: tuple[tuple[str, int, int], ...]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    del signature  # The signature participates in Streamlit's cache key.
    path = Path(root)
    bars, conflicts = build_exploratory_view(path)
    return bars, conflicts, inventory_sources(path)


def load_view(root: Path = ROOT) -> tuple[list[str], pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    symbols = display_universe(root)
    bars, conflicts, inventory = _cached_view(str(root), source_signature(root))
    return symbols, bars[bars["symbol"].isin(symbols)].copy(), conflicts, inventory


def _range_controls(bars: pd.DataFrame, key: str, default: str = "6M") -> tuple[pd.Timestamp, pd.Timestamp, str]:
    preset = st.selectbox("Time range", RANGES, index=RANGES.index(default), key=f"{key}_range")
    custom = None
    if preset == "Custom" and not bars.empty:
        data_min, data_max = bars["Date"].min().date(), bars["Date"].max().date()
        controls = st.columns(2)
        start_default = (pd.Timestamp(data_max) - pd.Timedelta(days=180)).date()
        start = controls[0].date_input("Start date", value=max(data_min, start_default), min_value=data_min, max_value=data_max, key=f"{key}_start")
        end = controls[1].date_input("End date", value=data_max, min_value=data_min, max_value=data_max, key=f"{key}_end")
        custom = (start, end)
    start, end = date_window(bars, preset, custom)
    return start, end, preset


def _slice(bars: pd.DataFrame, symbols: list[str], start: pd.Timestamp, end: pd.Timestamp) -> pd.DataFrame:
    return bars[bars["symbol"].isin(symbols) & bars["Date"].between(start, end)].copy()


def _metrics_row(bars: pd.DataFrame, symbols: list[str], conflicts: pd.DataFrame) -> None:
    current = bars[bars["symbol"].isin(symbols)]
    available = current.groupby("symbol").size()
    dates = current.groupby("symbol")["Date"].max()
    latest = current["Date"].max() if not current.empty else None
    cards = st.columns(6)
    cards[0].metric("Display universe", f"{len(available)} / {len(symbols)}")
    cards[1].metric("Latest source date", latest.date().isoformat() if latest is not None else "No data")
    today = pd.Timestamp.now(tz="Asia/Bangkok").normalize().tz_localize(None)
    stale = int((today - dates).dt.days.gt(7).sum()) if latest is not None else len(symbols)
    cards[2].metric("Stale > 7 days", stale)
    cards[3].metric("Insufficient history", int((available.reindex(symbols, fill_value=0) < 50).sum()))
    cards[4].metric("Conflicting dates excluded", len(conflicts))
    invalid_bars = int(current["ohlc_status"].eq("INVALID").sum()) if "ohlc_status" in current else 0
    cards[5].metric("Invalid source OHLC rows", invalid_bars)
    if invalid_bars:
        st.warning(f"{invalid_bars} source rows violate OHLC range checks. Close-based views retain these real source closes; invalid candles are omitted from the candlestick trace and remain listed in detail provenance/quality.")
    if latest is not None and (today - pd.Timestamp(latest)).days > 7:
        st.warning(f"Stored daily history is stale relative to today: newest source date is {pd.Timestamp(latest).date()}. No live prices or missing bars are synthesized.")
    missing = sorted(set(symbols) - set(available.index))
    if missing:
        st.warning(f"No usable daily close: {', '.join(missing)}")


def _small_multiples(bars: pd.DataFrame, symbols: list[str], mode: str, start: pd.Timestamp, end: pd.Timestamp) -> None:
    window = _slice(bars, symbols, start, end)
    if window.empty:
        st.warning("No daily observations in this date range.")
        return
    calculation_bars = _slice(bars, display_universe(), start, end) if mode == "Relative performance" else window
    values = series_for_mode(calculation_bars, symbols, mode, basket_symbols=display_universe())
    cols = 4
    rows = int(np.ceil(len(symbols) / cols))
    fig = make_subplots(rows=rows, cols=cols, shared_xaxes=True, shared_yaxes=False,
                        subplot_titles=[s for s in symbols], vertical_spacing=0.035, horizontal_spacing=0.04)
    for index, symbol in enumerate(symbols):
        if symbol not in values or values[symbol].notna().sum() == 0:
            continue
        row, col = divmod(index, cols)
        series = values[symbol].dropna()
        fig.add_trace(go.Scattergl(x=series.index, y=series.to_numpy(), mode="lines",
                                   line={"width": 1.25, "color": "#2584a8"},
                                   customdata=window[window["symbol"].eq(symbol)].set_index("Date").reindex(series.index)["Close"].to_numpy(),
                                   hovertemplate="%{x|%Y-%m-%d}<br>View: %{y:.3f}<br>Close: %{customdata:.3f}<extra>" + symbol + "</extra>",
                                   showlegend=False, name=symbol), row=row + 1, col=col + 1)
    descriptions = {
        "Raw close": "Raw observed closing prices (THB).",
        "Normalized performance": "Each line starts at 100 at its first actual observation in this range.",
        "Cumulative return": "Compounded close-to-close return (%); no initial or missing return is imputed.",
        "Relative performance": "Percentage-point return versus the equal-weight current 50-name display basket.",
    }
    st.caption(descriptions[mode])
    fig.update_layout(height=rows * 190, margin={"l": 35, "r": 15, "t": 35, "b": 25},
                      showlegend=False, hovermode="x unified",
                      paper_bgcolor="#10151d", plot_bgcolor="#141b25")
    fig.update_xaxes(showgrid=False, tickformat="%b %y", showticklabels=True, nticks=3)
    fig.update_yaxes(title_text="", tickfont={"size": 8}, nticks=4,
                     gridcolor="#2b3544", zeroline=False)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False, "scrollZoom": False})
    missing = [s for s in symbols if s not in values or values[s].notna().sum() == 0]
    if missing:
        st.caption(f"No observations in this window: {', '.join(missing)}")
    st.caption(f"{cols} columns × {rows} rows; {len(symbols)} symbols in this group. Values use each security’s actual observed dates; unavailable dates stay missing.")


def _header_warning() -> None:
    st.warning("Current SET50 display universe only — historical charts show each security’s genuine available history, not historical SET50 membership. Exploratory continuity is not survivorship-safe backtest evidence.", icon=":material/warning:")


def render_overview(root: Path = ROOT) -> None:
    st.title("Market overview", icon=":material/monitoring:")
    st.caption("A read-only visual scan of current SET50 names using historical daily Yahoo OHLCV already stored in this repository.")
    symbols, bars, conflicts, _ = load_view(root)
    _header_warning()
    _metrics_row(bars, symbols, conflicts)
    breadth, metrics = breadth_summary(bars, symbols)
    returns = daily_returns(bars[bars["symbol"].isin(symbols)])
    median_20d = metrics["return_20d"].median() if not metrics.empty else float("nan")
    median_vol = metrics["volatility_20d"].median() if not metrics.empty else float("nan")
    cards = st.columns(4)
    cards[0].metric("Above SMA20", f"{breadth['above_sma20'][0]} / {breadth['above_sma20'][1]}")
    cards[1].metric("Above SMA50", f"{breadth['above_sma50'][0]} / {breadth['above_sma50'][1]}")
    cards[2].metric("Median 20D return", f"{median_20d:.1%}" if pd.notna(median_20d) else "—")
    cards[3].metric("Median 20D volatility, annualized", f"{median_vol:.1%}" if pd.notna(median_vol) else "—")
    if not returns.empty:
        common = returns.pivot(index="Date", columns="symbol", values="return").reindex(columns=symbols)
        eligible = common.notna().sum(axis=1).ge(max(1, int(np.ceil(len(symbols) * 0.8))))
        if eligible.any():
            latest_date = eligible[eligible].index[-1]
            row = common.loc[latest_date].dropna()
            advances, declines = int(row.gt(0).sum()), int(row.lt(0).sum())
            st.caption(f"Latest common breadth observation (≥80% coverage): {latest_date.date()} — {advances} advancing / {declines} declining / {len(row)} observed.")

    st.subheader("SET50 watchlist")
    if not metrics.empty:
        watchlist = metrics.reset_index().copy()
        latest_daily_date = pd.to_datetime(watchlist["Date"], errors="coerce").max()
        watchlist["freshness"] = pd.to_datetime(watchlist["Date"], errors="coerce").map(
            lambda value: "UNKNOWN" if pd.isna(value) else "FRESH" if (pd.Timestamp.now().normalize() - value.normalize()).days <= 3 else "STALE"
        )
        gap_report_path = Path(root) / "reports" / "settrade_gap_recovery.json"
        try:
            gap_report = json.loads(gap_report_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            gap_report = {}
        bbo_by_symbol = gap_report.get("today_dataset_coverage", {}).get("production", {}).get("normalized_bbo", {}).get("today_bbo_by_symbol", {})
        now_bkk = pd.Timestamp.now(tz="Asia/Bangkok")
        bbo_age, spread_bps = [], []
        for symbol in watchlist["symbol"]:
            quote = bbo_by_symbol.get(symbol, {})
            stamp = pd.to_datetime(quote.get("timestamp_bangkok"), errors="coerce", utc=True)
            bbo_age.append((now_bkk.tz_convert("UTC") - stamp).total_seconds() / 60 if pd.notna(stamp) else float("nan"))
            try:
                bid, ask = float(quote.get("bid")), float(quote.get("ask"))
                midpoint = (bid + ask) / 2
                spread_bps.append((ask - bid) / midpoint * 10000 if bid > 0 and ask >= bid and midpoint > 0 else float("nan"))
            except (TypeError, ValueError):
                spread_bps.append(float("nan"))
        watchlist["BBO age (min)"] = bbo_age
        watchlist["spread_bps"] = spread_bps
        query = st.text_input("Filter symbols", placeholder="Type a SET symbol", key="overview_watchlist_filter").strip().upper()
        sort_options = {"Symbol": "symbol", "1D return": "return_1d", "5D return": "return_5d", "20D return": "return_20d", "20D volatility": "volatility_20d", "Volume / 20D": "volume_ratio_20d", "Spread bps": "spread_bps", "BBO age": "BBO age (min)", "Latest close": "Close"}
        sort_label = st.selectbox("Sort watchlist by", list(sort_options), key="overview_watchlist_sort")
        shown = watchlist[watchlist["symbol"].str.contains(query, regex=False)] if query else watchlist
        shown = shown.sort_values(sort_options[sort_label], ascending=(sort_label == "Symbol"), na_position="last")
        st.dataframe(
            shown[["symbol", "Close", "return_1d", "return_5d", "return_20d", "volume_ratio_20d", "volatility_20d", "spread_bps", "BBO age (min)", "Date", "freshness"]],
            hide_index=True, width="stretch", height=340,
            column_config={
                "Close": st.column_config.NumberColumn("Last daily close (THB)", format="%.2f"),
                "return_1d": st.column_config.NumberColumn("1D", format="percent"),
                "return_5d": st.column_config.NumberColumn("5D", format="percent"),
                "return_20d": st.column_config.NumberColumn("20D", format="percent"),
                "volume_ratio_20d": st.column_config.NumberColumn("Volume / 20D", format="%.2fx"),
                "volatility_20d": st.column_config.NumberColumn("Volatility (ann.)", format="percent"),
                "spread_bps": st.column_config.NumberColumn("Stored BBO spread (bps)", format="%.1f"),
                "BBO age (min)": st.column_config.NumberColumn("Latest BBO age (min)", format="%.0f"),
                "Date": st.column_config.DateColumn("Market date", format="YYYY-MM-DD"),
            },
        )
        st.caption(f"Daily source: persisted Yahoo OHLCV · latest market date {latest_daily_date.date() if pd.notna(latest_daily_date) else 'unknown'} · BBO columns come from the persisted production recovery report generated {gap_report.get('generated_at', 'unknown')} and show last-observation age, not a live connection.")

        st.subheader("Market heatmap")
        heat_metric = st.selectbox(
            "Color by metric",
            ["Intraday return", "1D return", "5D return", "20D return", "Volatility", "ATR%", "Volume activity", "Spread bps", "Data freshness"],
            key="overview_heatmap_metric",
        )
        heat_fields = {"1D return": "return_1d", "5D return": "return_5d", "20D return": "return_20d", "Volatility": "volatility_20d", "Volume activity": "volume_ratio_20d"}
        if heat_metric == "Intraday return":
            st.info("Intraday return is unavailable because this panel uses persisted daily OHLCV. No quote snapshot is treated as a live return.")
        else:
            if heat_metric == "ATR%":
                atr_values = []
                for symbol in watchlist["symbol"]:
                    stock = bars[bars["symbol"].eq(symbol)].sort_values("Date").tail(15)
                    previous = stock["Close"].shift(1)
                    true_range = pd.concat([(stock["High"] - stock["Low"]), (stock["High"] - previous).abs(), (stock["Low"] - previous).abs()], axis=1).max(axis=1)
                    atr_values.append(true_range.mean() / stock["Close"].iloc[-1] if not stock.empty and stock["Close"].iloc[-1] else float("nan"))
                watchlist["atr_pct"] = atr_values
                heat_values = watchlist["atr_pct"]
                heat_label = "ATR%"
            elif heat_metric == "Data freshness":
                heat_values = (pd.Timestamp.now().normalize() - pd.to_datetime(watchlist["Date"], errors="coerce").dt.normalize()).dt.days
                heat_label = "Calendar days since market date"
            elif heat_metric == "Spread bps":
                heat_values = watchlist["spread_bps"]
                heat_label = "Last stored production BBO spread (bps)"
            else:
                heat_values = watchlist[heat_fields[heat_metric]]
                heat_label = heat_metric
            heat = go.Figure(go.Treemap(
                labels=watchlist["symbol"], parents=[""] * len(watchlist), values=[1] * len(watchlist),
                marker={"colors": heat_values, "colorscale": "RdYlGn_r" if heat_metric == "Spread bps" else "RdYlGn", "cmid": 0 if heat_metric not in {"Data freshness", "Spread bps"} else None, "reversescale": heat_metric == "Data freshness", "colorbar": {"title": heat_label}},
                customdata=heat_values,
                hovertemplate="%{label}<br>" + heat_label + ": %{customdata:.3f}<extra></extra>",
            ))
            heat.update_layout(height=390, margin={"t": 10, "b": 10, "l": 10, "r": 10})
            st.plotly_chart(heat, width="stretch", config={"displaylogo": False})
            st.caption("Daily-source values only except stored production BBO spread, which shows its observation age in the watchlist. Heatmap color is descriptive; missing values remain unavailable and are not replaced with zeros.")
    detail_controls = st.columns([3, 1], vertical_alignment="bottom")
    detail_symbol = detail_controls[0].selectbox("Quick stock detail", symbols, key="overview_detail_symbol")
    detail_controls[1].button("Open detail", icon=":material/open_in_new:", key="open_stock_detail",
                              on_click=_open_stock_detail, args=(detail_symbol,))
    group = st.segmented_control("Trend grid", ["Stocks 1–25", "Stocks 26–50"], default="Stocks 1–25", key="overview_group")
    start, end, _ = _range_controls(bars, "overview")
    mode = st.segmented_control("Chart mode", MODES, default="Normalized performance", key="overview_mode")
    selected = split_universe(symbols, group or "Stocks 1–25")
    st.subheader(f"{group or 'Stocks 1–25'} · {len(selected)} mini-charts")
    st.caption(f"{start.date()} to {end.date()} · latest daily close date {bars['Date'].max().date() if not bars.empty else 'unavailable'}")
    _small_multiples(bars, selected, mode or "Normalized performance", start, end)
    with st.expander("Source coverage and caveats"):
        st.dataframe(_coverage_table(symbols, bars), hide_index=True, width="stretch")
        if not conflicts.empty:
            st.dataframe(conflicts, hide_index=True, width="stretch")
        st.caption("Daily Volume is the vendor-reported Yahoo field only. Settrade intraday pilot candles remain separate and are not used to extend or patch daily history.")


def render_trends(root: Path = ROOT) -> None:
    st.title("Multi-stock trends", icon=":material/show_chart:")
    st.caption("Browse all 50 current display names in two fast 25-stock groups; switch price, return, or relative views together.")
    symbols, bars, conflicts, _ = load_view(root)
    _header_warning()
    group = st.segmented_control("Symbol group", ["Stocks 1–25", "Stocks 26–50"], default="Stocks 1–25", key="trends_group")
    mode = st.segmented_control("View mode", MODES, default="Normalized performance", key="trends_mode")
    start, end, _ = _range_controls(bars, "trends")
    selected = split_universe(symbols, group or "Stocks 1–25")
    st.caption(f"{len(selected)} symbols · {start.date()} to {end.date()} · normalized series use each symbol’s first actual close inside the range.")
    if mode == "Relative performance":
        st.info("Relative performance is percentage-point performance versus an equal-weight basket of the current 50 display names. Each date uses only genuine available returns; this is not the official SET Index.")
    _small_multiples(bars, selected, mode or MODES[1], start, end)
    if len(conflicts):
        st.warning(f"{len(conflicts)} conflicted symbol-dates are omitted from this exploratory view.")

    st.subheader("Relative-strength overlay")
    chosen = st.multiselect("Choose up to 10 securities", symbols, default=symbols[:5], max_selections=10, key="overlay_symbols")
    overlay_mode = st.segmented_control("Overlay view", ["Normalized performance", "Relative performance"], default="Normalized performance", key="overlay_mode")
    subset = _slice(bars, chosen, start, end)
    overlay = series_for_mode(_slice(bars, display_universe(), start, end), chosen, overlay_mode or "Normalized performance", basket_symbols=display_universe()) if chosen else pd.DataFrame()
    fig = go.Figure()
    for symbol in chosen:
        if symbol in overlay:
            series = overlay[symbol].dropna()
            fig.add_trace(go.Scattergl(x=series.index, y=series, mode="lines", name=symbol,
                                       hovertemplate="%{x|%Y-%m-%d}<br>View %{y:.2f}<extra>" + symbol + "</extra>"))
    fig.update_layout(height=430, yaxis_title="Indexed value / percentage points", hovermode="x unified", margin={"t": 20, "b": 20})
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})


def _correlation_inputs(bars: pd.DataFrame, symbols: list[str], start: pd.Timestamp, end: pd.Timestamp, window: int) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    returns = daily_returns(_slice(bars, symbols, start, end))
    wide = returns.pivot(index="Date", columns="symbol", values="return").reindex(columns=symbols).tail(window)
    min_overlap = max(10, int(np.ceil(window * 0.6)))
    corr, counts = return_correlation(wide, min_overlap=min_overlap)
    return returns, corr, counts


def render_correlation(root: Path = ROOT) -> None:
    st.title("Correlation lab", icon=":material/hub:")
    st.caption("Exploratory daily close-to-close return co-movement. Pairwise observations only; unavailable prices and returns are never forward-filled.")
    symbols, bars, conflicts, _ = load_view(root)
    _header_warning()
    controls = st.columns(2)
    window = int(controls[0].selectbox("Return window (trading observations)", [20, 60, 120, 252], index=1, format_func=lambda n: f"{n} trading days", key="corr_window"))
    start, end, _ = _range_controls(bars, "corr", default="Max available")
    returns, corr, counts = _correlation_inputs(bars, symbols, start, end, window)
    min_overlap = max(10, int(np.ceil(window * 0.6)))
    st.caption(f"Daily close-to-close percentage returns · latest {window} selected-universe trading dates in {start.date()}–{end.date()} · minimum pair overlap {min_overlap} observations. N is available on heatmap hover.")
    order = st.segmented_control("Heatmap order", ["Universe order", "Correlation clustered"], default="Universe order", key="corr_order")
    matrix = corr.copy()
    if order == "Correlation clustered":
        complete = matrix.columns[matrix.notna().all(axis=0) & matrix.notna().all(axis=1)]
        if len(complete) >= 3:
            try:
                from scipy.cluster.hierarchy import leaves_list, linkage
                from scipy.spatial.distance import squareform
                distance = ((1 - matrix.loc[complete, complete].to_numpy()) / 2).clip(0, 1)
                np.fill_diagonal(distance, 0)
                order_idx = leaves_list(linkage(squareform(distance, checks=False), method="average"))
                clustered = list(complete[order_idx]) + [s for s in symbols if s not in complete]
                matrix = matrix.reindex(index=clustered, columns=clustered)
                st.caption(f"Hierarchical average-linkage correlation-distance ordering; {len(complete)} complete symbols. Clusters are visual groupings, not sectors.")
            except (ImportError, ValueError):
                st.info("Clustering is unavailable for this matrix; showing the stable universe order.")
        else:
            st.info("Too many pairs have insufficient overlap for a complete clustered matrix; showing stable universe order.")
    x, y = list(matrix.columns), list(matrix.index)
    n = counts.reindex(index=y, columns=x)
    hover = np.empty((len(y), len(x)), dtype=object)
    for i, a in enumerate(y):
        for j, b in enumerate(x):
            value = matrix.loc[a, b]
            hover[i, j] = f"{a} × {b}<br>Correlation: {value:.3f}<br>Pairwise observations: {n.loc[a, b]}" if pd.notna(value) else f"{a} × {b}<br>Insufficient overlap<br>Pairwise observations: {n.loc[a, b]}"
    fig = go.Figure(go.Heatmap(z=matrix.to_numpy(), x=x, y=y, zmin=-1, zmax=1, zmid=0,
                               colorscale="RdBu", reversescale=True, customdata=hover,
                               hovertemplate="%{customdata}<extra></extra>", colorbar={"title": "Pearson r"}, connectgaps=False))
    fig.update_layout(height=860, margin={"l": 80, "r": 20, "t": 20, "b": 130}, xaxis_tickangle=-60)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
    st.caption("Blank/light cells are pairs below the overlap threshold. Pearson correlation is descriptive, not causal.")

    st.subheader("Pair inspection")
    pair_cols = st.columns(3)
    a = pair_cols[0].selectbox("Symbol A", symbols, index=0, key="pair_a")
    b_idx = 1 if len(symbols) > 1 else 0
    b = pair_cols[1].selectbox("Symbol B", symbols, index=b_idx, key="pair_b")
    rolling_window = int(pair_cols[2].selectbox("Rolling window", [20, 60], index=0, format_func=lambda n: f"{n} trading days", key="rolling_window"))
    pair = returns.pivot(index="Date", columns="symbol", values="return").reindex(columns=symbols)
    aligned = pair[[a, b]].dropna() if a != b else pd.DataFrame(columns=[a, b])
    pearson = aligned[a].corr(aligned[b]) if len(aligned) >= 2 else float("nan")
    pair_metrics = st.columns(3)
    pair_metrics[0].metric("Pearson correlation", f"{pearson:.3f}" if pd.notna(pearson) else "—")
    pair_metrics[1].metric("Aligned return observations", len(aligned))
    pair_metrics[2].metric("Date coverage", f"{aligned.index.min().date()} to {aligned.index.max().date()}" if not aligned.empty else "Insufficient data")
    if not aligned.empty:
        scatter = go.Figure(go.Scattergl(x=aligned[a], y=aligned[b], mode="markers", marker={"size": 6, "opacity": 0.55},
                                         customdata=aligned.index.astype(str), hovertemplate="%{customdata}<br>" + a + " return %{x:.2%}<br>" + b + " return %{y:.2%}<extra></extra>"))
        scatter.update_layout(height=360, xaxis_title=f"{a} daily return", yaxis_title=f"{b} daily return", margin={"t": 15, "b": 20})
        st.plotly_chart(scatter, width="stretch", config={"displaylogo": False})
        rolling = rolling_pair_correlation(pair[a], pair[b], rolling_window).dropna()
        if not rolling.empty:
            rolling_fig = go.Figure(go.Scattergl(x=rolling.index, y=rolling, mode="lines", line={"color": "#d26a3c", "width": 1.5}, name="Rolling Pearson r"))
            rolling_fig.update_layout(height=260, yaxis={"title": "Rolling Pearson r", "range": [-1, 1]}, xaxis_title="Date", margin={"t": 15, "b": 15})
            st.plotly_chart(rolling_fig, width="stretch", config={"displaylogo": False})
        else:
            st.info(f"Not enough complete aligned observations for a {rolling_window}-day rolling correlation.")
    elif a == b:
        st.info("Choose two different symbols to inspect paired returns.")
    else:
        st.info("No paired return observations are available for these symbols in the selected date window.")
    if len(conflicts):
        st.caption(f"{len(conflicts)} source-conflict dates were excluded before return calculation.")


def _coverage_table(symbols: list[str], bars: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol in symbols:
        frame = bars[bars["symbol"].eq(symbol)].sort_values("Date")
        rows.append({
            "symbol": symbol, "rows": len(frame),
            "first_date": frame["Date"].min().date().isoformat() if not frame.empty else "",
            "last_date": frame["Date"].max().date().isoformat() if not frame.empty else "",
            "sources": ", ".join(frame["source_type"].drop_duplicates().tolist()) if not frame.empty else "No usable data",
            "manifest_approved_rows": int(frame["approval_scope"].eq("within_manifest").sum()) if not frame.empty else 0,
            "volume_rows": int(frame["Volume"].notna().sum()) if not frame.empty else 0,
            "invalid_ohlc_rows": int(frame["ohlc_status"].eq("INVALID").sum()) if not frame.empty else 0,
            "identity_note": IDENTITY_NOTES.get(symbol, "Exact source symbol retained; no cross-symbol price mapping."),
        })
    return pd.DataFrame(rows)


def render_breadth(root: Path = ROOT) -> None:
    st.title("Market breadth and trend matrix", icon=":material/ssid_chart:")
    st.caption("Descriptive coverage-aware metrics; no score, ranking tier, or buy/sell recommendation.")
    symbols, bars, conflicts, _ = load_view(root)
    _header_warning()
    breadth, metrics = breadth_summary(bars, symbols)
    cards = st.columns(4)
    labels = {"above_sma20": "Above SMA20", "above_sma50": "Above SMA50", "return_20d": "Positive 20D return", "return_5d": "Positive 5D return"}
    for card, key in zip(cards, labels):
        value, denominator = breadth[key]
        card.metric(labels[key], f"{value} / {denominator}", f"{value / denominator:.1%} available" if denominator else "No sufficient history")
    st.caption("Each denominator includes only securities with enough actual observations for that metric. Moving averages use 20 or 50 observed closes; no missing close is filled.")
    if not metrics.empty:
        latest = metrics.reset_index().sort_values("symbol")
        st.subheader("Cross-sectional performance and trend matrix")
        st.dataframe(latest, hide_index=True, width="stretch", height=560,
                     column_config={
                         "Date": st.column_config.DateColumn("Latest date", format="YYYY-MM-DD"),
                         "Close": st.column_config.NumberColumn("Close (THB)", format="%.2f"),
                         "return_1d": st.column_config.NumberColumn("1D return", format="percent"),
                         "return_5d": st.column_config.NumberColumn("5D return", format="percent"),
                         "return_20d": st.column_config.NumberColumn("20D return", format="percent"),
                         "return_60d": st.column_config.NumberColumn("60D return", format="percent"),
                         "above_sma20": st.column_config.CheckboxColumn("Close > SMA20"),
                         "above_sma50": st.column_config.CheckboxColumn("Close > SMA50"),
                         "sma20_above_sma50": st.column_config.CheckboxColumn("SMA20 > SMA50"),
                         "distance_sma20": st.column_config.NumberColumn("Close vs SMA20", format="percent"),
                         "distance_sma50": st.column_config.NumberColumn("Close vs SMA50", format="percent"),
                         "volatility_20d": st.column_config.NumberColumn("20D realized volatility (ann.)", format="percent"),
                         "volume_ratio_20d": st.column_config.NumberColumn("Volume / 20D avg", format="%.2fx"),
                     })
        selected = st.selectbox("Inspect historical volume", symbols, key="breadth_volume_symbol")
        detail = bars[bars["symbol"].eq(selected)].sort_values("Date").tail(260)
        if detail["Volume"].notna().any():
            vol20 = detail["Volume"].rolling(20, min_periods=20).mean()
            fig = go.Figure()
            fig.add_trace(go.Bar(x=detail["Date"], y=detail["Volume"], name="Yahoo daily volume", marker_color="#9db6c5"))
            fig.add_trace(go.Scatter(x=detail["Date"], y=vol20, name="20-observation mean", line={"color": "#d26a3c", "width": 2}))
            fig.update_layout(height=300, title=f"{selected} · vendor-reported daily volume · {', '.join(detail['source_type'].unique())}", yaxis_title="Reported volume units", margin={"t": 40, "b": 15})
            st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
        else:
            st.info(f"No trusted daily volume values are available for {selected}.")
    if not conflicts.empty:
        st.warning(f"{len(conflicts)} conflicting OHLCV symbol-dates were excluded.")


def render_detail(root: Path = ROOT) -> None:
    st.title("Stock detail", icon=":material/candlestick_chart:")
    st.caption("One-security daily candles and volume with source provenance and data-quality context.")
    symbols, bars, conflicts, _ = load_view(root)
    controls = st.columns(2)
    symbol = controls[0].selectbox("Security", symbols, key="detail_symbol") if symbols else None
    if not symbol:
        st.warning("The current-set display universe is unavailable.")
        return
    selected_bars = bars[bars["symbol"].eq(symbol)].sort_values("Date")
    start, end, _ = _range_controls(selected_bars, "detail", default="Max available")
    frame = selected_bars[selected_bars["Date"].between(start, end)].copy()
    if frame.empty:
        st.warning(f"No usable OHLCV observations for {symbol}.")
        return
    source_list = ", ".join(frame["source_type"].drop_duplicates())
    metrics = st.columns(5)
    metrics[0].metric("Available bars", len(frame))
    metrics[1].metric("First date", frame["Date"].min().date().isoformat())
    metrics[2].metric("Last date", frame["Date"].max().date().isoformat())
    metrics[3].metric("Latest close", f"{frame['Close'].iloc[-1]:.2f}")
    metrics[4].metric("Sources", len(frame["source_file"].unique()))
    if symbol in IDENTITY_NOTES:
        st.warning(IDENTITY_NOTES[symbol], icon=":material/info:")
    st.caption(f"Provenance: {source_list}. Approved scope is shown separately from exploratory rows; this panel is not a backtest input.")
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.035, row_heights=[0.72, 0.28])
    valid_ohlc = frame[frame["ohlc_status"].eq("VALID")]
    fig.add_trace(go.Candlestick(x=valid_ohlc["Date"], open=valid_ohlc["Open"], high=valid_ohlc["High"], low=valid_ohlc["Low"], close=valid_ohlc["Close"], name=f"{symbol} valid OHLC"), row=1, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["Close"], mode="lines", name="All observed closes", line={"color": "#253e5e", "width": 1}), row=1, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["Close"].rolling(20, min_periods=20).mean(), mode="lines", name="SMA20", line={"color": "#d26a3c", "width": 1.3}), row=1, col=1)
    fig.add_trace(go.Scatter(x=frame["Date"], y=frame["Close"].rolling(50, min_periods=50).mean(), mode="lines", name="SMA50", line={"color": "#3d7e9a", "width": 1.3}), row=1, col=1)
    fig.add_trace(go.Bar(x=frame["Date"], y=frame["Volume"], name="Yahoo reported volume", marker_color="#9db6c5"), row=2, col=1)
    fig.update_layout(height=650, xaxis_rangeslider_visible=False, hovermode="x unified", margin={"t": 20, "b": 20}, legend={"orientation": "h"})
    fig.update_yaxes(title_text="Price (THB)", row=1, col=1)
    fig.update_yaxes(title_text="Vendor volume", row=2, col=1)
    st.plotly_chart(fig, width="stretch", config={"displaylogo": False})
    ret = frame["Close"].pct_change(fill_method=None)
    returns = [frame["Close"].iloc[-1] / frame["Close"].iloc[-n - 1] - 1 for n in (1, 5, 20, 60) if len(frame) > n]
    rcols = st.columns(4)
    for card, label, n in zip(rcols, ("1D", "5D", "20D", "60D"), (1, 5, 20, 60)):
        val = frame["Close"].iloc[-1] / frame["Close"].iloc[-n - 1] - 1 if len(frame) > n else float("nan")
        card.metric(f"{label} close return", f"{val:.2%}" if pd.notna(val) else "Insufficient history")
    provenance = frame.groupby(["source_type", "source_file", "approval_scope"], as_index=False).agg(rows=("Date", "size"), invalid_ohlc_rows=("ohlc_status", lambda values: int(values.eq("INVALID").sum())), first_date=("Date", "min"), last_date=("Date", "max"))
    st.subheader("Source provenance")
    st.dataframe(provenance, hide_index=True, width="stretch")
    st.caption(f"{int(frame['Volume'].notna().sum())} source volume observations · no gaps filled · {int(frame['ohlc_status'].eq('INVALID').sum())} invalid OHLC rows · {len(conflicts[conflicts['symbol'].eq(symbol)])} conflicting source dates excluded for this security.")


def render_source_inventory(root: Path = ROOT) -> None:
    symbols, bars, conflicts, inventory = load_view(root)
    st.title("Historical daily source inventory", icon=":material/database:")
    st.caption("Per-file audit of stored daily OHLCV sources. Source data are read-only; market calendars and identity boundaries are not inferred from ticker similarity.")
    st.metric("Current SET50 names with usable daily close", f"{bars['symbol'].nunique()} / {len(symbols)}")
    if not inventory.empty:
        st.dataframe(inventory, hide_index=True, width="stretch", height=580)
    if not conflicts.empty:
        st.subheader("Conflicting source dates excluded from the derived view")
        st.dataframe(conflicts, hide_index=True, width="stretch")
    st.info("Settrade 1m/5m/15m pilot candles are intraday and kept separate; event-driven BBO has no synthetic bars and is not part of daily history. Yahoo-reported Volume is visualized only as reported.")

"""Streamlit research UI for the current SET50 data foundation."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.data_catalog import (  # noqa: E402
    DataPaths,
    discover_paths,
    load_acquisition,
    load_audit,
    load_constituents,
    load_market_frame,
    load_metadata,
    market_data_files,
    quality_summary,
    load_settrade_bbo,
    load_settrade_candles,
    settrade_availability,
)

st.set_page_config(page_title="SET50 Research Desk", page_icon="R", layout="wide")


def _date_range(frame: pd.DataFrame) -> str:
    if frame.empty or "Date" not in frame:
        return "Unavailable"
    dates = pd.to_datetime(frame["Date"], errors="coerce").dropna()
    return f"{dates.min().date()} to {dates.max().date()}" if not dates.empty else "Unavailable"


def _reported_date_range(acquisition: pd.DataFrame) -> str:
    if acquisition.empty or not {"Requested Start", "Requested End"}.issubset(acquisition.columns):
        return "Unavailable"
    starts = pd.to_datetime(acquisition["Requested Start"], errors="coerce").dropna()
    ends = pd.to_datetime(acquisition["Requested End"], errors="coerce").dropna()
    return f"{starts.min().date()} to {ends.max().date()}" if not starts.empty and not ends.empty else "Unavailable"


def _status(paths: DataPaths, constituents: pd.DataFrame, audit: pd.DataFrame, acquisition: pd.DataFrame) -> None:
    files = market_data_files(paths)
    missing = acquisition[acquisition["Status"].isin(["NO_DATA", "FAILED"])] if "Status" in acquisition else pd.DataFrame()
    downloaded = int((acquisition["Rows"] > 0).sum()) if "Rows" in acquisition else len(files)
    st.title("SET50 Research Desk")
    st.caption("Read-only exploration of historical membership, Yahoo acquisition, and raw OHLCV quality.")
    cards = st.columns(6)
    sample = load_market_frame(next(iter(files.values()))) if files else pd.DataFrame()
    date_range = _date_range(sample) if not sample.empty else _reported_date_range(acquisition)
    values = [("Dataset", "Ready" if constituents.shape[0] else "Incomplete"), ("SET50 periods", str(constituents["period"].nunique()) if "period" in constituents else "0"), ("Symbols", str(constituents["symbol"].nunique()) if "symbol" in constituents else "0"), ("Downloaded", str(downloaded)), ("Date range", date_range), ("Missing / failed", str(len(missing)))]
    for card, (label, value) in zip(cards, values):
        card.metric(label, value)
    st.subheader("Mapping status")
    if "Status" in audit:
        st.dataframe(audit["Status"].value_counts().rename_axis("Status").reset_index(name="Symbols"), hide_index=True, use_container_width=True)
    else:
        st.warning("Yahoo ticker audit is unavailable.")
    if not acquisition.empty:
        st.subheader("Acquisition status")
        st.dataframe(acquisition["Status"].value_counts().rename_axis("Status").reset_index(name="Symbols"), hide_index=True, use_container_width=True)
    st.info(f"Raw directories discovered: {', '.join(str(path.relative_to(paths.root)) for path in paths.raw_directories)}")


def _universe(constituents: pd.DataFrame, audit: pd.DataFrame) -> None:
    st.header("Historical SET50 Universe")
    if constituents.empty:
        st.warning("Historical constituent data is unavailable.")
        return
    period = st.selectbox("Effective period", list(constituents["period"].drop_duplicates()))
    view = constituents[constituents["period"] == period].copy()
    mapping = audit[["SET Symbol", "Yahoo Ticker", "Status"]] if not audit.empty else pd.DataFrame()
    if not mapping.empty:
        view = view.merge(mapping, left_on="symbol", right_on="SET Symbol", how="left")
    columns = [column for column in ["symbol", "Yahoo Ticker", "Status", "company_name", "effective_from", "effective_to", "source_url", "provenance_source_url"] if column in view]
    st.caption("SET Symbol is the official historical membership identifier. Yahoo Ticker is a separate research-source mapping.")
    st.dataframe(view[columns], hide_index=True, use_container_width=True)


def _market_explorer(paths: DataPaths, audit: pd.DataFrame) -> None:
    st.header("Market Data Explorer")
    files = market_data_files(paths)
    symbols = sorted({symbol.split(".")[0] for symbol in files} | (set(audit["SET Symbol"]) if "SET Symbol" in audit else set()))
    if not symbols:
        st.warning("No raw market-data files were discovered.")
        return
    symbol = st.selectbox("Symbol", symbols)
    path = files.get(f"{symbol}.BK")
    if path is None:
        st.warning("This symbol has no downloaded raw file.")
        return
    frame = load_market_frame(path)
    date_column = next((column for column in frame.columns if column.lower() in {"date", "datetime"}), "Date")
    dates = pd.to_datetime(frame[date_column], errors="coerce").dropna()
    selected = st.date_input("Date range", value=(dates.min().date(), dates.max().date()) if not dates.empty else None)
    if isinstance(selected, (tuple, list)) and len(selected) == 2:
        start, end = map(pd.Timestamp, selected)
        frame = frame[(frame[date_column] >= start) & (frame[date_column] <= end)]
    report = quality_summary(frame, symbol)
    cols = st.columns(4)
    cols[0].metric("Rows", report["rows"])
    cols[1].metric("Missing values", sum(report["missing_values"].values()))
    cols[2].metric("Duplicate dates", report["duplicate_dates"])
    cols[3].metric("OHLC warnings", report["invalid_relationships"])
    chart = go.Figure()
    if all(column in frame for column in ["Open", "High", "Low", "Close"]):
        chart.add_trace(go.Candlestick(x=frame[date_column], open=frame["Open"], high=frame["High"], low=frame["Low"], close=frame["Close"], name=symbol))
    chart.update_layout(height=430, xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=25, b=10))
    st.plotly_chart(chart, use_container_width=True)
    if "Volume" in frame:
        volume = go.Figure(go.Bar(x=frame[date_column], y=frame["Volume"], name="Volume"))
        volume.update_layout(height=220, margin=dict(l=10, r=10, t=25, b=10))
        st.plotly_chart(volume, use_container_width=True)
    st.dataframe(frame, hide_index=True, use_container_width=True)
    with st.expander("Data quality details"):
        st.json(report)


def _quality(paths: DataPaths, audit: pd.DataFrame, acquisition: pd.DataFrame) -> None:
    st.header("Data Quality")
    if not acquisition.empty:
        st.dataframe(acquisition, hide_index=True, use_container_width=True)
    if not audit.empty:
        st.subheader("Yahoo ticker audit")
        st.dataframe(audit, hide_index=True, use_container_width=True)
    rows = [quality_summary(load_market_frame(path), ticker) for ticker, path in market_data_files(paths).items()]
    if rows:
        quality = pd.DataFrame(rows)
        quality["missing_values"] = quality["missing_values"].map(str)
        quality["missing_dates"] = quality["missing_dates"].map(str)
        st.subheader("Raw-file validation diagnostics")
        st.dataframe(quality, hide_index=True, use_container_width=True)


def _research_placeholders() -> None:
    st.header("Research Results")
    st.caption("Reserved for reproducible research outputs. No strategies or backtests are implemented here.")
    for name in ["Strategy Research", "Backtest", "Out-of-Sample", "Optimization", "Robustness", "Paper Trading"]:
        st.write(f"**{name}**: Not implemented")


def _settrade_explorer(paths: DataPaths) -> None:
    """Read-only pilot/staging explorer for Settrade market-data artifacts."""
    st.header("Settrade Data Explorer")
    st.caption("PILOT / UNAPPROVED — read-only. No credentials, orders, deletion, or promotion actions are available.")
    availability = settrade_availability(paths)
    candle_symbols = sorted(availability.loc[availability["datatype"] == "candles", "symbol"].unique()) if not availability.empty else []
    bbo_symbols = sorted(availability.loc[availability["datatype"] == "bbo", "symbol"].unique()) if not availability.empty else []
    symbols = sorted(set(candle_symbols) | set(bbo_symbols))
    if not symbols:
        st.warning("No normalized Settrade pilot data is available yet. The next market-session collector run will populate this view.")
        return
    controls = st.columns(4)
    symbol = controls[0].selectbox("Symbol", symbols)
    data_type = controls[1].selectbox("Data type", ["Candles", "BBO / Depth", "Price info", "Trades"])
    timeframe = controls[2].selectbox("Timeframe", ["1m", "5m", "15m"], disabled=data_type != "Candles")
    session_filter = controls[3].selectbox("Session filter", ["All timestamps", "Continuous sessions only", "Exclude midday break"])
    dates = pd.to_datetime(availability.loc[availability["symbol"] == symbol, "date"], errors="coerce").dropna()
    default_dates = (dates.min().date(), dates.max().date()) if not dates.empty else None
    selected_dates = st.date_input("Date range (Asia/Bangkok)", value=default_dates)
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start, end = selected_dates
    else:
        start = end = selected_dates

    if data_type == "Candles":
        frame = load_settrade_candles(paths, timeframe, symbol, start, end)
        if frame.empty:
            st.info("No persisted candle data for this selection.")
            return
        if session_filter != "All timestamps":
            local_times = frame["timestamp_local"].dt.time
            frame = frame[(local_times >= pd.Timestamp("09:30").time()) & (local_times < pd.Timestamp("16:40").time())]
            if session_filter == "Exclude midday break":
                frame = frame[(local_times < pd.Timestamp("12:30").time()) | (local_times >= pd.Timestamp("14:30").time())]
        quality = {"rows": len(frame), "duplicates": int(frame.duplicated(["symbol", "timestamp"]).sum()), "first": frame["timestamp_local"].min().isoformat(), "last": frame["timestamp_local"].max().isoformat(), "source": "SETTRADE_API_CANDLE", "volume_warning": "Source volume semantics are retained as provided; not used as a strategy feature."}
        cols = st.columns(4)
        cols[0].metric("Rows", quality["rows"])
        cols[1].metric("Duplicates", quality["duplicates"])
        cols[2].metric("First", quality["first"])
        cols[3].metric("Last", quality["last"])
        st.warning(quality["volume_warning"])
        chart = go.Figure(go.Candlestick(x=frame["timestamp_local"], open=frame["open"], high=frame["high"], low=frame["low"], close=frame["close"], name=f"{symbol} {timeframe}"))
        chart.update_layout(height=480, xaxis_rangeslider_visible=False, title="SETTRADE_API_CANDLE")
        st.plotly_chart(chart, use_container_width=True)
        if "volume" in frame:
            st.plotly_chart(go.Figure(go.Bar(x=frame["timestamp_local"], y=frame["volume"], name="source volume")), use_container_width=True)
        st.dataframe(frame, hide_index=True, use_container_width=True)
        with st.expander("Data quality"):
            st.json(quality)
        return

    if data_type == "BBO / Depth":
        frame = load_settrade_bbo(paths, symbol, start, end)
        if frame.empty:
            st.info("No persisted BBO data for this selection.")
            return
        event_keys = ["retrieved_at", "collector_session_id", "generation", "rotation_group"]
        events = frame[event_keys].drop_duplicates().reset_index(drop=True)
        choice = st.selectbox("BBO event", range(len(events)), format_func=lambda index: events.iloc[index]["retrieved_at"].isoformat())
        selected = events.iloc[choice]
        snapshot = frame[(frame["retrieved_at"] == selected["retrieved_at"]) & (frame["collector_session_id"] == selected["collector_session_id"]) & (frame["generation"] == selected["generation"]) & (frame["rotation_group"] == selected["rotation_group"])]
        bids = snapshot[snapshot["side"] == "bid"].sort_values("level")
        asks = snapshot[snapshot["side"] == "ask"].sort_values("level")
        best_bid = pd.to_numeric(bids["price"], errors="coerce").dropna().iloc[0] if not bids.empty and not pd.to_numeric(bids["price"], errors="coerce").dropna().empty else None
        best_ask = pd.to_numeric(asks["price"], errors="coerce").dropna().iloc[0] if not asks.empty and not pd.to_numeric(asks["price"], errors="coerce").dropna().empty else None
        midpoint = (best_bid + best_ask) / 2 if best_bid is not None and best_ask is not None else None
        metrics = st.columns(5)
        metrics[0].metric("Best bid", best_bid)
        metrics[1].metric("Best ask", best_ask)
        metrics[2].metric("Spread", best_ask - best_bid if midpoint is not None else None)
        metrics[3].metric("Midpoint", midpoint)
        metrics[4].metric("Levels", 10)
        st.caption(f"SETTRADE_BBO · event={selected['retrieved_at']} · collector={selected['collector_session_id']} · generation={selected['generation']} · rotation={selected['rotation_group']}")
        left, right = st.columns(2)
        left.subheader("Bid depth")
        left.dataframe(bids[["level", "price", "volume"]], hide_index=True, use_container_width=True)
        right.subheader("Ask depth")
        right.dataframe(asks[["level", "price", "volume"]], hide_index=True, use_container_width=True)
        depth = pd.concat([bids.assign(cumulative=pd.to_numeric(bids["volume"], errors="coerce").fillna(0).cumsum()), asks.assign(cumulative=pd.to_numeric(asks["volume"], errors="coerce").fillna(0).cumsum())])
        st.plotly_chart(go.Figure(go.Bar(x=depth["level"], y=depth["cumulative"], marker_color=depth["side"], name="cumulative depth")), use_container_width=True)
        history = frame.pivot_table(index="timestamp_local", columns="side", values="price", aggfunc="first").sort_index()
        if not history.empty:
            history["midpoint"] = history[[column for column in ["bid", "ask"] if column in history]].mean(axis=1)
            st.plotly_chart(go.Figure([go.Scatter(x=history.index, y=history[column], name=column) for column in history.columns]), use_container_width=True)
        st.subheader("Execution inspection (diagnostic only)")
        st.info("MODEL_V1 remains unchanged. This view shows the observed book and does not submit orders or recompute production decisions.")
        return

    if data_type == "Price info":
        st.info("No persisted price_info stream is currently enabled. API quote snapshots remain separate from realtime price_info updates.")
        return
    st.info("TRUE_TRADE_STREAM is not exposed by the inspected settrade-v2==2.2.1 equity realtime surface; no trade chart is enabled and price_info is never relabeled as trades.")


paths = discover_paths()
constituents = load_constituents(paths)
audit = load_audit(paths)
acquisition = load_acquisition(paths)
metadata = load_metadata(paths)
page = st.sidebar.radio("Workspace", ["Dashboard", "Historical SET50 Universe", "Market Data Explorer", "Settrade Data Explorer", "Data Quality", "Research Results"])
st.sidebar.caption("Source data is read-only")
if metadata:
    st.sidebar.caption(f"Acquisition: {metadata.get('acquisition_timestamp', 'unknown')}")
if page == "Dashboard":
    _status(paths, constituents, audit, acquisition)
elif page == "Historical SET50 Universe":
    _universe(constituents, audit)
elif page == "Market Data Explorer":
    _market_explorer(paths, audit)
elif page == "Settrade Data Explorer":
    _settrade_explorer(paths)
elif page == "Data Quality":
    _quality(paths, audit, acquisition)
else:
    _research_placeholders()

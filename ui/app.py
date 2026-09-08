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


paths = discover_paths()
constituents = load_constituents(paths)
audit = load_audit(paths)
acquisition = load_acquisition(paths)
metadata = load_metadata(paths)
page = st.sidebar.radio("Workspace", ["Dashboard", "Historical SET50 Universe", "Market Data Explorer", "Data Quality", "Research Results"])
st.sidebar.caption("Source data is read-only")
if metadata:
    st.sidebar.caption(f"Acquisition: {metadata.get('acquisition_timestamp', 'unknown')}")
if page == "Dashboard":
    _status(paths, constituents, audit, acquisition)
elif page == "Historical SET50 Universe":
    _universe(constituents, audit)
elif page == "Market Data Explorer":
    _market_explorer(paths, audit)
elif page == "Data Quality":
    _quality(paths, audit, acquisition)
else:
    _research_placeholders()
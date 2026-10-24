"""Streamlit research UI for the current SET50 data foundation."""

from __future__ import annotations

import json
import os
import sys
import time
from dataclasses import replace
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
    load_settrade_audit,
    load_settrade_runtime,
    market_data_files,
    quality_summary,
    load_settrade_bbo,
    load_settrade_candles,
    filter_settrade_candles,
    prepare_settrade_chart_frame,
    settrade_candle_quality,
    settrade_availability,
)
from ui.market_research import (  # noqa: E402
    render_breadth,
    render_correlation,
    render_detail,
    render_overview as render_market_overview,
    render_source_inventory,
    render_trends,
)
from ui.theme import apply_theme  # noqa: E402
from src.data.settrade.health import collect_health  # noqa: E402
from src.competition.tradesim_bridge.core import BridgeError, discover_official_repo, inspect_official, list_dates  # noqa: E402
from src.competition.tradesim_bridge.runtime import inventory_ticks, runtime_diagnostic  # noqa: E402

st.set_page_config(page_title="SET50 Research Desk", page_icon="R", layout="wide")
apply_theme()


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


def _collector_start(paths: DataPaths, selected_date: object) -> str | None:
    """Read the runner start timestamp for a selected Bangkok trading day."""
    try:
        day = pd.Timestamp(selected_date).date().isoformat()
        path = paths.root / "reports" / "runtime" / f"settrade_daily_{day}.json"
        return json.loads(path.read_text(encoding="utf-8")).get("start_time") if path.exists() else None
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return None


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
        st.dataframe(audit["Status"].value_counts().rename_axis("Status").reset_index(name="Symbols"), hide_index=True, width="stretch")
    else:
        st.warning("Yahoo ticker audit is unavailable.")
    if not acquisition.empty:
        st.subheader("Acquisition status")
        st.dataframe(acquisition["Status"].value_counts().rename_axis("Status").reset_index(name="Symbols"), hide_index=True, width="stretch")
    st.info(f"Raw directories discovered: {', '.join(str(path.relative_to(paths.root)) for path in paths.raw_directories)}")


def _overview(paths: DataPaths, constituents: pd.DataFrame, audit: pd.DataFrame, acquisition: pd.DataFrame) -> None:
    """Show measured system health and keep research navigation shallow."""
    st.markdown('<div class="hero"><div class="eyebrow">SET50 research desk · read only</div><h1>Overview</h1><p>One place for collection health, historical universe, and source-faithful research views.</p></div>', unsafe_allow_html=True)
    collection = load_settrade_audit(paths)
    readiness = collection.get("readiness", {})
    cards = st.columns(5)
    cards[0].metric("SET50 universe", readiness.get("universe", "UNKNOWN"))
    cards[1].metric("BBO readiness", readiness.get("bbo", "UNKNOWN"))
    candle_state = readiness.get("candles", "UNKNOWN")
    if isinstance(candle_state, dict):
        candle_state = " / ".join(f"{key} {value}" for key, value in candle_state.items())
    cards[2].metric("Candle state", str(candle_state))
    cards[3].metric("Orders", readiness.get("orders", "0"))
    cards[4].metric("Audit", "MEASURED" if collection else "NOT GENERATED")
    runtime = load_settrade_runtime(paths)
    if not runtime.empty:
        st.subheader("Recent collection runs")
        columns = [column for column in ["summary_file", "start_time", "end_time", "shutdown_status", "bbo_events_written", "one_minute_rows_written", "symbols_with_1m_data", "orders_placed"] if column in runtime]
        st.dataframe(runtime.tail(6)[columns], hide_index=True, width="stretch")
    st.info("Use Candle Explorer for session-aware candle coverage, Order Book Explorer for genuine callbacks, and Collection Health for cycle-level evidence. All Settrade views are pilot/read-only.")


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
    st.dataframe(view[columns], hide_index=True, width="stretch")


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
    st.plotly_chart(chart, width="stretch")
    if "Volume" in frame:
        volume = go.Figure(go.Bar(x=frame[date_column], y=frame["Volume"], name="Volume"))
        volume.update_layout(height=220, margin=dict(l=10, r=10, t=25, b=10))
        st.plotly_chart(volume, width="stretch")
    st.dataframe(frame, hide_index=True, width="stretch")
    with st.expander("Data quality details"):
        st.json(report)


def _quality(paths: DataPaths, audit: pd.DataFrame, acquisition: pd.DataFrame) -> None:
    st.header("Data Quality")
    if not acquisition.empty:
        st.dataframe(acquisition, hide_index=True, width="stretch")
    if not audit.empty:
        st.subheader("Yahoo ticker audit")
        st.dataframe(audit, hide_index=True, width="stretch")
    rows = [quality_summary(load_market_frame(path), ticker) for ticker, path in market_data_files(paths).items()]
    if rows:
        quality = pd.DataFrame(rows)
        quality["missing_values"] = quality["missing_values"].map(str)
        quality["missing_dates"] = quality["missing_dates"].map(str)
        st.subheader("Raw-file validation diagnostics")
        st.dataframe(quality, hide_index=True, width="stretch")


def _collection_health(paths: DataPaths) -> None:
    st.markdown('<div class="hero"><div class="eyebrow">Operational evidence · read only</div><h1>Collection Health</h1><p>Measured runner summaries, persisted coverage, rotation evidence, and known external limitations.</p></div>', unsafe_allow_html=True)
    from src.data.settrade.paths import configured_environment
    environment = configured_environment(paths.root)
    cutover_path = paths.root / "reports" / "settrade_production_cutover.json"
    smoke_path = paths.root / "reports" / "settrade_production_smoke.json"
    try:
        cutover = json.loads(cutover_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        cutover = {}
    try:
        smoke = json.loads(smoke_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        smoke = {}
    readiness_path = paths.root / "reports" / "settrade_production_readiness.json"
    try:
        readiness_check = json.loads(readiness_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        readiness_check = {}
    state_cards = st.columns(4)
    state_cards[0].metric("Configured environment", environment.upper())
    state_cards[1].metric("Market-data readiness", readiness_check.get("status", smoke.get("status", "UNKNOWN")))
    state_cards[2].metric("Authentication", smoke.get("authentication", "UNKNOWN"))
    state_cards[3].metric("Orders placed", smoke.get("orders_placed", 0))
    last_api_check = readiness_check.get("checked_at", readiness_check.get("completed_at", smoke.get("completed_at", smoke.get("started_at", "UNKNOWN"))))
    st.caption(f"Routing: broker {smoke.get('broker_id', '013' if environment == 'production' else 'UNKNOWN')} · app {smoke.get('app_code', 'ALGO_EQ' if environment == 'production' else 'UNKNOWN')} · SDK {smoke.get('sdk_version', 'UNKNOWN')} · last API check {last_api_check} · account/private API: REQUIRES_ACCOUNT_NUMBER")
    if readiness_check.get("warnings"):
        st.warning("Readiness warnings: " + "; ".join(readiness_check["warnings"]))
    st.subheader("Production cutover and provenance")
    cutover_utc = cutover.get("cutover_timestamp_utc")
    if cutover_utc:
        cutover_local = pd.Timestamp(cutover_utc).tz_convert("Asia/Bangkok")
        last_sandbox = cutover.get("last_known_sandbox_observation")
        last_sandbox_local = pd.Timestamp(last_sandbox).tz_convert("Asia/Bangkok").isoformat() if last_sandbox else "UNKNOWN"
        first = cutover.get("first_production_observation", {})
        session_started = first.get("session_started_at_utc")
        session_started_local = pd.Timestamp(session_started).tz_convert("Asia/Bangkok").isoformat() if session_started else "UNKNOWN"
        st.info(f"Production API cutover: {cutover_local:%Y-%m-%d %H:%M} Asia/Bangkok · last sandbox observation: {last_sandbox_local} · first production quote time: {first.get('timestamp_utc', 'UNKNOWN')} (smoke session start {session_started_local}; exact receipt UNKNOWN)")
    with st.expander("Cutover marker details"):
        st.json(cutover or {"status": "UNKNOWN", "reason": "No cutover marker is available."})
    gap_report_path = paths.root / "reports" / "settrade_gap_recovery.json"
    try:
        gap_report = json.loads(gap_report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        gap_report = {}
    if gap_report:
        st.subheader("Current-day coverage and session timeline")
        today_data = gap_report.get("today_dataset_coverage", {}).get("production", {})
        outage = gap_report.get("outage_assessment", {})
        cards = st.columns(4)
        cards[0].metric("Trading day", gap_report.get("today", "UNKNOWN"))
        cards[1].metric("Outage evidence", outage.get("classification", "UNKNOWN"))
        cards[2].metric("Current-day gaps", len(gap_report.get("gap_records", [])))
        cards[3].metric("Rows backfilled", gap_report.get("recovery", {}).get("rows_backfilled", 0))
        st.caption(outage.get("statement", "Outage evidence has not been reported."))
        coverage_rows = [{"dataset": dataset, "source/environment": "Settrade Open API / PRODUCTION", "rows today": details.get("today_rows", 0), "symbols": len(details.get("today_symbols", [])), "first Bangkok": details.get("today_first_bangkok"), "last Bangkok": details.get("today_last_bangkok"), "source file": details.get("path")} for dataset, details in today_data.items()]
        if coverage_rows:
            st.dataframe(pd.DataFrame(coverage_rows), hide_index=True, width="stretch", alt="Current-day source coverage and timestamps by production dataset")
        timeline_items = []
        def add_timeline(label: str, start_value: object, end_value: object, color: str) -> None:
            start_stamp = pd.to_datetime(start_value, errors="coerce", utc=True)
            end_stamp = pd.to_datetime(end_value, errors="coerce", utc=True)
            if pd.notna(start_stamp) and pd.notna(end_stamp) and end_stamp >= start_stamp:
                timeline_items.append((label, start_stamp.tz_convert("Asia/Bangkok"), end_stamp.tz_convert("Asia/Bangkok"), color))
        add_timeline("Morning session (scheduled)", f"{gap_report.get('today')}T09:30:00+07:00", f"{gap_report.get('today')}T12:30:00+07:00", "#4f718c")
        add_timeline("Afternoon session (scheduled)", f"{gap_report.get('today')}T14:30:00+07:00", f"{gap_report.get('today')}T16:40:00+07:00", "#4f718c")
        cycle_windows = gap_report.get("runtime_evidence", {}).get("log", {}).get("collector_cycle_windows_bangkok", [])
        for index, item in enumerate(cycle_windows, 1):
            add_timeline(f"Collector cycle {index}", item.get("start_bangkok"), item.get("end_bangkok"), "#62b5a5")
        for dataset, label, color in (("raw_bbo", "Persisted raw BBO span", "#d3a461"), ("candles_1m", "Persisted 1m candle span", "#8da9ce")):
            details = today_data.get(dataset, {})
            add_timeline(label, details.get("today_first_bangkok"), details.get("today_last_bangkok"), color)
        if timeline_items:
            timeline = go.Figure()
            for label, start_stamp, end_stamp, color in timeline_items:
                timeline.add_trace(go.Bar(y=[label], x=[end_stamp - start_stamp], base=[start_stamp], orientation="h", marker_color=color, hovertemplate=f"{label}<br>%{{base|%H:%M}} – %{{x}}<extra></extra>", showlegend=False))
            timeline.update_layout(height=max(280, len(timeline_items) * 25), barmode="overlay", margin={"t": 10, "b": 25, "l": 10, "r": 10}, xaxis={"type": "date", "tickformat": "%H:%M", "title": "Asia/Bangkok"}, yaxis={"autorange": "reversed"})
            st.plotly_chart(timeline, width="stretch", config={"displaylogo": False, "scrollZoom": True})
            st.caption("Collector bars span SDK subscription timestamps to runner receipt of cycle diagnostics. Scheduled session bars are separate. BBO spans show event bounds only; quiet time alone is not classified as an outage.")
        gaps = gap_report.get("gap_records", [])
        if gaps:
            st.subheader("Gap inspector")
            st.dataframe(pd.DataFrame(gaps), hide_index=True, width="stretch", height=360, alt="Observed missing candle intervals and missing dataset evidence without invented outage causes")
        dataset_names = list(today_data)
        selected_dataset = st.selectbox("Data source inspector", dataset_names, key="gap_report_inspector_dataset") if dataset_names else None
        if selected_dataset:
            details = today_data[selected_dataset]
            symbol_map = details.get("today_symbol_coverage", {})
            if symbol_map:
                selected_symbol = st.selectbox("Symbol provenance", sorted(symbol_map), key="gap_report_inspector_symbol")
                st.json({"dataset": selected_dataset, "symbol": selected_symbol, "environment": "PRODUCTION", "source_file": details.get("path"), **symbol_map[selected_symbol], "backfill": gap_report.get("recovery", {}).get("backfill_evidence", {}) if selected_symbol == gap_report.get("recovery", {}).get("backfill_evidence", {}).get("symbol") else None})
            else:
                st.json({"dataset": selected_dataset, "environment": "PRODUCTION", "source_file": details.get("path"), "rows": details.get("today_rows", 0), "latest_timestamp": details.get("today_last_bangkok"), "source": "Settrade Open API", "quality_note": "BBO event silence does not prove a collector failure."})
    if smoke:
        st.subheader("Production API capability smoke")
        with st.expander("Verified capability and probe details"):
            st.json({key: value for key, value in smoke.items() if key != "quote_PTT"})
    coverage_path = paths.root / "reports" / "settrade_production_coverage_audit.json"
    try:
        coverage = json.loads(coverage_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        coverage = {}
    if coverage:
        st.subheader("Historical coverage and gaps by source")
        st.caption(f"Production rows: {coverage.get('production_persisted_market_rows', 0)} · Backfill: {coverage.get('backfill_status', 'UNKNOWN')}")
        dataset_inventory = coverage.get("persisted_settrade_dataset_inventory", {})
        inventory_rows = [{"environment": source_environment, "dataset": dataset, **details} for source_environment, datasets in dataset_inventory.items() for dataset, details in datasets.items()]
        if inventory_rows:
            st.dataframe(pd.DataFrame(inventory_rows), hide_index=True, width="stretch", alt="Persisted Settrade row counts, paths, symbols and timestamps by environment")
        if coverage.get("structural_integrity_findings"):
            st.subheader("Malformed, duplicate and timestamp integrity findings")
            with st.expander("Structural integrity details"):
                st.json(coverage["structural_integrity_findings"])
        inventory = coverage.get("missing_data_inventory", {})
        st.json({"missing_data_counts": inventory.get("counts", {}), "recoverability_policy": inventory.get("recoverability"), "weekdays_without_artifacts": coverage.get("weekdays_without_artifacts", []), "BBO_gap_recoverability": coverage.get("bbo_gap_recoverability"), "historical_1m_recoverability": coverage.get("production_sampled_historical_1m_recoverability")})
        days_by_dataset = coverage.get("day_by_day_dataset_coverage", {})
        if days_by_dataset:
            dataset_name = st.selectbox("Coverage dataset", list(days_by_dataset), key="production_coverage_dataset")
            day_map = days_by_dataset[dataset_name]
            if day_map:
                selected_day = st.selectbox("Trading day / evidence date", list(day_map), key="production_coverage_day")
                day_rows = []
                for source_environment, details in day_map[selected_day].items():
                    day_rows.append({"environment": source_environment, "provenance": details.get("provenance"), "rows/events": details.get("rows_or_events"), "symbols": details.get("observed_symbol_count"), "expected universe": details.get("expected_universe_size"), "session coverage estimate": details.get("approximate_session_coverage"), "first Bangkok": details.get("first_timestamp_bangkok"), "last Bangkok": details.get("last_timestamp_bangkok"), "reason": details.get("reason_code"), "missing symbols": ", ".join(details.get("missing_symbols", []))})
                st.dataframe(pd.DataFrame(day_rows), hide_index=True, width="stretch", alt="Per-environment collection coverage and missing symbols for the selected date")
                for source_environment, details in day_map[selected_day].items():
                    if details.get("missing_interval_estimates"):
                        st.json({f"{source_environment} missing interval estimates": details["missing_interval_estimates"]})
        capability = smoke.get("capability_matrix", {})
        if capability:
            st.subheader("API capability matrix")
            st.dataframe(pd.DataFrame([{"capability": key, "status": value} for key, value in capability.items()]), hide_index=True, width="stretch", alt="Verified and unverified Settrade API capabilities")
        st.subheader("Account, portfolio, orders and deals")
        st.info("READ ONLY — NO LIVE ORDER ACTIONS ENABLED. Account/private state: REQUIRES_ACCOUNT_NUMBER; this workspace has no account number configured, so account, holdings, orders and deals were not queried.")
    health = _cached_health(str(paths.root), str(paths.settrade_root))
    st.caption(f"Active repository: `{health['active_repo_path']}` · active Settrade data root: `{health['active_data_root']}` · free space on that filesystem: {health['filesystem_free_gib']} GiB")
    last_ok = health.get("latest_successful_cycle") or {}
    last_failure = health.get("latest_failed_cycle") or {}
    checkpoint_root = Path(health["active_data_root"]) / "checkpoints"
    def _checkpoint(name: str) -> dict:
        try:
            value = json.loads((checkpoint_root / name).read_text(encoding="utf-8"))
            return value if isinstance(value, dict) else {}
        except (OSError, json.JSONDecodeError):
            return {}
    production_collector = _checkpoint("candles.json")
    provenance = _checkpoint("provenance.json")
    try:
        scheduler = json.loads((paths.root / "reports" / "settrade_scheduler_status.json").read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        scheduler = {"state": "UNKNOWN", "detail": "Run scripts/check_settrade_task.ps1 to refresh."}
    cycle_start = pd.to_datetime(last_ok.get("start_time"), errors="coerce", utc=True)
    cutover_stamp = pd.to_datetime(cutover_utc, errors="coerce", utc=True)
    cycle_environment = "PRE_CUTOVER_SANDBOX_ERA" if not pd.isna(cycle_start) and not pd.isna(cutover_stamp) and cycle_start < cutover_stamp else "UNKNOWN"
    st.subheader("Collector state")
    st.json({"production_last_authentication": provenance.get("authenticated_at", "UNKNOWN"), "production_candle_checkpoint_status": production_collector.get("status", "UNKNOWN"), "production_candle_rows": production_collector.get("rows", production_collector.get("rows_written", 0)), "runner_lock": health.get("runner_lock_status", "UNKNOWN"), "latest_unversioned_daily_cycle": last_ok.get("end_time") or last_ok.get("start_time"), "daily_cycle_environment": cycle_environment, "last_success_status": last_ok.get("shutdown_status", "UNKNOWN"), "last_failure_status": last_failure.get("shutdown_status"), "health_timeout_seconds": os.environ.get("SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS", "60 (default)"), "scheduler": scheduler})
    freshness = pd.DataFrame([{"dataset": name, "earliest": value.get("earliest"), "latest genuine observation": value.get("latest"), "last trading date": value.get("last_trading_date"), "freshness": value.get("freshness_status"), "rows": value.get("rows"), "symbols": value.get("symbols"), "source/environment": ("PRODUCTION" if environment == "production" and name.startswith(("raw_bbo", "normalized_bbo", "candles_")) else "SANDBOX" if environment == "sandbox" and name.startswith(("raw_bbo", "normalized_bbo", "candles_")) else "UNKNOWN" if name.startswith(("raw_bbo", "normalized_bbo", "candles_")) else value.get("source", "Yahoo/exploratory")), "partial day": value.get("partial_day", False), "timezone": value.get("timezone")} for name, value in health["datasets"].items()])
    st.subheader("Live data freshness (stored observations)")
    st.dataframe(freshness, hide_index=True, width="stretch", alt="Latest timestamp, source and freshness for each persisted market-data dataset")
    partial = [name for name, value in health["datasets"].items() if value.get("partial_day")]
    if partial:
        st.warning(f"Partial current-day observations: {', '.join(partial)}. Latest timestamps reflect persisted rows only.")
    report = load_settrade_audit(paths)
    if not report:
        st.warning("The durable Settrade audit report is not available. Run scripts/audit_settrade_collection.py.")
        return
    readiness = report.get("readiness", {})
    cards = st.columns(4)
    cards[0].metric("Universe", readiness.get("universe", "UNKNOWN"))
    cards[1].metric("BBO", readiness.get("bbo", "UNKNOWN"))
    candle_readiness = readiness.get("candles", "UNKNOWN")
    if isinstance(candle_readiness, dict):
        candle_readiness = " / ".join(f"{timeframe} {status}" for timeframe, status in candle_readiness.items())
    cards[2].metric("Candles", str(candle_readiness))
    cards[3].metric("Normalized BBO rows", report.get("bbo", {}).get("rows", 0))
    runtime = pd.DataFrame(report.get("runtime", []))
    if not runtime.empty:
        st.subheader("Runner timeline")
        st.dataframe(runtime, hide_index=True, width="stretch")
    st.subheader("Rotation and universe")
    st.json({"universe": report.get("universe", {}), "rotation": report.get("rotation", {})})
    st.subheader("Pre-cutover sandbox BBO evidence")
    st.json({"status": report.get("bbo", {}).get("status"), "duplicate_keys": report.get("bbo", {}).get("duplicate_keys"), "days": report.get("bbo", {}).get("days", {})})
    st.subheader("Pre-cutover sandbox candle availability")
    st.json(report.get("candles", {}))
    st.warning("Current-session candlestick availability is external and symbol-specific in the observed pilot. Missing rows are reported as missing; no candle or BBO values are synthesized.")


@st.cache_data(show_spinner=False, ttl=60)
def _cached_health(project_root: str, data_root: str) -> dict:
    return collect_health(Path(project_root), Path(data_root))


def _settrade_data_quality(paths: DataPaths) -> None:
    st.markdown('<div class="hero"><div class="eyebrow">Source quality · no repair</div><h1>Settrade Data Quality</h1><p>Coverage, gaps, duplicates, and persistence checks derived from the actual pilot artifacts.</p></div>', unsafe_allow_html=True)
    report = load_settrade_audit(paths)
    if not report:
        st.info("No Settrade audit report is available yet.")
        return
    for timeframe, value in report.get("candles", {}).get("timeframes", {}).items():
        st.subheader(f"Candles · {timeframe}")
        rows = []
        for day, details in value.get("days", {}).items():
            rows.append({"trading_day": day, "status": details.get("status"), "observed_rows": details.get("rows", 0), "expected_intervals": details.get("expected_intervals", 0), "coverage_pct": details.get("coverage_pct", 0), "missing_intervals": details.get("missing_intervals", 0), "largest_gap_seconds": details.get("largest_gap_seconds", 0), "morning_rows": details.get("morning_rows", 0), "afternoon_rows": details.get("afternoon_rows", 0)})
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    bbo = report.get("bbo", {})
    st.subheader("BBO integrity")
    st.json({key: bbo.get(key) for key in ["status", "rows", "symbols", "duplicate_keys", "negative_price", "negative_volume"]})
    st.caption("Expected intervals are diagnostics only. True timestamps and source values remain unchanged; missing intervals are never filled.")


def _research_placeholders() -> None:
    st.header("Research Results")
    st.caption("Descriptive execution research from persisted Settrade pilot BBO. Read only; no strategy recommendations or order actions.")
    diagnostics_path = ROOT / "reports" / "settrade_execution_diagnostics.json"
    if diagnostics_path.exists():
        try:
            diagnostics = json.loads(diagnostics_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            diagnostics = {}
        if diagnostics:
            stats = diagnostics.get("statistics", {})
            st.subheader("Settrade execution diagnostics")
            st.caption(f"Genuine BBO snapshots: {diagnostics.get('complete_snapshot_count', 0):,}; date range {diagnostics.get('dataset_date_range', ['unknown', 'unknown'])[0]} to {diagnostics.get('dataset_date_range', ['unknown', 'unknown'])[1]}. Hypothetical visible-book sweeps are not actual fills.")
            if stats:
                cards = st.columns(4)
                cards[0].metric("Median spread", f"{stats['spread_ticks']['median']:.2f} ticks")
                cards[1].metric("Median spread", f"{stats['spread_bps']['median']:.1f} bps")
                cards[2].metric("Top bid depth", f"{stats['best_bid_depth']['median']:,.0f}")
                cards[3].metric("Top ask depth", f"{stats['best_ask_depth']['median']:,.0f}")
                by_group = diagnostics.get("by_group", [])
                time_rows = next((group["rows"] for group in by_group if group.get("group_by") == ["time_bucket"]), [])
                if time_rows:
                    time_frame = pd.DataFrame(time_rows).sort_values("time_bucket")
                    st.subheader("Spread and visible depth by time of day")
                    chart = go.Figure()
                    chart.add_trace(go.Scatter(x=time_frame["time_bucket"], y=time_frame["spread_ticks_median"], name="Median spread (ticks)", yaxis="y"))
                    chart.add_trace(go.Scatter(x=time_frame["time_bucket"], y=time_frame["best_bid_depth_median"], name="Median best bid depth", yaxis="y2"))
                    chart.add_trace(go.Scatter(x=time_frame["time_bucket"], y=time_frame["best_ask_depth_median"], name="Median best ask depth", yaxis="y2"))
                    chart.update_layout(height=380, yaxis={"title": "Spread (ticks)"}, yaxis2={"title": "Displayed shares", "overlaying": "y", "side": "right"}, margin=dict(l=10, r=10, t=20, b=10))
                    st.plotly_chart(chart, width="stretch")
                    st.dataframe(time_frame[["time_bucket", "snapshot_count", "spread_ticks_median", "spread_bps_median", "best_bid_depth_median", "best_ask_depth_median", "bid_depth_3_median", "ask_depth_3_median"]], hide_index=True, width="stretch")
                symbol_rows = next((group["rows"] for group in by_group if group.get("group_by") == ["symbol"]), [])
                if symbol_rows:
                    st.subheader("Symbol-level descriptive profiles")
                    st.caption("Profiles are not ranked and do not imply execution quality or trading preference.")
                    st.dataframe(pd.DataFrame(symbol_rows), hide_index=True, width="stretch")
                st.info(f"{diagnostics.get('model_v1_review_status', 'MODEL_V1_UNCHANGED_INSUFFICIENT_EVIDENCE')}. Snapshots cannot establish queue priority, hidden liquidity, latency, or actual IOC fill probability.")
    else:
        st.info("Settrade execution diagnostics have not been generated yet.")
    st.subheader("Other research areas")
    for name in ["Strategy Research", "Backtest", "Out-of-Sample", "Optimization", "Robustness", "Paper Trading"]:
        st.write(f"**{name}**: Not implemented")


def _settrade_explorer_legacy(paths: DataPaths) -> None:
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
        st.plotly_chart(chart, width="stretch")
        if "volume" in frame:
            st.plotly_chart(go.Figure(go.Bar(x=frame["timestamp_local"], y=frame["volume"], name="source volume")), width="stretch")
        st.dataframe(frame, hide_index=True, width="stretch")
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
        left.dataframe(bids[["level", "price", "volume"]], hide_index=True, width="stretch")
        right.subheader("Ask depth")
        right.dataframe(asks[["level", "price", "volume"]], hide_index=True, width="stretch")
        depth = pd.concat([bids.assign(cumulative=pd.to_numeric(bids["volume"], errors="coerce").fillna(0).cumsum()), asks.assign(cumulative=pd.to_numeric(asks["volume"], errors="coerce").fillna(0).cumsum())])
        st.plotly_chart(go.Figure(go.Bar(x=depth["level"], y=depth["cumulative"], marker_color=depth["side"], name="cumulative depth")), width="stretch")
        history = frame.pivot_table(index="timestamp_local", columns="side", values="price", aggfunc="first").sort_index()
        if not history.empty:
            history["midpoint"] = history[[column for column in ["bid", "ask"] if column in history]].mean(axis=1)
            st.plotly_chart(go.Figure([go.Scatter(x=history.index, y=history[column], name=column) for column in history.columns]), width="stretch")
        st.subheader("Execution inspection (diagnostic only)")
        st.info("MODEL_V1 remains unchanged. This view shows the observed book and does not submit orders or recompute production decisions.")
        return

    if data_type == "Price info":
        st.info("No persisted price_info stream is currently enabled. API quote snapshots remain separate from realtime price_info updates.")
        return
    st.info("TRUE_TRADE_STREAM is not exposed by the inspected settrade-v2==2.2.1 equity realtime surface; no trade chart is enabled and price_info is never relabeled as trades.")


def _candle_explorer(paths: DataPaths) -> None:
    """Render the read-only Settrade pilot explorer with audited chart inputs."""
    st.markdown(
        '<div class="hero"><div class="eyebrow">Pilot observability · read only</div>'
        '<h1>Settrade Data Explorer</h1><p>Inspect persisted candles and genuine bid/offer callbacks without altering source data or production decisions.</p></div>',
        unsafe_allow_html=True,
    )
    controls = st.columns([1, 1.3, 1.4, 0.8, 1.2, 1])
    default_environment = "PRODUCTION" if paths.settrade_root.name.lower() == "production" else "SANDBOX"
    environment = controls[0].selectbox("Environment", ["PRODUCTION", "SANDBOX"], index=0 if default_environment == "PRODUCTION" else 1)
    source_view = controls[1].selectbox("Source", ["Candles", "BBO / Depth"])
    selected_root = paths.root / "data" / "pilot" / "settrade"
    selected_root = selected_root / "production" if environment == "PRODUCTION" else selected_root
    selected_paths = replace(paths, settrade_root=selected_root)
    availability = settrade_availability(selected_paths, include_bbo=source_view != "Candles")
    datatype = "candles" if source_view == "Candles" else "bbo"
    symbols = sorted(availability.loc[availability["datatype"] == datatype, "symbol"].unique()) if not availability.empty else []
    if not symbols:
        st.warning(f"No {environment.lower()} {source_view.lower()} rows are available for this selection.")
        return
    symbol = controls[2].selectbox("Symbol", symbols)
    timeframe = controls[3].selectbox("Timeframe", ["1m", "5m", "15m"], disabled=source_view != "Candles")
    session_filter = controls[4].selectbox("Session filter", ["All timestamps", "Continuous sessions only", "Exclude midday break"], disabled=source_view != "Candles")
    refresh_clicked = controls[5].button("Refresh local view", help="Reread persisted files; this does not call the Settrade API.")
    if refresh_clicked:
        st.rerun()
    auto_refresh = st.toggle("Auto-refresh persisted view every 60 seconds", value=False, help="Refreshes only the local display. It does not authenticate, collect data, or call Settrade.")
    if auto_refresh:
        @st.fragment(run_every="60s")
        def _local_refresh_timer() -> None:
            now = time.monotonic()
            last = st.session_state.get("settrade_view_last_refresh_monotonic")
            if last is None:
                st.session_state["settrade_view_last_refresh_monotonic"] = now
            elif now - float(last) >= 59:
                st.session_state["settrade_view_last_refresh_monotonic"] = now
                st.rerun(scope="app")
            st.caption("Local view refresh is enabled; no external API request is made.")
        _local_refresh_timer()
    else:
        st.session_state.pop("settrade_view_last_refresh_monotonic", None)
    dates = pd.to_datetime(availability.loc[(availability["symbol"] == symbol) & (availability["datatype"] == datatype), "date"], errors="coerce").dropna()
    latest_date = dates.max().date() if not dates.empty else None
    scope = st.selectbox("View scope", ["Single trading day", "Multiple trading days"], help="Intraday views default to one observed Bangkok trading day so sparse coverage is not hidden.")
    if scope == "Single trading day":
        selected_dates = st.date_input("Trading day (Asia/Bangkok)", value=latest_date)
    else:
        default_dates = (dates.min().date(), dates.max().date()) if not dates.empty else None
        selected_dates = st.date_input("Trading-day range (Asia/Bangkok)", value=default_dates)
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start, end = selected_dates
    else:
        start = end = selected_dates

    data_type = source_view
    if data_type == "Candles":
        frame = load_settrade_candles(selected_paths, timeframe, symbol, start, end)
        frame = filter_settrade_candles(frame, session_filter)
        if frame.empty:
            st.info("No observed candles remain for this selection; no rows were filled.")
            return
        timeline = st.selectbox("Timeline", ["Compact trading timeline", "Real clock time"], help="Compact mode removes non-trading gaps from the display only; timestamps remain available in hover and the table.")
        compact = timeline == "Compact trading timeline"
        chart_frame = prepare_settrade_chart_frame(frame, compact=compact)
        quality = settrade_candle_quality(frame, timeframe, collector_start=_collector_start(selected_paths, start))
        cols = st.columns(8)
        cols[0].metric("Observed rows", quality["rows"])
        cols[1].metric("Expected", quality["expected_intervals"])
        cols[2].metric("Coverage", f'{quality["coverage_pct"]}%')
        cols[3].metric("Status", quality["status"])
        cols[4].metric("First", quality["first_local"].split("T")[-1][:5])
        cols[5].metric("Last", quality["last_local"].split("T")[-1][:5])
        cols[6].metric("Morning", quality["morning_rows"])
        cols[7].metric("Afternoon", quality["afternoon_rows"])
        if quality["collector_expected_intervals"] is not None:
            st.caption(f'Coverage since collector start ({quality["collector_start_local"]}): {quality["collector_observed_rows"]} observed / {quality["collector_expected_intervals"]} expected ({quality["coverage_since_collector_start_pct"]}%). Full-session coverage remains {quality["coverage_pct"]}%.')
        if quality["gaps_over_interval"] or quality["duplicates"] or quality["invalid_ohlc"]:
            st.warning("Quality diagnostics found sparse or structurally invalid observations. The explorer preserves them and does not interpolate or repair source rows.")
        else:
            st.success("Observed candle rows pass structural checks; source values are shown unchanged.")
        customdata = chart_frame[["hover_time"]].to_numpy()
        overlays = st.columns(3)
        show_sma = overlays[0].toggle("SMA 20 / 50", value=False, key="settrade_show_sma")
        show_vwap = overlays[1].toggle("Session VWAP", value=False, key="settrade_show_vwap")
        compare_symbols = ["None", *[item for item in symbols if item != symbol]]
        compare_symbol = overlays[2].selectbox("Compare symbol", compare_symbols, key="settrade_compare_symbol")
        chart = go.Figure(go.Candlestick(x=chart_frame["plot_x"], open=chart_frame["open"], high=chart_frame["high"], low=chart_frame["low"], close=chart_frame["close"], customdata=customdata, hovertemplate="%{customdata[0]}<br>O %{open}<br>H %{high}<br>L %{low}<br>C %{close}<extra>" + symbol + "</extra>", name=f"{symbol} {timeframe}"))
        if show_sma:
            for period, color in ((20, "#d9a75f"), (50, "#77a9d1")):
                average = chart_frame["close"].rolling(period, min_periods=period).mean()
                chart.add_trace(go.Scatter(x=chart_frame["plot_x"], y=average, mode="lines", name=f"SMA {period}", line={"color": color, "width": 1.2}, hovertemplate="%{customdata[0]}<br>SMA %{y:.3f}<extra></extra>", customdata=customdata))
        if show_vwap:
            if "volume" in chart_frame and pd.to_numeric(chart_frame["volume"], errors="coerce").gt(0).any():
                volume_values = pd.to_numeric(chart_frame["volume"], errors="coerce")
                typical = (chart_frame["high"] + chart_frame["low"] + chart_frame["close"]) / 3
                session_key = chart_frame["timestamp_local"].dt.date
                weighted = typical.mul(volume_values)
                vwap = weighted.groupby(session_key).cumsum().div(volume_values.groupby(session_key).cumsum().replace(0, float("nan")))
                chart.add_trace(go.Scatter(x=chart_frame["plot_x"], y=vwap, mode="lines", name="Session VWAP", line={"color": "#b49bd4", "width": 1.3}, customdata=customdata, hovertemplate="%{customdata[0]}<br>VWAP %{y:.3f}<extra></extra>"))
            else:
                st.info("VWAP is unavailable because this selection has no positive source volume.")
        if compare_symbol != "None":
            comparison = load_settrade_candles(selected_paths, timeframe, compare_symbol, start, end)
            comparison = filter_settrade_candles(comparison, session_filter)
            if not comparison.empty:
                base = comparison["close"].dropna().iloc[0]
                chart.add_trace(go.Scatter(x=comparison["timestamp_local"], y=comparison["close"] / base * chart_frame["close"].dropna().iloc[0], mode="lines", name=f"{compare_symbol} indexed", line={"color": "#8795a7", "width": 1.2}, hovertemplate="%{x}<br>Indexed close %{y:.3f}<extra>" + compare_symbol + "</extra>"))
        if compact:
            tick_frame = chart_frame.iloc[::max(1, len(chart_frame) // 8)]
            chart.update_xaxes(type="linear", tickvals=tick_frame["compact_x"], ticktext=tick_frame["timestamp_local"].dt.strftime("%d %b %H:%M"))
            for row in chart_frame[chart_frame["day_separator"]].iloc[1:].itertuples():
                chart.add_vline(x=row.compact_x - 0.5, line_dash="dot", line_color="#9fb5cc")
            for index in chart_frame.index[chart_frame["active_session_gap"]]:
                previous = chart_frame.loc[index - 1]
                current = chart_frame.loc[index]
                chart.add_vrect(x0=previous.compact_x, x1=current.compact_x, fillcolor="#f59e0b", opacity=0.12, line_width=0, annotation_text="active-session gap", annotation_position="top")
        chart.update_layout(height=480, xaxis_rangeslider_visible=False, title=f"{symbol} · {timeframe} · {'compact' if compact else 'Asia/Bangkok clock'}", margin=dict(l=10, r=10, t=45, b=10))
        st.plotly_chart(chart, width="stretch", config={"displaylogo": False, "scrollZoom": True, "modeBarButtonsToAdd": ["resetScale2d"]})
        if "volume" in chart_frame:
            volume_chart = go.Figure(go.Bar(x=chart_frame["plot_x"], y=chart_frame["volume"], customdata=customdata, hovertemplate="%{customdata[0]}<br>Volume %{y}<extra>" + symbol + "</extra>", name="source volume"))
            volume_chart.update_layout(height=220, title="Persisted source volume", margin=dict(l=10, r=10, t=35, b=10))
            st.plotly_chart(volume_chart, width="stretch")
        st.caption(f"Chart input rows: {len(chart_frame)} · source rows displayed: {len(frame)} · no resampling, gap filling, or BBO-derived candles.")
        display_columns = [column for column in ["timestamp", "timestamp_local", "symbol", "open", "high", "low", "close", "volume", "source_label"] if column in frame]
        st.dataframe(frame[display_columns], hide_index=True, width="stretch")
        with st.expander("Data quality"):
            st.json(quality)
        return

    if data_type == "BBO / Depth":
        frame = load_settrade_bbo(selected_paths, symbol, start, end)
        if frame.empty:
            st.info("No persisted BBO data for this selection.")
            return
        event_keys = [key for key in ["retrieved_at", "collector_session_id", "generation", "rotation_group"] if key in frame]
        events = frame[event_keys].drop_duplicates().reset_index(drop=True)
        choice = st.selectbox("BBO event", range(len(events)), format_func=lambda index: events.iloc[index]["retrieved_at"].isoformat())
        selected = events.iloc[choice]
        snapshot = frame
        for key in event_keys:
            snapshot = snapshot[snapshot[key] == selected[key]]
        bids = snapshot[snapshot["side"] == "bid"].sort_values("level")
        asks = snapshot[snapshot["side"] == "ask"].sort_values("level")
        bid_prices = pd.to_numeric(bids["price"], errors="coerce").dropna()
        ask_prices = pd.to_numeric(asks["price"], errors="coerce").dropna()
        best_bid = bid_prices.iloc[0] if not bid_prices.empty else None
        best_ask = ask_prices.iloc[0] if not ask_prices.empty else None
        midpoint = (best_bid + best_ask) / 2 if best_bid is not None and best_ask is not None else None
        metrics = st.columns(5)
        metrics[0].metric("Best bid", best_bid)
        metrics[1].metric("Best ask", best_ask)
        metrics[2].metric("Spread", best_ask - best_bid if midpoint is not None else None)
        metrics[3].metric("Midpoint", midpoint)
        metrics[4].metric("Levels", int(snapshot["level"].nunique()) if "level" in snapshot else 0)
        left, right = st.columns(2)
        left.subheader("Bid depth")
        left.dataframe(bids[["level", "price", "volume"]], hide_index=True, width="stretch")
        right.subheader("Ask depth")
        right.dataframe(asks[["level", "price", "volume"]], hide_index=True, width="stretch")
        history = frame.pivot_table(index="timestamp_local", columns="side", values="price", aggfunc="first").sort_index()
        if not history.empty:
            history["midpoint"] = history[[column for column in ["bid", "ask"] if column in history]].mean(axis=1)
            st.plotly_chart(go.Figure([go.Scatter(x=history.index, y=history[column], name=column) for column in history.columns]), width="stretch")
        st.info("Observed BBO only. This view is diagnostic and never submits orders or changes MODEL_V1.")
        return
    if data_type == "Price info":
        st.info("No persisted price_info stream is currently enabled. Quote snapshots remain separate from realtime price_info updates.")
        return
    st.info("TRUE_TRADE_STREAM is not exposed by the inspected settrade-v2==2.2.1 equity realtime surface; price_info is never relabeled as trades.")


def _order_book_explorer(paths: DataPaths) -> None:
    """Render genuine persisted BBO events as a separate research destination."""
    st.markdown('<div class="hero"><div class="eyebrow">Pilot observability · read only</div><h1>Order book explorer</h1><p>Inspect genuine Settrade bid/offer callbacks, depth snapshots, and event timing.</p></div>', unsafe_allow_html=True)
    availability = settrade_availability(paths)
    symbols = sorted(availability.loc[availability["datatype"] == "bbo", "symbol"].unique()) if not availability.empty else []
    if not symbols:
        st.warning("No normalized BBO pilot data is available yet.")
        return
    symbol = st.selectbox("Symbol", symbols)
    dates = pd.to_datetime(availability.loc[(availability["datatype"] == "bbo") & (availability["symbol"] == symbol), "date"], errors="coerce").dropna()
    selected_date = st.date_input("Trading day (Asia/Bangkok)", value=dates.max().date() if not dates.empty else None)
    frame = load_settrade_bbo(paths, symbol, selected_date, selected_date)
    if frame.empty:
        st.info("No persisted BBO events for this selection.")
        return
    event_keys = [key for key in ["retrieved_at", "collector_session_id", "generation", "rotation_group"] if key in frame]
    events = frame[event_keys].drop_duplicates().reset_index(drop=True)
    choice = st.selectbox("Snapshot event", range(len(events)), format_func=lambda index: events.iloc[index]["retrieved_at"].isoformat())
    selected = events.iloc[choice]
    snapshot = frame
    for key in event_keys:
        snapshot = snapshot[snapshot[key] == selected[key]]
    bids = snapshot[snapshot["side"] == "bid"].sort_values("level")
    asks = snapshot[snapshot["side"] == "ask"].sort_values("level")
    bid_prices = pd.to_numeric(bids["price"], errors="coerce").dropna()
    ask_prices = pd.to_numeric(asks["price"], errors="coerce").dropna()
    best_bid = bid_prices.iloc[0] if not bid_prices.empty else None
    best_ask = ask_prices.iloc[0] if not ask_prices.empty else None
    midpoint = (best_bid + best_ask) / 2 if best_bid is not None and best_ask is not None else None
    metrics = st.columns(5)
    metrics[0].metric("Best bid", best_bid)
    metrics[1].metric("Best ask", best_ask)
    metrics[2].metric("Spread", best_ask - best_bid if midpoint is not None else None)
    metrics[3].metric("Midpoint", midpoint)
    metrics[4].metric("Observed events", len(events))
    left, right = st.columns(2)
    left.subheader("Bid depth")
    left.dataframe(bids[["level", "price", "volume"]], hide_index=True, width="stretch")
    right.subheader("Ask depth")
    right.dataframe(asks[["level", "price", "volume"]], hide_index=True, width="stretch")
    history = frame.pivot_table(index="timestamp_local", columns="side", values="price", aggfunc="first").sort_index()
    if not history.empty:
        history["midpoint"] = history[[column for column in ["bid", "ask"] if column in history]].mean(axis=1)
        st.plotly_chart(go.Figure([go.Scatter(x=history.index, y=history[column], name=column) for column in history.columns]), width="stretch")
    st.caption(f"{len(frame)} genuine normalized BBO rows · selected event {selected['retrieved_at']} · no order actions available.")


def _official_tradesim_page() -> None:
    st.title("Official TradeSim Validation")
    st.info("**Research Backtest** explores historical data. **Official TradeSim** validates competition behavior using the official simulator and supplied ticks.")
    try:
        official = discover_official_repo()
        info = inspect_official(official)
        st.success(f"Official repo detected · Python {info.python_version} · commit {info.commit[:12]} · {'dirty' if info.dirty else 'clean'}")
        inventory = list_dates(official)
        dates = [d for item in inventory for d in item['dates']]
        st.write(f"Practice dates: {len(dates)} ({min(dates) if dates else 'unknown'} to {max(dates) if dates else 'unknown'})")
        st.dataframe(pd.DataFrame([{'File':x['file'],'Date':', '.join(x['dates']),'First tick':x['first_timestamp'],'Last tick':x['last_timestamp'],'Rows':x['rows'],'Symbols':len(x['symbols'])} for x in inventory]), hide_index=True, use_container_width=True)
    except BridgeError as exc:
        st.warning(str(exc))
        st.caption('Set KGI_OFFICIAL_REPO in the environment used to launch Streamlit. Runs are CLI-only; this page is read-only.')
        return
    history = ROOT/'artifacts'/'official_tradesim_runs'
    rows=[]
    for result_file in sorted(history.glob('*/normalized_result.json'), reverse=True) if history.exists() else []:
        try:
            result=json.loads(result_file.read_text(encoding='utf-8')); meta=result.get('metadata',{})
            rows.append({'Run':result.get('run_id'),'Strategy':result.get('strategy'),'Dates':', '.join(result.get('dates',[])),'Return':result.get('net_return'),'SET50 return':result.get('benchmark_return'),'Excess return':result.get('excess_return'),'Orders':result.get('order_count'),'Fills':result.get('fill_count'),'Errors':len(result.get('errors',[])),'Official commit':str(meta.get('official_git',{}).get('commit',''))[:12],'Raw artifacts':meta.get('raw_artifacts')})
        except (OSError,json.JSONDecodeError):
            continue
    st.subheader('Past official runs')
    if rows: st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    else: st.caption('No official TradeSim runs have been collected yet.')
    st.caption('Run simulations explicitly with scripts/run_official_tradesim.py. This UI does not start TradeSim.')


def _tradesim_results_page() -> None:
    st.title("OFFICIAL TRADESIM 0.2.6 · Results")
    st.info("Local archive and saved simulation evidence only. This page does not open the separate KGI submission repository or run simulations.")
    diagnostic = runtime_diagnostic(ROOT)
    archive = diagnostic.get("archive", {})
    cards = st.columns(3)
    cards[0].metric("Simulator", archive.get("version", "UNKNOWN"))
    cards[1].metric("ZIP integrity", archive.get("integrity", "UNKNOWN"))
    cards[2].metric("Runtime", "BLOCKED" if diagnostic.get("status") == "BLOCKED" else diagnostic.get("status", "UNKNOWN"))
    runtime_cards = st.columns(2)
    python_status = diagnostic.get("python", {}).get("status", "UNKNOWN")
    runtime_cards[0].metric("Python 3.13.0", "MISSING" if python_status == "MISSING_EXACT_VERSION" else diagnostic.get("python", {}).get("version") or python_status)
    runtime_cards[1].metric("Adapter", "WARNINGS" if diagnostic.get("adapter_status") == "SUPPORTED_WITH_WARNINGS" else diagnostic.get("adapter_status", "UNKNOWN"))
    st.caption(f"Readiness: {diagnostic.get('status', 'UNKNOWN')} · Python check: {python_status} · Adapter status: {diagnostic.get('adapter_status', 'UNKNOWN')}")
    st.caption(f"Archive SHA-256: {archive.get('sha256', 'UNKNOWN')} · extracted: {diagnostic.get('extracted_runtime', 'UNKNOWN')}")
    st.caption("The official runner requires exactly Python 3.13.0; it never substitutes another patch release.")
    comparison_path = ROOT / "reports" / "tradesim_version_comparison.json"
    try:
        comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        comparison = {"future_status": "NOT_AVAILABLE_YET"}
    st.info(f"0.2.6 version status: {comparison.get('version_statuses', {}).get('0.2.6', comparison.get('future_status', 'NOT_AVAILABLE_YET'))}")
    diff = comparison.get("archive_diff") or {}
    if diff:
        st.caption(f"Version review · changed files {len(diff.get('changed_files', []))} · added {len(diff.get('added_files', []))} · removed {len(diff.get('removed_files', []))} · requirements {diff.get('requirements', {}).get('status', 'UNKNOWN')}")
    try:
        inventory_path = ROOT / "reports" / "tradesim_026_practice_data_inventory.json"
        if inventory_path.is_file():
            inventory_report = json.loads(inventory_path.read_text(encoding="utf-8"))
            inventory = inventory_report["tick_inventory"]
        else:
            inventory = inventory_ticks(ROOT)
        st.dataframe(pd.DataFrame([{"file": item["file"], "date": ", ".join(item.get("dates", [])),
                                    "first tick": item.get("first_timestamp"), "last tick": item.get("last_timestamp"),
                                    "rows": item.get("rows"), "symbols": item.get("symbol_count"),
                                    "integrity": item.get("integrity")} for item in inventory["files"]]),
                     hide_index=True, width="stretch")
    except (OSError, ValueError, RuntimeError) as exc:
        st.warning(f"Local practice-data inventory unavailable: {exc}")
    official_inventory_path = ROOT / "reports" / "tradesim_official_daily_ticks_package.json"
    comparison_path = ROOT / "reports" / "tradesim_vs_settrade_data_comparison.json"
    try:
        official_inventory = json.loads(official_inventory_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        official_inventory = {}
    if official_inventory:
        st.subheader("Official Daily_Ticks data quality")
        official_ticks = official_inventory.get("official_ticks", {})
        official_history = official_inventory.get("official_history", {})
        identity = official_inventory.get("archive_identity", {})
        nested = identity.get("nested_archives", {})
        summary = st.columns(5)
        summary[0].metric("Tick dates", official_ticks.get("file_count", 0))
        summary[1].metric("Latest official tick", (official_ticks.get("dates") or [None])[-1] or "UNKNOWN")
        summary[2].metric("Tick rows", f"{official_ticks.get('total_rows', 0):,}")
        summary[3].metric("History files", official_history.get("file_count", 0))
        summary[4].metric("History rows", f"{official_history.get('total_rows', 0):,}")
        st.caption(f"Outer SHA-256: {identity.get('outer_sha256', 'UNKNOWN')} · tick ZIP SHA-256: {nested.get('tradeSim_ticks.zip', {}).get('sha256', 'UNKNOWN')} · history ZIP SHA-256: {nested.get('tradeSim_history.zip', {}).get('sha256', 'UNKNOWN')}")
        st.caption(f"Tick dates: {', '.join(official_ticks.get('dates', []))} · symbols: {len(official_ticks.get('symbols', []))} · source: TRADESIM_OFFICIAL_TICKS")
        history_files = official_history.get("files", [])
        history_by_interval = {}
        for item in history_files:
            parts = Path(item.get("path", "")).parts
            interval = "daily" if "daily_history" in parts else next((part for part in parts if part in {"1m", "3m", "5m", "10m", "15m", "30m", "60m", "120m", "240m"}), "other")
            if interval != "other":
                bucket = history_by_interval.setdefault(interval, {"files": 0, "rows": 0, "issues": 0})
                bucket["files"] += 1
                bucket["rows"] += int(item.get("rows", 0) or 0)
                bucket["issues"] += sum(int(item.get(key, 0) or 0) for key in ("invalid_timestamps", "invalid_numeric_values", "invalid_ohlc_rows", "malformed_rows", "duplicate_full_rows"))
        st.dataframe(pd.DataFrame([{"interval": key, **value} for key, value in sorted(history_by_interval.items())]), hide_index=True, width="stretch")
        if comparison_path.is_file():
            try:
                comparison = json.loads(comparison_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                comparison = {}
            if comparison:
                st.subheader("Official history vs Settrade production / pilot")
                comparison_rows = []
                for timeframe, environments in comparison.get("history_settrade_comparison", {}).items():
                    for environment, detail in environments.items():
                        counts = detail.get("counts", {})
                        comparison_rows.append({"timeframe": timeframe, "environment": environment,
                            "overlap dates": ", ".join(detail.get("overlap_dates", [])),
                            "symbols": len(detail.get("overlap_symbols", [])),
                            "matched timestamps": counts.get("matched_timestamp_rows", 0),
                            "exact OHLCV": counts.get("exact_ohlcv_matches", 0),
                            "different OHLCV": counts.get("divergent_rows", 0),
                            "Settrade only": counts.get("settrade_only_rows", 0),
                            "TradeSim only": counts.get("tradesim_only_rows", 0),
                            "exact match rate": detail.get("exact_match_rate_on_overlap")})
                if comparison_rows:
                    st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, width="stretch")
                st.caption("Source-only timestamps are compared only inside dates shared by both sources. Unobserved exchange-grid intervals remain UNKNOWN; neither source fills the other.")
    run_root = ROOT / "artifacts" / "official_tradesim_runs"
    rows = []
    run_details = []
    for result_file in sorted(run_root.glob("*/normalized_result.json"), reverse=True) if run_root.exists() else []:
        try:
            result = json.loads(result_file.read_text(encoding="utf-8"))
            run_details.append(result)
            rows.append({"run": result.get("run_id"), "strategy": result.get("strategy"),
                         "data source": result.get("metadata", {}).get("data_source", "UNKNOWN"),
                         "dates": ", ".join(result.get("dates", [])), "net return": result.get("net_return"),
                         "simulator": result.get("tradesim_version") or result.get("metadata", {}).get("tradesim_version", "UNKNOWN"), "orders": result.get("order_count"),
                         "fills": result.get("fill_count"), "partial orders": result.get("partial_fill_count"),
                         "fees": result.get("total_fees"), "ending NAV": result.get("ending_nav"),
                         "errors": len(result.get("errors", []))})
        except (OSError, json.JSONDecodeError):
            continue
    st.subheader("Retained local runs")
    if rows:
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
        comparison_groups = {}
        for result in run_details:
            key = (result.get("strategy_sha256"), tuple(result.get("dates", [])))
            comparison_groups.setdefault(key, {})[str(result.get("tradesim_version"))] = result
        comparable = [(key, group) for key, group in comparison_groups.items()
                      if "0.2.5" in group and "0.2.6" in group]
        if comparable:
            st.subheader("0.2.5 vs 0.2.6 · same strategy and dates")
            comparison_rows = []
            for _, group in comparable:
                for version in ("0.2.5", "0.2.6"):
                    result = group[version]
                    comparison_rows.append({"simulator": version, "strategy": result.get("strategy"),
                        "dates": ", ".join(result.get("dates", [])), "ending NAV": result.get("ending_nav"),
                        "return": result.get("net_return"), "orders": result.get("order_count"),
                        "fills": result.get("fill_count"), "partial orders": result.get("partial_fill_count"),
                        "canceled orders": len(result.get("canceled_orders", [])),
                        "fees": result.get("total_fees"), "round-trips": result.get("round_trips"),
                        "holdings": result.get("ending_positions")})
            st.dataframe(pd.DataFrame(comparison_rows), hide_index=True, width="stretch")
        run_ids = [row["run"] for row in rows]
        selected_run = st.selectbox("Inspect saved run", run_ids)
        selected_path = run_root / selected_run / "normalized_result.json"
        try:
            selected = json.loads(selected_path.read_text(encoding="utf-8"))
            cols = st.columns(5)
            cols[0].metric("Fills", selected.get("fill_count"))
            cols[1].metric("Partial fill orders", selected.get("partial_fill_count"))
            cols[2].metric("Total fees", selected.get("total_fees"))
            cols[3].metric("Ending NAV", selected.get("ending_nav"))
            cols[4].metric("Round-trips", selected.get("round_trips"))
            details = st.columns(4)
            details[0].metric("Cash", selected.get("end_cash"))
            details[1].metric("Average exposure", selected.get("average_portfolio_exposure"))
            details[2].metric("Win rate", selected.get("win_rate"))
            details[3].metric("Expected payoff", selected.get("expected_payoff"))
            left, right = st.columns(2)
            left.subheader("Orders and residuals")
            left.dataframe(pd.DataFrame(selected.get("orders", [])), hide_index=True, width="stretch")
            right.subheader("Fills")
            right.dataframe(pd.DataFrame(selected.get("fills", [])), hide_index=True, width="stretch")
            st.subheader("Ending holdings")
            st.dataframe(pd.DataFrame(selected.get("ending_positions", [])), hide_index=True, width="stretch")
            if selected.get("warnings"):
                st.warning(" · ".join(selected["warnings"]))
            st.caption(f"Raw artifact: {selected.get('metadata', {}).get('raw_artifacts', 'UNKNOWN')}")
        except (OSError, json.JSONDecodeError):
            st.warning("The selected normalized run artifact could not be read.")
    else:
        st.caption("No TradeSim runtime artifacts exist yet.")


def _gap_inspector(paths: DataPaths) -> None:
    st.title("Gap Inspector")
    report_path = paths.root / "reports" / "settrade_gap_recovery.json"
    try:
        report = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        st.warning("Gap recovery report is unavailable. Generate it with scripts/build_settrade_gap_recovery_report.py.")
        return
    gaps = pd.DataFrame(report.get("gap_records", []))
    severity = report.get("gap_severity", {})
    st.caption("Estimated gaps are separate per timeframe; event-driven BBO silence is not proof of missing trades or network failure.")
    for timeframe, rows in severity.get("top_20_by_timeframe", {}).items():
        st.subheader(f"Worst symbols · {timeframe}")
        st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
    st.metric("Temporal overlaps across candle timeframes", severity.get("overlap_count", 0))
    st.caption(severity.get("interpretation", "Cross-timeframe overlap evidence unavailable."))
    if not gaps.empty:
        controls = st.columns(3)
        datasets = sorted(gaps["dataset"].dropna().unique())
        dataset = controls[0].selectbox("Dataset", datasets, key="gap_inspector_dataset") if datasets else None
        symbols = sorted(gaps.loc[gaps["dataset"].eq(dataset), "symbol"].dropna().unique()) if dataset else []
        symbol = controls[1].selectbox("Symbol", ["All", *symbols], key="gap_inspector_symbol")
        classes = sorted(gaps["classification"].dropna().unique())
        evidence_class = controls[2].selectbox("Evidence class", ["All", *classes], key="gap_inspector_class")
        shown = gaps[gaps["dataset"].eq(dataset)] if dataset else gaps
        if symbol != "All":
            shown = shown[shown["symbol"].eq(symbol)]
        if evidence_class != "All":
            shown = shown[shown["classification"].eq(evidence_class)]
        st.dataframe(shown, hide_index=True, width="stretch", height=420)
    st.caption(f"Generated {report.get('generated_at', 'UNKNOWN')} · Orders placed: {report.get('orders_placed', 0)}")


def _production_api_status(paths: DataPaths) -> None:
    st.title("Production API Status")
    for label, filename in (("Readiness", "settrade_production_readiness.json"),
                            ("Latest smoke", "settrade_production_smoke.json"),
                            ("Capability matrix", "settrade_api_capability.json")):
        try:
            value = json.loads((paths.root / "reports" / filename).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            value = {}
        st.subheader(label)
        def redact(item):
            if isinstance(item, dict):
                return {key: ("[REDACTED]" if any(token in str(key).lower() for token in ("secret", "app_id", "pin", "token", "password")) else redact(val)) for key, val in item.items()}
            if isinstance(item, list):
                return [redact(val) for val in item]
            return item
        if value:
            if label == "Readiness":
                cards = st.columns(4)
                cards[0].metric("State", value.get("status", "UNKNOWN"))
                cards[1].metric("Environment", str(value.get("environment", "UNKNOWN")).upper())
                cards[2].metric("Authentication", value.get("authentication", "UNKNOWN"))
                cards[3].metric("Account reads", value.get("account_reads", value.get("account_private_state", "UNKNOWN")))
                if value.get("warnings"):
                    st.warning(" · ".join(value["warnings"]))
            capabilities = value.get("capability_matrix", value.get("capabilities", {}))
            if isinstance(capabilities, dict) and capabilities:
                st.dataframe(pd.DataFrame([{"capability": key, "status": str(item) if isinstance(item, (str, int, float, bool)) else "AVAILABLE / DETAILS"} for key, item in capabilities.items()]), hide_index=True, width="stretch")
            with st.expander(f"Full {label.lower()} evidence"):
                st.json(redact(value))
        else:
            st.info("No report is available yet.")
    st.info("Read-only market data status. Account-number private reads remain disabled until an account number is configured. No trading methods are invoked here.")


def _competition_cockpit(paths: DataPaths) -> None:
    """Central read-only overview; no broker, order, or simulation side effects."""
    from src.competition.state import CompetitionSnapshot, derive_competition_state

    readiness_path = paths.root / "reports" / "settrade_production_readiness.json"
    try:
        readiness = json.loads(readiness_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        readiness = {}
    report_path = paths.root / "reports" / "tradesim_026_final_readiness.json"
    try:
        tradesim = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        tradesim = {}

    state = derive_competition_state(CompetitionSnapshot(
        market_open=False,
        data_fresh=None,
        holdings=0,
        rules_confirmed=False,
        simulation_only=True,
    ))
    st.markdown('<div class="hero"><div class="eyebrow">Competition operations · read only</div><h1>Competition Cockpit</h1><p>Source health, official simulator readiness, market attention, and explicit unknowns.</p></div>', unsafe_allow_html=True)
    st.warning(f"State: {state.value} · no portfolio snapshot or active-session source was provided. This cockpit has no order controls.")
    cards = st.columns(5)
    cards[0].metric("Settrade readiness", readiness.get("status", "UNKNOWN"))
    cards[1].metric("Authentication", readiness.get("authentication", "UNKNOWN"))
    cards[2].metric("Account state", readiness.get("account_private_state", "UNKNOWN"))
    cards[3].metric("TradeSim", tradesim.get("organizer_designated_version", "0.2.6"))
    cards[4].metric("Real orders", "0")
    if readiness.get("warnings"):
        st.warning("Settrade warnings: " + "; ".join(readiness["warnings"]))
    st.caption("Competition portfolio, qualification, award readiness, and round-trip metrics remain UNKNOWN until a saved official TradeSim run exists. Current-market analytics below are descriptive, current-universe exploratory data, not a competition strategy signal.")
    candidate_path = paths.root / "reports" / "research_candidate_summary.json"
    try:
        candidate_report = json.loads(candidate_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        candidate_report = {}
    st.subheader("Research candidate funnel")
    if candidate_report:
        candidate_rows = []
        for candidate_id, details in candidate_report.get("candidates", {}).items():
            candidate_rows.append({
                "candidate": candidate_id,
                "evidence": details.get("evidence_classification", "UNKNOWN"),
                "net return": details.get("first_pass", {}).get("net_return"),
                "positive OOS folds": f"{details.get('walk_forward', {}).get('positive_folds', 0)}/{details.get('walk_forward', {}).get('fold_count', 0)}",
                "official TradeSim": "NOT RUN" if details.get("promotion_gate") != "ELIGIBLE" else "PENDING",
            })
        st.dataframe(pd.DataFrame(candidate_rows), hide_index=True, width="stretch")
        st.caption(f"Promotion: {candidate_report.get('promotion_summary', 'UNKNOWN')} · engine: {candidate_report.get('engine', 'UNKNOWN')} · run: {candidate_report.get('run_id', 'UNKNOWN')}")
        st.info("Candle-only research selectors are exploratory candidates. They are not a selected competition strategy, and the cockpit has no order controls.")
    else:
        st.info("No candidate-discovery report is available yet.")
    weekend_path = paths.root / "reports" / "weekend_data_maintenance.json"
    try:
        weekend = json.loads(weekend_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        weekend = {}
    st.subheader("Weekend maintenance")
    if weekend:
        audited = weekend.get("audited_week", {})
        st.caption(f"Audited {audited.get('start')} to {audited.get('end')} · trading dates: {', '.join(audited.get('trading_dates', []))} · official TradeSim history through {max(weekend.get('official_tradesim', {}).get('history', {}).get('dates', ['unknown']))}")
        coverage = audited.get("coverage", {})
        st.dataframe(pd.DataFrame([{"date": date, **sources} for date, sources in coverage.items()]), hide_index=True, width="stretch")
        st.caption("Gap and source-coverage warnings")
        st.write(f"Backfills this maintenance: {weekend.get('gaps', {}).get('backfills_appended_this_maintenance', 0)} · official archive state: {weekend.get('official_tradesim', {}).get('manifest_status', 'UNKNOWN')} · no data merged across sources")
        st.dataframe(pd.DataFrame([{"dataset": name, "status": status} for name, status in weekend.get("data_quality_scorecard", {}).items()]), hide_index=True, width="stretch")
    else:
        st.info("Weekend maintenance report is not available yet.")
    round2_path = paths.root / "reports" / "research_round2_summary.json"
    try:
        round2 = json.loads(round2_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        round2 = {}
    st.subheader("Research Round 2 · signal diagnostic only")
    if round2:
        signals = round2.get("signals", {})
        st.caption(f"{round2.get('hypothesis_id')} · {signals.get('sample_size', 0)} signals across {signals.get('unique_symbols', 0)} symbols · signal gate: {round2.get('gate', {}).get('status', 'UNKNOWN')}")
        horizon_rows = [{"horizon": name, "n": metric.get("sample_size"), "mean": metric.get("mean"), "median": metric.get("median"), "hit rate": metric.get("hit_rate"), "95% CI": metric.get("approx_95pct_mean_ci")} for name, metric in round2.get("forward_returns", {}).items()]
        st.dataframe(pd.DataFrame(horizon_rows), hide_index=True, width="stretch")
        stage1 = round2.get("stage1", {})
        if isinstance(stage1, dict):
            st.write(f"Portfolio stage: {stage1.get('stage1_gate', 'UNKNOWN')} · gross {stage1.get('gross_return')} · net {stage1.get('net_return')} · turnover {stage1.get('turnover')}× · max DD {stage1.get('maximum_drawdown')}")
        st.warning(f"{round2.get('promotion_result', 'NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE')} · no strategy selected · no order controls")
    else:
        st.info("Round 2 report is not available yet.")
    render_market_overview(paths.root)


paths = discover_paths()
constituents = load_constituents(paths)
audit = load_audit(paths)
acquisition = load_acquisition(paths)
metadata = load_metadata(paths)
if st.sidebar.button("Refresh data"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.markdown("### Research")
page = st.sidebar.selectbox("Workspace", [
    "Competition Cockpit", "Market Overview", "Multi-Stock Trends", "Correlation Lab", "Market Breadth", "Stock Detail",
    "Overview", "Historical Data Explorer", "Historical SET50 Universe", "Market Data Explorer",
    "Candle Explorer", "Order Book Explorer", "Gap Inspector", "Collection Health", "Production API Status", "Data Quality", "Official TradeSim Validation", "TradeSim Results", "Research Results",
], index=6, label_visibility="collapsed", key="workspace_navigation")
st.sidebar.caption("Source data is read-only")
if metadata:
    st.sidebar.caption(f"Acquisition: {metadata.get('acquisition_timestamp', 'unknown')}")
if page == "Competition Cockpit":
    _competition_cockpit(paths)
elif page == "Market Overview":
    render_market_overview(paths.root)
elif page == "Multi-Stock Trends":
    render_trends(paths.root)
elif page == "Correlation Lab":
    render_correlation(paths.root)
elif page == "Market Breadth":
    render_breadth(paths.root)
elif page == "Stock Detail":
    render_detail(paths.root)
elif page == "Historical Data Explorer":
    render_source_inventory(paths.root)
elif page == "Overview":
    _overview(paths, constituents, audit, acquisition)
elif page == "Historical SET50 Universe":
    _universe(constituents, audit)
elif page == "Market Data Explorer":
    _market_explorer(paths, audit)
elif page == "Candle Explorer":
    _candle_explorer(paths)
elif page == "Order Book Explorer":
    _order_book_explorer(paths)
elif page == "Gap Inspector":
    _gap_inspector(paths)
elif page == "Collection Health":
    _collection_health(paths)
elif page == "Production API Status":
    _production_api_status(paths)
elif page == "Data Quality":
    _settrade_data_quality(paths)
elif page == "Official TradeSim Validation":
    _tradesim_results_page()
elif page == "TradeSim Results":
    _tradesim_results_page()
else:
    _research_placeholders()

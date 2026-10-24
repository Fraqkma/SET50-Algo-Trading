from __future__ import annotations

from pathlib import Path

import pandas as pd

from ui.data_catalog import (
    DataPaths,
    filter_settrade_candles,
    load_settrade_bbo,
    load_settrade_audit,
    load_settrade_candles,
    prepare_settrade_chart_frame,
    settrade_availability,
    settrade_candle_quality,
)


def _paths(root: Path) -> DataPaths:
    return DataPaths(root, root / "constituents.csv", root / "audit.csv", root / "acquisition.csv", root / "metadata.json", root / "data" / "pilot" / "settrade", ())


def test_settrade_catalog_loads_local_candles_and_availability(tmp_path: Path) -> None:
    root = tmp_path
    candle_path = root / "data" / "pilot" / "settrade" / "normalized" / "bars_1m" / "data.csv"
    candle_path.parent.mkdir(parents=True)
    pd.DataFrame([{"timestamp": "2026-09-21T03:00:00+00:00", "symbol": "PTT", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100}]).to_csv(candle_path, index=False)
    paths = _paths(root)
    frame = load_settrade_candles(paths, "1m", "PTT")
    assert len(frame) == 1
    assert frame.iloc[0]["source_label"] == "SETTRADE_API_CANDLE"
    index = settrade_availability(paths)
    assert index.iloc[0]["date"] == "2026-09-21"


def test_settrade_catalog_keeps_bbo_event_rows_separate(tmp_path: Path) -> None:
    root = tmp_path
    bbo_path = root / "data" / "pilot" / "settrade" / "normalized" / "bid_offer" / "data.csv"
    bbo_path.parent.mkdir(parents=True)
    rows = [{"retrieved_at": "2026-09-21T03:00:00+00:00", "symbol": "PTT", "side": "bid", "level": 1, "price": 10, "volume": 100, "collector_session_id": "s", "generation": 0, "rotation_group": 0}]
    pd.DataFrame(rows).to_csv(bbo_path, index=False)
    frame = load_settrade_bbo(_paths(root), "PTT")
    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "PTT"
    assert settrade_availability(_paths(root)).iloc[0]["datatype"] == "bbo"


def _candle_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2026-09-21T02:30:00+00:00", "symbol": "PTT", "open": 10, "high": 11, "low": 9, "close": 10.5, "volume": 100},
            {"timestamp": "2026-09-21T02:31:00+00:00", "symbol": "PTT", "open": 10.5, "high": 12, "low": 10, "close": 11, "volume": 120},
            {"timestamp": "2026-09-21T07:31:00+00:00", "symbol": "PTT", "open": 11, "high": 12, "low": 10.5, "close": 11.5, "volume": 140},
            {"timestamp": "2026-09-22T02:30:00+00:00", "symbol": "PTT", "open": 11.5, "high": 12, "low": 11, "close": 11.8, "volume": 90},
        ]
    ).assign(
        timestamp=lambda frame: pd.to_datetime(frame["timestamp"], utc=True),
        timestamp_local=lambda frame: pd.to_datetime(frame["timestamp"], utc=True).dt.tz_convert("Asia/Bangkok"),
        source_label="SETTRADE_API_CANDLE",
    )


def test_compact_chart_preserves_rows_and_compresses_non_trading_gaps() -> None:
    source = _candle_frame()
    compact = prepare_settrade_chart_frame(source, compact=True)
    clock = prepare_settrade_chart_frame(source, compact=False)
    assert len(compact) == len(source)
    assert compact["open"].tolist() == source["open"].tolist()
    assert compact["plot_x"].tolist() == compact["compact_x"].tolist()
    assert clock["plot_x"].tolist() == clock["timestamp_local"].tolist()
    assert compact.loc[2, "compact_x"] - compact.loc[1, "compact_x"] == 180
    assert compact.loc[3, "compact_x"] > compact.loc[2, "compact_x"]
    assert int(compact["day_separator"].sum()) == 2
    assert bool(compact.loc[3, "active_session_gap"]) is False


def test_candle_quality_reports_sparse_gaps_without_filling() -> None:
    source = _candle_frame()
    filtered = filter_settrade_candles(source, "Exclude midday break")
    report = settrade_candle_quality(filtered, "1m")
    assert len(filtered) == 4
    assert report["rows"] == 4
    assert report["gaps_over_interval"] == 0
    assert report["missing_intervals_estimate"] == 0
    assert report["invalid_ohlc"] == 0
    assert report["missing_values"]["volume"] == 0


def test_quality_distinguishes_full_session_from_late_sparse_data() -> None:
    source = _candle_frame()
    report = settrade_candle_quality(source.iloc[[0, 1]], "1m")
    assert report["expected_intervals"] == 330
    assert report["coverage_pct"] < 1
    assert report["status"] == "SPARSE"
    assert report["morning_rows"] == 2
    assert report["afternoon_rows"] == 0


def test_quality_expected_intervals_scale_with_observed_symbols() -> None:
    source = pd.concat([_candle_frame().iloc[:2].assign(symbol="PTT"), _candle_frame().iloc[:2].assign(symbol="ADVANC")], ignore_index=True)
    report = settrade_candle_quality(source, "1m")
    assert report["symbols"] == 2
    assert report["expected_intervals"] == 660
    assert report["rows"] == 4


def test_settrade_audit_report_is_a_distinct_loader(tmp_path: Path) -> None:
    report_path = tmp_path / "reports" / "settrade_collection_audit.json"
    report_path.parent.mkdir(parents=True)
    report_path.write_text('{"readiness": {"bbo": "READY_FOR_EXPLORATORY_RESEARCH"}}', encoding="utf-8")
    loaded = load_settrade_audit(_paths(tmp_path))
    assert loaded["readiness"]["bbo"] == "READY_FOR_EXPLORATORY_RESEARCH"


def test_quality_reports_coverage_since_actual_collector_start() -> None:
    report = settrade_candle_quality(_candle_frame().iloc[:3], "1m", collector_start="2026-09-21T09:45:00+07:00")
    assert report["expected_intervals"] == 330
    assert report["collector_expected_intervals"] == 315
    assert report["collector_observed_rows"] == 1
    assert report["coverage_since_collector_start_pct"] == round(100 / 315, 2)


def test_quality_classifies_prior_day_rows_as_stale() -> None:
    report = settrade_candle_quality(_candle_frame().iloc[:2], "1m", expected_session_date="2026-09-23")
    assert report["status"] == "STALE"


def test_compact_timeline_keeps_active_session_gap_visible() -> None:
    source = _candle_frame().iloc[[0, 2]].copy()
    compact = prepare_settrade_chart_frame(source, compact=True)
    assert compact.loc[1, "compact_x"] - compact.loc[0, "compact_x"] == 181
    assert bool(compact.loc[1, "active_session_gap"]) is False
    active = _candle_frame().iloc[[0, 1]].copy()
    active.loc[1, "timestamp"] = pd.Timestamp("2026-09-21T02:41:00+00:00")
    active.loc[1, "timestamp_local"] = active.loc[1, "timestamp"].tz_convert("Asia/Bangkok")
    compact_active = prepare_settrade_chart_frame(active, compact=True)
    assert compact_active.loc[1, "compact_x"] - compact_active.loc[0, "compact_x"] == 11
    assert bool(compact_active.loc[1, "active_session_gap"]) is True


def test_candle_quality_flags_invalid_ohlc_and_duplicate_source_rows() -> None:
    source = _candle_frame().iloc[[2, 0, 0]].copy()
    source.loc[source.index[0], "high"] = 8
    report = settrade_candle_quality(source, "1m")
    assert report["duplicates"] == 1
    assert report["invalid_ohlc"] == 1
    assert report["rows"] == 3

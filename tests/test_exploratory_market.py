from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from src.data.exploratory_market import (
    build_exploratory_view,
    breadth_summary,
    daily_returns,
    normalize_closes,
    return_correlation,
    rolling_pair_correlation,
)
from ui.market_research import date_window, display_universe, series_for_mode, split_universe


def _write_bars(path: Path, rows: list[tuple[str, float]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame([
        {"Date": d, "Open": p, "High": p + 1, "Low": p - 1, "Close": p, "Volume": 100}
        for d, p in rows
    ]).to_csv(path, index=False)


def test_derived_view_provenance_precedence_and_chronology(tmp_path: Path) -> None:
    _write_bars(tmp_path / "data/pilot/historical_daily/AAA_2010_2026.csv", [("2020-01-01", 10), ("2020-01-03", 12)])
    _write_bars(tmp_path / "data/raw/market_data/AAA_BK.csv", [("2020-01-03", 12), ("2020-01-06", 13)])
    (tmp_path / "data/processed").mkdir(parents=True)
    pd.DataFrame([{"set_symbol": "AAA", "approval_status": "APPROVED", "approved_from": "2020-01-03", "approved_to": "2020-01-06"}]).to_csv(
        tmp_path / "data/processed/approved_market_data_manifest.csv", index=False
    )
    bars, conflicts = build_exploratory_view(tmp_path)
    assert bars["Date"].is_monotonic_increasing
    assert bars["Close"].tolist() == [10, 12, 13]
    assert bars["source_type"].tolist() == ["yahoo_staging", "approved_yahoo", "approved_yahoo"]
    assert bars["approval_scope"].tolist() == ["exploratory_unapproved", "within_manifest", "within_manifest"]
    assert len(conflicts) == 0


def test_conflicting_symbol_date_is_reported_and_excluded(tmp_path: Path) -> None:
    _write_bars(tmp_path / "data/raw/market_data/AAA_BK.csv", [("2020-01-01", 10), ("2020-01-02", 12)])
    _write_bars(tmp_path / "data/pilot/historical_daily/AAA_2010_2026.csv", [("2020-01-02", 99), ("2020-01-03", 13)])
    bars, conflicts = build_exploratory_view(tmp_path)
    assert bars["Date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-01", "2020-01-03"]
    assert len(conflicts) == 1
    assert conflicts.iloc[0]["decision"] == "excluded_conflicting_date"


def test_availability_and_depth_staging_sources_extend_history_with_provenance(tmp_path: Path) -> None:
    _write_bars(tmp_path / "data/pilot/historical_daily/AAA_2010_2026.csv", [("2020-01-01", 10)])
    _write_bars(tmp_path / "data/pilot/historical_set50_availability/AAA_BK.csv", [("2020-01-02", 11)])
    _write_bars(tmp_path / "data/pilot/historical_depth_experiment/AAA_BK.csv", [("2020-01-03", 12)])
    bars, conflicts = build_exploratory_view(tmp_path)
    assert bars["Date"].dt.strftime("%Y-%m-%d").tolist() == ["2020-01-01", "2020-01-02", "2020-01-03"]
    assert bars["source_type"].tolist() == ["yahoo_staging", "yahoo_historical_availability_staging", "yahoo_historical_depth_staging"]
    assert conflicts.empty


def test_conflicting_duplicate_rows_within_file_are_not_silently_chosen(tmp_path: Path) -> None:
    _write_bars(tmp_path / "data/pilot/historical_daily/AAA_2010_2026.csv", [("2020-01-01", 10), ("2020-01-01", 11)])
    bars, conflicts = build_exploratory_view(tmp_path)
    assert bars.empty
    assert len(conflicts) == 1


def test_invalid_ohlc_is_flagged_without_changing_observed_close(tmp_path: Path) -> None:
    path = tmp_path / "data/pilot/historical_daily/AAA_2010_2026.csv"
    _write_bars(path, [("2020-01-01", 10)])
    frame = pd.read_csv(path)
    frame.loc[0, "High"] = 9
    frame.to_csv(path, index=False)
    bars, _ = build_exploratory_view(tmp_path)
    assert bars.iloc[0]["Close"] == 10
    assert bars.iloc[0]["ohlc_status"] == "INVALID"


def test_normalization_and_modes_keep_unequal_histories_missing() -> None:
    dates = pd.date_range("2025-01-01", periods=3)
    closes = pd.DataFrame({"AAA": [10.0, 11.0, 12.0], "BBB": [np.nan, 50.0, 45.0]}, index=dates)
    normalized = normalize_closes(closes)
    assert normalized.loc[dates[0], "AAA"] == 100
    assert normalized.loc[dates[1], "BBB"] == 100
    assert pd.isna(normalized.loc[dates[0], "BBB"])
    bars = closes.rename_axis("Date").stack().rename("Close").reset_index().rename(columns={"level_1": "symbol"})
    for column, value in (("Open", 1), ("High", 100), ("Low", 1), ("Volume", 1), ("source_type", "test"), ("source_file", "x"), ("approval_scope", "exploratory")):
        bars[column] = value
    assert series_for_mode(bars, ["AAA", "BBB"], "Normalized performance").loc[dates[1], "BBB"] == 100


def test_daily_returns_and_correlations_align_without_fill() -> None:
    frame = pd.DataFrame([
        ("AAA", "2025-01-01", 10), ("AAA", "2025-01-02", 11), ("AAA", "2025-01-04", 12),
        ("BBB", "2025-01-01", 20), ("BBB", "2025-01-02", 22), ("BBB", "2025-01-03", 24), ("BBB", "2025-01-04", 26),
        ("DDD", "2025-01-01", 30), ("DDD", "2025-01-02", 33), ("DDD", "2025-01-03", 36), ("DDD", "2025-01-04", 39),
        ("CCC", "2025-01-01", 10), ("CCC", "2025-01-02", 11), ("CCC", "2025-01-03", 12.21), ("CCC", "2025-01-04", 13.73625),
    ], columns=["symbol", "Date", "Close"])
    frame["Date"] = pd.to_datetime(frame["Date"])
    for c in ("Open", "High", "Low", "Volume", "source_type", "source_file", "approval_scope"):
        frame[c] = 1
    returns = daily_returns(frame)
    assert returns.loc[returns["symbol"].eq("AAA"), "return"].iloc[0] != returns.loc[returns["symbol"].eq("AAA"), "return"].iloc[0]
    wide = returns.pivot(index="Date", columns="symbol", values="return")
    corr, counts = return_correlation(wide, min_overlap=3)
    assert counts.loc["AAA", "BBB"] == 2
    assert pd.isna(corr.loc["AAA", "BBB"])
    assert corr.loc["BBB", "CCC"] < 0
    assert corr.loc["BBB", "DDD"] == 1


def test_rolling_correlation_requires_full_aligned_window() -> None:
    index = pd.date_range("2025-01-01", periods=5)
    a = pd.Series([1, 2, 3, 4, 5], index=index, dtype=float)
    b = pd.Series([5, 4, 3, 2, 1], index=index, dtype=float)
    rolling = rolling_pair_correlation(a, b, window=3)
    assert rolling.iloc[:2].isna().all()
    assert np.allclose(rolling.iloc[2:], -1)


def test_breadth_denominators_only_count_sufficient_history() -> None:
    rows = []
    for symbol, count, gain in (("AAA", 55, 0.01), ("BBB", 10, -0.01)):
        for i, date_value in enumerate(pd.date_range("2025-01-01", periods=count)):
            price = 10 * (1 + gain) ** i
            rows.append({"symbol": symbol, "Date": date_value, "Close": price, "Volume": 100})
    bars = pd.DataFrame(rows)
    breadth, metrics = breadth_summary(bars, ["AAA", "BBB", "MISSING"])
    assert breadth["above_sma20"] == (1, 1)
    assert breadth["above_sma50"] == (1, 1)
    assert len(metrics) == 2


def test_current_universe_and_25_plus_25_navigation() -> None:
    symbols = display_universe(Path(__file__).parents[1])
    assert len(symbols) == 50
    assert len(split_universe(symbols, "Stocks 1–25")) == 25
    assert len(split_universe(symbols, "Stocks 26–50")) == 25
    assert split_universe(symbols, "Stocks 1–25")[-1] != split_universe(symbols, "Stocks 26–50")[0]


def test_max_history_date_window_is_actual_source_bounds() -> None:
    bars = pd.DataFrame({"Date": pd.to_datetime(["2018-01-01", "2026-09-04"])})
    start, end = date_window(bars, "Max available")
    assert start == pd.Timestamp("2018-01-01")
    assert end == pd.Timestamp("2026-09-04")

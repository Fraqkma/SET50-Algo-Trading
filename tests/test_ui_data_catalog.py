from pathlib import Path

import pandas as pd

from ui.data_catalog import discover_paths, quality_summary


def test_discover_paths_prefers_metadata_raw_directory(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    (reports / "data_acquisition_metadata.json").write_text('{"raw_directory": "data/raw/market_data"}', encoding="utf-8")
    paths = discover_paths(tmp_path)
    assert paths.raw_directories[0] == tmp_path / "data" / "raw" / "market_data"
    assert paths.constituents == tmp_path / "data" / "processed" / "constituents" / "historical_set50.csv"


def test_quality_summary_reports_missing_values_duplicates_and_ohlc() -> None:
    frame = pd.DataFrame({"Date": ["2026-01-01", "2026-01-01", "2026-01-20"], "Open": [10.0, 10.0, 10.0], "High": [9.0, 11.0, 11.0], "Low": [10.0, 9.0, 9.0], "Close": [10.0, 10.0, 10.0], "Volume": [100, None, 100]})
    report = quality_summary(frame, "BANPU")
    assert report["duplicate_dates"] == 1
    assert report["missing_values"]["Volume"] == 1
    assert report["invalid_relationships"] == 1
    assert report["missing_dates"]
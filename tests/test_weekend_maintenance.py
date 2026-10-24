from __future__ import annotations

import zipfile
from pathlib import Path

from scripts.build_weekend_maintenance_report import (
    _archive,
    _name,
    classify_gap,
    manifest_delta,
    trading_dates_for_week,
)


def test_weekly_calendar_excludes_sourced_holiday_and_weekend() -> None:
    dates = ["2026-10-19", "2026-10-20", "2026-10-21", "2026-10-22", "2026-10-23", "2026-10-24"]
    assert trading_dates_for_week(dates, {"2026-10-23"}) == dates[:4]


def test_weekly_gap_classes_preserve_both_source_presence() -> None:
    assert classify_gap(True, True, True) == "SOURCE_SEMANTIC_DIFFERENCE"
    assert classify_gap(True, False) == "TRADESIM_ONLY_GAP"
    assert classify_gap(False, True) == "SETTRADE_ONLY_GAP"
    assert classify_gap(False, False) == "BOTH_SOURCES_GAP"


def test_manifest_delta_reports_added_removed_changed_and_unchanged() -> None:
    result = manifest_delta({"a": "1", "b": "2", "c": "3"}, {"a": "1", "b": "changed", "d": "4"})
    assert result == {"added": ["d"], "removed": ["c"], "changed": ["b"], "unchanged": ["a"]}


def test_archive_manifest_names_normalize_windows_paths() -> None:
    assert _name(r"D:\data\tradesim\tradeSim_history.zip") == "tradeSim_history.zip"


def test_official_archive_inventory_is_read_only(tmp_path: Path) -> None:
    archive_path = tmp_path / "tradeSim_history.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("marketInfo/daily_history/PTT.csv", "Date,Close\n2026-10-21,10\n")
    before = archive_path.read_bytes()
    result = _archive(archive_path)
    assert result["zip_integrity"] == "PASS"
    assert archive_path.read_bytes() == before

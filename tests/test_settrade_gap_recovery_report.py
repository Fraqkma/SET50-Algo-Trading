from datetime import datetime
from zoneinfo import ZoneInfo

from scripts.build_settrade_gap_recovery_report import gap_severity, session_for


LOCAL = ZoneInfo("Asia/Bangkok")


def test_gap_report_uses_session_boundaries() -> None:
    assert session_for(datetime(2026, 10, 21, 9, 29, tzinfo=LOCAL)) is None
    assert session_for(datetime(2026, 10, 21, 9, 30, tzinfo=LOCAL)) == "morning"
    assert session_for(datetime(2026, 10, 21, 12, 30, tzinfo=LOCAL)) is None
    assert session_for(datetime(2026, 10, 21, 13, 57, tzinfo=LOCAL)) is None
    assert session_for(datetime(2026, 10, 21, 14, 30, tzinfo=LOCAL)) == "afternoon"
    assert session_for(datetime(2026, 10, 21, 16, 40, tzinfo=LOCAL)) == "pre_close"
    assert session_for(datetime(2026, 10, 21, 17, 0, tzinfo=LOCAL)) is None


def test_gap_severity_splits_timeframes_and_reports_overlaps_without_adding_them():
    gaps = [
        {"date": "2026-10-21", "dataset": "candles_1m", "environment": "PRODUCTION", "symbol": "PTT",
         "gap_start": "2026-10-21T10:00:00+07:00", "gap_end": "2026-10-21T10:05:00+07:00",
         "duration_seconds": 300, "missing_intervals_estimate": 4},
        {"date": "2026-10-21", "dataset": "candles_5m", "environment": "PRODUCTION", "symbol": "PTT",
         "gap_start": "2026-10-21T10:00:00+07:00", "gap_end": "2026-10-21T10:10:00+07:00",
         "duration_seconds": 600, "missing_intervals_estimate": 1},
    ]
    result = gap_severity(gaps)
    assert result["top_20_by_timeframe"]["1m"][0]["symbol"] == "PTT"
    assert result["top_20_by_timeframe"]["5m"][0]["symbol"] == "PTT"
    assert result["overlap_count"] == 1
    assert "not additive" in result["interpretation"]

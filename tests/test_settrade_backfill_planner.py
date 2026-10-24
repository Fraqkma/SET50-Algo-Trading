from scripts.plan_settrade_backfill import build_plan


def test_planner_groups_adjacent_gaps_filters_and_bounds_requests():
    gaps = [
        {"date": "2026-10-21", "dataset": "candles_1m", "environment": "PRODUCTION", "symbol": "PTT",
         "gap_start": "2026-10-21T10:00:00+07:00", "gap_end": "2026-10-21T10:03:00+07:00",
         "classification": "UNKNOWN"},
        {"date": "2026-10-21", "dataset": "candles_1m", "environment": "PRODUCTION", "symbol": "PTT",
         "gap_start": "2026-10-21T10:04:00+07:00", "gap_end": "2026-10-21T10:06:00+07:00",
         "classification": "UNKNOWN"},
        {"date": "2026-10-21", "dataset": "raw_bbo", "environment": "PRODUCTION", "symbol": "PTT",
         "gap_start": "2026-10-21T10:00:00+07:00", "gap_end": "2026-10-21T10:03:00+07:00",
         "classification": "UNKNOWN"},
    ]
    plan = build_plan({"gap_records": gaps}, symbol="PTT", timeframe="1m", max_minutes=2, max_requests=2)
    assert plan["source_gap_records"] == 2
    assert len(plan["planned_requests"]) == 2
    assert all(item["apply"] is False for item in plan["planned_requests"])
    assert plan["synthetic_realtime_recovery"] is False

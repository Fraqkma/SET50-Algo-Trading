from datetime import date, datetime, timezone

import pytest

from src.competition.metrics import competition_metrics_for_period
from src.competition.period import (
    boundary_fill_status,
    competition_calendar,
    competition_scope,
    filter_daily_records,
    load_competition_period,
)


def test_canonical_dates_and_confirmed_calendar():
    period = load_competition_period()
    assert period.start == date(2026, 12, 16)
    assert period.end == date(2027, 1, 15)
    assert period.timezone == "Asia/Bangkok"
    assert date(2027, 1, 1) not in period.trading_dates
    assert date(2026, 12, 31) not in period.trading_dates
    calendar = competition_calendar(period)
    assert calendar["trading_day_count"] == 21
    assert next(row for row in calendar["rows"] if row["date"] == "2027-01-01")["status"] == "SET_HOLIDAY"
    assert next(row for row in calendar["rows"] if row["date"] == "2026-12-31")["status"] == "SET_HOLIDAY"
    assert period.state_at(datetime(2026, 12, 15, tzinfo=timezone.utc)) == "PRE_COMPETITION"
    assert period.state_at(datetime(2026, 12, 16, tzinfo=timezone.utc)) == "IN_COMPETITION"
    assert period.state_at(datetime(2027, 1, 16, tzinfo=timezone.utc)) == "POST_COMPETITION"


def test_scope_and_filter_exclude_pre_post_weekends_and_holiday():
    period = load_competition_period()
    full = competition_scope(period.trading_dates, period)
    assert full["status"] == "COMPLETE_COMPETITION_PERIOD"
    assert full["metrics_authorized"]
    mixed = competition_scope([date(2026, 12, 15), *period.trading_dates, date(2027, 1, 16)], period)
    assert mixed["status"] == "MIXED_PERIOD"
    rows = [{"date": "2026-12-15"}, {"date": "2026-12-16"},
            {"date": "2027-01-01"}, {"date": "2027-01-15"}, {"date": "2027-01-16"}]
    assert [row["date"] for row in filter_daily_records(rows, period=period)] == ["2026-12-16", "2027-01-15"]


def test_cross_boundary_fifo_cases_remain_unresolved():
    period = load_competition_period()
    preperiod = boundary_fill_status([
        {"Symbol": "AAA", "Side": "Buy", "Volume": 100, "Timestamp": "2026-12-15T15:00:00"},
        {"Symbol": "AAA", "Side": "Sell", "Volume": 100, "Timestamp": "2026-12-16T10:00:00"},
    ], period)
    assert preperiod["status"] == "UNKNOWN"
    assert preperiod["boundary_cases"][0]["status"] == "PRE_COMPETITION_POSITION"
    postperiod = boundary_fill_status([
        {"Symbol": "AAA", "Side": "Buy", "Volume": 100, "Timestamp": "2027-01-15T10:00:00"},
        {"Symbol": "AAA", "Side": "Sell", "Volume": 100, "Timestamp": "2027-01-18T10:00:00"},
    ], period)
    assert postperiod["boundary_cases"][0]["status"] == "POST_COMPETITION_CLOSE_PENDING_RULE"
    still_open = boundary_fill_status([
        {"Symbol": "AAA", "Side": "Buy", "Volume": 100, "Timestamp": "2027-01-15T10:00:00"},
    ], period)
    assert still_open["boundary_cases"][0]["status"] == "IN_COMPETITION_OPEN"


def test_period_metrics_use_exact_days_and_return_unknown_if_incomplete():
    period = load_competition_period()
    days = [day.isoformat() for day in period.trading_dates]
    rows = [{"date": day, "nav_close": 100 + i * 0.5,
             "benchmark_close": 200 + i * 0.25, "invested_value": 50 + i * 0.25}
            for i, day in enumerate(days)]
    complete = competition_metrics_for_period(rows, [], expected_trading_dates=days, starting_nav=100)
    assert complete["classification"] == "RESEARCH_ESTIMATE"
    assert complete["metrics"]["portfolio_total_return"] == pytest.approx(10)
    assert complete["metrics"]["average_portfolio_exposure"] == pytest.approx(0.5)
    incomplete = competition_metrics_for_period(rows[:-1], [], expected_trading_dates=days, starting_nav=100)
    assert incomplete["classification"] == "UNKNOWN_OR_INCOMPLETE"
    assert incomplete["metrics"]["portfolio_total_return"] is None
    assert all(item["status"] == "UNKNOWN" for item in incomplete["qualification"].values())

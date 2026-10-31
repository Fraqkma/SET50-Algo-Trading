"""Canonical competition period and confirmed SET trading-day calendar."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / "config/competition.yaml"


@dataclass(frozen=True)
class CompetitionPeriod:
    start: date
    end: date
    timezone: str
    calendar_status: str
    holidays: frozenset[date]
    benchmark: dict[str, Any]
    round_trip_boundary_policy: str

    @property
    def trading_dates(self) -> tuple[date, ...]:
        holidays = self.holidays
        count = (self.end - self.start).days
        return tuple(day for offset in range(count + 1)
                     if (day := date.fromordinal(self.start.toordinal() + offset)).weekday() < 5
                     and day not in holidays)

    def state_at(self, value: datetime) -> str:
        local = value.astimezone(ZoneInfo(self.timezone)) if value.tzinfo else value.replace(tzinfo=ZoneInfo(self.timezone))
        if local.date() < self.start:
            return "PRE_COMPETITION"
        if local.date() > self.end:
            return "POST_COMPETITION"
        return "IN_COMPETITION"


def load_competition_period(path: Path = CONFIG_PATH) -> CompetitionPeriod:
    value = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    item = value["competition"]
    start, end = date.fromisoformat(item["start_date"]), date.fromisoformat(item["end_date"])
    benchmark, metrics, calendar = item["benchmark"], item["metrics"], item["calendar"]
    if start > end:
        raise ValueError("competition start date must not follow end date")
    if benchmark["start_date"] != start.isoformat() or benchmark["end_date"] != end.isoformat():
        raise ValueError("benchmark window must match canonical competition dates")
    if metrics["start_date"] != start.isoformat() or metrics["end_date"] != end.isoformat():
        raise ValueError("metric window must match canonical competition dates")
    return CompetitionPeriod(start, end, item["timezone"], calendar["status"],
                             frozenset(date.fromisoformat(x) for x in calendar.get("holidays", [])),
                             benchmark, metrics["round_trip_boundary_policy"])


def competition_calendar(period: CompetitionPeriod | None = None) -> dict[str, Any]:
    period = period or load_competition_period()
    holiday_dates = period.holidays
    rows = []
    for offset in range((period.end - period.start).days + 1):
        day = date.fromordinal(period.start.toordinal() + offset)
        if day.weekday() >= 5:
            status, reason = "WEEKEND", "Saturday/Sunday"
        elif day in holiday_dates:
            status, reason = "SET_HOLIDAY", "Listed on official SET holiday calendar"
        else:
            status, reason = "EXPECTED_TRADING_DAY", "Weekday not listed as SET holiday as of calendar verification"
        rows.append({"date": day.isoformat(), "status": status, "reason": reason,
                     "trading_day_ordinal": sum(r["status"] == "EXPECTED_TRADING_DAY" for r in rows) + 1
                     if status == "EXPECTED_TRADING_DAY" else None})
    return {"period_start": period.start.isoformat(), "period_end": period.end.isoformat(),
            "timezone": period.timezone, "status": period.calendar_status,
            "verified_as_of": "2026-10-30", "source_urls": [
                "https://www.set.or.th/en/about/event-calendar/holiday?year=2026",
                "https://www.set.or.th/th/about/event-calendar/holiday?year=2027"],
            "trading_day_count": sum(row["status"] == "EXPECTED_TRADING_DAY" for row in rows),
            "rows": rows,
            "note": "Calendar is verified against official SET holiday pages, not inferred from weekdays alone; refresh if SET publishes an amendment."}


def competition_scope(run_dates: Iterable[str | date], period: CompetitionPeriod | None = None) -> dict[str, Any]:
    """Classify an input run against the official period without scoring other dates."""
    period = period or load_competition_period()
    observed_values = set()
    for value in run_dates:
        if isinstance(value, datetime):
            observed_values.add(value.date())
        elif isinstance(value, date):
            observed_values.add(value)
        else:
            observed_values.add(date.fromisoformat(str(value)[:10]))
    observed = sorted(observed_values)
    expected = set(period.trading_dates)
    in_period = [value for value in observed if period.start <= value <= period.end]
    outside = [value for value in observed if not period.start <= value <= period.end]
    missing = sorted(expected - set(in_period))
    unexpected = sorted(set(in_period) - expected)
    if outside and in_period:
        status = "MIXED_PERIOD"
    elif outside:
        status = "OUTSIDE_OFFICIAL_COMPETITION_PERIOD"
    elif not in_period:
        status = "NO_COMPETITION_DATES"
    elif missing or unexpected:
        status = "INCOMPLETE_COMPETITION_PERIOD"
    else:
        status = "COMPLETE_COMPETITION_PERIOD"
    return {"status": status, "period_start": period.start.isoformat(), "period_end": period.end.isoformat(),
            "observed_in_period_dates": [d.isoformat() for d in in_period],
            "excluded_outside_period_dates": [d.isoformat() for d in outside],
            "missing_trading_dates": [d.isoformat() for d in missing],
            "unexpected_in_period_dates": [d.isoformat() for d in unexpected],
            "expected_trading_dates": [d.isoformat() for d in period.trading_dates],
            "metrics_authorized": status == "COMPLETE_COMPETITION_PERIOD"}


def filter_daily_records(records: Iterable[dict[str, Any]], date_key: str = "date",
                         period: CompetitionPeriod | None = None) -> list[dict[str, Any]]:
    """Select inclusive competition dates and confirmed trading dates only."""
    period = period or load_competition_period()
    trading_dates = set(period.trading_dates)
    selected = []
    for row in records:
        raw = row.get(date_key)
        day = raw.date() if isinstance(raw, datetime) else raw if isinstance(raw, date) else date.fromisoformat(str(raw)[:10])
        if day in trading_dates:
            selected.append(row)
    return selected


def boundary_fill_status(fills: Iterable[dict[str, Any]], period: CompetitionPeriod | None = None) -> dict[str, Any]:
    """Flag FIFO lots crossing either official boundary; do not guess qualification treatment."""
    period = period or load_competition_period()
    queues: dict[str, list[dict[str, Any]]] = {}
    flags: list[dict[str, Any]] = []
    ordered = sorted(fills, key=lambda row: str(row.get("Timestamp", row.get("timestamp", ""))))
    for index, fill in enumerate(ordered):
        stamp_raw = fill.get("Timestamp", fill.get("timestamp"))
        if not stamp_raw:
            flags.append({"fill_index": index, "status": "UNKNOWN_TIMESTAMP"})
            continue
        try:
            day = date.fromisoformat(str(stamp_raw)[:10])
        except ValueError:
            flags.append({"fill_index": index, "status": "UNKNOWN_TIMESTAMP"})
            continue
        symbol = str(fill.get("Symbol", fill.get("symbol", "")))
        side = str(fill.get("Side", fill.get("side", ""))).upper()
        quantity = int(float(fill.get("Volume", fill.get("quantity", 0)) or 0))
        if side == "BUY":
            queues.setdefault(symbol, []).append({"opened": day, "remaining": quantity})
            continue
        if side != "SELL":
            continue
        lot_queue = queues.setdefault(symbol, [])
        remaining = quantity
        while remaining > 0 and lot_queue:
            lot = lot_queue[0]
            matched = min(remaining, lot["remaining"])
            if lot["opened"] < period.start and day >= period.start:
                flags.append({"symbol": symbol, "open_date": lot["opened"].isoformat(), "close_date": day.isoformat(),
                              "status": "PRE_COMPETITION_POSITION"})
            elif period.start <= lot["opened"] <= period.end < day:
                flags.append({"symbol": symbol, "open_date": lot["opened"].isoformat(), "close_date": day.isoformat(),
                              "status": "POST_COMPETITION_CLOSE_PENDING_RULE"})
            lot["remaining"] -= matched
            remaining -= matched
            if lot["remaining"] == 0:
                lot_queue.pop(0)
        if remaining > 0 and period.start <= day <= period.end:
            flags.append({"symbol": symbol, "close_date": day.isoformat(), "status": "UNMATCHED_SELL_REQUIRES_PRE_PERIOD_HOLDING_CONTEXT"})
    for symbol, lots in queues.items():
        for lot in lots:
            if lot["remaining"] and period.start <= lot["opened"] <= period.end:
                flags.append({"symbol": symbol, "open_date": lot["opened"].isoformat(), "remaining_quantity": lot["remaining"],
                              "status": "IN_COMPETITION_OPEN"})
    return {"policy": period.round_trip_boundary_policy, "status": "UNKNOWN" if flags else "NO_BOUNDARY_CASES_OBSERVED",
            "boundary_cases": flags}

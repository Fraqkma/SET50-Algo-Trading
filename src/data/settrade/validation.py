"""Non-repairing quality checks for normalized pilot data."""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from .schemas import BarRecord, QuoteRecord, ValidationIssue


def validate_bar_records(records: Iterable[BarRecord]) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    seen: set[tuple[str, str, object]] = set()
    previous = None
    for index, record in enumerate(records):
        key = (record.symbol, record.interval, record.timestamp)
        if key in seen:
            issues.append(ValidationIssue("DUPLICATE", "duplicate symbol/interval/timestamp", index))
        seen.add(key)
        if previous is not None and record.timestamp <= previous:
            issues.append(ValidationIssue("NON_MONOTONIC", "timestamps are not strictly increasing", index))
        previous = record.timestamp
        values = (record.open, record.high, record.low, record.close)
        if any(value is not None and value <= 0 for value in values):
            issues.append(ValidationIssue("INVALID_PRICE", "OHLC contains a non-positive price", index))
        if all(value is not None for value in values):
            assert record.high is not None and record.low is not None
            if record.high < max(record.open, record.close) or record.low > min(record.open, record.close) or record.high < record.low:
                issues.append(ValidationIssue("OHLC_INCONSISTENT", "OHLC relationship is invalid", index))
        if record.volume is not None and record.volume < 0:
            issues.append(ValidationIssue("NEGATIVE_VOLUME", "volume is negative", index))
        if record.turnover is not None and record.turnover < 0:
            issues.append(ValidationIssue("NEGATIVE_TURNOVER", "turnover is negative", index))
    return issues


def validate_quote(record: QuoteRecord) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    if record.last is not None and record.last <= Decimal("0"):
        issues.append(ValidationIssue("INVALID_PRICE", "last price is non-positive"))
    if record.bid is not None and record.ask is not None and record.bid > record.ask:
        issues.append(ValidationIssue("CROSSED_BBO", "bid is greater than ask"))
    return issues

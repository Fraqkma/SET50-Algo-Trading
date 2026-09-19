"""Typed normalized records for pilot Settrade data."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class BarRecord:
    timestamp: datetime
    symbol: str
    interval: str
    open: Decimal | None
    high: Decimal | None
    low: Decimal | None
    close: Decimal | None
    volume: Decimal | None
    turnover: Decimal | None
    source: str
    retrieved_at: datetime
    timezone: str
    session: str | None = None
    adjustment_status: str = "UNKNOWN"


@dataclass(frozen=True)
class QuoteRecord:
    timestamp: datetime | None
    symbol: str
    last: Decimal | None
    bid: Decimal | None
    ask: Decimal | None
    bid_size: Decimal | None
    ask_size: Decimal | None
    market_status: str | None
    source: str
    retrieved_at: datetime
    timezone: str


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str
    row: int | None = None

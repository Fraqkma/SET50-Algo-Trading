"""Normalize official SDK responses without manufacturing unavailable fields."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any

from .schemas import BarRecord, QuoteRecord


def _decimal(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _epoch(value: Any) -> datetime | None:
    if value is None:
        return None
    try:
        return datetime.fromtimestamp(float(value), tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def normalize_candlestick(
    result: dict[str, Any], symbol: str, interval: str, retrieved_at: datetime | None = None
) -> list[BarRecord]:
    """Convert the SDK's parallel arrays into auditable UTC records."""
    retrieved = retrieved_at or datetime.now(timezone.utc)
    times = result.get("time") or []
    fields = {name: result.get(name) or [] for name in ("open", "high", "low", "close", "volume", "value")}
    records: list[BarRecord] = []
    for index, raw_time in enumerate(times):
        timestamp = _epoch(raw_time)
        if timestamp is None:
            continue
        get = lambda name: _decimal(fields[name][index]) if index < len(fields[name]) else None
        records.append(BarRecord(timestamp, symbol, interval, get("open"), get("high"), get("low"), get("close"), get("volume"), get("value"), "settrade", retrieved, "UTC"))
    return records


def normalize_quote(result: dict[str, Any], symbol: str, retrieved_at: datetime | None = None) -> QuoteRecord:
    """Normalize quote fields; absent bid/ask fields remain null."""
    retrieved = retrieved_at or datetime.now(timezone.utc)
    timestamp = _epoch(result.get("timestamp") or result.get("time"))
    return QuoteRecord(timestamp, symbol, _decimal(result.get("last")), _decimal(result.get("bid")), _decimal(result.get("ask")), _decimal(result.get("bidSize")), _decimal(result.get("askSize")), result.get("marketStatus"), "settrade", retrieved, "UTC")

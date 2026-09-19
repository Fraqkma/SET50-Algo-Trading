"""Deterministic aggregation of observed minute bars."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal

from .schemas import BarRecord


@dataclass(frozen=True)
class AggregatedBar:
    bar: BarRecord
    observed_source_bars: int
    incomplete_bucket: bool


def aggregate_bars(records: list[BarRecord], minutes: int) -> list[AggregatedBar]:
    """Aggregate only contiguous observed bars; gaps are never filled."""
    if minutes not in {5, 15}:
        raise ValueError("minutes must be 5 or 15")
    ordered = sorted(records, key=lambda item: item.timestamp)
    result: list[AggregatedBar] = []
    bucket: list[BarRecord] = []
    bucket_start = None
    expected = timedelta(minutes=minutes)
    for record in ordered:
        if bucket_start is None:
            bucket_start = record.timestamp
        if bucket and (record.timestamp - bucket[-1].timestamp != timedelta(minutes=1) or record.timestamp >= bucket_start + expected):
            result.append(_finish(bucket, minutes))
            bucket = []
            bucket_start = record.timestamp
        bucket.append(record)
    if bucket:
        result.append(_finish(bucket, minutes))
    return result


def _finish(bucket: list[BarRecord], minutes: int) -> AggregatedBar:
    first, last = bucket[0], bucket[-1]
    opens = [x.open for x in bucket if x.open is not None]
    highs = [x.high for x in bucket if x.high is not None]
    lows = [x.low for x in bucket if x.low is not None]
    closes = [x.close for x in bucket if x.close is not None]
    volumes = [x.volume for x in bucket if x.volume is not None]
    bar = BarRecord(
        timestamp=first.timestamp,
        symbol=first.symbol,
        interval=f"{minutes}m",
        open=opens[0] if opens else None,
        high=max(highs) if highs else None,
        low=min(lows) if lows else None,
        close=closes[-1] if closes else None,
        volume=sum(volumes, Decimal("0")) if volumes else None,
        turnover=None,
        source=first.source,
        retrieved_at=first.retrieved_at,
        timezone=first.timezone,
        session=first.session,
        adjustment_status=first.adjustment_status,
    )
    return AggregatedBar(bar, len(bucket), len(bucket) != minutes)

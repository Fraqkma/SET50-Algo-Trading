"""Diagnostic IOC plausibility, not matching-engine simulation."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from .book import book_sweep_vwap


def ioc_fill_status(side: str, limit_price: Decimal, quantity: Decimal, levels: Iterable[tuple[Decimal, Decimal]] | None) -> str:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if levels is None:
        return "NO_BOOK"
    book = list(levels)
    if not book:
        return "NO_MARKETABLE_QUOTE"
    marketable = [(price, volume) for price, volume in book if (price <= limit_price if side.upper() == "BUY" else price >= limit_price)]
    if not marketable:
        return "NO_MARKETABLE_QUOTE"
    available = sum((volume for _, volume in marketable), Decimal("0"))
    if available >= quantity:
        return "FULL_DEPTH_AVAILABLE"
    return "PARTIAL_DEPTH_AVAILABLE"


LIMITATIONS = ("queue priority", "hidden orders", "event latency", "cancellations", "timestamp synchronization", "auction behavior")

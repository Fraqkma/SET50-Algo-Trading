"""Observed-book cost diagnostics using Decimal arithmetic."""
from __future__ import annotations

from decimal import Decimal
from typing import Iterable


def spread_metrics(best_bid: Decimal | None, best_ask: Decimal | None) -> dict[str, Decimal | None]:
    if best_bid is None or best_ask is None:
        return {"mid_price": None, "spread": None, "spread_bps": None}
    mid = (best_bid + best_ask) / Decimal("2")
    spread = best_ask - best_bid
    return {"mid_price": mid, "spread": spread, "spread_bps": spread / mid * Decimal("10000") if mid else None}


def depth_metrics(levels: Iterable[tuple[Decimal, Decimal]], depth: int) -> dict[str, Decimal | None]:
    selected = list(levels)[:depth]
    total = sum((volume for _, volume in selected), Decimal("0"))
    return {"depth": Decimal(depth), "total_depth": total}


def book_sweep_vwap(levels: Iterable[tuple[Decimal, Decimal]], quantity: Decimal) -> Decimal | None:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    remaining = quantity
    notional = Decimal("0")
    for price, volume in levels:
        if price < 0 or volume < 0:
            raise ValueError("price and volume must be nonnegative")
        filled = min(remaining, volume)
        notional += filled * price
        remaining -= filled
        if remaining == 0:
            return notional / quantity
    return None


def one_tick_cost(price: Decimal, quantity: Decimal, tick: Decimal) -> Decimal:
    if price < 0 or quantity <= 0 or tick <= 0:
        raise ValueError("price, quantity and tick must be valid")
    return quantity * tick


def crossing_cost(side: str, reference_price: Decimal, quantity: Decimal, opposite_quote: Decimal | None) -> Decimal | None:
    if quantity <= 0:
        raise ValueError("quantity must be positive")
    if opposite_quote is None:
        return None
    return quantity * ((opposite_quote - reference_price) if side.upper() == "BUY" else (reference_price - opposite_quote))

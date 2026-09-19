"""Pure order-book normalization and quality checks for Settrade events."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any


def _number(value: Any) -> Decimal | None:
    try:
        return None if value in (None, "") else Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def normalize_bid_offer(payload: dict[str, Any]) -> list[dict[str, Any]]:
    symbol = payload.get("symbol")
    rows: list[dict[str, Any]] = []
    for level in range(1, 11):
        rows.append({"symbol": symbol, "side": "bid", "level": level, "price": _number(payload.get(f"bid_price{level}")), "volume": _number(payload.get(f"bid_volume{level}"))})
        rows.append({"symbol": symbol, "side": "ask", "level": level, "price": _number(payload.get(f"ask_price{level}")), "volume": _number(payload.get(f"ask_volume{level}"))})
    return rows


def assess_orderbook(payload: dict[str, Any]) -> dict[str, Any]:
    bids = [_number(payload.get(f"bid_price{i}")) for i in range(1, 11)]
    asks = [_number(payload.get(f"ask_price{i}")) for i in range(1, 11)]
    bids = [x for x in bids if x is not None]
    asks = [x for x in asks if x is not None]
    bid = bids[0] if bids else None
    ask = asks[0] if asks else None
    bid_volumes = [_number(payload.get(f"bid_volume{i}")) or Decimal(0) for i in range(1, 11)]
    ask_volumes = [_number(payload.get(f"ask_volume{i}")) or Decimal(0) for i in range(1, 11)]
    bid_volume = sum(bid_volumes, Decimal(0))
    ask_volume = sum(ask_volumes, Decimal(0))
    mid = (bid + ask) / 2 if bid is not None and ask is not None else None
    spread = ask - bid if bid is not None and ask is not None else None
    metrics: dict[str, Any] = {}
    for depth in (1, 5, 10):
        bid_depth = sum(bid_volumes[:depth], Decimal(0))
        ask_depth = sum(ask_volumes[:depth], Decimal(0))
        metrics.update({f"bid_depth_{depth}": bid_depth, f"ask_depth_{depth}": ask_depth, f"total_depth_{depth}": bid_depth + ask_depth, f"imbalance_{depth}": (bid_depth - ask_depth) / (bid_depth + ask_depth) if bid_depth + ask_depth else None})
    return {"symbol": payload.get("symbol"), "bid_levels": len(bids), "ask_levels": len(asks), "best_bid": bid, "best_ask": ask, "mid_price": mid, "spread": spread, "spread_bps": spread / mid * Decimal("10000") if spread is not None and mid else None, "crossed": bid is not None and ask is not None and bid > ask, "bid_volume_total": bid_volume, "ask_volume_total": ask_volume, "imbalance": (bid_volume - ask_volume) / (bid_volume + ask_volume) if bid_volume + ask_volume else None, "bid_prices_descending": bids == sorted(bids, reverse=True), "ask_prices_ascending": asks == sorted(asks), **metrics}

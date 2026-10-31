"""Observe official 0.2.7 objects without changing validation or matching."""
from __future__ import annotations

import inspect
from typing import Any


class OrderObserver:
    """Retain requests and one-shot outcomes missing from the fill-only CSV."""

    def __init__(self, order_class: type, commission_service: type) -> None:
        self.orders: list[Any] = []
        self.rejections: list[dict[str, Any]] = []
        self.attempts: dict[str, dict[str, Any]] = {}
        self.service = commission_service
        original = order_class.__init__
        signature = inspect.signature(original)

        def observe(order: Any, *args: Any, **kwargs: Any) -> None:
            values = signature.bind(order, *args, **kwargs).arguments
            try:
                original(order, *args, **kwargs)
            except (ValueError, KeyError, FileNotFoundError) as error:
                self.rejections.append({
                    "order_id": None, "requested_quantity": values.get("volume"),
                    "requested_price": values.get("price"), "symbol": values.get("symbol"),
                    "side": values.get("side"), "status": "REJECTED",
                    "rejection_reason": str(error), "simulator_version": "0.2.7",
                })
                raise
            self.orders.append(order)

        order_class.__init__ = observe

    def attach(self, execution: Any) -> None:
        match = execution.isMatch
        market = execution.isMatchMarketOrder

        def record(order: Any, row: Any) -> None:
            if order.get_symbol() != row["ShareCode"]:
                return
            last = float(row["LastPrice"])
            price = self.service.market_fill_price(last, order.get_side(), row["TradeDateTime"])
            self.attempts[order.get_order_number()] = {
                "reference_latest_price": last, "applicable_tick_size": abs(price - last),
                "matching_timestamp": str(row["TradeDateTime"]), "tick_volume": int(row["Volume"]),
                "tick_flag": row.get("Flag"),
            }

        def limit(row: Any) -> Any:
            for order in list(execution.Orders_Book):
                record(order, row)
            return match(row)

        def at_market(row: Any, order: Any) -> Any:
            if order is not None:
                record(order, row)
            return market(row, order)

        execution.isMatch = limit
        execution.isMatchMarketOrder = at_market

    def snapshot(self) -> list[dict[str, Any]]:
        result = []
        for order in self.orders:
            requested = int(order.get_volume())
            filled = int(order.get_last_fill_volume())
            canceled = requested - filled
            attempt = self.attempts.get(order.get_order_number(), {})
            result.append({
                "order_id": order.get_order_number(), "symbol": order.get_symbol(),
                "side": order.get_side(), "order_type": order.get_order_type(),
                "normalized_order_type": "MARKET_TO_LIMIT" if order.get_order_type() == "Market" else "LIMIT",
                "requested_price": order.get_price(), "requested_quantity": requested,
                "filled_quantity": filled, "remaining_quantity": canceled,
                "canceled_quantity": canceled, "validity": "IOC", "one_shot_matching": True,
                "status": ("FILLED" if not canceled else "PARTIALLY_FILLED_IOC_CANCELED" if filled
                           else "IOC_CANCELED" if attempt else "EOD_CANCELED_BEFORE_SYMBOL_TICK"),
                "placed_timestamp": order.get_formatted_placed_timestamp(),
                "execution_price": order.get_fill_price(), "simulator_version": "0.2.7",
                "observation_source": "official objects; raw transaction CSV preserved", **attempt,
            })
        return result

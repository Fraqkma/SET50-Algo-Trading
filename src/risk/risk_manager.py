"""Risk validation utilities."""

from __future__ import annotations

from src.execution.order_manager import OrderSide


def validate_long_only_order(position_quantity: int, side: OrderSide, quantity: int) -> None:
    """Validate that an order does not violate the long-only constraint."""

    if quantity <= 0:
        raise ValueError("Order quantity must be positive.")

    if side is OrderSide.SELL and quantity > position_quantity:
        raise ValueError("Short selling is not allowed.")
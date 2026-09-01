"""Tests for risk checks."""

from __future__ import annotations

import pytest

from src.execution.order_manager import OrderSide
from src.risk.risk_manager import validate_long_only_order


def test_long_only_rejects_excess_sell_quantity() -> None:
    """Selling more shares than are held must be rejected."""

    with pytest.raises(ValueError):
        validate_long_only_order(position_quantity=10, side=OrderSide.SELL, quantity=11)
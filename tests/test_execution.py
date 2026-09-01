"""Tests for allowed order types and execution validation."""

from __future__ import annotations

from decimal import Decimal

import pytest

from src.execution.order_manager import OrderRequest, OrderSide, OrderType, Validity, validate_order_request


def test_allowed_order_type_and_validity_are_accepted() -> None:
    """Allowed order types and IOC validity should pass validation."""

    request = OrderRequest(
        symbol="AOT",
        side=OrderSide.BUY,
        quantity=100,
        order_type=OrderType.LIMIT,
        validity=Validity.IOC,
        price=Decimal("10.00"),
    )

    validate_order_request(request)


def test_disallowed_order_type_is_rejected() -> None:
    """Order types outside the competition rules must fail validation."""

    request = OrderRequest(
        symbol="AOT",
        side=OrderSide.BUY,
        quantity=100,
        order_type="MARKET",
        validity=Validity.IOC,
        price=Decimal("10.00"),
    )

    with pytest.raises(ValueError):
        validate_order_request(request)
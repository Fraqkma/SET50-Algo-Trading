"""Order models and validation for the competition execution layer."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import Enum


class OrderSide(str, Enum):
    """Supported order sides."""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    """Allowed competition order types."""

    LIMIT = "LIMIT"
    MARKET_TO_LIMIT = "MARKET_TO_LIMIT"


class Validity(str, Enum):
    """Allowed order validity values."""

    IOC = "IOC"


@dataclass(frozen=True)
class OrderRequest:
    """Competition order request representation."""

    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    validity: Validity
    price: Decimal | None = None


@dataclass(frozen=True)
class ExecutionReport:
    """Execution response placeholder."""

    symbol: str
    side: OrderSide
    quantity: int
    order_type: OrderType
    validity: Validity
    requested_price: Decimal | None
    executed_price: Decimal | None
    status: str


def validate_order_request(order_request: OrderRequest) -> None:
    """Validate the order against the competition's allowed order model."""

    if order_request.quantity <= 0:
        raise ValueError("Order quantity must be positive.")

    if order_request.order_type not in {OrderType.LIMIT, OrderType.MARKET_TO_LIMIT}:
        raise ValueError("Only LIMIT and MARKET_TO_LIMIT orders are allowed.")

    if order_request.validity is not Validity.IOC:
        raise ValueError("Only IOC validity is allowed.")

    if order_request.price is None:
        raise ValueError("An order price is required for allowed order types.")
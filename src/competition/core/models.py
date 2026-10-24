"""Small, dependency-free value objects shared by competition components."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Mapping


class Side(StrEnum):
    BUY = "BUY"
    SELL = "SELL"


class SignalAction(StrEnum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class OrderType(StrEnum):
    LIMIT = "LIMIT"
    MARKET_TO_LIMIT = "MARKET_TO_LIMIT"


class TimeInForce(StrEnum):
    IOC = "IOC"


@dataclass(frozen=True)
class MarketBar:
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Signal:
    symbol: str
    action: SignalAction
    timestamp: datetime
    reason: str = ""


@dataclass(frozen=True)
class PortfolioSnapshot:
    timestamp: datetime
    cash: float
    holdings: Mapping[str, int] = field(default_factory=dict)
    nav: float | None = None


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    side: Side
    quantity: int
    order_type: OrderType
    time_in_force: TimeInForce | None
    decision_timestamp: datetime
    limit_price: float | None = None

    def __post_init__(self) -> None:
        if not self.symbol.strip():
            raise ValueError("order intent requires a symbol")
        if self.quantity <= 0:
            raise ValueError("order intent quantity must be positive")
        if self.order_type is OrderType.LIMIT and (
            self.limit_price is None or self.limit_price <= 0
        ):
            raise ValueError("limit orders require a positive limit_price")
        if self.order_type is OrderType.MARKET_TO_LIMIT and self.time_in_force is not TimeInForce.IOC:
            raise ValueError("market-to-limit orders require IOC validity")


@dataclass(frozen=True)
class ExecutionReport:
    status: str
    order_id: str | None = None
    fills: tuple[Mapping[str, object], ...] = ()
    message: str | None = None

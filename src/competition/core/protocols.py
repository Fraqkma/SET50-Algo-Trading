"""Layer contracts that keep research logic independent of UI and engines."""

from __future__ import annotations

from typing import Iterable, Mapping, Protocol

from .models import (
    ExecutionReport,
    MarketBar,
    OrderIntent,
    PortfolioSnapshot,
    Signal,
)


class DataInput(Protocol):
    def iter_bars(self, start: str, end: str) -> Iterable[MarketBar]: ...


class FeatureProvider(Protocol):
    def transform(self, bar: MarketBar) -> Mapping[str, float | None]: ...


class SignalProvider(Protocol):
    def generate(self, bar: MarketBar, features: Mapping[str, float | None],
                 portfolio: PortfolioSnapshot) -> Iterable[Signal]: ...


class PortfolioRiskPolicy(Protocol):
    def create_order_intents(self, signals: Iterable[Signal],
                             portfolio: PortfolioSnapshot) -> Iterable[OrderIntent]: ...


class ExecutionAdapter(Protocol):
    def execute(self, order: OrderIntent) -> ExecutionReport: ...

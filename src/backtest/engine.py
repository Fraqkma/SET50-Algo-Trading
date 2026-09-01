"""Backtest engine placeholder."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Any


@dataclass(frozen=True)
class BacktestResult:
    """Summary of a backtest run."""

    final_equity: Decimal | None = None
    total_return: Decimal | None = None
    unique_symbols_traded: int = 0


class BacktestEngine:
    """Placeholder backtest engine.

    TODO: Implement event-ordered simulation after the order and risk layers are in place.
    """

    def run(self, strategy: Any, market_data: Any) -> BacktestResult:
        raise NotImplementedError("Backtest simulation is not implemented yet.")
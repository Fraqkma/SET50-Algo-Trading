"""Performance metric interfaces for backtests."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class TradeRecord:
    """Minimal trade record used by placeholder metrics."""

    symbol: str


def count_unique_symbols_traded(trades: Iterable[TradeRecord]) -> int:
    """Count distinct symbols that were traded."""

    return len({trade.symbol for trade in trades})


def meets_minimum_unique_symbols(trades: Iterable[TradeRecord], minimum: int = 5) -> bool:
    """Check whether the minimum unique-symbol trading requirement is met."""

    return count_unique_symbols_traded(trades) >= minimum
"""Baseline strategy placeholder."""

from __future__ import annotations

from typing import Any

from .base import Strategy


class BaselineStrategy(Strategy):
    """Placeholder baseline strategy.

    TODO: Implement a reproducible baseline after the data pipeline exists.
    """

    def generate_signal(self, market_data: Any) -> Any:
        raise NotImplementedError("Baseline strategy is not implemented yet.")
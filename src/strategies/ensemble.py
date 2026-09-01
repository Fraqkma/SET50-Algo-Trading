"""Ensemble strategy placeholder."""

from __future__ import annotations

from typing import Any

from .base import Strategy


class EnsembleStrategy(Strategy):
    """Placeholder ensemble strategy.

    TODO: Add only after simpler strategies have been validated out-of-sample.
    """

    def generate_signal(self, market_data: Any) -> Any:
        raise NotImplementedError("Ensemble strategy is not implemented yet.")
"""Strategy abstraction for signal generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class Strategy(ABC):
    """Abstract strategy interface for generating trading signals."""

    @abstractmethod
    def generate_signal(self, market_data: Any) -> Any:
        """Generate a signal from market data.

        TODO: Define a concrete signal schema when the strategy layer is added.
        """

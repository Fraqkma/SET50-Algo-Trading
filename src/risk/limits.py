"""Risk limit placeholders."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RiskLimits:
    """Placeholder for risk limit configuration."""

    max_position_size: int | None = None
    max_portfolio_exposure: float | None = None
    cash_reserve: float | None = None
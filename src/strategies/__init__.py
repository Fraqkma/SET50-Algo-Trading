"""Strategy interfaces and baseline implementations."""

from .base import Strategy
from .baseline import BaselineStrategy
from .cross_sectional import rank_time_series_candidates
from .timing import next_trading_session, rebalance_dates

__all__ = [
    "Strategy",
    "BaselineStrategy",
    "rank_time_series_candidates",
    "rebalance_dates",
    "next_trading_session",
]

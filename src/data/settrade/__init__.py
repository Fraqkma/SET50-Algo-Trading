"""Isolated Settrade pilot data infrastructure.

This package is deliberately market-data only.  Account and order APIs are not
constructed by :class:`SettradeClient`.
"""

from .client import SettradeClient, SettradeConfig
from .aggregation import AggregatedBar, aggregate_bars
from .normalization import normalize_candlestick, normalize_quote
from .rate_limiter import RateLimiter
from .storage import PilotStorage
from .validation import ValidationIssue, validate_bar_records, validate_quote
from .rotation import RotationScheduler
from .disk import DiskStatus, check_disk, require_disk

__all__ = [
    "PilotStorage",
    "RateLimiter",
    "SettradeClient",
    "SettradeConfig",
    "AggregatedBar",
    "aggregate_bars",
    "ValidationIssue",
    "normalize_candlestick",
    "normalize_quote",
    "validate_bar_records",
    "validate_quote",
    "RotationScheduler",
    "DiskStatus",
    "check_disk",
    "require_disk",
]

"""SET/Thailand session labels used as metadata, not as trading signals."""
from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

THAILAND = ZoneInfo("Asia/Bangkok")


def session_state(timestamp: datetime) -> str:
    local = timestamp.astimezone(THAILAND).time()
    if local < time(9, 30):
        return "PRE_OPEN"
    if local < time(12, 30):
        return "CONTINUOUS_MORNING"
    if local < time(14, 30):
        return "MIDDAY_BREAK"
    if local < time(16, 40):
        return "CONTINUOUS_AFTERNOON"
    if local < time(17, 0):
        return "PRE_CLOSE_AUCTION"
    return "CLOSED"

"""Deterministic, strategy-neutral realtime topic rotation."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class RotationGroup:
    generation: int
    group_index: int
    symbols: tuple[str, ...]
    started_at: datetime


class RotationScheduler:
    """Partition symbols into groups at or below the internal topic ceiling."""

    def __init__(self, symbols: list[str], max_topics: int = 35, interval_seconds: int = 300) -> None:
        if not symbols or max_topics < 1 or interval_seconds < 1:
            raise ValueError("symbols, max_topics and interval_seconds must be positive")
        self.symbols = tuple(dict.fromkeys(symbols))
        self.max_topics = max_topics
        self.interval_seconds = interval_seconds
        self.groups = tuple(tuple(self.symbols[i : i + max_topics]) for i in range(0, len(self.symbols), max_topics))

    def group(self, generation: int = 0, now: datetime | None = None) -> RotationGroup:
        started = now or datetime.now(timezone.utc)
        index = generation % len(self.groups)
        return RotationGroup(generation, index, self.groups[index], started)

    def metadata(self, generation: int = 0, session_id: str | None = None, now: datetime | None = None) -> dict[str, object]:
        current = self.group(generation, now)
        return {"rotation_generation": current.generation, "rotation_group": current.group_index, "subscription_started_at": current.started_at.isoformat(), "collector_session_id": session_id, "active_topics": len(current.symbols), "group_count": len(self.groups), "symbols": list(current.symbols)}

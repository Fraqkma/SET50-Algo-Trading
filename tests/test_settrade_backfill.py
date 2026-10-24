from __future__ import annotations

from scripts.backfill_settrade_candles import merge_plan


def _row(timestamp: str, close: str = "10") -> dict[str, str]:
    return {"symbol": "PTT", "interval": "1m", "timestamp": timestamp, "open": "10", "high": "11", "low": "9", "close": close, "volume": "100"}


def test_backfill_merge_appends_only_new_rows_and_dedupes_identical_rows() -> None:
    existing = [_row("2026-10-21T03:00:00+00:00")]
    plan = merge_plan(existing, [_row("2026-10-21T03:00:00+00:00"), _row("2026-10-21T03:01:00+00:00")])
    assert plan["blocked"] is False
    assert plan["duplicates"] == 1
    assert len(plan["additions"]) == 1
    assert plan["conflicts"] == []


def test_backfill_conflict_blocks_the_entire_batch_without_overwrite() -> None:
    existing = [_row("2026-10-21T03:00:00+00:00", close="10")]
    plan = merge_plan(existing, [_row("2026-10-21T03:00:00+00:00", close="10.5"), _row("2026-10-21T03:01:00+00:00")])
    assert plan["blocked"] is True
    assert plan["additions"] == []
    assert len(plan["conflicts"]) == 1


def test_backfill_merge_treats_equivalent_timezone_timestamps_as_same_bar() -> None:
    existing = [_row("2026-10-21T03:00:00+00:00")]
    proposed = [_row("2026-10-21T10:00:00+07:00")]
    plan = merge_plan(existing, proposed)
    assert plan["additions"] == []
    assert plan["duplicates"] == 1
    assert plan["conflicts"] == []

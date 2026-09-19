from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from src.data.settrade.aggregation import aggregate_bars
from src.data.settrade.client import SettradeConfig, redact_error
from src.data.settrade.normalization import normalize_candlestick, normalize_quote
from src.data.settrade.orderbook import assess_orderbook, normalize_bid_offer
from src.data.settrade.rotation import RotationScheduler
from src.data.settrade.session import session_state
from src.research.execution.book import book_sweep_vwap, spread_metrics
from src.research.execution.ioc import ioc_fill_status
from src.research.execution.alignment import classify_daily_book
from src.data.settrade.rate_limiter import RateLimiter
from src.data.settrade.retry import call_with_retries, is_retryable
from src.data.settrade.schemas import BarRecord
from src.data.settrade.storage import PilotStorage
from src.data.settrade.validation import validate_bar_records, validate_quote


def _bars(count: int = 5) -> list[BarRecord]:
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)
    return [BarRecord(now.replace(minute=i), "PTT", "1m", Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("100"), None, "settrade", now, "UTC") for i in range(count)]


def test_config_repr_and_error_redact_secrets() -> None:
    config = SettradeConfig("SANDBOX", "SANDBOX", "app-id", "app-secret")
    assert "app-secret" not in repr(config)
    assert redact_error(RuntimeError("app-id app-secret failed"), ("app-id", "app-secret")) == "[REDACTED] [REDACTED] failed"


def test_normalize_parallel_arrays_and_validate() -> None:
    result = {"time": [1767546000], "open": [10], "high": [11], "low": [9], "close": [10], "volume": [100], "value": [None]}
    records = normalize_candlestick(result, "PTT", "1m")
    assert len(records) == 1
    assert not validate_bar_records(records)
    assert not validate_quote(normalize_quote({"last": 10, "marketStatus": "Close"}, "PTT"))


def test_validation_rejects_duplicate_and_bad_ohlc() -> None:
    records = _bars(1)
    bad = records[0].__class__(records[0].timestamp, "PTT", "1m", Decimal("10"), Decimal("8"), Decimal("9"), Decimal("10"), Decimal("-1"), None, "settrade", records[0].retrieved_at, "UTC")
    issues = validate_bar_records([bad, bad])
    assert {issue.code for issue in issues} >= {"DUPLICATE", "OHLC_INCONSISTENT", "NEGATIVE_VOLUME"}


def test_aggregation_preserves_gaps_and_flags_incomplete() -> None:
    aggregated = aggregate_bars(_bars(5), 5)
    assert len(aggregated) == 1
    assert aggregated[0].bar.interval == "5m"
    assert aggregated[0].bar.volume == Decimal("500")
    assert not aggregated[0].incomplete_bucket
    assert aggregate_bars(_bars(3), 5)[0].incomplete_bucket


def test_rate_limiter_and_retry_are_bounded() -> None:
    limiter = RateLimiter(10)
    assert limiter.acquire() == 0
    assert is_retryable(ConnectionError("temporary"))
    assert not is_retryable(ValueError("bad request"))
    attempts = []
    result = call_with_retries(lambda: attempts.append(1) or "ok", retries=2, sleep=lambda _: None)
    assert result == "ok" and len(attempts) == 1


def test_storage_append_and_checkpoint_resume() -> None:
    with TemporaryDirectory(dir=Path("data/pilot")) as directory:
        tmp_path = Path(directory)
        storage = PilotStorage(tmp_path)
        storage.append_jsonl("raw/realtime/test.jsonl", {"symbol": "PTT"})
        storage.append_jsonl("raw/realtime/test.jsonl", {"symbol": "KTB"})
        storage.write_checkpoint("test", {"last": "PTT"})
        assert storage.read_checkpoint("test") == {"last": "PTT"}
        assert len((tmp_path / "raw/realtime/test.jsonl").read_text().splitlines()) == 2


def test_orderbook_normalization_and_quality() -> None:
    payload = {"symbol": "PTT", "bid_price1": 10, "bid_price2": 9.9, "ask_price1": 10.1, "ask_price2": 10.2, "bid_volume1": 100, "ask_volume1": 200}
    rows = normalize_bid_offer(payload)
    quality = assess_orderbook(payload)
    assert len(rows) == 20
    assert quality["best_bid"] == Decimal("10")
    assert quality["best_ask"] == Decimal("10.1")
    assert quality["spread"] == Decimal("0.1")
    assert quality["crossed"] is False
    assert quality["bid_depth_1"] == Decimal("100")
    assert quality["ask_depth_1"] == Decimal("200")
    assert quality["imbalance_1"] == Decimal("-0.3333333333333333333333333333")


def test_current_set50_artifact_is_exactly_50() -> None:
    import csv
    path = Path("reports/current_set50_universe.csv")
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    assert len(rows) == 50
    assert len({row["symbol"] for row in rows}) == 50


def test_rotation_is_strategy_neutral_and_below_topic_limit() -> None:
    scheduler = RotationScheduler([f"S{i}" for i in range(50)], max_topics=35, interval_seconds=300)
    assert [len(group) for group in scheduler.groups] == [35, 15]
    assert max(map(len, scheduler.groups)) <= 35
    assert scheduler.group(1).symbols[0] == "S35"


def test_session_labels_and_execution_diagnostics() -> None:
    timestamp = datetime(2026, 1, 2, 3, tzinfo=timezone.utc)
    assert session_state(timestamp) == "CONTINUOUS_MORNING"
    metrics = spread_metrics(Decimal("10"), Decimal("10.1"))
    assert metrics["mid_price"] == Decimal("10.05")
    assert book_sweep_vwap([(Decimal("10.1"), Decimal("5")), (Decimal("10.2"), Decimal("5"))], Decimal("7")) == Decimal("10.12857142857142857142857143")
    assert ioc_fill_status("BUY", Decimal("10.2"), Decimal("7"), [(Decimal("10.1"), Decimal("5")), (Decimal("10.2"), Decimal("5"))]) == "FULL_DEPTH_AVAILABLE"
    assert classify_daily_book(True, False) == "DAILY_ONLY"

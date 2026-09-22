from __future__ import annotations

import json
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
from scripts.run_settrade_collector import candle_window, collect_bid_offer, collect_candles


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


def test_checkpoint_does_not_reuse_stale_fixed_temp_file(tmp_path: Path) -> None:
    storage = PilotStorage(tmp_path)
    stale = tmp_path / "checkpoints" / "candles.json.tmp"
    stale.write_text("stale pilot temp data", encoding="utf-8")
    storage.write_checkpoint("candles", {"symbols_completed": 50})
    assert storage.read_checkpoint("candles") == {"symbols_completed": 50}
    assert stale.exists()


def test_candle_window_is_current_bangkok_day() -> None:
    start, end = candle_window(datetime.fromisoformat("2026-09-21T16:00:00+00:00"))
    assert (start, end) == ("2026-09-21T00:00:00", "2026-09-22T00:00:00")


def test_candle_collection_passes_explicit_current_day_window(tmp_path: Path) -> None:
    calls = []

    class Client:
        def candlestick(self, symbol, interval, **kwargs):
            calls.append((symbol, interval, kwargs))
            return {"time": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "value": []}

    collect_candles(Client(), PilotStorage(tmp_path), ["PTT"], 100, datetime.fromisoformat("2026-09-21T16:00:00+00:00"))
    assert calls == [("PTT", "1m", {"limit": 100, "start": "2026-09-21T00:00:00", "end": "2026-09-22T00:00:00"})]


def test_stale_candle_response_is_not_counted_as_completed(tmp_path: Path) -> None:
    class Client:
        def candlestick(self, symbol, interval, **kwargs):
            return {"time": ["1789720200"], "open": [10], "high": [10], "low": [10], "close": [10], "volume": [1], "value": [0]}

    result = collect_candles(Client(), PilotStorage(tmp_path), ["PTT"], 100, datetime.fromisoformat("2026-09-21T16:00:00+00:00"))
    assert result["status"] == "STALE_RESPONSE"
    assert result["symbols"] == 0
    storage_checkpoint = PilotStorage(tmp_path).read_checkpoint("candles_PTT")
    assert storage_checkpoint
    assert storage_checkpoint["status"] == "STALE_RESPONSE"


def test_empty_current_session_response_is_explicit_no_data(tmp_path: Path) -> None:
    class Client:
        def candlestick(self, symbol, interval, **kwargs):
            return {"time": [], "open": [], "high": [], "low": [], "close": [], "volume": [], "value": []}

    result = collect_candles(Client(), PilotStorage(tmp_path), ["PTT"], 100, datetime.fromisoformat("2026-09-22T04:00:00+00:00"))
    assert result["status"] == "NO_DATA"
    assert result["symbols"] == 0
    assert result["no_data_symbols"] == ["PTT"]
    assert PilotStorage(tmp_path).read_checkpoint("candles_PTT")["status"] == "NO_DATA"


def test_collector_success_main_path_emits_json_and_returns_zero(monkeypatch, capsys) -> None:
    import sys
    import scripts.run_settrade_collector as collector

    monkeypatch.setattr(sys, "argv", ["run_settrade_collector.py", "--mode", "candles"])
    monkeypatch.setattr(collector, "run", lambda _args: {"status": "SUCCESS", "orders_placed": 0})
    assert collector.main() == 0
    output = capsys.readouterr().out.strip()
    assert json.loads(output) == {"orders_placed": 0, "status": "SUCCESS"}


def test_bid_offer_collects_callback_events_and_respects_topic_ceiling(tmp_path: Path, monkeypatch) -> None:
    class Subscription:
        def __init__(self, symbol, callback):
            self.symbol, self.callback = symbol, callback
        def start(self):
            self.callback({"data": {"symbol": self.symbol, "bid_price1": 10, "ask_price1": 10.1}})
        def stop(self):
            return None

    class Realtime:
        token = "dispatcher"
        def _fetch_host_token(self):
            return None
        def subscribe_bid_offer(self, symbol, callback):
            return Subscription(symbol, callback)
        def _stop(self):
            return None

    class Client:
        def realtime(self):
            return Realtime()

    clock = iter([0.0, 2.0])
    monkeypatch.setattr("scripts.run_settrade_collector.time.monotonic", lambda: next(clock))
    monkeypatch.setattr("scripts.run_settrade_collector.time.sleep", lambda _: None)
    result = collect_bid_offer(Client(), PilotStorage(tmp_path), [f"S{i}" for i in range(50)], 35, 300, 1)
    assert result["events"] == 35
    assert result["active_topics"] == 35
    assert len((tmp_path / "raw/bid_offer/events.jsonl").read_text(encoding="utf-8").splitlines()) == 35
    normalized = (tmp_path / "normalized/bid_offer/data.csv").read_text(encoding="utf-8")
    assert "collector_session_id" in normalized
    assert len(normalized.splitlines()) == 35 * 20 + 1


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

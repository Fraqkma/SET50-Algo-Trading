from __future__ import annotations

import json
import socket
from datetime import date
from pathlib import Path

import pandas as pd
from types import SimpleNamespace

from src.data.settrade.health import collect_health, freshness_status, is_partial_day
from src.data.settrade.integrity import scan_integrity
from src.data.settrade.paths import resolve_data_root
from src.data.settrade.automation import AlreadyRunningError, SingleInstanceLock
from src.data.settrade.disk import check_disk
from src.data.settrade.storage import PilotStorage
from scripts.run_settrade_collector import collect_candles
from ui.data_catalog import discover_paths, load_settrade_candles


def test_repo_relative_and_external_data_root_resolution(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SET50_DATA_ROOT", raising=False)
    assert resolve_data_root(tmp_path, "data/pilot/settrade") == (tmp_path / "data/pilot/settrade").resolve()

    monkeypatch.setenv("SET50_DATA_ROOT", "E:/Research Data")
    assert resolve_data_root(tmp_path) == Path("E:/Research Data/pilot/settrade")


def test_dotenv_data_root_and_ui_select_same_external_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("SET50_DATA_ROOT", raising=False)
    (tmp_path / ".env").write_text("SET50_DATA_ROOT=E:/shared-data\n", encoding="utf-8")
    external = Path("E:/shared-data/pilot/settrade")
    assert resolve_data_root(tmp_path) == external
    paths = discover_paths(tmp_path)
    assert paths.settrade_root == external


def test_ui_does_not_fall_back_to_empty_repo_data_when_external_root_set(tmp_path: Path, monkeypatch) -> None:
    external = tmp_path / "mounted-data"
    monkeypatch.setenv("SET50_DATA_ROOT", str(external))
    path = external / "pilot/settrade/normalized/bars_1m/data.csv"
    path.parent.mkdir(parents=True)
    pd.DataFrame([{"timestamp": "2026-10-06T03:00:00+00:00", "symbol": "PTT", "open": 10, "high": 10, "low": 10, "close": 10, "volume": 5}]).to_csv(path, index=False)

    paths = discover_paths(tmp_path)
    loaded = load_settrade_candles(paths, "1m", "PTT")
    assert len(loaded) == 1
    assert paths.settrade_root == external / "pilot/settrade"


def test_health_uses_row_timestamps_and_distinguishes_daily_sources(tmp_path: Path, monkeypatch) -> None:
    data_root = tmp_path / "data/pilot/settrade"
    candle = data_root / "normalized/bars_1m/data.csv"
    candle.parent.mkdir(parents=True)
    pd.DataFrame([
        {"timestamp": "2026-10-01T05:29:00+00:00", "symbol": "AAA"},
        {"timestamp": "2026-10-01T05:30:00+00:00", "symbol": "BBB"},
    ]).to_csv(candle, index=False)
    (tmp_path / "reports").mkdir()
    (tmp_path / "reports/exploratory_market_view_summary.json").write_text(json.dumps({"first_date": "2010-01-04", "last_date": "2026-10-03", "rows": 2, "current_universe_with_data": 1}), encoding="utf-8")
    (tmp_path / "reports/settrade_collection_audit.json").write_text(json.dumps({"daily_collection": {"2026-10-01": {"quality": "PARTIAL_SESSION_PROBABLE_COLLECTOR_OR_LOG_GAP"}}}), encoding="utf-8")
    config = tmp_path / "config"
    config.mkdir()
    (config / "settrade_collection.yaml").write_text("current_set50: [AAA]\n", encoding="utf-8")
    raw = tmp_path / "data/raw/market_data/AAA_BK.csv"
    raw.parent.mkdir(parents=True)
    raw.write_text("Date,Open,High,Low,Close,Volume\n2026-10-03,10,11,9,10,5\n", encoding="utf-8")

    health = collect_health(tmp_path, data_root)
    candles = health["datasets"]["candles_1m"]
    assert candles["earliest"] == "2026-10-01T12:29:00+07:00"
    assert candles["latest"] == "2026-10-01T12:30:00+07:00"
    assert candles["rows"] == 2 and candles["symbols"] == 2
    assert candles["partial_day"] is True
    assert candles["freshness_status"] == "PARTIAL"
    assert health["datasets"]["exploratory_market_view"]["latest"] == "2026-10-03"
    assert health["datasets"]["candles_5m"]["freshness_status"] == "NO_DATA"


def test_partial_day_and_freshness_classification_are_deterministic() -> None:
    latest = pd.Timestamp("2026-10-07T03:00:00Z").tz_convert("Asia/Bangkok")
    assert is_partial_day(latest, date(2026, 10, 7))
    assert not is_partial_day(latest, date(2026, 10, 8))
    assert freshness_status("2026-10-07", date(2026, 10, 7)) == "FRESH"
    assert freshness_status("2026-10-01", date(2026, 10, 7)) == "AGING"
    assert freshness_status(None, date(2026, 10, 7)) == "NO_DATA"


def test_integrity_scan_flags_malformed_final_jsonl_without_mutating_source(tmp_path: Path) -> None:
    path = tmp_path / "raw/bid_offer/events.jsonl"
    path.parent.mkdir(parents=True)
    original = b'{"received_at":"2026-10-01T00:00:00Z","symbol":"PTT"}\n{"received_at":"truncated"'
    path.write_bytes(original)

    finding = scan_integrity(tmp_path)[0]
    assert finding["rows"] == 1
    assert finding["malformed_rows"] == 1
    assert finding["truncated_final_record"] is True
    assert path.read_bytes() == original


def test_integrity_scan_finds_zero_byte_artifact(tmp_path: Path) -> None:
    path = tmp_path / "normalized/bid_offer/data.csv"
    path.parent.mkdir(parents=True)
    path.touch()
    assert scan_integrity(tmp_path)[0]["issues"] == ["ZERO_BYTE"]


def test_integrity_scan_flags_interrupted_final_csv_row(tmp_path: Path) -> None:
    path = tmp_path / "normalized/bid_offer/data.csv"
    path.parent.mkdir(parents=True)
    path.write_text("retrieved_at,symbol,side,level\n2026-10-01T00:00:00Z,PTT,bid,1\n2026-10-01T00:00:01Z,PTT,bid", encoding="utf-8")

    finding = scan_integrity(tmp_path)[0]
    assert finding["malformed_rows"] == 1
    assert finding["truncated_final_record"] is True
    assert "TRUNCATED_FINAL_RECORD" in finding["issues"]


def test_disk_space_check_uses_configured_data_filesystem(tmp_path: Path, monkeypatch) -> None:
    inspected: list[Path] = []

    def disk_usage(path: Path):
        inspected.append(Path(path))
        return SimpleNamespace(total=100, used=20, free=80)

    monkeypatch.setattr("src.data.settrade.disk.shutil.disk_usage", disk_usage)
    check_disk(tmp_path / "external-market-data")
    assert inspected == [tmp_path]


def test_failed_candle_persistence_does_not_advance_checkpoint(tmp_path: Path, monkeypatch) -> None:
    storage = PilotStorage(tmp_path)

    class Client:
        def candlestick(self, symbol, interval, **kwargs):
            return {"time": ["1790821800"], "open": [10], "high": [11], "low": [9], "close": [10], "volume": [2], "value": [20]}

    def fail(*args, **kwargs):
        raise OSError("disk full")

    monkeypatch.setattr(storage, "append_csv", fail)
    try:
        collect_candles(Client(), storage, ["PTT"], 100, pd.Timestamp("2026-10-01T05:00:00Z").to_pydatetime())
    except OSError:
        pass
    else:
        raise AssertionError("persistence failure should fail the collection cycle")
    assert not (tmp_path / "checkpoints/candles_PTT.json").exists()


def test_candle_replay_is_idempotent(tmp_path: Path) -> None:
    storage = PilotStorage(tmp_path)
    rows = [{"timestamp": "2026-10-01T05:00:00+00:00", "symbol": "PTT", "interval": "1m", "close": 10}]
    fields = ["timestamp", "symbol", "interval", "close"]
    key = ("symbol", "interval", "timestamp")

    assert storage.append_csv_deduplicated("normalized/bars_1m/data.csv", rows, fields, key)["written"] == 1
    assert storage.append_csv_deduplicated("normalized/bars_1m/data.csv", rows, fields, key)["duplicates"] == 1
    assert len(pd.read_csv(tmp_path / "normalized/bars_1m/data.csv")) == 1


def test_stale_lock_is_recovered_without_touching_live_runner(tmp_path: Path) -> None:
    lock_path = tmp_path / "daily.lock"
    lock_path.write_text(json.dumps({"pid": 0, "host": socket.gethostname(), "token": "stale"}), encoding="utf-8")
    lock = SingleInstanceLock(lock_path)
    lock.acquire()
    try:
        assert json.loads(lock_path.read_text(encoding="utf-8"))["token"] == lock.token
    finally:
        lock.release()
    assert not lock_path.exists()


def test_lock_from_another_host_is_not_deleted(tmp_path: Path) -> None:
    lock_path = tmp_path / "daily.lock"
    lock_path.write_text(json.dumps({"pid": 0, "host": "different-host", "token": "remote"}), encoding="utf-8")
    lock = SingleInstanceLock(lock_path)
    try:
        lock.acquire()
    except AlreadyRunningError:
        pass
    else:
        raise AssertionError("remote-host lock must be treated as active")
    assert json.loads(lock_path.read_text(encoding="utf-8"))["token"] == "remote"

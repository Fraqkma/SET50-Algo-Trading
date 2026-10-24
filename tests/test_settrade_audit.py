from __future__ import annotations

from pathlib import Path

import pandas as pd

from src.data.settrade.audit import bbo_audit, candle_audit
from scripts.audit_settrade_collection import classify_runtime_market_day


def test_bbo_audit_counts_symbols_and_duplicate_keys(tmp_path: Path) -> None:
    path = tmp_path / "normalized" / "bid_offer"
    path.mkdir(parents=True)
    rows = [
        {"retrieved_at": "2026-09-23T03:00:00Z", "symbol": "PTT", "side": "bid", "level": 1, "price": 10, "volume": 100, "collector_session_id": "s", "generation": 0, "rotation_group": 0},
        {"retrieved_at": "2026-09-23T03:00:00Z", "symbol": "PTT", "side": "ask", "level": 1, "price": 11, "volume": 100, "collector_session_id": "s", "generation": 0, "rotation_group": 0},
    ]
    pd.DataFrame(rows).to_csv(path / "data.csv", index=False)
    report = bbo_audit(tmp_path, ["PTT"], [["PTT"]])
    assert report["rows"] == 2
    assert report["duplicate_keys"] == 0
    assert report["persisted_rows"] == 2
    assert report["negative_price"] == 0
    assert report["negative_volume"] == 0
    assert report["locked_or_crossed_best_quotes"] == 0
    assert report["days"]["2026-09-23"]["groups"][0]["observed_symbols"] == 1


def test_candle_audit_reports_per_day_quality(tmp_path: Path) -> None:
    path = tmp_path / "normalized" / "bars_1m"
    path.mkdir(parents=True)
    pd.DataFrame([{"timestamp": "2026-09-23T02:30:00Z", "symbol": "PTT", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100}]).to_csv(path / "data.csv", index=False)
    report = candle_audit(tmp_path)
    assert report["timeframes"]["1m"]["days"]["2026-09-23"]["status"] == "SPARSE"


def test_runtime_nontrading_flag_does_not_hide_persisted_rows() -> None:
    runtime = {"market_day": False}
    assert classify_runtime_market_day(runtime, raw_bbo_events=3, candle_rows=0) == "RUNTIME_MARKET_DAY_CONFLICT_WITH_DATA"
    assert classify_runtime_market_day(runtime, raw_bbo_events=0, candle_rows=1) == "RUNTIME_MARKET_DAY_CONFLICT_WITH_DATA"
    assert classify_runtime_market_day(runtime, raw_bbo_events=0, candle_rows=0) == "NON_TRADING_DAY"

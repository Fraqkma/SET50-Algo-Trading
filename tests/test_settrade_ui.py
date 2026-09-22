from __future__ import annotations

from pathlib import Path

import pandas as pd

from ui.data_catalog import DataPaths, load_settrade_bbo, load_settrade_candles, settrade_availability


def _paths(root: Path) -> DataPaths:
    return DataPaths(root, root / "constituents.csv", root / "audit.csv", root / "acquisition.csv", root / "metadata.json", root / "data" / "pilot" / "settrade", ())


def test_settrade_catalog_loads_local_candles_and_availability(tmp_path: Path) -> None:
    root = tmp_path
    candle_path = root / "data" / "pilot" / "settrade" / "normalized" / "bars_1m" / "data.csv"
    candle_path.parent.mkdir(parents=True)
    pd.DataFrame([{"timestamp": "2026-09-21T03:00:00+00:00", "symbol": "PTT", "open": 10, "high": 11, "low": 9, "close": 10, "volume": 100}]).to_csv(candle_path, index=False)
    paths = _paths(root)
    frame = load_settrade_candles(paths, "1m", "PTT")
    assert len(frame) == 1
    assert frame.iloc[0]["source_label"] == "SETTRADE_API_CANDLE"
    index = settrade_availability(paths)
    assert index.iloc[0]["date"] == "2026-09-21"


def test_settrade_catalog_keeps_bbo_event_rows_separate(tmp_path: Path) -> None:
    root = tmp_path
    bbo_path = root / "data" / "pilot" / "settrade" / "normalized" / "bid_offer" / "data.csv"
    bbo_path.parent.mkdir(parents=True)
    rows = [{"retrieved_at": "2026-09-21T03:00:00+00:00", "symbol": "PTT", "side": "bid", "level": 1, "price": 10, "volume": 100, "collector_session_id": "s", "generation": 0, "rotation_group": 0}]
    pd.DataFrame(rows).to_csv(bbo_path, index=False)
    frame = load_settrade_bbo(_paths(root), "PTT")
    assert len(frame) == 1
    assert frame.iloc[0]["symbol"] == "PTT"
    assert settrade_availability(_paths(root)).iloc[0]["datatype"] == "bbo"

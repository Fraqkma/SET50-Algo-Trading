from __future__ import annotations

from decimal import Decimal

import pandas as pd

from scripts.build_settrade_execution_diagnostics import _snapshot_rows, _summarize


def test_snapshot_diagnostics_keep_both_sides_and_sweep_only_visible_depth() -> None:
    rows = []
    for side, levels in (("bid", [(10.00, 100), (9.99, 200)]), ("ask", [(10.02, 100), (10.04, 200)])):
        for level, (price, volume) in enumerate(levels, start=1):
            rows.append({"retrieved_at": "2026-09-23T03:00:00Z", "symbol": "PTT", "side": side, "level": level, "price": price, "volume": volume, "collector_session_id": "s", "generation": 1, "rotation_group": 0})
    snapshots = _snapshot_rows(pd.DataFrame(rows))
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert Decimal(snapshot["spread"]) == Decimal("0.02")
    assert Decimal(snapshot["bid_depth_3"]) == Decimal("300")
    assert Decimal(snapshot["ask_depth_3"]) == Decimal("300")
    assert snapshot["buy_100000_fillable"] is False
    assert snapshot["sell_100000_fillable"] is False
    assert snapshot["buy_100000_visible_quantity"] == 300
    assert snapshot["sell_100000_visible_quantity"] == 300
    assert snapshot["buy_100000_visible_vwap"] is not None


def test_execution_summary_reports_time_and_symbol_groups() -> None:
    rows = []
    for side, price in (("bid", 10.00), ("ask", 10.02)):
        rows.append({"symbol": "PTT", "trading_day": "2026-09-23", "session": "morning", "time_bucket": "10:00", "spread": "0.02", "spread_ticks": "1", "spread_bps": "19.98", "best_bid_depth": "100", "best_ask_depth": "120", "bid_depth_3": "100", "ask_depth_3": "120", "bid_depth_5": "100", "ask_depth_5": "120", "bid_depth_10": "100", "ask_depth_10": "120", "buy_100000_fillable": False, "sell_100000_fillable": False, "buy_100000_slippage_bps": None, "sell_100000_slippage_bps": None, "buy_100000_slippage_ticks": None, "sell_100000_slippage_ticks": None, "buy_500000_fillable": False, "sell_500000_fillable": False, "buy_500000_slippage_bps": None, "sell_500000_slippage_bps": None, "buy_500000_slippage_ticks": None, "sell_500000_slippage_ticks": None, "buy_1000000_fillable": False, "sell_1000000_fillable": False, "buy_1000000_slippage_bps": None, "sell_1000000_slippage_bps": None, "buy_1000000_slippage_ticks": None, "sell_1000000_slippage_ticks": None})
    frame = pd.DataFrame(rows[:1])
    for notional in (100_000, 500_000, 1_000_000):
        for side in ("buy", "sell"):
            prefix = f"{side}_{notional}"
            frame[f"{prefix}_quantity"] = 10_000
            frame[f"{prefix}_visible_quantity"] = 100
            frame[f"{prefix}_visible_slippage_bps"] = 0.0
            frame[f"{prefix}_visible_slippage_ticks"] = 0.0
    stats, groups = _summarize(frame)
    assert stats["spread_tick_fractions"]["at_most_one_tick"] == 1
    assert {tuple(group["group_by"]) for group in groups} >= {("symbol",), ("time_bucket",), ("symbol", "session")}

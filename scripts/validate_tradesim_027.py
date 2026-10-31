"""Controlled simulator-only regression inputs, never market-data ingestion."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--version", choices=("0.2.6", "0.2.7"), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if sys.version_info[:3] != (3, 13, 0):
        raise RuntimeError("Exact Python 3.13.0 required")
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root / "tools/kgi_tradesim" / args.version))
    sys.path.insert(0, str(root))
    import pandas as pd
    from tradeSim import TradeSim, CommissionService, Order
    from src.competition.tradesim_bridge.observation import OrderObserver
    from src.competition.metrics import fifo_metrics_from_fills

    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=False)
    os.chdir(args.output)
    results = args.output / "result"
    observer = OrderObserver(Order.order, CommissionService.commissionService) if args.version == "0.2.7" else None
    cases = []

    def case(name: str, *, kind: str = "Limit", side: str = "Buy", price: float = 42.25,
             last: float = 42.0, volume: int = 350, quantity: int = 1000,
             flag: str = "Sell", day: str = "2026-10-21", cap: int = 100000,
             second: bool = False) -> dict:
        sim = TradeSim.tradeSim(name, folder="result", load_existing=False, current_date=day)
        if observer:
            observer.attach(sim.execution)
        if side == "Sell":
            seed = {"ShareCode": "PTT", "TradeDateTime": pd.Timestamp(day + " 10:00:00"),
                    "LastPrice": last, "Volume": 10000, "Flag": "Sell"}
            sim.record_tick(seed)
            sim.create_order_at_market(2000, "Buy", "PTT", 100000, 100000, seed)
        row = {"ShareCode": "PTT", "TradeDateTime": pd.Timestamp(day + " 10:01:00"),
               "LastPrice": last, "Volume": volume, "Flag": flag}
        sim.record_tick(row)
        before = sim.portfolio.get_cash_balance()
        before_holdings = sim.portfolio.get_total_stock_volume_by_symbol("PTT")
        if kind == "Limit":
            reply = sim.create_order_to_limit(quantity, price, side, "PTT", cap, cap, row)
            sim.isMatch(row)
        else:
            reply = sim.create_order_at_market(quantity, side, "PTT", cap, cap, row)
        immediate_holdings = sim.portfolio.get_total_stock_volume_by_symbol("PTT")
        immediate_cash = sim.portfolio.get_cash_balance()
        pending_first = sim.get_open_orders()
        if second:
            next_row = {**row, "TradeDateTime": row["TradeDateTime"] + pd.Timedelta(minutes=1), "LastPrice": last - 0.5}
            sim.record_tick(next_row)
            sim.isMatch(next_row)
        pending_last = sim.get_open_orders()
        sim.flushTransactionLog()
        path = results / name / f"{name}_transaction_log.csv"
        fills = list(csv.DictReader(path.open(encoding="utf-8-sig"))) if path.exists() else []
        ledger, metrics = fifo_metrics_from_fills(fills, 0.00157, 0.07)
        sim.save_portfolio()
        next_day = TradeSim.tradeSim(name, folder="result", current_date="2026-10-22")
        result = {"case": name, "kind": kind, "side": side, "day": day,
                  "requested_quantity": quantity, "tick_volume": volume, "limit": price,
                  "latest_price": last, "reply": str(reply), "rejected": isinstance(reply, Exception),
                  "cash_before": before, "cash_after_first": immediate_cash,
                  "holdings_before": before_holdings, "holdings_after_first": immediate_holdings,
                  "holdings_after_second": sim.portfolio.get_total_stock_volume_by_symbol("PTT"),
                  "next_day_holdings": next_day.portfolio.get_total_stock_volume_by_symbol("PTT"),
                  "pending_first": pending_first, "pending_last": pending_last,
                  "next_day_pending": next_day.get_open_orders(), "fills": fills,
                  "fifo_metrics": metrics, "fifo_lot_count": len(ledger.lots)}
        cases.append(result)
        return result

    case("large_limit", second=True)
    case("close_limit", price=42.0, second=True)
    case("invalid_tick", price=42.01)
    case("market_buy", kind="Market", second=True)
    case("market_sell", kind="Market", side="Sell", flag="Buy", second=True)
    case("limit_sell", side="Sell", price=41.75, flag="Buy", second=True)
    case("daily_cap", quantity=1000, cap=250, volume=1000)
    case("auction_limit", flag="ATC")
    case("auction_market", flag="ATC", kind="Market")
    case("sell_band_edge", side="Sell", last=100.0, price=99.75, flag="Buy")
    case("pre_switch_invalid", day="2026-11-15", price=42.1)
    case("post_switch_valid", day="2026-11-16", price=42.1)
    case("below_board_lot", volume=99)
    # Multiple requests share a tick budget; canceled shares never create lots.
    sim = TradeSim.tradeSim("fifo_shared_tick", folder="result", load_existing=False, current_date="2026-10-21")
    if observer:
        observer.attach(sim.execution)
    row = {"ShareCode": "PTT", "TradeDateTime": pd.Timestamp("2026-10-21 11:00:00"), "LastPrice": 42.0, "Volume": 550, "Flag": "Sell"}
    sim.record_tick(row)
    for qty in (300, 400):
        sim.create_order_to_limit(qty, 42.25, "Buy", "PTT", 100000, 100000, row)
        sim.isMatch(row)
    shared_holdings = sim.portfolio.get_total_stock_volume_by_symbol("PTT")
    for minute, qty, vol in ((1, 500, 250), (2, 300, 350)):
        sell = {**row, "TradeDateTime": row["TradeDateTime"] + pd.Timedelta(minutes=minute), "Volume": vol, "Flag": "Buy"}
        sim.record_tick(sell)
        sim.create_order_to_limit(qty, 41.75, "Sell", "PTT", 100000, 100000, sell)
        sim.isMatch(sell)
    sim.flushTransactionLog()
    fifo_path = results / "fifo_shared_tick/fifo_shared_tick_transaction_log.csv"
    fifo_fills = list(csv.DictReader(fifo_path.open(encoding="utf-8-sig"))) if fifo_path.exists() else []
    fifo_ledger, fifo_metrics = fifo_metrics_from_fills(fifo_fills, 0.00157, 0.07)

    delayed = TradeSim.tradeSim("cross_symbol", folder="result", load_existing=False, current_date="2026-10-21")
    if observer:
        observer.attach(delayed.execution)
    other = {**row, "ShareCode": "KBANK"}
    delayed.record_tick(other)
    delayed.create_order_to_limit(100, 42.25, "Buy", "PTT", 100000, 100000, other)
    delayed.isMatch(other)
    pending_other = delayed.get_open_orders()
    later = {**row, "TradeDateTime": row["TradeDateTime"] + pd.Timedelta(minutes=1)}
    delayed.record_tick(later)
    delayed.isMatch(later)
    delayed.flushTransactionLog()
    delayed_path = results / "cross_symbol/cross_symbol_transaction_log.csv"
    delayed_fills = list(csv.DictReader(delayed_path.open(encoding="utf-8-sig"))) if delayed_path.exists() else []
    checks = {}
    if args.version == "0.2.7":
        by = {c["case"]: c for c in cases}
        checks = {
            "limit_tick_cap": by["large_limit"]["holdings_after_first"] == 300,
            "no_second_match": by["large_limit"]["holdings_after_second"] == 300,
            "close_does_not_fill": by["close_limit"]["holdings_after_second"] == 0,
            "valid_price_fills": by["large_limit"]["fills"][0]["Price"] == "42.25",
            "invalid_price_rejects": by["invalid_tick"]["rejected"],
            "market_buy_cap": by["market_buy"]["holdings_after_first"] == 300,
            "market_sell_cap": by["market_sell"]["holdings_after_first"] == 1700,
            "sell_price": float(by["limit_sell"]["fills"][-1]["Price"]) == 41.75,
            "market_sell_price": float(by["market_sell"]["fills"][-1]["Price"]) == 41.75,
            "daily_cap_clips": by["daily_cap"]["holdings_after_first"] == 200,
            "auctions_excluded": all(by[n]["holdings_after_first"] == 0 for n in ("auction_limit", "auction_market")),
            "sell_band_edge": float(by["sell_band_edge"]["fills"][-1]["Price"]) == 99.75,
            "pre_switch": by["pre_switch_invalid"]["rejected"],
            "post_switch": by["post_switch_valid"]["holdings_after_first"] == 300,
            "board_lot_floor": by["below_board_lot"]["holdings_after_first"] == 0,
            "all_books_empty": all(not c["pending_first"] and not c["next_day_pending"] for c in cases),
            "cross_day_holdings": by["large_limit"]["next_day_holdings"] == 300,
            "fee_only_actual_fill": abs(by["large_limit"]["cash_before"] - by["large_limit"]["cash_after_first"] - 300*42.25*1.0016799) < 1e-6,
            "shared_tick_cap": shared_holdings == 500,
            "fifo_actual_lots": len(fifo_ledger.lots) == 2 and sum(l.initial_quantity for l in fifo_ledger.lots) == 500,
            "fifo_partial_sells": fifo_metrics["round_trips"] == 2 and sim.portfolio.get_total_stock_volume_by_symbol("PTT") == 0,
            "cross_symbol_deferred_once": bool(pending_other) and not delayed.get_open_orders() and len(delayed_fills) == 1,
        }
        ladders = {day: {str(price): CommissionService.commissionService._get_slippage(price, day)
                         for price in (1, 2, 5, 10, 25, 42, 50, 100, 200, 400)}
                   for day in ("2026-11-15", "2026-11-16")}
    else:
        ladders = None
    report = {"version": args.version, "python": sys.version, "evidence_class": "CONTROLLED_SIMULATOR_FIXTURES_NOT_MARKET_DATA",
              "cases": cases, "checks": checks, "all_checks_pass": bool(checks) and all(checks.values()),
              "tick_ladders": ladders, "observed_orders": observer.snapshot() if observer else [],
              "fifo_shared_tick": {"holdings_after_buys": shared_holdings, "fills": fifo_fills, "metrics": fifo_metrics},
              "cross_symbol": {"pending_before_own_tick": pending_other, "fills": delayed_fills,
                               "note": "Cross-symbol limits wait for the first eligible own-symbol tick; compare Placed versus Timestamp."},
              "rejections": observer.rejections if observer else [], "real_orders_placed": 0}
    (args.output / "matrix.json").write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps({"report": str(args.output / "matrix.json"), "checks": checks}))
    if checks and not all(checks.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()

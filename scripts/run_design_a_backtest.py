"""Run the first deterministic Design A research backtest.

This script reads approved market data only and writes reports under
``reports/``. It never modifies raw data. The tick-size function is explicit
and injected into the engine; replace it only with an approved mapping.
"""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import BacktestEngine, ExecutionPolicy
from src.data.features import build_features
from src.data.research import load_approved_market_data
from src.data.eligibility import MarketDataEligibilityGate

REPORT_DIR = ROOT / "reports"


def set_tick_size(price: Decimal) -> Decimal:
    """Explicit SET price-band tick mapping injected into this run.

    This mapping is deliberately kept in code at the call boundary rather than
    guessed by the engine. It must be replaced if the competition supplies a
    different official schedule.
    """
    if price < Decimal("2"):
        return Decimal("0.01")
    if price < Decimal("5"):
        return Decimal("0.02")
    if price < Decimal("10"):
        return Decimal("0.05")
    if price < Decimal("25"):
        return Decimal("0.10")
    if price < Decimal("100"):
        return Decimal("0.25")
    if price < Decimal("200"):
        return Decimal("0.50")
    if price < Decimal("400"):
        return Decimal("1")
    return Decimal("2")


class RecordingGate:
    def __init__(self, gate: MarketDataEligibilityGate) -> None:
        self.gate = gate
        self.reasons: Counter[str] = Counter()

    def assess(self, symbol: str, requested_date):
        decision = self.gate.assess(symbol, requested_date)
        if not decision.eligible:
            self.reasons[decision.reason or "UNKNOWN"] += 1
        return decision

    def membership_end(self, symbol: str, requested_date):
        return self.gate.membership_end(symbol, requested_date)


def _decimal(value: Decimal) -> str:
    return format(value, "f")


def _optional_decimal(value: Decimal | None) -> str | None:
    return None if value is None else _decimal(value)


def _load_features(gate: MarketDataEligibilityGate) -> tuple[dict[str, pd.DataFrame], Counter[str]]:
    manifest = pd.read_csv(ROOT / "data" / "processed" / "approved_market_data_manifest.csv")
    frames: dict[str, pd.DataFrame] = {}
    exclusions: Counter[str] = Counter()
    for symbol in manifest["set_symbol"].astype(str).str.upper():
        try:
            prices = load_approved_market_data(symbol, gate=gate)
            frames[symbol] = build_features(prices)
        except (FileNotFoundError, ValueError) as exc:
            exclusions[f"LOAD_{type(exc).__name__}"] += 1
    return frames, exclusions


def main() -> None:
    base_gate = MarketDataEligibilityGate(ROOT)
    gate = RecordingGate(base_gate)
    feature_frames, load_exclusions = _load_features(base_gate)
    if not feature_frames:
        raise RuntimeError("No approved feature frames were loaded.")
    engine = BacktestEngine(
        initial_cash=Decimal("10000000"),
        top_n=10,
        rebalance_every=3,
        design="A",
        execution_policy=ExecutionPolicy(tick_size=set_tick_size),
        gate=gate,
    )
    result = engine.run(feature_frames)
    snapshots = result.snapshots
    orders = result.orders
    dates = [snapshot.timestamp for snapshot in snapshots]
    non_fills = [event for event in orders if event.status == "NON_FILL"]
    fills = [event for event in orders if event.status == "FILLED"]
    boundary_events = [event for event in orders if event.reason and event.reason.startswith("UNIVERSE_BOUNDARY_EXIT")]
    boundary_fills = [event for event in boundary_events if event.status == "FILLED"]
    boundary_non_fills = [event for event in boundary_events if event.status == "NON_FILL"]
    valuation_gaps = sorted({symbol for snapshot in snapshots for symbol in snapshot.valuation_gaps})
    report = {
        "design": "A",
        "research_period": {"start": dates[0].date().isoformat(), "end": dates[-1].date().isoformat()},
        "observations": len(dates),
        "approved_symbols_loaded": len(feature_frames),
        "starting_capital": _decimal(engine.initial_cash),
        "final_equity": _optional_decimal(result.final_equity),
        "gross_return": _optional_decimal(result.gross_return),
        "net_return": _optional_decimal(result.net_return),
        "volatility": _optional_decimal(result.volatility),
        "maximum_drawdown": _optional_decimal(result.maximum_drawdown),
        "turnover": _decimal(result.turnover),
        "commission": _decimal(result.commission),
        "vat": _decimal(result.vat),
        "total_fees": _decimal(result.total_fees),
        "slippage": _decimal(result.slippage),
        "trade_count": result.trade_count,
        "unique_symbols_traded": result.unique_symbols_traded,
        "rebalance_count": len(result.selections),
        "fills": len(fills),
        "non_fills": len(non_fills),
        "valuation_gaps": valuation_gaps,
        "valuation_complete": result.valuation_complete,
        "complete_valuation_snapshots": result.complete_valuation_snapshots,
        "incomplete_valuation_snapshots": result.incomplete_valuation_snapshots,
        "unvalued_positions": result.unvalued_positions,
        "boundary_exit_events": len(boundary_events),
        "boundary_exit_fills": len(boundary_fills),
        "boundary_exit_non_fills": len(boundary_non_fills),
        "boundary_exit_symbols": sorted({event.symbol for event in boundary_events}),
        "data_exclusions": dict(load_exclusions),
        "eligibility_exclusions": dict(gate.reasons),
        "execution_assumptions": {
            "order_type": "LIMIT",
            "validity": "IOC",
            "commission_rate": "0.00157",
            "vat_rate": "0.07",
            "buy_request": "next_session_open_plus_one_tick",
            "sell_request": "next_session_open_minus_one_tick",
            "fill_rule": "requested_price_inside_low_high",
            "tick_mapping": "scripts/run_design_a_backtest.py:set_tick_size",
        },
        "benchmark": "Design A is the reference; no separate benchmark series was run.",
    }
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "design_a_backtest_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8"
    )
    with (REPORT_DIR / "design_a_backtest_orders.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = list(orders[0].__dataclass_fields__) if orders else []
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for event in orders:
            writer.writerow({field: getattr(event, field) for field in fields})
    with (REPORT_DIR / "design_a_backtest_selections.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["signal_date", "execution_date", "selected_symbols"])
        writer.writeheader()
        for event in result.selections:
            writer.writerow({
                "signal_date": event.signal_date,
                "execution_date": event.execution_date,
                "selected_symbols": "|".join(event.selected_symbols),
            })
    with (REPORT_DIR / "design_a_backtest_snapshots.csv").open("w", encoding="utf-8", newline="") as handle:
        fields = [
            "timestamp", "signal_date", "execution_date", "cash", "positions",
            "market_value", "equity", "gross_return", "net_return", "drawdown", "valuation_gaps",
            "valuation_status", "valuation_gap_reasons", "unvalued_positions",
        ]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for snapshot in result.snapshots:
            writer.writerow({
                "timestamp": snapshot.timestamp,
                "signal_date": snapshot.signal_date,
                "execution_date": snapshot.execution_date,
                "cash": snapshot.cash,
                "positions": json.dumps(snapshot.positions, sort_keys=True),
                "market_value": snapshot.market_value,
                "equity": snapshot.equity,
                "gross_return": snapshot.gross_return,
                "net_return": snapshot.net_return,
                "drawdown": snapshot.drawdown,
                "valuation_gaps": "|".join(snapshot.valuation_gaps),
                "valuation_status": snapshot.valuation_status,
                "valuation_gap_reasons": json.dumps(snapshot.valuation_gap_reasons, sort_keys=True),
                "unvalued_positions": json.dumps(snapshot.unvalued_positions, sort_keys=True),
            })
    (REPORT_DIR / "design_a_backtest_report.md").write_text(_markdown(report), encoding="utf-8")
    print(json.dumps(report, indent=2))


def _markdown(report: dict[str, object]) -> str:
    lines = ["# Design A Backtest Report", "", "This is the first fixed-assumption research run; no optimization or OOS testing was performed.", ""]
    for key, value in report.items():
        if isinstance(value, dict):
            lines.append(f"## {key}")
            for child, child_value in value.items():
                lines.append(f"- `{child}`: `{child_value}`")
        else:
            lines.append(f"- `{key}`: `{value}`")
    lines.append("")
    return "\n".join(lines)


if __name__ == "__main__":
    main()

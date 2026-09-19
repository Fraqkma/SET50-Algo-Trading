"""Run the fixed Design C comparison without changing Design A artifacts."""

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
from src.data.eligibility import MarketDataEligibilityGate
from src.data.features import build_features
from src.data.research import load_approved_market_data
from scripts.run_design_a_backtest import RecordingGate, set_tick_size

REPORT_DIR = ROOT / "reports"


def _load_features(gate: MarketDataEligibilityGate) -> tuple[dict[str, pd.DataFrame], Counter[str]]:
    manifest = pd.read_csv(ROOT / "data" / "processed" / "approved_market_data_manifest.csv")
    frames: dict[str, pd.DataFrame] = {}
    exclusions: Counter[str] = Counter()
    for symbol in manifest["set_symbol"].astype(str).str.upper():
        try:
            frames[symbol] = build_features(load_approved_market_data(symbol, gate=gate))
        except (FileNotFoundError, ValueError) as exc:
            exclusions[f"LOAD_{type(exc).__name__}"] += 1
    return frames, exclusions


def _run(frames: dict[str, pd.DataFrame], design: str):
    gate = RecordingGate(MarketDataEligibilityGate(ROOT))
    engine = BacktestEngine(
        initial_cash=Decimal("10000000"), top_n=10, rebalance_every=3,
        design=design, execution_policy=ExecutionPolicy(tick_size=set_tick_size), gate=gate,
    )
    return engine.run(frames), engine, gate


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _report(result, engine, gate, frames, load_exclusions, design: str) -> dict[str, object]:
    orders = result.orders
    fills = [event for event in orders if event.status == "FILLED"]
    non_fills = [event for event in orders if event.status == "NON_FILL"]
    boundary = [event for event in orders if event.reason and event.reason.startswith("UNIVERSE_BOUNDARY_EXIT")]
    dates = [snapshot.timestamp for snapshot in result.snapshots]
    return {
        "design": design,
        "research_period": {"start": dates[0].date().isoformat(), "end": dates[-1].date().isoformat()},
        "observations": len(dates),
        "approved_symbols_loaded": len(frames),
        "starting_capital": format(engine.initial_cash, "f"),
        "final_equity": _decimal(result.final_equity),
        "gross_return": _decimal(result.gross_return),
        "net_return": _decimal(result.net_return),
        "volatility": _decimal(result.volatility),
        "maximum_drawdown": _decimal(result.maximum_drawdown),
        "turnover": format(result.turnover, "f"),
        "commission": format(result.commission, "f"),
        "vat": format(result.vat, "f"),
        "total_fees": format(result.total_fees, "f"),
        "slippage": format(result.slippage, "f"),
        "fills": len(fills), "non_fills": len(non_fills),
        "trade_count": result.trade_count, "unique_symbols_traded": result.unique_symbols_traded,
        "rebalance_count": len(result.selections),
        "valuation_complete": result.valuation_complete,
        "complete_valuation_snapshots": result.complete_valuation_snapshots,
        "incomplete_valuation_snapshots": result.incomplete_valuation_snapshots,
        "unvalued_positions": result.unvalued_positions,
        "valuation_gaps": sorted({symbol for s in result.snapshots for symbol in s.valuation_gaps}),
        "eligibility_exclusions": dict(gate.reasons),
        "eligibility_exclusion_count": sum(gate.reasons.values()),
        "data_exclusions": dict(load_exclusions),
        "boundary_exit_events": len(boundary),
        "boundary_exit_fills": sum(event.status == "FILLED" for event in boundary),
        "boundary_exit_non_fills": sum(event.status == "NON_FILL" for event in boundary),
        "boundary_exit_symbols": sorted({event.symbol for event in boundary}),
    }


def _write_artifacts(prefix: str, result, report: dict[str, object]) -> None:
    (REPORT_DIR / f"{prefix}_backtest_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    orders = result.orders
    with (REPORT_DIR / f"{prefix}_backtest_orders.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = list(orders[0].__dataclass_fields__) if orders else []
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for event in orders: writer.writerow({field: getattr(event, field) for field in fields})
    with (REPORT_DIR / f"{prefix}_backtest_selections.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["signal_date", "execution_date", "selected_symbols"]); writer.writeheader()
        for event in result.selections:
            writer.writerow({"signal_date": event.signal_date, "execution_date": event.execution_date,
                             "selected_symbols": "|".join(event.selected_symbols)})
    with (REPORT_DIR / f"{prefix}_backtest_snapshots.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["timestamp", "signal_date", "execution_date", "cash", "positions", "market_value", "equity",
                  "gross_return", "net_return", "drawdown", "valuation_gaps", "valuation_status",
                  "valuation_gap_reasons", "unvalued_positions"]
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
        for s in result.snapshots:
            writer.writerow({"timestamp": s.timestamp, "signal_date": s.signal_date, "execution_date": s.execution_date,
                             "cash": s.cash, "positions": json.dumps(s.positions, sort_keys=True), "market_value": s.market_value,
                             "equity": s.equity, "gross_return": s.gross_return, "net_return": s.net_return,
                             "drawdown": s.drawdown, "valuation_gaps": "|".join(s.valuation_gaps),
                             "valuation_status": s.valuation_status, "valuation_gap_reasons": json.dumps(s.valuation_gap_reasons, sort_keys=True),
                             "unvalued_positions": json.dumps(s.unvalued_positions, sort_keys=True)})
    (REPORT_DIR / f"{prefix}_backtest_report.md").write_text(_markdown(f"{prefix.upper()} Backtest Report", report), encoding="utf-8")


def _selection_analysis(a_result, c_result, frames, c_gate) -> dict[str, object]:
    from src.strategies.cross_sectional import rank_time_series_candidates
    a_by_date = {event.signal_date: set(event.selected_symbols) for event in a_result.selections}
    c_by_date = {event.signal_date: set(event.selected_symbols) for event in c_result.selections}
    qualifying: list[int] = []
    differences: list[dict[str, object]] = []
    for event in c_result.selections:
        ranked = rank_time_series_candidates(frames, event.signal_date.date(), top_n=len(frames), gate=c_gate)
        count = len(ranked); qualifying.append(count)
        a_set = a_by_date.get(event.signal_date, set()); c_set = c_by_date.get(event.signal_date, set())
        differences.append({"signal_date": event.signal_date.date().isoformat(), "design_a_only": sorted(a_set - c_set),
                            "design_c_only": sorted(c_set - a_set), "design_a_count": len(a_set), "design_c_count": len(c_set)})
    return {
        "signal_dates": len(qualifying), "fewer_than_10_qualifying_count": sum(n < 10 for n in qualifying),
        "fewer_than_10_qualifying_fraction": (sum(n < 10 for n in qualifying) / len(qualifying)) if qualifying else 0,
        "qualifying_count_average": (sum(qualifying) / len(qualifying)) if qualifying else 0,
        "qualifying_count_median": float(pd.Series(qualifying).median()) if qualifying else 0,
        "selected_count_average": (sum(len(v) for v in c_by_date.values()) / len(c_by_date)) if c_by_date else 0,
        "selected_count_median": float(pd.Series([len(v) for v in c_by_date.values()]).median()) if c_by_date else 0,
        "selection_differences": differences,
    }


def _markdown(title: str, report: dict[str, object]) -> str:
    lines = [f"# {title}", "", "Deterministic fixed-parameter research run; no optimization or OOS tuning was performed.", ""]
    for key, value in report.items():
        if isinstance(value, dict):
            lines.append(f"## {key}")
            lines.extend(f"- `{child}`: `{child_value}`" for child, child_value in value.items())
        else: lines.append(f"- `{key}`: `{value}`")
    return "\n".join(lines) + "\n"


def main() -> None:
    base_gate = MarketDataEligibilityGate(ROOT)
    frames, load_exclusions = _load_features(base_gate)
    a_result, a_engine, a_gate = _run(frames, "A")
    c_result, c_engine, c_gate = _run(frames, "C")
    a_report = _report(a_result, a_engine, a_gate, frames, load_exclusions, "A")
    c_report = _report(c_result, c_engine, c_gate, frames, load_exclusions, "C")
    _write_artifacts("design_c", c_result, c_report)
    analysis = _selection_analysis(a_result, c_result, frames, c_gate)
    comparison = {"research_period": c_report["research_period"], "starting_capital": c_report["starting_capital"],
                  "design_a": a_report, "design_c": c_report, "selection_analysis": analysis,
                  "turnover_difference_c_minus_a": str(Decimal(c_report["turnover"]) - Decimal(a_report["turnover"])),
                  "trade_activity_difference_c_minus_a": c_report["fills"] - a_report["fills"],
                  "interpretation": "Descriptive comparison only; no claim that either design is better and no optimization was performed."}
    (REPORT_DIR / "design_a_vs_c_comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    (REPORT_DIR / "design_a_vs_c_comparison.md").write_text(_markdown("Design A vs Design C Comparison", comparison), encoding="utf-8")
    print(json.dumps(comparison, indent=2))


if __name__ == "__main__":
    main()

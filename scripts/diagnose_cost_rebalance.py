"""Fixed, non-optimizing transaction-cost and rebalance-frequency diagnostics."""

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
from src.strategies.cross_sectional import rank_time_series_candidates
from scripts.run_design_a_backtest import RecordingGate, set_tick_size

REPORTS = ROOT / "reports"
INITIAL = Decimal("10000000")
OFFICIAL_COMMISSION = Decimal("0.00157")
OFFICIAL_VAT = Decimal("0.07")


def load_frames() -> dict[str, pd.DataFrame]:
    gate = MarketDataEligibilityGate(ROOT)
    manifest = pd.read_csv(ROOT / "data" / "processed" / "approved_market_data_manifest.csv")
    return {symbol: build_features(load_approved_market_data(symbol, gate=gate))
            for symbol in manifest["set_symbol"].astype(str).str.upper()}


def run_case(frames, design: str, every: int, commission: Decimal, vat: Decimal, slippage_ticks: int):
    gate = RecordingGate(MarketDataEligibilityGate(ROOT))
    engine = BacktestEngine(initial_cash=INITIAL, top_n=10, rebalance_every=every, design=design,
                            execution_policy=ExecutionPolicy(tick_size=set_tick_size, slippage_ticks=slippage_ticks),
                            commission_rate=commission, vat_rate=vat, gate=gate)
    return engine.run(frames), gate


def candidate_counts(frames, result, gate, cache: dict[str, int]) -> tuple[float, float]:
    counts = []
    for event in result.selections:
        key = event.signal_date.date().isoformat()
        if key not in cache:
            ranked = rank_time_series_candidates(frames, event.signal_date.date(), top_n=len(frames), gate=gate)
            cache[key] = len(ranked)
        counts.append(cache[key])
    return (sum(counts) / len(counts), float(pd.Series(counts).median())) if counts else (0.0, 0.0)


def metrics(result, gate, frames, candidate_cache) -> dict[str, object]:
    orders = result.orders
    fills = [event for event in orders if event.status == "FILLED"]
    nonfills = [event for event in orders if event.status == "NON_FILL"]
    boundary = [event for event in orders if event.reason and event.reason.startswith("UNIVERSE_BOUNDARY_EXIT")]
    avg_candidates, median_candidates = candidate_counts(frames, result, gate, candidate_cache)
    selected_counts = [len(event.selected_symbols) for event in result.selections]
    return {
        "final_equity": None if result.final_equity is None else str(result.final_equity),
        "gross_return": None if result.gross_return is None else str(result.gross_return),
        "net_return": None if result.net_return is None else str(result.net_return),
        "maximum_drawdown": None if result.maximum_drawdown is None else str(result.maximum_drawdown),
        "volatility": None if result.volatility is None else str(result.volatility),
        "turnover": str(result.turnover), "commission": str(result.commission), "vat": str(result.vat),
        "total_fees": str(result.total_fees), "slippage": str(result.slippage),
        "fills": len(fills), "non_fills": len(nonfills), "trade_count": result.trade_count,
        "unique_symbols_traded": result.unique_symbols_traded, "rebalance_events": len(result.selections),
        "average_qualifying_candidates": avg_candidates, "median_qualifying_candidates": median_candidates,
        "average_selected_candidates": sum(selected_counts) / len(selected_counts) if selected_counts else 0,
        "valuation_complete": result.valuation_complete, "boundary_exits": len(boundary),
        "non_fill_reasons": dict(Counter(event.reason for event in nonfills)),
    }


def main() -> None:
    frames = load_frames()
    cost_scenarios = {
        "official": (OFFICIAL_COMMISSION, OFFICIAL_VAT, 1),
        "zero_transaction_cost": (Decimal("0"), Decimal("0"), 0),
        "fee_only": (OFFICIAL_COMMISSION, OFFICIAL_VAT, 0),
        "slippage_only": (Decimal("0"), Decimal("0"), 1),
    }
    frequencies = {"every_1_observed_row": 1, "every_3_observed_rows": 3, "every_5_observed_rows_weekly_style": 5, "every_10_observed_rows": 10}
    output: dict[str, object] = {"research_period": {"start": "2023-01-03", "end": "2026-09-04"},
                                 "starting_capital": str(INITIAL), "cost_sensitivity": {}, "frequency_sensitivity": {},
                                 "interpretation": {"counterfactuals_are_diagnostic_only": True, "no_parameter_search": True}}
    candidate_cache: dict[str, int] = {}
    for scenario, (commission, vat, ticks) in cost_scenarios.items():
        output["cost_sensitivity"][scenario] = {"assumptions": {"commission_rate": str(commission), "vat_rate": str(vat), "slippage_ticks": ticks}, "Design A": {}, "Design C": {}}
        for design in ("A", "C"):
            result, gate = run_case(frames, design, 3, commission, vat, ticks)
            output["cost_sensitivity"][scenario][f"Design {design}"] = metrics(result, gate, frames, candidate_cache)
    official_a = output["cost_sensitivity"]["official"]["Design A"]
    official_c = output["cost_sensitivity"]["official"]["Design C"]
    for scenario, values in output["cost_sensitivity"].items():
        if scenario == "official": continue
        for design, baseline in (("Design A", official_a), ("Design C", official_c)):
            values[design]["final_equity_difference_vs_official"] = None if values[design]["final_equity"] is None else str(dec(values[design]["final_equity"]) - dec(baseline["final_equity"]))
            values[design]["net_return_difference_vs_official"] = None if values[design]["net_return"] is None else str(dec(values[design]["net_return"]) - dec(baseline["net_return"]))
    for label, every in frequencies.items():
        output["frequency_sensitivity"][label] = {"every_n_observed_rows": every, "Design A": {}, "Design C": {}}
        for design in ("A", "C"):
            result, gate = run_case(frames, design, every, OFFICIAL_COMMISSION, OFFICIAL_VAT, 1)
            output["frequency_sensitivity"][label][f"Design {design}"] = metrics(result, gate, frames, candidate_cache)
    base = output["frequency_sensitivity"]["every_3_observed_rows"]
    for label, values in output["frequency_sensitivity"].items():
        if label == "every_3_observed_rows": continue
        for design in ("Design A", "Design C"):
            for key in ("final_equity", "net_return", "turnover", "total_fees", "slippage", "fills", "non_fills", "trade_count"):
                        values[design][f"{key}_difference_vs_every_3"] = str(dec(values[design][key]) - dec(base[design][key])) if isinstance(values[design][key], str) else values[design][key] - base[design][key]
    output["diagnostic_answers"] = _answers(output)
    (REPORTS / "design_a_c_cost_rebalance_diagnostic.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    _write_csv(output)
    (ROOT / "docs" / "DESIGN_A_C_COST_REBALANCE_DIAGNOSTIC.md").write_text(markdown(output), encoding="utf-8")
    print(json.dumps({"status": "ok", "output": "reports/design_a_c_cost_rebalance_diagnostic.json"}, indent=2))


def dec(value): return Decimal(str(value))


def _answers(output: dict[str, object]) -> dict[str, object]:
    costs = output["cost_sensitivity"]
    frequencies = output["frequency_sensitivity"]
    answers = {}
    for design in ("Design A", "Design C"):
        official = costs["official"][design]; zero = costs["zero_transaction_cost"][design]
        fee = costs["fee_only"][design]; slip = costs["slippage_only"][design]
        answers[design] = {
            "net_return_improvement_zero_cost_vs_official": str(dec(zero["net_return"]) - dec(official["net_return"])),
            "net_return_improvement_fee_only_vs_official": str(dec(fee["net_return"]) - dec(official["net_return"])),
            "net_return_improvement_slippage_only_vs_official": str(dec(slip["net_return"]) - dec(official["net_return"])),
            "net_return_zero_cost_minus_fee_only": str(dec(zero["net_return"]) - dec(fee["net_return"])),
            "net_return_zero_cost_minus_slippage_only": str(dec(zero["net_return"]) - dec(slip["net_return"])),
        }
    answers["slippage_vs_fees_by_starting_capital"] = {
        design: {"slippage_fraction": str(dec(costs["official"][design]["slippage"]) / INITIAL), "fees_fraction": str(dec(costs["official"][design]["total_fees"]) / INITIAL)}
        for design in ("Design A", "Design C")
    }
    answers["frequency_tradeoff"] = {
        label: {design: {"turnover": frequencies[label][design]["turnover"], "total_fees": frequencies[label][design]["total_fees"], "slippage": frequencies[label][design]["slippage"]}
                for design in ("Design A", "Design C")}
        for label in frequencies
    }
    answers["conclusion"] = "The official 3-row run is highly cost-sensitive. Lower frequencies reduce turnover and costs in this sample, but these are diagnostics and do not establish an optimal frequency."
    return answers


def _write_csv(output):
    rows = []
    for family, scenarios in (("cost", output["cost_sensitivity"]), ("frequency", output["frequency_sensitivity"])):
        for scenario, value in scenarios.items():
            for design in ("Design A", "Design C"):
                row = {"family": family, "scenario": scenario, "design": design}; row.update(value[design]); rows.append(row)
    fields = sorted({key for row in rows for key in row})
    with (REPORTS / "design_a_c_cost_rebalance_diagnostic.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)


def markdown(data):
    lines = ["# Design A/C Cost and Rebalance Diagnostic", "", "These are fixed counterfactual diagnostics, not optimized performance estimates.", ""]
    for section in ("research_period", "starting_capital", "cost_sensitivity", "frequency_sensitivity", "interpretation"):
        lines += [f"## {section.replace('_', ' ').title()}", "", "```json", json.dumps(data[section], indent=2), "```", ""]
    lines += ["## Diagnostic interpretation", "", "```json", json.dumps(data["diagnostic_answers"], indent=2), "```", "", "- Zero-cost, fee-only, and slippage-only cases isolate cost components; none changes the official baseline.", "- Frequency results describe turnover/cost trade-offs and do not identify an optimal schedule.", "- The next research round should keep official assumptions and strategy parameters unchanged until an explicit OOS/walk-forward protocol is approved.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()

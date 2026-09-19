"""Read-only diagnostic analysis of the completed Design A/C artifacts."""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
INITIAL = Decimal("10000000")


def dec(value: object) -> Decimal:
    return Decimal(str(value))


def read_csv(name: str) -> list[dict[str, str]]:
    with (REPORTS / name).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def period_attribution(prefix: str, rows: list[dict[str, str]]) -> list[dict[str, object]]:
    by_year: defaultdict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_year[pd.Timestamp(row["timestamp"]).strftime("%Y")].append(row)
    result = []
    for year, period_rows in sorted(by_year.items()):
        equities = [dec(row["equity"]) for row in period_rows]
        start, end = equities[0], equities[-1]
        drawdowns = [(dec(row["drawdown"]), row["timestamp"]) for row in period_rows]
        worst, worst_date = min(drawdowns, key=lambda item: item[0])
        result.append({"period": year, "start_equity": str(start), "end_equity": str(end),
                       "period_return": str((end - start) / start), "worst_drawdown": str(worst),
                       "worst_drawdown_date": worst_date, "observations": len(period_rows)})
    return result


def cost_attribution(report: dict[str, object]) -> dict[str, object]:
    fees = dec(report["total_fees"]); slippage = dec(report["slippage"])
    return {"commission": report["commission"], "vat": report["vat"], "total_fees": report["total_fees"],
            "slippage": report["slippage"], "fees_as_fraction_of_start": str(fees / INITIAL),
            "slippage_as_fraction_of_start": str(slippage / INITIAL),
            "fees_plus_slippage_as_fraction_of_start": str((fees + slippage) / INITIAL),
            "gross_minus_net_return": str(dec(report["gross_return"]) - dec(report["net_return"]))}


def turnover_diagnostics(orders: list[dict[str, str]], selections: list[dict[str, str]]) -> dict[str, object]:
    by_date: defaultdict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    filled_by_date: Counter[str] = Counter()
    for row in orders:
        if row["status"] == "FILLED":
            by_date[row["execution_date"]] += dec(row["order_value"])
            filled_by_date[row["execution_date"]] += 1
    turnover = [value / INITIAL for value in by_date.values()]
    selection_sets = [set(filter(None, row["selected_symbols"].split("|"))) for row in selections]
    changed = sum(selection_sets[i] != selection_sets[i - 1] for i in range(1, len(selection_sets)))
    return {"rebalance_dates_with_fills": len(by_date), "turnover_per_execution_date": {k: str(v) for k, v in sorted(by_date.items())},
            "average_turnover_per_filled_execution_date": str(sum(turnover, Decimal("0")) / len(turnover)) if turnover else "0",
            "median_turnover_per_filled_execution_date": str(pd.Series([float(v) for v in turnover]).median()) if turnover else "0",
            "rebalances_with_selection_change": changed, "selection_change_fraction": changed / (len(selection_sets) - 1) if len(selection_sets) > 1 else 0,
            "filled_order_count_by_execution_date": dict(filled_by_date)}


def symbol_diagnostics(orders: list[dict[str, str]]) -> list[dict[str, object]]:
    grouped: defaultdict[str, dict[str, object]] = defaultdict(lambda: {"fills": 0, "non_fills": 0, "buy_notional": Decimal("0"), "sell_notional": Decimal("0"), "fees": Decimal("0"), "slippage": Decimal("0")})
    for row in orders:
        item = grouped[row["symbol"]]
        if row["status"] == "FILLED":
            item["fills"] += 1; item["fees"] += dec(row["total_fees"]); item["slippage"] += dec(row["slippage"])
            item["buy_notional" if row["side"] == "BUY" else "sell_notional"] += dec(row["order_value"])
        else: item["non_fills"] += 1
    output = []
    for symbol, item in grouped.items():
        gross_cash = item["sell_notional"] - item["buy_notional"]
        net_cash = gross_cash - item["fees"]
        output.append({"symbol": symbol, **{key: (str(value) if isinstance(value, Decimal) else value) for key, value in item.items()},
                       "gross_cash_flow_contribution": str(gross_cash), "net_cash_flow_contribution": str(net_cash)})
    return sorted(output, key=lambda row: dec(row["net_cash_flow_contribution"]))


def selection_diagnostics(comparison: dict[str, object], a_orders: list[dict[str, str]], c_orders: list[dict[str, str]]) -> dict[str, object]:
    differences = comparison["selection_analysis"]["selection_differences"]
    a_only = sorted({symbol for row in differences for symbol in row["design_a_only"]})
    c_only = sorted({symbol for row in differences for symbol in row["design_c_only"]})
    a_contrib = {row["symbol"]: row for row in symbol_diagnostics(a_orders)}
    c_contrib = {row["symbol"]: row for row in symbol_diagnostics(c_orders)}
    return {"dates_with_different_selection": sum(bool(row["design_a_only"] or row["design_c_only"]) for row in differences),
            "total_signal_dates": len(differences), "symbols_only_design_a": a_only, "symbols_only_design_c": c_only,
            "design_a_only_net_cash_contributions": {symbol: a_contrib.get(symbol, {}).get("net_cash_flow_contribution", "0") for symbol in a_only},
            "design_c_only_net_cash_contributions": {symbol: c_contrib.get(symbol, {}).get("net_cash_flow_contribution", "0") for symbol in c_only},
            "interpretation": "These are realized order cash-flow diagnostics, not causal or hindsight-adjusted attribution."}


def fill_diagnostics(a_orders: list[dict[str, str]], c_orders: list[dict[str, str]]) -> dict[str, object]:
    def summarize(rows):
        return {"fills": sum(row["status"] == "FILLED" for row in rows), "non_fills": sum(row["status"] == "NON_FILL" for row in rows),
                "non_fill_reasons": dict(Counter(row["reason"] for row in rows if row["status"] == "NON_FILL"))}
    return {"design_a": summarize(a_orders), "design_c": summarize(c_orders),
            "observation": "Both designs use identical execution mechanics; differences reflect their selected orders and resulting cash availability."}


def main() -> None:
    comparison = json.loads((REPORTS / "design_a_vs_c_comparison.json").read_text(encoding="utf-8"))
    a_orders, c_orders = read_csv("design_a_backtest_orders.csv"), read_csv("design_c_backtest_orders.csv")
    a_selections, c_selections = read_csv("design_a_backtest_selections.csv"), read_csv("design_c_backtest_selections.csv")
    a_snapshots, c_snapshots = read_csv("design_a_backtest_snapshots.csv"), read_csv("design_c_backtest_snapshots.csv")
    diagnostics = {
        "research_period": comparison["research_period"], "starting_capital": comparison["starting_capital"],
        "time_period_attribution": {"design_a": period_attribution("A", a_snapshots), "design_c": period_attribution("C", c_snapshots)},
        "cost_attribution": {"design_a": cost_attribution(comparison["design_a"]), "design_c": cost_attribution(comparison["design_c"])},
        "turnover_diagnostics": {"design_a": turnover_diagnostics(a_orders, a_selections), "design_c": turnover_diagnostics(c_orders, c_selections)},
        "candidate_count_diagnostics": comparison["selection_analysis"],
        "selection_difference_attribution": selection_diagnostics(comparison, a_orders, c_orders),
        "symbol_diagnostics": {"design_a": symbol_diagnostics(a_orders), "design_c": symbol_diagnostics(c_orders)},
        "fill_nonfill_diagnostics": fill_diagnostics(a_orders, c_orders),
        "drawdown_diagnostics": {"design_a_max_drawdown": comparison["design_a"]["maximum_drawdown"], "design_c_max_drawdown": comparison["design_c"]["maximum_drawdown"],
                                  "design_a_drawdown_date": min(a_snapshots, key=lambda row: dec(row["drawdown"]))["timestamp"],
                                  "design_c_drawdown_date": min(c_snapshots, key=lambda row: dec(row["drawdown"]))["timestamp"]},
        "data_integrity": {"design_a_valuation_complete": comparison["design_a"]["valuation_complete"], "design_c_valuation_complete": comparison["design_c"]["valuation_complete"],
                            "design_a_unvalued_positions": comparison["design_a"]["unvalued_positions"], "design_c_unvalued_positions": comparison["design_c"]["unvalued_positions"],
                            "raw_data_modified": False, "historical_gate_and_boundary_exits_enforced": True},
        "interpretation": {"observed_facts": ["Design C has lower final equity and net return in this sample.", "Design C has slightly higher turnover but fewer fills.", "Most signal dates have fewer than ten qualifying candidates, so ranking changes selection mainly when the filter produces more than ten candidates."],
                           "plausible_explanations": ["Momentum ranking changes which qualifying names receive equal-weight capital when the candidate set exceeds ten.", "Different selected orders alter cash availability, fills, and realized costs under IOC execution."],
                           "hypotheses_requiring_future_testing": ["Whether ranking remains useful out of sample.", "Whether rebalance frequency or execution-cost sensitivity explains the small performance gap."],
                           "no_parameter_change_recommended": True},
        "research_decision_point": [
            {"direction": "Rebalance-frequency diagnostic", "question": "Does replacement pressure change with schedule frequency?", "change": "Only schedule frequency in a separately approved experiment.", "overfitting_risk": "High if selected after inspecting this result.", "timing": "After OOS/walk-forward plan is fixed."},
            {"direction": "Execution-cost sensitivity", "question": "How much is the gap driven by conservative fills and costs?", "change": "Pre-specify cost scenarios without changing the base run.", "overfitting_risk": "Moderate; scenario cherry-picking can mislead.", "timing": "Before interpreting strategy superiority, with fixed scenarios."},
            {"direction": "Feature-choice research", "question": "Is momentum_20 the right ranking factor?", "change": "Evaluate a pre-specified alternative feature in a new candidate design.", "overfitting_risk": "High with many features or parameter searches.", "timing": "After a walk-forward protocol is approved."},
            {"direction": "Different selection design", "question": "Does another simple selection rule behave differently?", "change": "Add one explicitly approved design, not tune C.", "overfitting_risk": "High if designs are selected by realized return.", "timing": "After OOS/walk-forward methodology is fixed."},
            {"direction": "Statistical comparison", "question": "Is the observed A/C difference distinguishable from noise?", "change": "Use a pre-specified paired time-series comparison.", "overfitting_risk": "Moderate; repeated tests inflate false positives.", "timing": "Before selecting a production direction."},
        ],
    }
    (REPORTS / "design_a_c_diagnostic.json").write_text(json.dumps(diagnostics, indent=2), encoding="utf-8")
    (ROOT / "docs" / "DESIGN_A_C_DIAGNOSTIC.md").write_text(markdown(diagnostics), encoding="utf-8")
    print(json.dumps({"status": "ok", "output": "reports/design_a_c_diagnostic.json"}, indent=2))


def markdown(data: dict[str, object]) -> str:
    lines = ["# Design A vs Design C Diagnostic", "", "This is a read-only diagnosis of the completed fixed-parameter runs. It does not optimize or change either strategy.", ""]
    lines += ["## Executive summary", "", "Design C had lower final equity and net return in this sample, slightly higher turnover, and fewer fills. This is descriptive evidence, not a strategy verdict.", ""]
    for section in ("research_period", "starting_capital", "time_period_attribution", "cost_attribution", "turnover_diagnostics", "candidate_count_diagnostics", "selection_difference_attribution", "fill_nonfill_diagnostics", "drawdown_diagnostics", "data_integrity"):
        value = data[section]; lines += [f"## {section.replace('_', ' ').title()}", "", "```json", json.dumps(value, indent=2), "```", ""]
    lines += ["## Interpretation", "", "### Observed facts", ""]
    lines += [f"- {item}" for item in data["interpretation"]["observed_facts"]] + ["", "### Plausible explanations", ""]
    lines += [f"- {item}" for item in data["interpretation"]["plausible_explanations"]] + ["", "### Hypotheses requiring future testing", ""]
    lines += [f"- {item}" for item in data["interpretation"]["hypotheses_requiring_future_testing"]] + ["", "## Research Decision Point", ""]
    for item in data["research_decision_point"]:
        lines += [f"### {item['direction']}", f"- Question: {item['question']}", f"- Change: {item['change']}", f"- Overfitting risk: {item['overfitting_risk']}", f"- Timing: {item['timing']}", ""]
    lines += ["No parameter changes are recommended from this diagnostic alone.", ""]
    return "\n".join(lines)


if __name__ == "__main__":
    main()

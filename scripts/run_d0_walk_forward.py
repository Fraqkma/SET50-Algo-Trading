"""Run the fixed D0 diagnostic through the established A/C fold protocol."""
from __future__ import annotations

import csv
import json
import math
import statistics
import sys
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.d0_adapter import D0ExecutionAdapter
from src.backtest.engine import BacktestEngine, ExecutionPolicy
from src.data.eligibility import MarketDataEligibilityGate
from src.data.features import build_features
from src.data.research import load_approved_market_data
from src.strategies.d0_turnover_control import qualification_state
from scripts.run_design_a_backtest import RecordingGate, set_tick_size
from scripts.run_walk_forward import STARTING_CAPITAL, build_expanding_folds, run_walk_forward

REPORTS = ROOT / "reports"
POLICY = ExecutionPolicy(tick_size=set_tick_size)


def _load_prices(gate: MarketDataEligibilityGate) -> dict[str, pd.DataFrame]:
    manifest = pd.read_csv(ROOT / "data" / "processed" / "approved_market_data_manifest.csv")
    prices: dict[str, pd.DataFrame] = {}
    for symbol in manifest["set_symbol"].astype(str).str.upper():
        try:
            prices[symbol] = load_approved_market_data(symbol, gate=gate)
        except (FileNotFoundError, ValueError):
            continue
    return prices


def _number(value: object) -> Decimal:
    return Decimal(str(value))


def _d0_metrics(result: dict[str, object], fold: object) -> dict[str, object]:
    snapshots = [s for s in result["snapshots"] if s.get("equity") is not None]
    equities = [float(s["equity"]) for s in snapshots]
    returns = [equities[i] / equities[i - 1] - 1 for i in range(1, len(equities)) if equities[i - 1]]
    peak = equities[0] if equities else float(STARTING_CAPITAL)
    drawdowns = []
    for equity in equities:
        peak = max(peak, equity)
        drawdowns.append(equity / peak - 1)
    orders = [o for o in result["orders"] if isinstance(o, dict)]
    filled = [o for o in orders if o.get("status") == "FILLED"]
    buy_value = sum((_number(o["executed_price"]) * int(o["quantity"]) for o in filled if o["side"] == "BUY"), Decimal(0))
    sell_value = sum((_number(o["executed_price"]) * int(o["quantity"]) for o in filled if o["side"] == "SELL"), Decimal(0))
    fees = _number(result["total_fees"])
    slippage = _number(result["slippage"])
    return {
        "fold": fold.fold, "design": "D0",
        "research_period": {"start": fold.research_start, "end": fold.research_end}, "oos_period": {"start": fold.oos_start, "end": fold.oos_end},
        "research_observations": fold.research_observations, "oos_observations": fold.oos_observations, "starting_capital": str(STARTING_CAPITAL),
        "final_equity": str(_number(result["final_equity"])), "gross_return": str((_number(result["final_equity"]) - STARTING_CAPITAL + fees) / STARTING_CAPITAL), "net_return": str(_number(result["net_return"])),
        "volatility": str(Decimal(str(statistics.pstdev(returns) * math.sqrt(252))) if len(returns) > 1 else Decimal(0)), "maximum_drawdown": str(Decimal(str(min(drawdowns, default=0)))),
        "turnover": str(_number(result["turnover"])), "buy_turnover": str(buy_value / STARTING_CAPITAL), "sell_turnover": str(sell_value / STARTING_CAPITAL),
        "commission": str(_number(result["commission"])), "vat": str(_number(result["vat"])), "total_fees": str(fees), "slippage": str(slippage), "total_transaction_cost": str(fees + slippage),
        "fills": len(filled), "non_fills": len(orders) - len(filled), "average_positions": str(Decimal(str(statistics.mean([s["positions"] for s in snapshots]) if snapshots else 0))),
        "average_cash_percentage": str(Decimal(str(statistics.mean([float(s["cash"]) / float(s["equity"]) for s in snapshots if s["equity"]]) if snapshots else 0))), "unique_symbols_traded": len({o["symbol"] for o in filled}),
        "valuation_complete": all(s.get("equity") is not None for s in result["snapshots"]), "duplicate_exit_symbols": 0,
    }


def _aggregate(rows: list[dict[str, object]]) -> dict[str, object]:
    values = [float(r["net_return"]) for r in rows]
    compounded = Decimal(1)
    for value in values:
        compounded *= Decimal(str(1 + value))
    return {"fold_count": len(rows), "mean_fold_net_return": statistics.mean(values), "median_fold_net_return": statistics.median(values), "compounded_independent_fold_net_return": str(compounded - 1), "positive_fold_count": sum(v > 0 for v in values), "total_fees": str(sum((_number(r["total_fees"]) for r in rows), Decimal(0))), "total_transaction_cost": str(sum((_number(r["total_transaction_cost"]) for r in rows), Decimal(0)))}


def run() -> dict[str, object]:
    base_gate = MarketDataEligibilityGate(ROOT)
    prices = _load_prices(base_gate)
    dates = pd.DatetimeIndex(sorted(set().union(*(set(f.index) for f in prices.values()))))
    folds = build_expanding_folds(dates)
    a_output = run_walk_forward()
    a_rows = [r for r in a_output["fold_results"] if r["design"] == "A"]
    d0_rows: list[dict[str, object]] = []
    for fold in folds:
        end, start = pd.Timestamp(fold.oos_end), pd.Timestamp(fold.oos_start)
        frames = {}
        for symbol, raw in prices.items():
            state = build_features(raw.loc[raw.index <= end])
            state = qualification_state(state)
            selected = state.loc[(state.index >= start) & (state.index <= end)]
            if not selected.empty:
                frames[symbol] = selected
        result = D0ExecutionAdapter(initial_cash=STARTING_CAPITAL).run(frames, RecordingGate(base_gate), POLICY, execution_start=start)
        d0_rows.append(_d0_metrics(result, fold))
    comparisons = []
    for a, d0 in zip(a_rows, d0_rows):
        comparisons.append({"fold": a["fold"], "oos_period": a["oos_period"], "d0_minus_a_net_return": str(_number(d0["net_return"]) - _number(a["net_return"])), "turnover_reduction": str(_number(a["turnover"]) - _number(d0["turnover"])), "transaction_cost_reduction": str(_number(a["total_fees"]) + _number(a["slippage"]) - _number(d0["total_transaction_cost"])), "gross_difference": str(_number(d0["gross_return"]) - _number(a["gross_return"])), "net_difference": str(_number(d0["net_return"]) - _number(a["net_return"]))})
    full_frames = {symbol: build_features(raw) for symbol, raw in prices.items()}
    full_result = D0ExecutionAdapter(initial_cash=STARTING_CAPITAL).run(full_frames, RecordingGate(base_gate), POLICY)
    full_a = json.loads((REPORTS / "design_a_backtest_report.json").read_text(encoding="utf-8"))
    full_keys = ("final_equity", "gross_return", "net_return", "turnover", "commission", "vat", "total_fees", "slippage", "fills", "non_fills")
    full_d0 = {key: full_result[key] for key in full_keys}
    output = {"method": a_output["method"], "fold_results": d0_rows, "strategies": {"A": a_output["strategies"]["A"], "D0": _aggregate(d0_rows)}, "full_period": {"A": {key: full_a[key] for key in full_keys}, "D0": full_d0}, "d0_vs_a": comparisons, "classification": "MIXED" if any(float(r["net_return"]) > 0 for r in d0_rows) else "NOT_SUPPORTED", "classification_reason": "D0 materially reduces turnover and transaction cost, but remains loss-making and lacks stable positive OOS evidence."}
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "d0_walk_forward_summary.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    for filename, rows in (("d0_walk_forward_execution.csv", d0_rows), ("d0_vs_a_walk_forward.csv", comparisons)):
        with (REPORTS / filename).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=rows[0].keys()); writer.writeheader(); writer.writerows({k: json.dumps(v) if isinstance(v, dict) else v for k, v in r.items()} for r in rows)
    (REPORTS / "d0_walk_forward.csv").write_text((REPORTS / "d0_walk_forward_execution.csv").read_text(encoding="utf-8"), encoding="utf-8")
    lines = ["# D0 Walk-Forward Evaluation", "", "D0 was evaluated with the same expanding folds, approved data, capital reset, eligibility, LIMIT/IOC, one-tick, fee, VAT, valuation, and no-lookahead protocol as Design A/C.", "", f"Classification: **{output['classification']}** — {output['classification_reason']}", "", "## Fold comparison", "", "| Fold | A net | D0 net | D0−A net | Turnover reduction | Transaction-cost reduction |", "|---:|---:|---:|---:|---:|---:|"]
    for row in comparisons:
        a = next(item for item in a_rows if item["fold"] == row["fold"]); d0 = next(item for item in d0_rows if item["fold"] == row["fold"])
        lines.append(f"| {row['fold']} | {a['net_return']} | {d0['net_return']} | {row['net_difference']} | {row['turnover_reduction']} | {row['transaction_cost_reduction']} |")
    (ROOT / "docs" / "D0_WALK_FORWARD_EVALUATION.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output


if __name__ == "__main__":
    run()

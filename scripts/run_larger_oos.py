"""Run the pre-specified comparable-block OOS A/C evaluation."""

from __future__ import annotations

import csv
import json
import sys
from dataclasses import asdict
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.backtest.engine import BacktestEngine, ExecutionPolicy
from src.data.eligibility import MarketDataEligibilityGate
from src.data.features import build_features
from scripts.run_design_a_backtest import RecordingGate, set_tick_size
from scripts.run_walk_forward import (
    INITIAL_RESEARCH_OBSERVATIONS,
    STARTING_CAPITAL,
    _load_prices,
    _metrics,
    aggregate_metrics,
    build_expanding_folds,
)

INITIAL_HISTORY = 250
OOS_BLOCK = 80
MINIMUM_FULL_BLOCK = OOS_BLOCK
REPORTS = ROOT / "reports"


def build_larger_oos_folds(dates: pd.DatetimeIndex):
    """Return only equal-sized blocks from the fixed observed-row design.

    A terminal remainder shorter than one complete block is retained in the
    data boundary record but is not promoted to a shorter statistical block.
    """
    all_folds = build_expanding_folds(
        dates,
        initial_research_observations=INITIAL_HISTORY,
        oos_observations=OOS_BLOCK,
    )
    usable = [fold for fold in all_folds if fold.oos_observations >= MINIMUM_FULL_BLOCK]
    remainder = [fold for fold in all_folds if fold.oos_observations < MINIMUM_FULL_BLOCK]
    return usable, remainder


def run_larger_oos() -> dict:
    base_gate = MarketDataEligibilityGate(ROOT)
    prices = _load_prices(base_gate)
    dates = pd.DatetimeIndex(sorted(set().union(*(set(frame.index) for frame in prices.values()))))
    folds, remainder = build_larger_oos_folds(dates)
    rows: list[dict] = []
    for fold in folds:
        oos_start = pd.Timestamp(fold.oos_start)
        oos_end = pd.Timestamp(fold.oos_end)
        oos_frames = {}
        for symbol, price_frame in prices.items():
            # Causal truncation occurs before feature construction.
            historical = price_frame.loc[price_frame.index <= oos_end]
            features = build_features(historical)
            oos = features.loc[(features.index >= oos_start) & (features.index <= oos_end)]
            if not oos.empty:
                oos_frames[symbol] = oos
        for design in ("A", "C"):
            gate = RecordingGate(base_gate)
            engine = BacktestEngine(
                initial_cash=STARTING_CAPITAL,
                top_n=10,
                rebalance_every=3,
                design=design,
                execution_policy=ExecutionPolicy(tick_size=set_tick_size),
                gate=gate,
            )
            row = _metrics(engine.run(oos_frames), fold, design)
            row["eligibility_exclusions"] = dict(gate.reasons)
            rows.append(row)

    comparisons = []
    for fold in folds:
        a = next(r for r in rows if r["fold"] == fold.fold and r["design"] == "A")
        c = next(r for r in rows if r["fold"] == fold.fold and r["design"] == "C")
        difference = Decimal(c["net_return"]) - Decimal(a["net_return"])
        comparisons.append({
            "fold": fold.fold,
            "oos_period": a["oos_period"],
            "oos_observations": fold.oos_observations,
            "a_net_return": a["net_return"],
            "c_net_return": c["net_return"],
            "c_minus_a_net_return": format(difference, "f"),
            "status": "positive" if difference > 0 else "negative" if difference < 0 else "tied",
        })
    differences = [Decimal(row["c_minus_a_net_return"]) for row in comparisons]
    strategy_summary = {
        design: aggregate_metrics([row for row in rows if row["design"] == design])
        for design in ("A", "C")
    }
    return {
        "method": {
            "fold_rule": "expanding observed rows with equal-sized OOS blocks",
            "initial_research_observations": INITIAL_HISTORY,
            "oos_block_observations": OOS_BLOCK,
            "capital_reset_per_block": True,
            "usable_block_count": len(folds),
            "terminal_remainder_blocks": [asdict(fold) for fold in remainder],
            "terminal_remainder_policy": "do not evaluate a shorter terminal block",
            "aggregate_return_method": "compound independent-block returns descriptively only",
            "causal_truncation": "truncate approved raw rows at each OOS end before feature construction",
            "statistical_test_run": False,
        },
        "folds": [asdict(fold) for fold in folds],
        "fold_results": rows,
        "a_vs_c": comparisons,
        "paired_summary": {
            "mean_c_minus_a_net_return": str(sum(differences, Decimal("0")) / len(differences)),
            "median_c_minus_a_net_return": str(sorted(differences)[len(differences) // 2]),
            "positive_blocks": sum(d > 0 for d in differences),
            "negative_blocks": sum(d < 0 for d in differences),
            "tied_blocks": sum(d == 0 for d in differences),
            "sign_pattern": ["+" if d > 0 else "-" if d < 0 else "0" for d in differences],
            "final_block_materially_shorter": False,
            "design_a_compounded_independent_block_return": strategy_summary["A"]["compounded_independent_fold_net_return"],
            "design_c_compounded_independent_block_return": strategy_summary["C"]["compounded_independent_fold_net_return"],
        },
        "strategies": strategy_summary,
    }


def main() -> None:
    output = run_larger_oos()
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "larger_oos_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    rows = output["fold_results"]
    with (REPORTS / "larger_oos_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow({key: json.dumps(value) if isinstance(value, dict) else value for key, value in row.items()})
    summary = output["paired_summary"]
    lines = [
        "# Larger Comparable-Block OOS Results", "",
        "Fixed-parameter paired evaluation of Design A and Design C.", "",
        "## Method", "",
        f"The study uses {INITIAL_HISTORY} observed rows of expanding initial history and {OOS_BLOCK}-row OOS blocks. Eight equal-sized blocks are usable; the deterministic terminal remainder is not promoted to a shorter block. Each block resets to THB 10,000,000. Features are built only after truncating approved rows at that block's OOS end.", "",
        "## Paired summary", "", "```json", json.dumps(summary, indent=2), "```", "",
        "## Block comparison", "",
        "| Block | OOS period | Rows | A net | C net | C − A | Status |", "|---:|---|---:|---:|---:|---:|:---:|",
    ]
    for row in output["a_vs_c"]:
        period = f"{row['oos_period']['start']}–{row['oos_period']['end']}"
        lines.append(f"| {row['fold']} | {period} | {row['oos_observations']} | {row['a_net_return']} | {row['c_net_return']} | {row['c_minus_a_net_return']} | {row['status']} |")
    lines += ["", "## Per-block metrics", "", "The machine-readable JSON contains all fields. The table below repeats the required accounting and data-quality fields for each strategy/block.", "", "| Block | Design | Gross | Net | Volatility | Max drawdown | Turnover | Commission | VAT | Fees | Slippage | Fills | Non-fills | Unique symbols | Valuation complete |", "|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
    for row in output["fold_results"]:
        lines.append(f"| {row['fold']} | {row['design']} | {row['gross_return']} | {row['net_return']} | {row['volatility']} | {row['maximum_drawdown']} | {row['turnover']} | {row['commission']} | {row['vat']} | {row['total_fees']} | {row['slippage']} | {row['fills']} | {row['non_fills']} | {row['unique_symbols_traded']} | {row['valuation_complete']} |")
    lines += ["", "## Statistical status", "", "The pre-registered statistical test was not run. More blocks improve descriptive coverage but do not make expanding-window blocks independent. The results require human approval before any inferential test.", ""]
    (REPORTS / "larger_oos_report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()

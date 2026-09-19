"""Run the fixed-parameter expanding-window A/C walk-forward study."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import Counter
from dataclasses import asdict, dataclass
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

REPORTS = ROOT / "reports"
INITIAL_RESEARCH_OBSERVATIONS = 400
OOS_OBSERVATIONS = 120
STARTING_CAPITAL = Decimal("10000000")


@dataclass(frozen=True)
class WalkForwardFold:
    fold: int
    research_start: str
    research_end: str
    oos_start: str
    oos_end: str
    research_observations: int
    oos_observations: int


def build_expanding_folds(
    dates: pd.DatetimeIndex,
    *,
    initial_research_observations: int = INITIAL_RESEARCH_OBSERVATIONS,
    oos_observations: int = OOS_OBSERVATIONS,
) -> list[WalkForwardFold]:
    """Build non-overlapping chronological folds from observed dates."""
    dates = pd.DatetimeIndex(sorted(pd.to_datetime(dates).unique()))
    if initial_research_observations < 1 or oos_observations < 1:
        raise ValueError("Fold sizes must be positive.")
    folds: list[WalkForwardFold] = []
    start = initial_research_observations
    number = 1
    while start < len(dates):
        end = min(start + oos_observations, len(dates))
        folds.append(WalkForwardFold(
            number, dates[0].date().isoformat(), dates[start - 1].date().isoformat(),
            dates[start].date().isoformat(), dates[end - 1].date().isoformat(),
            start, end - start,
        ))
        start = end
        number += 1
    return folds


def _dec(value: Decimal | None) -> str | None:
    return None if value is None else format(value, "f")


def _metrics(result, fold: WalkForwardFold, design: str) -> dict:
    orders = list(result.orders)
    return {
        "fold": fold.fold, "design": design,
        "research_period": {"start": fold.research_start, "end": fold.research_end},
        "oos_period": {"start": fold.oos_start, "end": fold.oos_end},
        "research_observations": fold.research_observations,
        "oos_observations": fold.oos_observations,
        "starting_capital": _dec(STARTING_CAPITAL), "final_equity": _dec(result.final_equity),
        "gross_return": _dec(result.gross_return), "net_return": _dec(result.net_return),
        "volatility": _dec(result.volatility), "maximum_drawdown": _dec(result.maximum_drawdown),
        "turnover": _dec(result.turnover), "commission": _dec(result.commission),
        "vat": _dec(result.vat), "total_fees": _dec(result.total_fees),
        "slippage": _dec(result.slippage), "fills": sum(e.status == "FILLED" for e in orders),
        "trade_count": result.trade_count, "non_fills": sum(e.status == "NON_FILL" for e in orders),
        "unique_symbols_traded": result.unique_symbols_traded,
        "valuation_complete": result.valuation_complete,
        "complete_valuation_snapshots": result.complete_valuation_snapshots,
        "incomplete_valuation_snapshots": result.incomplete_valuation_snapshots,
        "rebalances": len(result.selections),
        "boundary_exits": sum(bool(e.reason and e.reason.startswith("UNIVERSE_BOUNDARY_EXIT")) for e in orders),
        "eligibility_exclusions": {},
    }


def aggregate_metrics(rows: list[dict]) -> dict:
    values = [float(row["net_return"]) for row in rows if row["net_return"] is not None]
    final_values = [Decimal(row["final_equity"]) for row in rows if row["final_equity"] is not None]
    compounded = Decimal("1")
    for value in values:
        compounded *= Decimal(str(1.0 + value))
    return {
        "fold_count": len(rows), "mean_oos_net_return": statistics.mean(values) if values else None,
        "median_oos_net_return": statistics.median(values) if values else None,
        "std_oos_net_return_population": statistics.pstdev(values) if len(values) > 1 else 0.0,
        "positive_fold_fraction": (sum(v > 0 for v in values) / len(values)) if values else None,
        "compounded_independent_fold_net_return": str(compounded - 1),
        "mean_final_equity": str(sum(final_values, Decimal("0")) / len(final_values)) if final_values else None,
        "total_commission": str(sum((Decimal(r.get("commission", "0")) for r in rows), Decimal("0"))),
        "total_vat": str(sum((Decimal(r.get("vat", "0")) for r in rows), Decimal("0"))),
        "total_fees": str(sum((Decimal(r.get("total_fees", "0")) for r in rows), Decimal("0"))),
        "total_slippage": str(sum((Decimal(r.get("slippage", "0")) for r in rows), Decimal("0"))),
        "mean_turnover": str(sum((Decimal(r.get("turnover", "0")) for r in rows), Decimal("0")) / len(rows)) if rows else None,
        "worst_fold_drawdown": str(min((Decimal(r.get("maximum_drawdown", "0")) for r in rows), default=Decimal("0"))),
        "all_valuation_complete": all(r.get("valuation_complete", True) for r in rows),
        "mean_fills": (sum(r.get("fills", 0) for r in rows) / len(rows)) if rows else None,
        "mean_non_fills": (sum(r.get("non_fills", 0) for r in rows) / len(rows)) if rows else None,
    }


def _load_prices(gate: MarketDataEligibilityGate) -> dict[str, pd.DataFrame]:
    manifest = pd.read_csv(ROOT / "data" / "processed" / "approved_market_data_manifest.csv")
    frames: dict[str, pd.DataFrame] = {}
    for symbol in manifest["set_symbol"].astype(str).str.upper():
        try:
            frames[symbol] = load_approved_market_data(symbol, gate=gate)
        except (FileNotFoundError, ValueError):
            continue
    return frames


def run_walk_forward() -> dict:
    base_gate = MarketDataEligibilityGate(ROOT)
    prices = _load_prices(base_gate)
    dates = pd.DatetimeIndex(sorted(set().union(*(set(frame.index) for frame in prices.values()))))
    folds = build_expanding_folds(dates)
    all_rows: list[dict] = []
    for fold in folds:
        oos_end = pd.Timestamp(fold.oos_end)
        oos_start = pd.Timestamp(fold.oos_start)
        frames = {}
        for symbol, price_frame in prices.items():
            historical = price_frame.loc[price_frame.index <= oos_end]
            features = build_features(historical)
            selected = features.loc[(features.index >= oos_start) & (features.index <= oos_end)]
            if not selected.empty:
                frames[symbol] = selected
        for design in ("A", "C"):
            gate = RecordingGate(base_gate)
            engine = BacktestEngine(
                initial_cash=STARTING_CAPITAL, top_n=10, rebalance_every=3,
                design=design, execution_policy=ExecutionPolicy(tick_size=set_tick_size), gate=gate,
            )
            row = _metrics(engine.run(frames), fold, design)
            row["eligibility_exclusions"] = dict(gate.reasons)
            all_rows.append(row)
    by_design = {design: aggregate_metrics([r for r in all_rows if r["design"] == design]) for design in ("A", "C")}
    comparisons = []
    for fold in folds:
        a = next(r for r in all_rows if r["fold"] == fold.fold and r["design"] == "A")
        c = next(r for r in all_rows if r["fold"] == fold.fold and r["design"] == "C")
        comparisons.append({"fold": fold.fold, "oos_period": a["oos_period"],
                            "a_net_return": a["net_return"], "c_net_return": c["net_return"],
                            "c_minus_a_net_return": str(Decimal(c["net_return"]) - Decimal(a["net_return"]))})
    return {"method": {"fold_rule": "expanding observed rows", "initial_research_observations": INITIAL_RESEARCH_OBSERVATIONS,
                        "oos_observations": OOS_OBSERVATIONS, "capital_reset_per_fold": True,
                        "aggregate_return_method": "compound independent fold net returns"},
            "folds": [asdict(f) for f in folds], "strategies": by_design,
            "fold_results": all_rows, "a_vs_c": comparisons}


def main() -> None:
    output = run_walk_forward()
    REPORTS.mkdir(exist_ok=True)
    (REPORTS / "walk_forward_results.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    rows = output["fold_results"]
    with (REPORTS / "walk_forward_results.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=rows[0].keys())
        writer.writeheader()
        for row in rows:
            writer.writerow({k: json.dumps(v) if isinstance(v, dict) else v for k, v in row.items()})
    lines = ["# Expanding-Window Walk-Forward Results", "", "Fixed-parameter OOS evaluation of Design A and Design C.", "",
             "## Method", "", "The data contain 898 observed union trading rows. Each fold uses the first 400 rows as research history and the next 120 rows as OOS; the research window expands and each fold resets to THB 10,000,000. The final fold uses the remaining rows. Features are built only through each fold's OOS end, then only OOS rows are passed to the engine. No parameters are optimized.", ""]
    for design in ("A", "C"):
        lines += [f"## Design {design} aggregate", "", "```json", json.dumps(output["strategies"][design], indent=2), "```", ""]
        lines += [f"### Design {design} fold metrics", "", "| Fold | OOS period | Final equity | Gross return | Net return | Volatility | Max drawdown | Turnover | Fees | Slippage | Fills | Non-fills | Rebalances | Valuation complete |", "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|:---:|"]
        for row in [r for r in output["fold_results"] if r["design"] == design]:
            period = f"{row['oos_period']['start']}–{row['oos_period']['end']}"
            lines.append(f"| {row['fold']} | {period} | {row['final_equity']} | {row['gross_return']} | {row['net_return']} | {row['volatility']} | {row['maximum_drawdown']} | {row['turnover']} | {row['total_fees']} | {row['slippage']} | {row['fills']} | {row['non_fills']} | {row['rebalances']} | {row['valuation_complete']} |")
        lines.append("")
    lines += ["## Fold comparison", "", "| Fold | OOS period | A net | C net | C − A |", "|---:|---|---:|---:|---:|"]
    for row in output["a_vs_c"]:
        lines.append(f"| {row['fold']} | {row['oos_period']['start']}–{row['oos_period']['end']} | {row['a_net_return']} | {row['c_net_return']} | {row['c_minus_a_net_return']} |")
    (REPORTS / "walk_forward_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

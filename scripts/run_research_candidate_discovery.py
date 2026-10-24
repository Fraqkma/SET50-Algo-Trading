"""Run a small predeclared candidate funnel on approved daily research data."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_design_a_backtest import set_tick_size
from scripts.run_walk_forward import _load_prices, build_expanding_folds
from src.backtest.engine import BacktestEngine, ExecutionPolicy
from src.data.eligibility import MarketDataEligibilityGate
from src.data.features import FeatureContext, build_features
from src.strategies.research_candidates import select_candidate

CANDIDATES = ["CANDIDATE_TREND20", "CANDIDATE_BREAKOUT20", "CANDIDATE_MEANREV5", "CANDIDATE_REL_STRENGTH"]


class LoadedRowsGate:
    """Fast gate for dates already independently filtered by the approved loader."""
    def __init__(self, source: MarketDataEligibilityGate, frames: dict[str, pd.DataFrame]) -> None:
        self.source = source
        self.valid = {(symbol, timestamp.date()) for symbol, frame in frames.items() for timestamp in frame.index}

    def assess(self, symbol: str, requested_date):
        normalized = str(symbol).upper()
        day = pd.Timestamp(requested_date).date()
        if (normalized, day) in self.valid:
            from src.data.eligibility import EligibilityDecision
            return EligibilityDecision(normalized, day, True, None)
        from src.data.eligibility import EligibilityDecision
        return EligibilityDecision(normalized, day, False, "NOT_IN_APPROVED_LOADED_ROWS")

    def membership_end(self, symbol: str, requested_date):
        return self.source.membership_end(symbol, requested_date)


def _features(symbol: str, frame: pd.DataFrame, gate: MarketDataEligibilityGate) -> pd.DataFrame:
    """Pass explicit context after loader has independently enforced PIT eligibility."""
    approval = gate.approved_manifest_record(symbol)
    if approval is None:
        raise ValueError(f"Approved manifest context is missing for {symbol}.")
    return build_features(frame, context=FeatureContext(
        security_id=symbol, pit_membership=True, identity_status="VERIFIED",
        data_status=approval["approval_status"], information_cutoff=frame.index,
        data_timestamp=frame.index, feature_timestamp=frame.index,
        source_data="approved_market_data_manifest.csv",
    ))


def _run(candidate: str, frames: dict[str, pd.DataFrame], gate: object, *, fees: Decimal = Decimal("0.00157"), ticks: int = 1) -> dict:
    result = BacktestEngine(
        initial_cash=Decimal("10000000"), top_n=10, rebalance_every=3,
        execution_policy=ExecutionPolicy(tick_size=set_tick_size, slippage_ticks=ticks),
        gate=gate, commission_rate=fees,
        candidate_selector=lambda data, date, eligibility, n: select_candidate(candidate, data, date, eligibility, n),
    ).run(frames)
    fills = [order for order in result.orders if order.status == "FILLED"]
    symbol_pnl: dict[str, Decimal] = {}
    lots: dict[str, list[list[Decimal | int | pd.Timestamp]]] = {}
    closed: list[dict] = []
    for order in fills:
        if order.side == "BUY":
            unit_cost = (order.order_value + order.total_fees) / order.quantity
            lots.setdefault(order.symbol, []).append([order.quantity, unit_cost, order.execution_date])
        else:
            remaining = order.quantity
            unit_proceeds = (order.order_value - order.total_fees) / order.quantity
            while remaining and lots.get(order.symbol):
                lot = lots[order.symbol][0]
                quantity = min(remaining, int(lot[0]))
                pnl = (unit_proceeds - Decimal(lot[1])) * quantity
                symbol_pnl[order.symbol] = symbol_pnl.get(order.symbol, Decimal("0")) + pnl
                closed.append({"symbol": order.symbol, "quantity": quantity, "net_pnl": str(pnl), "holding_observations": int((order.execution_date - lot[2]).days)})
                remaining -= quantity
                lot[0] = int(lot[0]) - quantity
                if lot[0] == 0:
                    lots[order.symbol].pop(0)
    snapshot_rows = [s for s in result.snapshots if s.equity is not None]
    exposure = [float((s.equity - s.cash) / s.equity) for s in snapshot_rows if s.equity and s.equity > 0]
    yearly: dict[str, dict] = {}
    for year in sorted({s.timestamp.year for s in snapshot_rows}):
        year_rows = [s for s in snapshot_rows if s.timestamp.year == year]
        yearly[str(year)] = {"start_equity": str(year_rows[0].equity), "end_equity": str(year_rows[-1].equity),
                             "net_change": str(year_rows[-1].equity - year_rows[0].equity)}
    total_realized = sum(symbol_pnl.values(), Decimal("0"))
    positive_symbols = sum(value > 0 for value in symbol_pnl.values())
    gross_pnl = (result.gross_return * Decimal("10000000")) if result.gross_return is not None else None
    fees_paid = result.total_fees
    return {
        "net_return": str(result.net_return) if result.net_return is not None else None,
        "gross_return": str(result.gross_return) if result.gross_return is not None else None,
        "final_equity": str(result.final_equity) if result.final_equity is not None else None,
        "maximum_drawdown": str(result.maximum_drawdown) if result.maximum_drawdown is not None else None,
        "volatility": str(result.volatility) if result.volatility is not None else None,
        "turnover": str(result.turnover), "commission": str(result.commission),
        "vat": str(result.vat), "total_fees": str(result.total_fees), "slippage": str(result.slippage),
        "filled_orders": sum(order.status == "FILLED" for order in result.orders),
        "non_fills": sum(order.status == "NON_FILL" for order in result.orders),
        "unique_symbols_traded": result.unique_symbols_traded,
        "valuation_complete": result.valuation_complete,
        "gross_pnl": str(gross_pnl) if gross_pnl is not None else None,
        "fees_as_fraction_of_gross_pnl": str(fees_paid / gross_pnl) if gross_pnl and gross_pnl > 0 else "NOT_MEANINGFUL_GROSS_PNL_NONPOSITIVE",
        "slippage_model_cost": str(result.slippage),
        "average_equity_exposure": sum(exposure) / len(exposure) if exposure else None,
        "maximum_equity_exposure": max(exposure) if exposure else None,
        "yearly_equity_change": yearly,
        "completed_fifo_round_trips": len(closed),
        "fifo_realized_net_pnl": str(total_realized),
        "profitable_symbols": positive_symbols,
        "losing_symbols": sum(value < 0 for value in symbol_pnl.values()),
        "top_symbol_realized_pnl": sorted(({"symbol": symbol, "net_pnl": str(value)} for symbol, value in symbol_pnl.items()), key=lambda row: Decimal(row["net_pnl"]), reverse=True)[:5],
        "fifo_trade_distribution": {
            "winners": sum(Decimal(item["net_pnl"]) > 0 for item in closed),
            "losers": sum(Decimal(item["net_pnl"]) < 0 for item in closed),
            "mean_net_pnl": str(sum((Decimal(item["net_pnl"]) for item in closed), Decimal("0")) / len(closed)) if closed else None,
            "median_net_pnl": str(pd.Series([float(item["net_pnl"]) for item in closed]).median()) if closed else None,
            "largest_loss": str(min((Decimal(item["net_pnl"]) for item in closed), default=Decimal("0"))),
            "mean_holding_calendar_days": sum(item["holding_observations"] for item in closed) / len(closed) if closed else None,
        },
        "orders": [
            {"date": order.execution_date.date().isoformat(), "symbol": order.symbol, "side": order.side,
             "quantity": order.quantity, "status": order.status, "reason": order.reason,
             "price": str(order.executed_price) if order.executed_price is not None else None,
             "fees": str(order.total_fees), "slippage": str(order.slippage)}
            for order in result.orders
        ],
    }


def main() -> None:
    source_gate = MarketDataEligibilityGate(ROOT)
    prices = _load_prices(source_gate)
    gate = LoadedRowsGate(source_gate, prices)
    dates = pd.DatetimeIndex(sorted(set().union(*(set(frame.index) for frame in prices.values()))))
    full_frames = {symbol: _features(symbol, frame, source_gate) for symbol, frame in prices.items()}
    folds = build_expanding_folds(dates)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_candidate_discovery"
    output_dir = ROOT / "artifacts" / "research_runs" / run_id
    output_dir.mkdir(parents=True, exist_ok=False)
    result: dict = {
        "schema_version": 1, "run_id": run_id, "engine": "RESEARCH_BACKTEST",
        "source": "approved_market_data_manifest.csv; approved daily loader; PIT eligibility gate",
        "period": {"start": dates.min().date().isoformat(), "end": dates.max().date().isoformat(), "observed_union_rows": len(dates)},
        "universe": {"symbols_loaded": sorted(full_frames), "policy": "PIT eligibility rechecked on signal and execution dates; approved-data coverage only"},
        "execution_model": {"version": "RESEARCH_EXECUTION_V1", "order_type": "LIMIT", "validity": "IOC", "slippage_ticks": 1, "commission_rate": "0.00157", "vat_rate": "0.07", "fill_rule": "requested open plus/minus one tick must be within observed bar range", "status": "research assumption; not official execution fact"},
        "walk_forward": {"folds": [fold.__dict__ for fold in folds], "configuration": "400 initial union observations; 120 OOS rows; expanding; capital reset; final short fold downweighted"},
        "candidates": {},
    }
    for candidate in CANDIDATES:
        full = _run(candidate, full_frames, gate)
        fold_results = []
        stage1_survivor = full["net_return"] is not None and float(full["net_return"]) > 0
        for fold in (folds if stage1_survivor else []):
            start, end = pd.Timestamp(fold.oos_start), pd.Timestamp(fold.oos_end)
            fold_frames = {}
            for symbol, prices_frame in prices.items():
                history = prices_frame.loc[prices_frame.index <= end]
                if history.empty:
                    continue
                features = _features(symbol, history, source_gate)
                oos = features.loc[(features.index >= start) & (features.index <= end)]
                if not oos.empty:
                    fold_frames[symbol] = oos
            metrics = _run(candidate, fold_frames, gate)
            fold_results.append({"fold": fold.fold, "start": fold.oos_start, "end": fold.oos_end, "observations": fold.oos_observations,
                                 **{k: v for k, v in metrics.items() if k != "orders"}})
        positive = sum(float(row["net_return"] or 0) > 0 for row in fold_results)
        robustness = ({
            "cost_1_5x_commission_one_tick": _run(candidate, full_frames, gate, fees=Decimal("0.002355")),
            "base_fees_two_tick_slippage": _run(candidate, full_frames, gate, ticks=2),
            "costs_and_execution_sensitivity_is_diagnostic_not_rule_change": True,
        } if stage1_survivor and positive >= max(1, (len(fold_results) + 1) // 2) else {
            "status": "NOT_RUN_AFTER_EARLY_REJECTION", "reason": "candidate failed stage-1 or walk-forward sign-consistency pruning",
        })
        # Promotion requires positive full-period and majority positive OOS folds, neither can be inferred from a single fit.
        evidence = "REJECTED_STAGE_1" if not stage1_survivor else ("REJECTED_WALK_FORWARD" if positive < max(1, (len(fold_results) + 1) // 2) else "WEAK")
        if stage1_survivor and len(fold_results) < 4:
            evidence = "NEEDS_MORE_DATA"
        result["candidates"][candidate] = {
            "candidate_id": candidate, "hypothesis_id": {"CANDIDATE_TREND20": "H1", "CANDIDATE_BREAKOUT20": "H2", "CANDIDATE_MEANREV5": "H5", "CANDIDATE_REL_STRENGTH": "H3"}[candidate],
            "first_pass": {k: v for k, v in full.items() if k != "orders"}, "walk_forward": {"folds": fold_results, "positive_folds": positive, "fold_count": len(fold_results)},
            "robustness": {k: {metric: value for metric, value in v.items() if metric != "orders"} if isinstance(v, dict) and "net_return" in v else v for k, v in robustness.items()},
            "evidence_classification": evidence,
            "promotion_gate": "NO_CANDIDATE_PASSED_PROMOTION_GATE" if evidence not in {"PROMISING", "STRONG_EVIDENCE"} else "ELIGIBLE",
            "full_run_orders": full["orders"],
        }
    result["hypotheses_not_testable"] = {
        "H1_MOVEMENT_LIQUIDITY_EFFICIENCY": "NEEDS_MORE_DATA: no approved historical BBO/spread/depth; daily volume is only a coarse activity proxy",
        "H2_ACTIVITY_TIGHT_SPREAD_BREAKOUT": "PARTIAL: breakout/activity tested, spread condition unavailable",
        "H3_LEADERSHIP_POSITIVE_BREADTH": "PARTIAL: relative strength tested; no separately conditioned breadth candidate",
        "H4_MOVEMENT_WITHOUT_LIQUIDITY": "NEEDS_MORE_DATA: historical spread/depth unavailable",
        "H5_LOW_DIRECTIONALITY_MEAN_REVERSION": "PARTIAL: simple five-observation pullback proxy tested; directional efficiency unavailable",
        "market_regime_conditioning": "INSUFFICIENT_DATA for defensible breadth/dispersion with this partial universe",
    }
    result["promotion_summary"] = "NO_CANDIDATE_PASSED_PROMOTION_GATE"
    result["official_tradesim_validation"] = "NOT_RUN_FOR_CANDIDATES: no candidate met PROMISING/STRONG_EVIDENCE gate; prior engine smoke is not candidate validation"
    (output_dir / "candidate_discovery.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (ROOT / "reports" / "research_candidate_summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"run_id": run_id, "path": str(output_dir), "candidates": {k: {"net": v["first_pass"]["net_return"], "positive_folds": v["walk_forward"]["positive_folds"], "folds": v["walk_forward"]["fold_count"], "evidence": v["evidence_classification"]} for k, v in result["candidates"].items()}}, indent=2))


if __name__ == "__main__":
    main()

"""Run the pre-registered Round 2 signal-only diagnostic on approved daily data.

This module deliberately stops before portfolio simulation unless the signal
gate passes. Signal returns are descriptive diagnostics, not executable PnL.
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
HYPOTHESIS_ID = "H6_REGIME_CONDITIONED_LOW_TURNOVER_MEAN_REVERSION"
PARAMETERS = {
    "pullback_return_5d_min": -0.08,
    "pullback_return_5d_max": -0.03,
    "close_above_sma50": True,
    "sma50_at_least_sma100": True,
    "directional_efficiency_10_max": 0.35,
    "benchmark": "official TradeSim SET50 daily index close; source timestamp is session date",
    "benchmark_regime": "SET50 above SMA50 and 20-session return >= -1%",
    "portfolio_design_preregistered": "top 3 equal weight; 5-session selection cadence; retain unchanged holdings while thesis remains valid; exit on thesis invalidation; no fixed maximum hold",
}
HORIZONS = {"next_open_next_close": 1, "next_open_plus_2_sessions": 2,
            "next_open_plus_3_sessions": 3, "next_open_plus_5_sessions": 5,
            "next_open_plus_10_sessions": 10}


def persist_selection(previous: list[str], thesis_valid: list[str], entrants: list[str], top_n: int) -> list[str]:
    """Retain unchanged names while thesis holds, then fill remaining slots."""
    selected = [symbol for symbol in previous if symbol in thesis_valid][:top_n]
    selected.extend(symbol for symbol in entrants if symbol not in selected and len(selected) < top_n)
    return selected


def cost_decomposition(gross_return, net_return, commission, vat, slippage, starting_capital):
    """Return cost components; modeled slippage is embedded in gross return."""
    gross_pnl = gross_return * starting_capital
    net_pnl = net_return * starting_capital
    fees = commission + vat
    return {"gross_pnl": gross_pnl, "commission": commission, "vat": vat,
            "total_fees": fees, "modeled_slippage": slippage, "net_pnl": net_pnl,
            "net_reconciliation_difference": net_pnl - (gross_pnl - fees),
            "slippage_treatment": "already reflected in gross_return; reported separately for attribution"}


def promotion_gate(stage1_gate: str, signal_gate: str, oos_consistency: bool, robustness: bool, concentration_ok: bool) -> str:
    if stage1_gate != "PASS" or signal_gate != "SIGNAL_DIAGNOSTIC_NOT_CLEARLY_POOR" or not oos_consistency or not robustness or not concentration_ok:
        return "NO_ROUND2_CANDIDATE_PASSED_PROMOTION_GATE"
    return "ELIGIBLE_FOR_HUMAN_REVIEW_ONLY"


def _load_inputs():
    from scripts.run_walk_forward import _load_prices
    from src.data.eligibility import MarketDataEligibilityGate

    prices = _load_prices(MarketDataEligibilityGate(ROOT))
    benchmark_path = ROOT / "data/official/tradesim/history/benchmark/SET50.csv"
    benchmark = pd.read_csv(benchmark_path, parse_dates=["Date"]).set_index("Date")["Close"].sort_index()
    if benchmark.index.has_duplicates:
        raise ValueError("SET50 benchmark input has duplicate dates; refusing silent deduplication")
    return prices, benchmark


def _regime(benchmark: pd.Series, prices: dict[str, pd.DataFrame]) -> pd.DataFrame:
    result = pd.DataFrame(index=benchmark.index)
    result["benchmark_close"] = benchmark
    result["benchmark_sma50"] = benchmark.rolling(50, min_periods=50).mean()
    result["benchmark_return20"] = benchmark.pct_change(20)
    daily_returns = pd.concat({symbol: frame["adj_close" if "adj_close" in frame else "adjusted_close"].pct_change() for symbol, frame in prices.items()}, axis=1)
    result["cross_sectional_dispersion"] = daily_returns.std(axis=1, ddof=0).where(daily_returns.notna().sum(axis=1) >= 10)
    result["benchmark_volatility20"] = benchmark.pct_change().rolling(20, min_periods=20).std(ddof=0)
    result["dispersion_threshold_past"] = result["cross_sectional_dispersion"].expanding(min_periods=60).median().shift(1)
    result["volatility_threshold_past"] = result["benchmark_volatility20"].expanding(min_periods=60).median().shift(1)
    result["benchmark_trend_state"] = np.where(result["benchmark_close"] > result["benchmark_sma50"], "ABOVE_SMA50", "BELOW_OR_EQUAL_SMA50")
    result["benchmark_return_state"] = np.where(result["benchmark_return20"] >= 0, "POSITIVE_20D", "NEGATIVE_20D")
    result["volatility_state"] = np.where(result["benchmark_volatility20"] > result["volatility_threshold_past"], "HIGH_VOL", "LOW_VOL")
    result["dispersion_state"] = np.where(result["cross_sectional_dispersion"] > result["dispersion_threshold_past"], "HIGH_DISPERSION", "LOW_DISPERSION")
    result["regime"] = np.where(
        (result["benchmark_close"] > result["benchmark_sma50"])
        & (result["benchmark_return20"] >= -0.01), "NEUTRAL_POSITIVE", "WEAK_OR_UNKNOWN"
    )
    result.loc[result[["benchmark_sma50", "benchmark_return20"]].isna().any(axis=1), "regime"] = "UNKNOWN"
    result.loc[result[["benchmark_volatility20", "dispersion_threshold_past", "volatility_threshold_past", "cross_sectional_dispersion"]].isna().any(axis=1), ["volatility_state", "dispersion_state"]] = "UNKNOWN"
    return result


def _events(prices: dict[str, pd.DataFrame], regime: pd.DataFrame, *, enforce_regime: bool = True) -> list[dict]:
    rows: list[dict] = []
    for symbol, frame in sorted(prices.items()):
        data = frame.sort_index()
        if data.index.has_duplicates:
            raise ValueError(f"Duplicate dates in approved data for {symbol}")
        adjusted_column = "adjusted_close" if "adjusted_close" in data else "adj_close"
        close = pd.to_numeric(data[adjusted_column], errors="coerce")
        raw_close = pd.to_numeric(data["close"], errors="coerce")
        adj_factor = close / raw_close
        adj_open = pd.to_numeric(data["open"], errors="coerce") * adj_factor
        ret5 = close.pct_change(5)
        sma50 = close.rolling(50, min_periods=50).mean()
        sma100 = close.rolling(100, min_periods=100).mean()
        efficiency = (close - close.shift(10)).abs() / close.diff().abs().rolling(10, min_periods=10).sum()
        eligibility = data.get("validity_status", pd.Series("VALID", index=data.index)).astype(str).str.upper()
        for pos, stamp in enumerate(data.index):
            if pos + 10 >= len(data):
                continue
            if stamp not in regime.index or regime.at[stamp, "regime"] == "UNKNOWN":
                continue
            if eligibility.iloc[pos] not in {"VALID", "USE", "USE_WITH_FLAG"}:
                continue
            values = (ret5.iloc[pos], sma50.iloc[pos], sma100.iloc[pos], efficiency.iloc[pos])
            if any(pd.isna(value) for value in values) or close.iloc[pos] <= 0:
                continue
            if not (PARAMETERS["pullback_return_5d_min"] <= ret5.iloc[pos] <= PARAMETERS["pullback_return_5d_max"]):
                continue
            if not (close.iloc[pos] > sma50.iloc[pos] and sma50.iloc[pos] >= sma100.iloc[pos]
                    and efficiency.iloc[pos] <= PARAMETERS["directional_efficiency_10_max"]
                    and (not enforce_regime or regime.at[stamp, "regime"] == "NEUTRAL_POSITIVE")):
                continue
            entry = adj_open.iloc[pos + 1]
            if pd.isna(entry) or entry <= 0:
                continue
            event = {"symbol": symbol, "signal_date": stamp.date().isoformat(),
                     "execution_date": data.index[pos + 1].date().isoformat(),
                     "pullback_return_5d": float(ret5.iloc[pos]),
                     "directional_efficiency_10": float(efficiency.iloc[pos]),
                     "regime": str(regime.at[stamp, "regime"]),
                     "benchmark_return20": float(regime.at[stamp, "benchmark_return20"]),
                     "benchmark_above_sma50": bool(regime.at[stamp, "benchmark_close"] > regime.at[stamp, "benchmark_sma50"]),
                     "benchmark_trend_state": str(regime.at[stamp, "benchmark_trend_state"]),
                     "benchmark_return_state": str(regime.at[stamp, "benchmark_return_state"]),
                     "volatility_state": str(regime.at[stamp, "volatility_state"]),
                     "dispersion_state": str(regime.at[stamp, "dispersion_state"])}
            for horizon, offset in HORIZONS.items():
                exit_close = close.iloc[pos + offset]
                event[horizon] = float(exit_close / entry - 1) if pd.notna(exit_close) else None
                event.setdefault("forward_exit_dates", {})[horizon] = data.index[pos + offset].date().isoformat()
            rows.append(event)
    return rows


def _summary(values: list[float]) -> dict:
    array = np.asarray(values, dtype=float)
    n = len(array)
    mean = float(array.mean()) if n else None
    se = float(array.std(ddof=1) / math.sqrt(n)) if n > 1 else None
    return {"sample_size": n, "mean": mean,
            "median": float(np.median(array)) if n else None,
            "hit_rate": float((array > 0).mean()) if n else None,
            "std_dev": float(array.std(ddof=1)) if n > 1 else None,
            "approx_95pct_mean_ci": [mean - 1.96 * se, mean + 1.96 * se] if se is not None else None,
            "quantiles": {str(q): float(np.quantile(array, q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)} if n else {}}


def _portfolio(prices: dict[str, pd.DataFrame], regime: pd.DataFrame) -> dict:
    from decimal import Decimal
    from scripts.run_design_a_backtest import set_tick_size
    from scripts.run_research_candidate_discovery import LoadedRowsGate, _features
    from src.backtest.engine import BacktestEngine, ExecutionPolicy
    from src.data.eligibility import MarketDataEligibilityGate

    source_gate = MarketDataEligibilityGate(ROOT)
    gate = LoadedRowsGate(source_gate, prices)
    features = {symbol: _features(symbol, frame, source_gate) for symbol, frame in prices.items()}
    for symbol, frame in features.items():
        frame["sma_100"] = frame["adjusted_close"].rolling(100, min_periods=100).mean()
    previous: list[str] = []

    def selector(frames, as_of, eligibility, top_n):
        nonlocal previous
        eligible = []
        for symbol, frame in frames.items():
            history = frame.loc[frame.index <= as_of]
            if history.empty or history.index[-1] != as_of or not eligibility.assess(symbol, as_of.date()).eligible:
                continue
            row = history.iloc[-1]
            if (as_of not in regime.index or regime.at[as_of, "regime"] != "NEUTRAL_POSITIVE"
                    or pd.isna(row.get("sma_50")) or pd.isna(row.get("sma_100"))
                    or row["close"] <= row["sma_50"] or row["sma_50"] < row["sma_100"]):
                continue
            ret5 = float(row["adjusted_close"] / history["adjusted_close"].iloc[-6] - 1) if len(history) >= 6 else math.nan
            efficiency = abs(float(row["adjusted_close"] - history["adjusted_close"].iloc[-11])) / float(history["adjusted_close"].diff().abs().iloc[-10:].sum()) if len(history) >= 11 and history["adjusted_close"].diff().abs().iloc[-10:].sum() else math.nan
            if math.isfinite(ret5) and PARAMETERS["pullback_return_5d_min"] <= ret5 <= PARAMETERS["pullback_return_5d_max"] and efficiency <= PARAMETERS["directional_efficiency_10_max"]:
                eligible.append((symbol, -ret5))
        eligible.sort(key=lambda value: (-value[1], value[0]))
        fresh = [symbol for symbol, _ in eligible]
        # Previously selected names persist while their broader trend thesis
        # remains valid; entry threshold is required only for new names.
        persistent = [symbol for symbol in previous if symbol in frames and as_of in frames[symbol].index
                      and eligibility.assess(symbol, as_of.date()).eligible
                      and frames[symbol].at[as_of, "close"] > frames[symbol].at[as_of, "sma_50"]
                      and frames[symbol].at[as_of, "sma_50"] >= frames[symbol].at[as_of, "sma_100"]
                      and as_of in regime.index and regime.at[as_of, "regime"] == "NEUTRAL_POSITIVE"]
        selected = persist_selection(persistent, persistent, fresh, top_n)
        previous = selected
        return selected

    result = BacktestEngine(
        initial_cash=Decimal("10000000"), top_n=3, rebalance_every=5,
        execution_policy=ExecutionPolicy(tick_size=set_tick_size, slippage_ticks=1),
        gate=gate, candidate_selector=selector,
    ).run(features)
    session_order = {stamp: index for index, stamp in enumerate(sorted({stamp for frame in features.values() for stamp in frame.index}))}
    fifo: dict[str, list[list]] = {}
    roundtrips: list[int] = []
    closed_fifo_pnls: list[Decimal] = []
    symbol_pnl: dict[str, Decimal] = {}
    for order in result.orders:
        if order.status != "FILLED":
            continue
        if order.side == "BUY":
            unit_cost = (order.order_value + order.total_fees) / order.quantity
            fifo.setdefault(order.symbol, []).append([order.quantity, order.execution_date, unit_cost, Decimal("0")])
            continue
        remaining = order.quantity
        while remaining and fifo.get(order.symbol):
            lot = fifo[order.symbol][0]
            matched = min(remaining, lot[0])
            unit_proceeds = (order.order_value - order.total_fees) / order.quantity
            realized_chunk = (unit_proceeds - lot[2]) * matched
            symbol_pnl[order.symbol] = symbol_pnl.get(order.symbol, Decimal("0")) + realized_chunk
            lot[3] += realized_chunk
            remaining -= matched
            lot[0] -= matched
            if lot[0] == 0:
                roundtrips.append(session_order[order.execution_date] - session_order[lot[1]])
                closed_fifo_pnls.append(lot[3])
                fifo[order.symbol].pop(0)
    snapshots_by_year: dict[str, dict] = {}
    for year in sorted({snapshot.timestamp.year for snapshot in result.snapshots if snapshot.equity is not None}):
        yearly = [snapshot for snapshot in result.snapshots if snapshot.equity is not None and snapshot.timestamp.year == year]
        snapshots_by_year[str(year)] = {"start_equity": str(yearly[0].equity), "end_equity": str(yearly[-1].equity), "net_change": str(yearly[-1].equity - yearly[0].equity)}
    regime_metrics = {}
    for field in ("benchmark_trend_state", "benchmark_return_state", "volatility_state", "dispersion_state"):
        grouped: dict[str, list[dict]] = {}
        group_orders: dict[str, list] = {}
        for order in result.orders:
            if order.status != "FILLED":
                continue
            order_label = str(regime.at[order.execution_date, field]) if order.execution_date in regime.index else "UNKNOWN"
            group_orders.setdefault(order_label, []).append(order)
        for index, snapshot in enumerate(result.snapshots):
            label = str(regime.at[snapshot.timestamp, field]) if snapshot.timestamp in regime.index else "UNKNOWN"
            if snapshot.equity is None:
                continue
            previous_equity = result.snapshots[index - 1].equity if index else None
            change = snapshot.equity - previous_equity if previous_equity is not None else Decimal("0")
            exposure = float((snapshot.equity - snapshot.cash) / snapshot.equity) if snapshot.equity else 0.0
            grouped.setdefault(label, []).append({"change": change, "exposure": exposure, "drawdown": snapshot.drawdown})
        regime_metrics[field] = {}
        for label, items in grouped.items():
            orders_in_state = group_orders.get(label, [])
            net_change = sum((item["change"] for item in items), Decimal("0"))
            fees_in_state = sum((order.total_fees for order in orders_in_state), Decimal("0"))
            gross_change = net_change + fees_in_state
            state_turnover = sum((order.order_value for order in orders_in_state), Decimal("0")) / Decimal("10000000")
            daily_changes = [item["change"] for item in items[1:]]
            regime_metrics[field][label] = {
                "sample_count": len(items), "gross_pnl_before_fees_after_modeled_slippage": str(gross_change),
                "gross_return_on_initial_capital": str(gross_change / Decimal("10000000")),
                "net_pnl": str(net_change), "net_return_on_initial_capital": str(net_change / Decimal("10000000")),
                "fees": str(fees_in_state), "hit_rate_of_observed_equity_changes": sum(change > 0 for change in daily_changes) / len(daily_changes) if daily_changes else None,
                "maximum_observed_portfolio_drawdown_in_state": str(min((item["drawdown"] for item in items if item["drawdown"] is not None), default=Decimal("0"))),
                "turnover": str(state_turnover), "filled_orders": len(orders_in_state),
                "average_exposure": sum(item["exposure"] for item in items) / len(items),
                "interpretation": "Descriptive state-conditioned snapshots; state intervals are non-contiguous and not independent folds.",
            }
    pnl_total = sum(symbol_pnl.values(), Decimal("0"))
    ordered_pnl = sorted(symbol_pnl.items(), key=lambda item: item[1], reverse=True)
    symbol_contributions = {"basis": "FIFO realized net PnL for fully/partially closed lots; open-lot mark-to-market excluded", "symbols_with_closed_pnl": len(symbol_pnl), "profitable_symbols": sum(value > 0 for value in symbol_pnl.values()), "losing_symbols": sum(value < 0 for value in symbol_pnl.values()), "top_positive": [{"symbol": key, "net_pnl": str(value)} for key, value in ordered_pnl[:5]], "top_negative": [{"symbol": key, "net_pnl": str(value)} for key, value in sorted(symbol_pnl.items(), key=lambda item: item[1])[:5]], "top_1_absolute_pnl_share": str(max((abs(ordered_pnl[0][1]) / sum((abs(v) for v in symbol_pnl.values()), Decimal("0"))), Decimal("0"))) if ordered_pnl and sum((abs(v) for v in symbol_pnl.values()), Decimal("0")) else None, "top_3_absolute_pnl_share": str(sum((abs(value) for _, value in ordered_pnl[:3]), Decimal("0")) / sum((abs(value) for value in symbol_pnl.values()), Decimal("0"))) if symbol_pnl and sum((abs(value) for value in symbol_pnl.values()), Decimal("0")) else None, "fifo_total_closed_net_pnl": str(pnl_total)}
    decomposition = cost_decomposition(result.gross_return, result.net_return, result.commission, result.vat, result.slippage, Decimal("10000000"))
    positive_pnls = [value for value in closed_fifo_pnls if value > 0]
    negative_pnls = [value for value in closed_fifo_pnls if value < 0]
    expected_payoff = (sum(positive_pnls, Decimal("0")) / len(positive_pnls)) / abs(sum(negative_pnls, Decimal("0")) / len(negative_pnls)) if positive_pnls and negative_pnls else None
    return {
        "candidate_id": "H6_TOP3_5SESSION_PERSIST_THESIS",
        "net_return": str(result.net_return), "gross_return": str(result.gross_return),
        "final_equity": str(result.final_equity), "maximum_drawdown": str(result.maximum_drawdown),
        "turnover": str(result.turnover), "commission": str(result.commission), "vat": str(result.vat),
        "total_fees": str(result.total_fees), "modeled_slippage": str(result.slippage),
        "cost_decomposition": {key: str(value) if isinstance(value, Decimal) else value for key, value in decomposition.items()},
        "filled_orders": sum(order.status == "FILLED" for order in result.orders),
        "non_fills": sum(order.status == "NON_FILL" for order in result.orders),
        "unique_symbols_traded": result.unique_symbols_traded,
        "average_equity_exposure": (sum(float((s.equity - s.cash) / s.equity) for s in result.snapshots if s.equity) / max(1, sum(bool(s.equity) for s in result.snapshots))),
        "completed_fifo_roundtrips": len(roundtrips),
        "average_holding_observations": sum(roundtrips) / len(roundtrips) if roundtrips else None,
        "fifo_win_rate": len(positive_pnls) / len(closed_fifo_pnls) if closed_fifo_pnls else None,
        "fifo_expected_payoff": str(expected_payoff) if expected_payoff is not None else None,
        "fifo_symbol_concentration": symbol_contributions,
        "yearly_equity_change": snapshots_by_year,
        "portfolio_regime_analysis": regime_metrics,
        "valuation_complete": result.valuation_complete,
        "stage1_gate": "PASS" if result.net_return is not None and result.net_return > 0 and result.maximum_drawdown is not None and abs(result.maximum_drawdown) <= Decimal("0.35") else "REJECTED_STAGE_1",
        "walk_forward": "NOT_RUN_AFTER_STAGE1_REJECTION" if result.net_return is None or result.net_return <= 0 or result.maximum_drawdown is None or abs(result.maximum_drawdown) > Decimal("0.35") else "REQUIRES_CHRONOLOGICAL_FOLDS",
        "orders": [{"date": order.execution_date.date().isoformat(), "symbol": order.symbol, "side": order.side,
                    "quantity": order.quantity, "status": order.status, "gross_value": str(order.order_value),
                    "executed_price": str(order.executed_price) if order.executed_price is not None else None,
                    "commission": str(order.commission), "vat": str(order.vat), "slippage": str(order.slippage)}
                   for order in result.orders],
    }


def main() -> None:
    prices, benchmark = _load_inputs()
    regimes = _regime(benchmark, prices)
    events = _events(prices, regimes)
    unconditioned_events = _events(prices, regimes, enforce_regime=False)
    by_horizon = {name: _summary([row[name] for row in events if row.get(name) is not None])
                  for name in HORIZONS}
    by_regime = {}
    for label in sorted({row["regime"] for row in unconditioned_events}):
        subset = [row for row in unconditioned_events if row["regime"] == label]
        by_regime[label] = {horizon: _summary([row[horizon] for row in subset if row.get(horizon) is not None])
                            for horizon in HORIZONS}
    regime_breakdown = {}
    for field in ("benchmark_trend_state", "benchmark_return_state", "volatility_state", "dispersion_state"):
        regime_breakdown[field] = {}
        for label in sorted({row[field] for row in unconditioned_events}):
            subset = [row for row in unconditioned_events if row[field] == label]
            regime_breakdown[field][label] = {horizon: _summary([row[horizon] for row in subset if row.get(horizon) is not None]) for horizon in HORIZONS}
    # Conservative gate: enough independent symbols and events plus positive
    # mean at >=3 horizons; overlapping events remain a dependence limitation.
    unique_symbols = len({row["symbol"] for row in events})
    positive_horizons = sum((value["mean"] or 0) > 0 for value in by_horizon.values())
    gate = "SIGNAL_DIAGNOSTIC_NOT_CLEARLY_POOR" if len(events) >= 100 and unique_symbols >= 10 and positive_horizons >= 3 else "REJECTED_SIGNAL_DIAGNOSTIC"
    stage1 = "NOT_RUN_AFTER_EARLY_REJECTION" if gate == "REJECTED_SIGNAL_DIAGNOSTIC" else _portfolio(prices, regimes)
    round1 = json.loads((ROOT / "reports/research_candidate_summary.json").read_text(encoding="utf-8"))["candidates"]["CANDIDATE_MEANREV5"]["first_pass"]
    promotion_result = promotion_gate(stage1.get("stage1_gate", "NOT_RUN") if isinstance(stage1, dict) else "NOT_RUN", gate, False, False, False)
    report = {
        "schema_version": 1, "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_round2_signal",
        "hypothesis_id": HYPOTHESIS_ID, "evidence_classification": "SIGNAL_DIAGNOSTIC_ONLY",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_source": "approved_market_data_manifest.csv daily OHLCV + official TradeSim SET50 benchmark history",
        "data_period": {"stock_data_end": max(frame.index.max() for frame in prices.values()).date().isoformat(),
                        "benchmark_end": benchmark.index.max().date().isoformat(),
                        "symbols_loaded": len(prices)},
        "preregistered_parameters": PARAMETERS, "signals": {"sample_size": len(events), "unique_symbols": unique_symbols,
            "regime_counts": pd.Series([row["regime"] for row in events]).value_counts().to_dict()},
        "forward_returns": by_horizon, "regime_forward_returns_unconditioned_stock_setup": by_regime,
        "mandatory_regime_analysis": regime_breakdown,
        "portfolio_stage": stage1,
        "round1_meanrev5_comparison": {"round1_net_return": round1["net_return"], "round1_gross_return": round1["gross_return"], "round1_maximum_drawdown": round1["maximum_drawdown"], "round1_turnover": round1["turnover"], "round1_fees": round1["total_fees"], "round1_slippage": round1["slippage"], "round2_turnover_reduction_fraction": (1 - float(stage1["turnover"]) / float(round1["turnover"])) if isinstance(stage1, dict) else None},
        "walk_forward": "NOT_RUN_AFTER_STAGE1_REJECTION" if isinstance(stage1, dict) and stage1.get("stage1_gate") != "PASS" else "NOT_RUN",
        "robustness": "NOT_RUN_AFTER_STAGE1_REJECTION" if isinstance(stage1, dict) and stage1.get("stage1_gate") != "PASS" else "NOT_RUN",
        "cost_sensitivity": {"baseline": "RESEARCH_EXECUTION_V1", "zero_slippage": "NOT_RUN_AFTER_STAGE1_REJECTION", "half_tick_diagnostic": "NOT_RUN_AFTER_STAGE1_REJECTION", "worse_cost_case": "NOT_RUN_AFTER_STAGE1_REJECTION"},
        "gate": {"status": gate, "positive_horizons": positive_horizons,
                 "rule": ">=100 events, >=10 symbols, positive mean at 3 of 5 horizons; independent evidence remains subject to temporal/symbol dependence"},
        "limitations": ["Signal statistics are not executable PnL.", "Events overlap in time and by symbol; approximate normal confidence intervals do not adjust for dependence.", "No historical BBO, spread, or depth is used.", "The benchmark series is official TradeSim history and has no fabricated rows."],
        "events": events, "unconditioned_stock_setup_events": unconditioned_events,
        "stage1": stage1,
        "promotion_result": promotion_result,
    }
    (ROOT / "reports/research_round2_summary.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({key: report[key] for key in ("run_id", "signals", "forward_returns", "gate", "stage1")}, indent=2))


if __name__ == "__main__":
    main()

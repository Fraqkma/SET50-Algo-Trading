"""Deterministic FIFO trade accounting and competition metric calculations.

Competition dates and metric scoping come from the canonical period config.
Metric thresholds remain UNKNOWN unless verified from the organizer's supplied
performance criteria and a continuous, complete scored-period portfolio run.
"""
from __future__ import annotations

from collections import defaultdict, deque
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any, Iterable

from src.competition.period import boundary_fill_status, competition_scope


@dataclass
class BuyLot:
    lot_id: str
    symbol: str
    open_event: str
    open_timestamp: str
    initial_quantity: int
    remaining_quantity: int
    entry_price: float
    entry_fees_remaining: float = 0.0
    matched_sell_quantity: int = 0
    closing_events: list[str] = field(default_factory=list)
    net_pnl: float = 0.0
    completed: bool = False


class FifoLotLedger:
    """Match actual fill quantities FIFO independently for each symbol."""

    def __init__(self) -> None:
        self.open_lots: dict[str, deque[BuyLot]] = defaultdict(deque)
        self.lots: list[BuyLot] = []
        self._sequence = 0
        self._events: dict[str, tuple[tuple[Any, ...], Any]] = {}

    def buy(self, symbol: str, quantity: int, price: float, timestamp: str,
            event_id: str | None = None, fees: float = 0.0) -> BuyLot:
        self._validate_fill(symbol, quantity, price)
        event_id = event_id or f"buy-{self._sequence + 1}"
        signature = ("buy", symbol, quantity, float(price), timestamp, float(fees))
        duplicate = self._duplicate_event(event_id, signature)
        if duplicate is not None:
            return duplicate
        self._sequence += 1
        lot = BuyLot(f"{event_id}-{self._sequence}", symbol,
                     event_id, timestamp,
                     quantity, quantity, float(price), float(fees))
        self.open_lots[symbol].append(lot)
        self.lots.append(lot)
        self._events[event_id] = (signature, lot)
        return lot

    def sell(self, symbol: str, quantity: int, price: float, timestamp: str,
             event_id: str, fees: float = 0.0) -> list[dict[str, Any]]:
        self._validate_fill(symbol, quantity, price)
        if not event_id:
            raise ValueError("sell fills require a stable event_id for duplicate detection")
        signature = ("sell", symbol, quantity, float(price), timestamp, float(fees))
        duplicate = self._duplicate_event(event_id, signature)
        if duplicate is not None:
            return duplicate
        available = sum(l.remaining_quantity for l in self.open_lots[symbol])
        if quantity > available:
            raise ValueError(f"sell fill {quantity} exceeds held {available} for {symbol}")
        remaining = quantity
        matches: list[tuple[BuyLot, int]] = []
        while remaining:
            lot = self.open_lots[symbol][0]
            matched = min(remaining, lot.remaining_quantity)
            matches.append((lot, matched))
            lot.remaining_quantity -= matched
            lot.matched_sell_quantity += matched
            lot.closing_events.append(event_id)
            remaining -= matched
            if lot.remaining_quantity == 0:
                lot.completed = True
                self.open_lots[symbol].popleft()
        total_value = quantity * float(price)
        result = []
        for lot, matched in matches:
            # Allocate fees proportionally to actual matched notional/quantity.
            buy_fee = lot.entry_fees_remaining * matched / (matched + lot.remaining_quantity)
            lot.entry_fees_remaining -= buy_fee
            sell_fee = float(fees) * matched / quantity
            pnl = matched * (float(price) - lot.entry_price) - buy_fee - sell_fee
            lot.net_pnl += pnl
            result.append({"symbol": symbol, "lot_id": lot.lot_id,
                           "open_event": lot.open_event, "close_event": event_id,
                           "quantity": matched, "timestamp": timestamp,
                           "net_pnl": pnl, "completed_roundtrip": lot.completed})
        assert sum(x[1] for x in matches) == quantity and total_value >= 0
        self._events[event_id] = (signature, result)
        return result

    def _duplicate_event(self, event_id: str, signature: tuple[Any, ...]) -> Any | None:
        previous = self._events.get(event_id)
        if previous is None:
            return None
        previous_signature, result = previous
        if previous_signature != signature:
            raise ValueError(f"event_id {event_id!r} was already used for a different fill")
        return deepcopy(result)

    @staticmethod
    def _validate_fill(symbol: str, quantity: int, price: float) -> None:
        if not symbol or quantity <= 0 or price <= 0:
            raise ValueError("fills require symbol, positive integer quantity, and positive price")
        if int(quantity) != quantity:
            raise ValueError("fill quantity must be an integer")

    @property
    def completed_roundtrips(self) -> list[BuyLot]:
        return [lot for lot in self.lots if lot.completed]


def _max_drawdown(values: Iterable[float]) -> float | None:
    points = list(values)
    if not points:
        return None
    peak = points[0]
    worst = 0.0
    for value in points:
        if value > peak:
            peak = value
        if peak > 0:
            worst = max(worst, (peak - value) / peak * 100)
    return worst


def competition_metrics(portfolio_closes: Iterable[float] | None,
                        benchmark_closes: Iterable[float] | None,
                        invested_values: Iterable[float] | None = None,
                        roundtrips: Iterable[BuyLot] | None = None,
                        starting_nav: float | None = None) -> dict[str, Any]:
    """Calculate close-based returns, drawdowns and completed-lot trade stats."""
    navs = [] if portfolio_closes is None else list(portfolio_closes)
    benchmarks = [] if benchmark_closes is None else list(benchmark_closes)
    metrics: dict[str, Any] = {
        "portfolio_total_return": None, "benchmark_return": None,
        "portfolio_max_drawdown": _max_drawdown(navs),
        "benchmark_max_drawdown": _max_drawdown(benchmarks),
        "excess_return": None, "calmar_ratio": None,
        "average_portfolio_exposure": None, "round_trips": None,
        "win_rate": None, "average_win": None, "average_loss": None,
        "expected_payoff": None,
    }
    start = starting_nav if starting_nav is not None else (navs[0] if navs else None)
    if start and navs:
        metrics["portfolio_total_return"] = (navs[-1] / start - 1) * 100
    if benchmarks and benchmarks[0] != 0:
        metrics["benchmark_return"] = (benchmarks[-1] / benchmarks[0] - 1) * 100
    if metrics["portfolio_total_return"] is not None and metrics["benchmark_return"] is not None:
        metrics["excess_return"] = metrics["portfolio_total_return"] - metrics["benchmark_return"]
    dd = metrics["portfolio_max_drawdown"]
    if dd is not None and metrics["portfolio_total_return"] is not None:
        metrics["calmar_ratio"] = metrics["portfolio_total_return"] / dd if dd else None
    if invested_values is not None and navs:
        invested = list(invested_values)
        if len(invested) == len(navs) and all(nav > 0 for nav in navs):
            metrics["average_portfolio_exposure"] = sum(v / n for v, n in zip(invested, navs)) / len(navs)
    completed = None if roundtrips is None else [lot.net_pnl for lot in roundtrips if lot.completed]
    if completed is not None:
        metrics["round_trips"] = len(completed)
        wins = [pnl for pnl in completed if pnl > 0]
        losses = [pnl for pnl in completed if pnl < 0]
        counted = len(wins) + len(losses)
        metrics["win_rate"] = len(wins) / counted * 100 if counted else 0.0
        metrics["average_win"] = sum(wins) / len(wins) if wins else 0.0
        metrics["average_loss"] = abs(sum(losses) / len(losses)) if losses else 0.0
        metrics["expected_payoff"] = (
            (len(wins) / counted * metrics["average_win"] - len(losses) / counted * metrics["average_loss"])
            if counted else 0.0
        )
    return metrics


def competition_metrics_for_period(
    daily_records: Iterable[dict[str, Any]],
    fills: Iterable[dict[str, Any]],
    *,
    expected_trading_dates: Iterable[str],
    starting_nav: float | None = None,
    commission_rate: float = 0.00157,
    vat_rate: float = 0.07,
    evidence_classification: str = "RESEARCH_ESTIMATE",
) -> dict[str, Any]:
    """Calculate official-window estimates only when calendar and boundaries are complete.

    Daily rows require date, nav_close, benchmark_close, and invested_value. The caller
    must pass the canonical SET trading-date list. Cross-boundary FIFO treatment is
    deliberately UNKNOWN until the organizer resolves it.
    """
    from src.competition.period import filter_daily_records, load_competition_period

    period = load_competition_period()
    daily = filter_daily_records(daily_records, "date", period)
    dates = [str(row["date"])[:10] for row in daily]
    scope = competition_scope(dates, period)
    expected = sorted(str(value)[:10] for value in expected_trading_dates)
    calendar_matches = expected == scope["expected_trading_dates"]
    values_present = all(all(row.get(key) is not None for key in ("nav_close", "benchmark_close", "invested_value")) for row in daily)
    complete = scope["status"] == "COMPLETE_COMPETITION_PERIOD" and calendar_matches and values_present
    boundary = boundary_fill_status(fills, period)
    result: dict[str, Any] = {
        "period_scope": scope,
        "calendar_matches_canonical": calendar_matches,
        "boundary_status": boundary,
        "classification": evidence_classification if complete and boundary["status"] != "UNKNOWN" else "UNKNOWN_OR_INCOMPLETE",
    }
    if not complete:
        result["metrics"] = competition_metrics(None, None, None, None, starting_nav)
        result["qualification"] = qualification_report(result["metrics"], "CANONICAL_COMPETITION_WINDOW_INCOMPLETE")
        return result

    daily.sort(key=lambda row: str(row["date"])[:10])
    ledger, fifo = fifo_metrics_from_fills(fills, commission_rate, vat_rate)
    metrics = competition_metrics(
        [float(row["nav_close"]) for row in daily],
        [float(row["benchmark_close"]) for row in daily],
        [float(row["invested_value"]) for row in daily],
        ledger.completed_roundtrips if boundary["status"] != "UNKNOWN" else None,
        starting_nav=starting_nav,
    )
    if boundary["status"] == "UNKNOWN":
        for key in ("round_trips", "win_rate", "average_win", "average_loss", "expected_payoff"):
            metrics[key] = None
    result["metrics"] = metrics
    result["qualification"] = qualification_report(
        metrics,
        "CANONICAL_COMPETITION_WINDOW; FIFO boundary treatment unresolved" if boundary["status"] == "UNKNOWN"
        else "CANONICAL_COMPETITION_WINDOW",
    )
    result["fifo_fill_metrics"] = fifo
    return result


def qualification_report(metrics: dict[str, Any], source_evidence: str = "TASK_SPECIFICATION_PDF_NOT_VERIFIED") -> dict[str, dict[str, Any]]:
    """Evaluate supplied Common Criteria; preserve evidence and threshold margin."""
    drawdown_limit = (None if metrics.get("benchmark_max_drawdown") is None
                      else 1.5 * metrics["benchmark_max_drawdown"])
    checks: dict[str, tuple[Any, str, Any, Any]] = {
        "drawdown_vs_benchmark": (metrics.get("portfolio_max_drawdown"),
                                  f"< {drawdown_limit} (% of NAV)", drawdown_limit,
                                  None if drawdown_limit is None or metrics.get("portfolio_max_drawdown") is None
                                  else drawdown_limit - metrics["portfolio_max_drawdown"]),
        "minimum_roundtrips": (metrics.get("round_trips"), ">= 5", 5,
                               None if metrics.get("round_trips") is None else metrics["round_trips"] - 5),
        "average_exposure": (metrics.get("average_portfolio_exposure"), ">= 0.50", 0.50,
                             None if metrics.get("average_portfolio_exposure") is None else metrics["average_portfolio_exposure"] - 0.50),
        "expected_payoff": (metrics.get("expected_payoff"), "> 0", 0,
                            metrics.get("expected_payoff")),
    }
    result = {}
    for name, (value, threshold, comparator, margin) in checks.items():
        passed = None if value is None or comparator is None else (
            value < comparator if name == "drawdown_vs_benchmark" else
            value >= comparator if name in {"minimum_roundtrips", "average_exposure"} else value > comparator
        )
        status = "UNKNOWN" if passed is None else "PASS" if passed else "FAIL"
        explanation = (
            "Required metric or comparison value is unavailable."
            if passed is None else
            "Measured value satisfies the stated threshold."
            if passed else
            "Measured value does not satisfy the stated threshold."
        )
        result[name] = {"status": status, "value": value,
                        "threshold": threshold, "margin": margin,
                        "explanation": explanation, "source_evidence": source_evidence}
    return result


def fifo_metrics_from_fills(fills: Iterable[dict[str, Any]], commission_rate: float,
                            vat_rate: float) -> tuple[FifoLotLedger, dict[str, Any]]:
    """Rebuild FIFO round-trips from actual fill records and official fee rates."""
    ledger = FifoLotLedger()
    for index, fill in enumerate(fills, start=1):
        symbol = str(fill.get("Symbol", "")).strip()
        quantity = int(float(fill.get("Volume")))
        price = float(fill.get("Price"))
        notional = quantity * price
        fee = notional * commission_rate * (1 + vat_rate)
        timestamp = str(fill.get("Timestamp", ""))
        event = f"{fill.get('Order Number') or 'fill'}-{index}"
        if fill.get("Side") == "Buy":
            ledger.buy(symbol, quantity, price, timestamp, event, fee)
        elif fill.get("Side") == "Sell":
            ledger.sell(symbol, quantity, price, timestamp, event, fee)
        else:
            raise ValueError(f"unknown fill side: {fill.get('Side')!r}")
    return ledger, competition_metrics([], [], roundtrips=ledger.completed_roundtrips)


def award_readiness(metrics: dict[str, Any]) -> dict[str, Any]:
    """Expose descriptive award criteria and ranking inputs without scoring."""
    total, excess = metrics.get("portfolio_total_return"), metrics.get("excess_return")
    alpha_criteria = {
                "portfolio_total_return_nonnegative": "UNKNOWN" if total is None else "PASS" if total >= 0 else "FAIL",
                "excess_return_nonnegative": "UNKNOWN" if excess is None else "PASS" if excess >= 0 else "FAIL"}
    return {"best_alpha": {"criteria": alpha_criteria,
            "award_eligible": "UNKNOWN" if "UNKNOWN" in alpha_criteria.values() else "PASS" if all(value == "PASS" for value in alpha_criteria.values()) else "FAIL",
            "ranking_metrics": {k: metrics.get(k) for k in ("excess_return", "calmar_ratio", "portfolio_total_return")}},
            "best_risk_control_ranking_metrics": {k: metrics.get(k) for k in ("calmar_ratio", "excess_return", "portfolio_max_drawdown")},
            "most_active_trader_roundtrips": metrics.get("round_trips"),
            "precision_trader_win_rate": metrics.get("win_rate")}


def rank_award_candidates(candidates: dict[str, dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Rank only supplied candidate records; unknown inputs remain unranked."""
    def value(item: tuple[str, dict[str, Any]], key: str) -> float | None:
        raw = item[1].get(key)
        return None if raw is None else float(raw)

    def rows(names: list[tuple[str, dict[str, Any]]], fields: tuple[str, ...], order: tuple[bool, ...]) -> list[dict[str, Any]]:
        names.sort(key=lambda item: tuple((-value(item, field) if descending else value(item, field)) for field, descending in zip(fields, order)))
        return [{"rank": index, "candidate": name,
                 "metrics": {field: candidate.get(field) for field in fields}}
                for index, (name, candidate) in enumerate(names, start=1)]

    items = list(candidates.items())
    alpha_eligible = [item for item in items
                      if value(item, "portfolio_total_return") is not None
                      and value(item, "excess_return") is not None
                      and value(item, "calmar_ratio") is not None
                      and value(item, "portfolio_total_return") >= 0
                      and value(item, "excess_return") >= 0]
    risk_ready = [item for item in items
                  if all(value(item, key) is not None
                         for key in ("calmar_ratio", "excess_return", "portfolio_max_drawdown"))]
    activity_ready = [item for item in items if value(item, "round_trips") is not None]
    precision_ready = [item for item in items if value(item, "win_rate") is not None]
    return {
        "best_alpha": rows(alpha_eligible, ("excess_return", "calmar_ratio", "portfolio_total_return"), (True, True, True)),
        "best_risk_control": rows(risk_ready, ("calmar_ratio", "excess_return", "portfolio_max_drawdown"), (True, True, False)),
        "most_active_trader": rows(activity_ready, ("round_trips",), (True,)),
        "precision_trader": rows(precision_ready, ("win_rate",), (True,)),
    }

"""Event-ordered research backtest harness.

The engine deliberately requires an explicit execution policy. Competition
rules constrain order type, IOC validity, fees, and one-tick slippage, but do
not fully specify a historical bar fill model or SET tick-size mapping.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, ROUND_DOWN
from math import sqrt
from typing import Callable, Mapping

import pandas as pd

from src.data.eligibility import MarketDataEligibilityGate
from src.execution.order_manager import OrderSide, OrderType, Validity
from src.strategies.cross_sectional import rank_time_series_candidates
from src.strategies.timing import next_trading_session, rebalance_dates

from .transaction_cost import calculate_transaction_costs

TickSizeFn = Callable[[Decimal], Decimal]


@dataclass(frozen=True)
class ExecutionPolicy:
    """Explicit LIMIT IOC bar-fill policy used by the research harness."""

    tick_size: TickSizeFn
    order_type: OrderType = OrderType.LIMIT
    validity: Validity = Validity.IOC

    def __post_init__(self) -> None:
        if self.order_type not in {OrderType.LIMIT, OrderType.MARKET_TO_LIMIT}:
            raise ValueError("Only LIMIT and MARKET_TO_LIMIT orders are allowed.")
        if self.validity is not Validity.IOC:
            raise ValueError("Only IOC validity is allowed.")

    def requested_price(self, side: OrderSide, open_price: Decimal) -> Decimal:
        tick = self.tick_size(open_price)
        if tick <= 0:
            raise ValueError("tick_size must return a positive Decimal.")
        return open_price + tick if side is OrderSide.BUY else open_price - tick

    def fill_price(self, side: OrderSide, requested: Decimal, low: Decimal, high: Decimal) -> Decimal | None:
        return requested if low <= requested <= high else None


@dataclass(frozen=True)
class OrderEvent:
    signal_date: pd.Timestamp
    execution_date: pd.Timestamp
    symbol: str
    side: str
    quantity: int
    order_type: str
    validity: str
    requested_price: Decimal | None
    executed_price: Decimal | None
    status: str
    reason: str | None
    order_value: Decimal
    commission: Decimal
    vat: Decimal
    total_fees: Decimal
    slippage: Decimal
    membership_end_date: pd.Timestamp | None = None


@dataclass(frozen=True)
class SelectionEvent:
    signal_date: pd.Timestamp
    execution_date: pd.Timestamp
    selected_symbols: tuple[str, ...]


@dataclass(frozen=True)
class PortfolioSnapshot:
    timestamp: pd.Timestamp
    signal_date: pd.Timestamp | None
    execution_date: pd.Timestamp | None
    cash: Decimal
    positions: dict[str, int]
    market_value: Decimal
    equity: Decimal | None
    gross_return: Decimal | None
    net_return: Decimal | None
    drawdown: Decimal | None
    valuation_gaps: tuple[str, ...] = ()
    valuation_status: str = "COMPLETE"
    valuation_gap_reasons: dict[str, str] = field(default_factory=dict)
    unvalued_positions: dict[str, int] = field(default_factory=dict)


@dataclass(frozen=True)
class BacktestResult:
    """Auditable output of one deterministic event-ordered run."""

    final_equity: Decimal | None
    gross_return: Decimal | None
    net_return: Decimal | None
    volatility: Decimal | None
    maximum_drawdown: Decimal | None
    turnover: Decimal
    commission: Decimal
    vat: Decimal
    total_fees: Decimal
    slippage: Decimal
    trade_count: int
    unique_symbols_traded: int
    orders: tuple[OrderEvent, ...] = ()
    selections: tuple[SelectionEvent, ...] = ()
    snapshots: tuple[PortfolioSnapshot, ...] = ()
    valuation_complete: bool = True
    complete_valuation_snapshots: int = 0
    incomplete_valuation_snapshots: int = 0
    unvalued_positions: dict[str, int] = field(default_factory=dict)


class BacktestEngine:
    """Run Design C selection with Design A filtering and explicit timing.

    ``market_data`` must be a mapping of symbol to feature frames obtained via
    the approved research loader. The engine never fills missing dates and
    rechecks the eligibility gate before signal and execution events.
    """

    def __init__(
        self,
        *,
        initial_cash: Decimal = Decimal("10000000"),
        top_n: int = 10,
        rebalance_every: int = 3,
        execution_policy: ExecutionPolicy,
        design: str = "A",
        gate: object | None = None,
    ) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive.")
        if top_n < 1:
            raise ValueError("top_n must be positive.")
        if design not in {"A", "C"}:
            raise ValueError("design must be 'A' or 'C'.")
        self.initial_cash = initial_cash
        self.top_n = top_n
        self.rebalance_every = rebalance_every
        self.execution_policy = execution_policy
        self.design = design
        self.gate = gate or MarketDataEligibilityGate()

    def run(self, market_data: Mapping[str, pd.DataFrame]) -> BacktestResult:
        dates = _union_dates(market_data)
        if len(dates) < 2:
            raise ValueError("At least two observed trading dates are required.")
        schedule = set(rebalance_dates(dates, every_n_trading_days=self.rebalance_every)[1:])
        cash = self.initial_cash
        positions: dict[str, int] = {}
        orders: list[OrderEvent] = []
        selections: list[SelectionEvent] = []
        snapshots: list[PortfolioSnapshot] = []
        peak = self.initial_cash
        pending: dict[pd.Timestamp, tuple[pd.Timestamp, list[str]]] = {}
        boundary_attempted: set[str] = set()
        for current_date in dates:
            signal_date = None
            execution_date = None
            if current_date in pending:
                signal_date, selected_symbols = pending.pop(current_date)
                execution_date = current_date
                cash, events = self._rebalance(
                    signal_date, execution_date, selected_symbols, market_data, positions, cash
                )
                orders.extend(events)
            for symbol in sorted(tuple(positions)):
                membership_end = _membership_end(self.gate, symbol, current_date)
                if (
                    positions.get(symbol, 0) > 0
                    and symbol not in boundary_attempted
                    and membership_end == current_date.date()
                ):
                    boundary_attempted.add(symbol)
                    cash, event = self._submit(
                        current_date, current_date, symbol, OrderSide.SELL,
                        positions.get(symbol, 0), market_data[symbol], cash, positions,
                        event_reason="UNIVERSE_BOUNDARY_EXIT",
                        membership_end_date=current_date,
                    )
                    orders.append(event)
            if current_date in schedule and current_date != dates[-1]:
                signal_date = current_date
                selected = rank_time_series_candidates(
                    market_data, current_date.date(),
                    top_n=len(market_data) if self.design == "A" else self.top_n,
                    gate=self.gate,
                )
                next_session = next_trading_session(current_date, dates)
                if next_session <= current_date:
                    raise AssertionError("Execution must be strictly after signal date.")
                selected_symbols = selected["symbol"].tolist()
                pending[next_session] = (current_date, selected_symbols)
                selections.append(SelectionEvent(current_date, next_session, tuple(selected_symbols)))
            market_value, valuation_gaps, gap_reasons = _market_value(
                positions, market_data, current_date, gate=self.gate
            )
            valuation_status = "INCOMPLETE" if valuation_gaps else "COMPLETE"
            equity = cash + market_value if valuation_status == "COMPLETE" else None
            if equity is not None:
                peak = max(peak, equity)
                returns = (equity - self.initial_cash) / self.initial_cash
                drawdown = (equity - peak) / peak
            else:
                returns = None
                drawdown = None
            snapshots.append(
                PortfolioSnapshot(
                    current_date, signal_date, execution_date, cash, dict(positions), market_value,
                    equity, returns, returns, drawdown, tuple(valuation_gaps), valuation_status,
                    gap_reasons, {symbol: positions[symbol] for symbol in valuation_gaps},
                )
            )
        return _result(self.initial_cash, snapshots, orders, selections)

    def _rebalance(
        self,
        signal_date: pd.Timestamp,
        execution_date: pd.Timestamp,
        selected: list[str],
        market_data: Mapping[str, pd.DataFrame],
        positions: dict[str, int],
        cash: Decimal,
    ) -> tuple[Decimal, list[OrderEvent]]:
        events: list[OrderEvent] = []
        target = {str(symbol).upper() for symbol in selected}
        prices = {symbol: _bar(market_data[symbol], execution_date) for symbol in target if symbol in market_data}
        equity_before = cash + _market_value(positions, market_data, execution_date, gate=self.gate)[0]
        slot_value = equity_before / Decimal(len(target)) if target else Decimal("0")

        for symbol, current_quantity in list(positions.items()):
            desired = 0
            if symbol in target and symbol in prices and prices[symbol] is not None:
                desired = _target_quantity(
                    slot_value,
                    _buy_budget_price(
                        self.execution_policy.requested_price(OrderSide.BUY, prices[symbol]["open"])
                    ),
                )
            if current_quantity > desired:
                cash, event = self._submit(
                    signal_date, execution_date, symbol, OrderSide.SELL,
                    current_quantity - desired, market_data[symbol], cash, positions,
                )
                events.append(event)

        for symbol in sorted(target):
            if symbol not in prices or prices[symbol] is None:
                events.append(_non_fill(signal_date, execution_date, symbol, "BUY", "DATA_UNAVAILABLE"))
                continue
            desired = _target_quantity(
                slot_value,
                _buy_budget_price(
                    self.execution_policy.requested_price(OrderSide.BUY, prices[symbol]["open"])
                ),
            )
            quantity = max(0, desired - positions.get(symbol, 0))
            if quantity:
                cash, event = self._submit(
                    signal_date, execution_date, symbol, OrderSide.BUY,
                    quantity, market_data[symbol], cash, positions,
                )
                events.append(event)
        return cash, events

    def _submit(
        self,
        signal_date: pd.Timestamp,
        execution_date: pd.Timestamp,
        symbol: str,
        side: OrderSide,
        quantity: int,
        frame: pd.DataFrame,
        cash: Decimal,
        positions: dict[str, int],
        event_reason: str | None = None,
        membership_end_date: pd.Timestamp | None = None,
    ) -> tuple[Decimal, OrderEvent]:
        decision = self.gate.assess(symbol, execution_date.date())
        if not decision.eligible:
            reason = f"{event_reason}_{decision.reason}" if event_reason else (decision.reason or "INELIGIBLE")
            return cash, _non_fill(signal_date, execution_date, symbol, side.value, reason, membership_end_date=membership_end_date, event_quantity=quantity)
        bar = _bar(frame, execution_date)
        if bar is None:
            reason = f"{event_reason}_DATA_UNAVAILABLE" if event_reason else "DATA_UNAVAILABLE"
            return cash, _non_fill(signal_date, execution_date, symbol, side.value, reason, membership_end_date=membership_end_date, event_quantity=quantity)
        requested = self.execution_policy.requested_price(side, bar["open"])
        executed = self.execution_policy.fill_price(side, requested, bar["low"], bar["high"])
        if executed is None:
            reason = f"{event_reason}_IOC_LIMIT_NOT_FILLED" if event_reason else "IOC_LIMIT_NOT_FILLED"
            return cash, _non_fill(signal_date, execution_date, symbol, side.value, reason, requested, membership_end_date, quantity)
        costs = calculate_transaction_costs(executed * quantity)
        if side is OrderSide.BUY and cash < executed * quantity + costs.total_fees:
            reason = f"{event_reason}_INSUFFICIENT_CASH" if event_reason else "INSUFFICIENT_CASH"
            return cash, _non_fill(signal_date, execution_date, symbol, side.value, reason, requested, membership_end_date, quantity)
        if side is OrderSide.SELL and positions.get(symbol, 0) < quantity:
            reason = f"{event_reason}_INSUFFICIENT_HOLDINGS" if event_reason else "INSUFFICIENT_HOLDINGS"
            return cash, _non_fill(signal_date, execution_date, symbol, side.value, reason, requested, membership_end_date, quantity)
        if side is OrderSide.BUY:
            cash -= executed * quantity + costs.total_fees
            positions[symbol] = positions.get(symbol, 0) + quantity
        else:
            cash += executed * quantity - costs.total_fees
            positions[symbol] = positions.get(symbol, 0) - quantity
            if positions[symbol] == 0:
                del positions[symbol]
        return cash, OrderEvent(
            signal_date, execution_date, symbol, side.value, quantity,
            self.execution_policy.order_type.value, self.execution_policy.validity.value,
            requested, executed, "FILLED", event_reason, executed * quantity,
            costs.commission, costs.vat, costs.total_fees,
            abs(executed - bar["open"]) * quantity,
            membership_end_date,
        )


def _union_dates(market_data: Mapping[str, pd.DataFrame]) -> pd.DatetimeIndex:
    all_dates: list[pd.Timestamp] = []
    for frame in market_data.values():
        all_dates.extend(pd.to_datetime(frame.index, errors="raise").tolist())
    return pd.DatetimeIndex(sorted(set(all_dates)))


def _bar(frame: pd.DataFrame, timestamp: pd.Timestamp) -> dict[str, Decimal] | None:
    indexed = frame.copy()
    if not isinstance(indexed.index, pd.DatetimeIndex):
        indexed.index = pd.to_datetime(indexed.index, errors="raise")
    rows = indexed.loc[indexed.index == timestamp]
    if len(rows) != 1:
        return None
    row = rows.iloc[0]
    try:
        return {key: Decimal(str(row[key])) for key in ("open", "high", "low", "close")}
    except (KeyError, TypeError, ValueError):
        return None


def _target_quantity(value: Decimal, price: Decimal) -> int:
    return 0 if price <= 0 else int((value / price).to_integral_value(rounding=ROUND_DOWN))


def _buy_budget_price(price: Decimal) -> Decimal:
    """Reserve commission and VAT while preserving equal-weight allocation."""
    costs = calculate_transaction_costs(price)
    return price + costs.total_fees


def _market_value(
    positions: Mapping[str, int], market_data: Mapping[str, pd.DataFrame], timestamp: pd.Timestamp,
    gate: object | None = None,
) -> tuple[Decimal, tuple[str, ...], dict[str, str]]:
    total = Decimal("0")
    gaps: list[str] = []
    reasons: dict[str, str] = {}
    for symbol, quantity in positions.items():
        if gate is not None:
            decision = gate.assess(symbol, timestamp.date())
            if not decision.eligible:
                gaps.append(symbol)
                reasons[symbol] = decision.reason or "INELIGIBLE_VALUATION_DATE"
                continue
        bar = _bar(market_data[symbol], timestamp)
        if bar is not None:
            total += bar["close"] * quantity
        else:
            gaps.append(symbol)
            reasons[symbol] = "NO_VALID_VALUATION_ROW"
    ordered = tuple(sorted(gaps))
    return total, ordered, {symbol: reasons[symbol] for symbol in ordered}


def _membership_end(gate: object, symbol: str, timestamp: pd.Timestamp):
    resolver = getattr(gate, "membership_end", None)
    return resolver(symbol, timestamp.date()) if resolver is not None else None


def _non_fill(
    signal_date: pd.Timestamp,
    execution_date: pd.Timestamp,
    symbol: str,
    side: str,
    reason: str,
    requested: Decimal | None = None,
    membership_end_date: pd.Timestamp | None = None,
    event_quantity: int = 0,
) -> OrderEvent:
    return OrderEvent(
        signal_date, execution_date, symbol, side, event_quantity, OrderType.LIMIT.value, Validity.IOC.value,
        requested, None, "NON_FILL", reason, Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
        membership_end_date=membership_end_date,
    )


def _result(
    initial_cash: Decimal,
    snapshots: list[PortfolioSnapshot],
    orders: list[OrderEvent],
    selections: list[SelectionEvent],
) -> BacktestResult:
    final_snapshot = snapshots[-1]
    complete_snapshots = [snapshot for snapshot in snapshots if snapshot.valuation_status == "COMPLETE"]
    valuation_complete = len(complete_snapshots) == len(snapshots)
    final = final_snapshot.equity if final_snapshot.valuation_status == "COMPLETE" else None
    filled = [event for event in orders if event.status == "FILLED"]
    commission = sum((event.commission for event in filled), Decimal("0"))
    vat = sum((event.vat for event in filled), Decimal("0"))
    fees = sum((event.total_fees for event in filled), Decimal("0"))
    slippage = sum((event.slippage for event in filled), Decimal("0"))
    turnover = sum((event.order_value for event in filled), Decimal("0")) / initial_cash
    if valuation_complete:
        returns = pd.Series([float(snapshot.net_return) for snapshot in snapshots]).diff().dropna()
        volatility: Decimal | None = Decimal(str(returns.std(ddof=0) * sqrt(252))) if len(returns) else Decimal("0")
        maximum_drawdown: Decimal | None = min(
            (snapshot.drawdown for snapshot in snapshots if snapshot.drawdown is not None),
            default=Decimal("0"),
        )
    else:
        volatility = None
        maximum_drawdown = None
    if final is not None:
        total_return: Decimal | None = (final - initial_cash) / initial_cash
        gross_return: Decimal | None = total_return + fees / initial_cash
    else:
        total_return = None
        gross_return = None
    unvalued_positions = dict(final_snapshot.unvalued_positions)
    return BacktestResult(
        final, gross_return, total_return, volatility, maximum_drawdown, turnover,
        commission, vat, fees, slippage, len(filled), len({event.symbol for event in filled}),
        tuple(orders), tuple(selections), tuple(snapshots), valuation_complete,
        len(complete_snapshots), len(snapshots) - len(complete_snapshots), unvalued_positions,
    )

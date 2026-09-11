from __future__ import annotations

from decimal import Decimal

import pandas as pd

from src.backtest.engine import BacktestEngine, ExecutionPolicy


class _Gate:
    def __init__(self, excluded: set[str] | None = None) -> None:
        self.excluded = excluded or set()
        self.calls: list[tuple[str, object]] = []

    def assess(self, symbol: str, requested_date):
        self.calls.append((symbol, requested_date))
        return type("Decision", (), {"eligible": symbol not in self.excluded, "reason": "EXCLUDED"})()


class _BoundaryGate(_Gate):
    def __init__(self, end: pd.Timestamp) -> None:
        super().__init__()
        self.end = end.date()

    def membership_end(self, symbol: str, requested_date):
        return self.end if symbol == "AAA" and requested_date <= self.end else None

    def assess(self, symbol: str, requested_date):
        if symbol == "AAA" and requested_date > self.end:
            return type("Decision", (), {"eligible": False, "reason": "OUTSIDE_SET50_MEMBERSHIP_PERIOD"})()
        return super().assess(symbol, requested_date)


def _frame(momentum: float, *, high: float = 102.0) -> pd.DataFrame:
    dates = pd.date_range("2024-01-01", periods=6, freq="D")
    return pd.DataFrame(
        {
            "open": [100.0] * 6,
            "high": [high] * 6,
            "low": [99.0] * 6,
            "close": [100.0] * 6,
            "momentum_20": [momentum] * 6,
            "sma_20": [90.0] * 6,
            "trend_20_50": [0.1] * 6,
            "volatility_20": [0.02] * 6,
        },
        index=dates,
    )


def _frame_periods(momentum: float, periods: int = 8) -> pd.DataFrame:
    frame = _frame(momentum)
    dates = pd.date_range("2024-01-01", periods=periods, freq="D")
    return frame.reindex(dates).ffill()


def _engine(gate: _Gate | None = None, **kwargs) -> BacktestEngine:
    return BacktestEngine(
        initial_cash=Decimal("1000000"),
        execution_policy=ExecutionPolicy(lambda _: Decimal("1")),
        gate=gate or _Gate(),
        design=kwargs.pop("design", "C"),
        **kwargs,
    )


def test_engine_uses_top_ten_and_equal_weight_with_next_session_execution() -> None:
    data = {f"S{index:02d}": _frame(0.01 * index) for index in range(1, 13)}
    result = _engine().run(data)
    fills = [event for event in result.orders if event.status == "FILLED"]
    assert fills
    assert {event.symbol for event in fills} == {f"S{index:02d}" for index in range(3, 13)}
    assert all(event.execution_date > event.signal_date for event in fills)
    assert result.unique_symbols_traded == 10
    assert result.final_equity <= Decimal("1000000")
    assert result.commission > 0
    assert result.vat > 0
    assert result.slippage > 0


def test_engine_holds_all_candidates_when_fewer_than_ten() -> None:
    result = _engine().run({"AAA": _frame(0.2), "BBB": _frame(0.1)})
    assert {event.symbol for event in result.orders if event.status == "FILLED"} == {"AAA", "BBB"}


def test_engine_records_non_fill_without_fabricating_data() -> None:
    result = _engine().run({"AAA": _frame(0.2, high=100.5)})
    assert any(
        event.status == "NON_FILL" and event.reason == "IOC_LIMIT_NOT_FILLED" and event.side == "BUY"
        for event in result.orders
    )
    assert result.trade_count == 0


def test_engine_preserves_known_date_gap_as_non_fill() -> None:
    frame = _frame(0.2).drop(pd.Timestamp("2024-01-05"))
    result = _engine().run({"AAA": frame, "BBB": _frame(0.1)})
    assert any(event.reason == "DATA_UNAVAILABLE" for event in result.orders)


def test_engine_enforces_gate_and_long_only() -> None:
    gate = _Gate({"EXCLUDED"})
    result = _engine(gate).run({"AAA": _frame(0.2), "EXCLUDED": _frame(0.3)})
    assert all(event.symbol != "EXCLUDED" or event.status != "FILLED" for event in result.orders)
    assert all(quantity >= 0 for snapshot in result.snapshots for quantity in snapshot.positions.values())
    assert any(symbol == "EXCLUDED" for symbol, _ in gate.calls)


def test_engine_is_deterministic() -> None:
    data = {"AAA": _frame(0.2), "BBB": _frame(0.1)}
    first = _engine().run(data)
    second = _engine().run(data)
    assert first == second


def test_incomplete_valuation_is_explicit_and_never_zero_filled() -> None:
    data = {"AAA": _frame(0.2), "BBB": _frame(0.1).drop(pd.Timestamp("2024-01-06"))}
    result = _engine().run(data)

    incomplete = [snapshot for snapshot in result.snapshots if snapshot.valuation_status == "INCOMPLETE"]
    assert incomplete
    snapshot = incomplete[-1]
    assert snapshot.equity is None
    assert snapshot.market_value >= 0
    assert snapshot.valuation_gaps == ("BBB",)
    assert snapshot.valuation_gap_reasons == {"BBB": "NO_VALID_VALUATION_ROW"}
    assert snapshot.unvalued_positions["BBB"] == snapshot.positions["BBB"]
    assert result.valuation_complete is False
    assert result.final_equity is None
    assert result.gross_return is None
    assert result.net_return is None
    assert result.volatility is None
    assert result.maximum_drawdown is None
    assert result.unvalued_positions["BBB"] == snapshot.positions["BBB"]


def test_universe_boundary_exit_uses_current_final_eligible_session() -> None:
    end = pd.Timestamp("2024-01-06")
    gate = _BoundaryGate(end)
    result = _engine(gate).run({"AAA": _frame_periods(0.2)})
    events = [event for event in result.orders if event.reason == "UNIVERSE_BOUNDARY_EXIT"]
    assert len(events) == 1
    event = events[0]
    assert event.side == "SELL"
    assert event.status == "FILLED"
    assert event.execution_date == end
    assert event.signal_date == end
    assert event.membership_end_date == end
    assert event.executed_price == Decimal("99")
    assert result.snapshots[-1].positions == {}
    assert all("AAA" not in snapshot.unvalued_positions for snapshot in result.snapshots)


def test_universe_boundary_exit_nonfill_is_explicit_and_not_retried() -> None:
    end = pd.Timestamp("2024-01-06")
    gate = _BoundaryGate(end)
    result = _engine(gate).run({"AAA": _frame_periods(0.2).assign(low=99.5)})
    events = [event for event in result.orders if event.reason and event.reason.startswith("UNIVERSE_BOUNDARY_EXIT")]
    assert len(events) == 1
    assert events[0].status == "NON_FILL"
    assert events[0].reason == "UNIVERSE_BOUNDARY_EXIT_IOC_LIMIT_NOT_FILLED"
    assert events[0].membership_end_date == end
    assert result.snapshots[-1].positions["AAA"] > 0
    assert result.snapshots[-1].positions["AAA"] > 0

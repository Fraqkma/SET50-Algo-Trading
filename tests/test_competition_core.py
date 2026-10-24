from datetime import datetime
import pytest

from src.competition.core import (
    ExecutionAdapter,
    ExecutionReport,
    MarketBar,
    OrderIntent,
    OrderType,
    PortfolioSnapshot,
    Side,
    Signal,
    SignalAction,
    TimeInForce,
)


def test_portable_competition_contracts_import_without_ui_dependencies():
    moment = datetime(2026, 9, 9, 10, 0)
    bar = MarketBar("AOT", moment, 60, 61, 59, 60.5, 1000)
    portfolio = PortfolioSnapshot(moment, 1_000_000, {"AOT": 100}, 1_006_050)
    signal = Signal("AOT", SignalAction.SELL, moment, "risk policy test input")
    intent = OrderIntent("AOT", Side.SELL, 100, OrderType.MARKET_TO_LIMIT,
                         TimeInForce.IOC, moment)

    assert bar.close == 60.5
    assert portfolio.holdings["AOT"] == 100
    assert signal.action is SignalAction.SELL
    assert intent.time_in_force is TimeInForce.IOC
    assert ExecutionReport("UNKNOWN").fills == ()
    assert callable(getattr(ExecutionAdapter, "execute"))


@pytest.mark.parametrize("kwargs", [
    {"quantity": 0, "order_type": OrderType.LIMIT, "time_in_force": None, "limit_price": 10},
    {"quantity": 100, "order_type": OrderType.LIMIT, "time_in_force": None, "limit_price": None},
    {"quantity": 100, "order_type": OrderType.MARKET_TO_LIMIT, "time_in_force": None, "limit_price": None},
])
def test_order_intent_rejects_invalid_quantity_or_order_semantics(kwargs):
    moment = datetime(2026, 9, 9, 10, 0)
    with pytest.raises(ValueError):
        OrderIntent(symbol="AOT", side=Side.BUY, decision_timestamp=moment, **kwargs)

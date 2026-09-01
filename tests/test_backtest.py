"""Tests for backtest cost and metric placeholders."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from src.backtest.metrics import TradeRecord, count_unique_symbols_traded, meets_minimum_unique_symbols
from src.backtest.transaction_cost import calculate_transaction_costs


def test_transaction_cost_calculation_includes_commission_and_vat() -> None:
    """Commission and VAT should follow the competition rules."""

    costs = calculate_transaction_costs(Decimal("1000"))

    assert costs.commission == Decimal("1.57")
    assert costs.vat == Decimal("0.1099")
    assert costs.total_fees == Decimal("1.6799")


def test_unique_symbol_tracking_counts_distinct_symbols() -> None:
    """Unique symbols traded should be counted distinctly."""

    trades = [
        TradeRecord(symbol="A"),
        TradeRecord(symbol="A"),
        TradeRecord(symbol="B"),
        TradeRecord(symbol="C"),
        TradeRecord(symbol="D"),
        TradeRecord(symbol="E"),
    ]

    assert count_unique_symbols_traded(trades) == 5
    assert meets_minimum_unique_symbols(trades, minimum=5)


def test_initial_capital_is_configured_correctly() -> None:
    """The competition initial capital must match the approved configuration."""

    config_path = Path(__file__).resolve().parents[1] / "config" / "config.yaml"
    initial_capital_line = next(
        line for line in config_path.read_text(encoding="utf-8").splitlines() if line.startswith("initial_capital:")
    )

    assert initial_capital_line.split(":", maxsplit=1)[1].strip() == "10000000"
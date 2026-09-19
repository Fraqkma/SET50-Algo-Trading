from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from src.execution.order_manager import OrderRequest, OrderSide, OrderType, Validity
from src.execution.settrade_paper import DryRunExecutor, SettradeTradingAdapter


def _order() -> OrderRequest:
    return OrderRequest("PTT", OrderSide.BUY, 100, OrderType.LIMIT, Validity.IOC, Decimal("40"))


def test_dry_run_writes_without_submission() -> None:
    with TemporaryDirectory(dir=Path("data/pilot")) as directory:
        path = Path(directory) / "orders.jsonl"
        executor = DryRunExecutor(path)
        result = executor.submit(_order())
        assert result.submitted is False
        assert executor.orders_submitted == 0
        assert "submitted" in path.read_text()


def test_trading_adapter_rejects_real_submission() -> None:
    with pytest.raises(RuntimeError, match="disabled"):
        SettradeTradingAdapter().place_order(_order())

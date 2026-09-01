"""Paper trader placeholder."""

from __future__ import annotations

from .broker import Broker
from .order_manager import ExecutionReport, OrderRequest


class PaperTrader(Broker):
    """Placeholder paper trader implementation."""

    def submit_order(self, order_request: OrderRequest) -> ExecutionReport:
        raise NotImplementedError("Paper trading is not implemented yet.")
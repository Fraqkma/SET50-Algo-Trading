"""Broker interface for competition execution."""

from __future__ import annotations

from abc import ABC, abstractmethod

from .order_manager import ExecutionReport, OrderRequest


class Broker(ABC):
    """Abstract broker interface."""

    @abstractmethod
    def submit_order(self, order_request: OrderRequest) -> ExecutionReport:
        """Submit an order for execution.

        TODO: Wire to a real broker only after competition integration details are known.
        """

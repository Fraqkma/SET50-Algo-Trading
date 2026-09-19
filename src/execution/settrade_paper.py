"""Dry-run-only execution foundation for future sandbox integration."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

from .order_manager import OrderRequest, validate_order_request


@dataclass(frozen=True)
class AccountSnapshot:
    account_no: str | None
    cash: Decimal | None
    buying_power: Decimal | None
    positions: dict[str, int]
    source: str = "unavailable"


@dataclass(frozen=True)
class PaperOrderStatus:
    client_order_id: str
    status: str
    reason: str
    submitted: bool = False


class DryRunExecutor:
    """Serialize validated intentions without any SDK/account/order call."""

    def __init__(self, output: Path) -> None:
        self.output = output
        self.orders_submitted = 0

    def submit(self, order: OrderRequest) -> PaperOrderStatus:
        validate_order_request(order)
        client_order_id = f"DRYRUN-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
        record: dict[str, Any] = {"client_order_id": client_order_id, "created_at": datetime.now(timezone.utc).isoformat(), "order": asdict(order), "submitted": False}
        self.output.parent.mkdir(parents=True, exist_ok=True)
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, default=str, sort_keys=True) + "\n")
        return PaperOrderStatus(client_order_id, "DRY_RUN", "SDK submission intentionally disabled", submitted=False)


class SettradeTradingAdapter:
    """Placeholder boundary; account/order methods are intentionally unavailable."""

    def account_snapshot(self, account_no: str | None = None) -> AccountSnapshot:
        return AccountSnapshot(account_no, None, None, {}, source="not_requested")

    def place_order(self, *_: Any, **__: Any) -> None:
        raise RuntimeError("Settrade trading is disabled in this pilot; use DryRunExecutor")

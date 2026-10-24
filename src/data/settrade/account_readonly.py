"""Read-only equity account adapter; intentionally omits all order mutation APIs."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from dotenv import dotenv_values


def configured_account_number(project_root: Path, env_name: str = "SETTRADE_ACCOUNT_NO") -> str | None:
    """Read account number from process env or ignored .env without displaying it."""
    value = os.environ.get(env_name)
    if value:
        return value
    return dotenv_values(Path(project_root) / ".env").get(env_name) or None


class ReadOnlyEquityAdapter:
    """Expose only safe read endpoints from the SDK equity client."""

    def __init__(self, equity_client: Any) -> None:
        self.__equity = equity_client

    @classmethod
    def from_investor(cls, investor: Any, account_number: str) -> "ReadOnlyEquityAdapter":
        if not account_number:
            raise ValueError("account number is required for read-only equity access")
        return cls(investor.Equity(account_number))

    def account_summary(self) -> Any:
        return self.__equity.get_account_info()

    def portfolio(self) -> Any:
        return self.__equity.get_portfolios()

    def orders(self) -> Any:
        return self.__equity.get_orders()

    def deals(self) -> Any:
        return self.__equity.get_trades()

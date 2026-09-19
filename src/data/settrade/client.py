"""Runtime-only, market-data-only wrapper around the official Settrade SDK."""

from __future__ import annotations

import os
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Iterator, TypeVar

from dotenv import load_dotenv

from .rate_limiter import RateLimiter

T = TypeVar("T")


@contextmanager
def _sdk_import_environment() -> Iterator[None]:
    """Give the SDK a writable local home only while it is imported.

    ``settrade-v2`` creates its log handler at import time from the Windows
    home-directory environment variables.  The managed runtime can read the
    user's normal SDK directory but cannot write there.  Keeping the override
    scoped to import preserves the caller's environment, credentials, and SDK
    configuration behavior while making only the SDK's local log/config path
    writable.
    """
    runtime_home = Path(__file__).resolve().parents[3] / ".settrade-runtime"
    # The Windows SDK appends ``AppData`` to USERPROFILE before creating its
    # config and log paths.
    (runtime_home / "AppData").mkdir(parents=True, exist_ok=True)
    names = ("HOMEDRIVE", "HOMEPATH", "USERPROFILE")
    previous = {name: os.environ.get(name) for name in names}
    os.environ["HOMEDRIVE"] = ""
    os.environ["HOMEPATH"] = ""
    os.environ["USERPROFILE"] = str(runtime_home)
    try:
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def redact_error(error: BaseException, secrets: tuple[str, ...] = ()) -> str:
    """Return a bounded error string with credentials removed."""
    message = str(error)
    for secret in secrets:
        if secret:
            message = message.replace(secret, "[REDACTED]")
    return message[:500]


@dataclass(frozen=True)
class SettradeConfig:
    """Non-secret runtime settings; secrets are intentionally excluded from repr."""

    app_code: str
    broker_id: str
    app_id: str = ""
    app_secret: str = ""

    def __repr__(self) -> str:
        return f"SettradeConfig(app_code={self.app_code!r}, broker_id={self.broker_id!r})"

    @classmethod
    def from_env(cls, env_path: Path | None = None) -> "SettradeConfig":
        if env_path is not None:
            load_dotenv(env_path, override=False)
        app_id = os.getenv("SETTRADE_APP_ID", "")
        app_secret = os.getenv("SETTRADE_APP_SECRET", "")
        if not app_id or not app_secret:
            raise RuntimeError("SETTRADE_APP_ID and SETTRADE_APP_SECRET are required at runtime")
        return cls(
            app_code=os.getenv("SETTRADE_APP_CODE", "SANDBOX"),
            broker_id=os.getenv("SETTRADE_BROKER_ID", "SANDBOX"),
            app_id=app_id,
            app_secret=app_secret,
        )


class SettradeClient:
    """Small authenticated wrapper that exposes only read-only SDK surfaces."""

    def __init__(self, config: SettradeConfig, market_rps: float = 3.0) -> None:
        self.config = config
        self.market_limiter = RateLimiter(market_rps)
        self._investor: Any = None
        self._market: Any = None
        self._realtime: Any = None

    @property
    def authenticated(self) -> bool:
        return self._investor is not None

    def authenticate(self) -> Any:
        """Perform the real SDK login and return the SDK ``Investor`` instance."""
        with _sdk_import_environment():
            from settrade_v2 import Investor
            from settrade_v2.config import config as sdk_config

        # The official SDK's SANDBOX alias is a UAT environment.  Set this in
        # memory so a collector never edits the user's SDK config file.
        if self.config.broker_id.upper() == "SANDBOX":
            sdk_config["environment"] = "uat"

        self._investor = Investor(
            self.config.app_id,
            self.config.app_secret,
            self.config.app_code,
            self.config.broker_id,
            is_auto_queue=False,
        )
        return self._investor

    def market_data(self) -> Any:
        if not self.authenticated:
            raise RuntimeError("authenticate() must succeed before market_data()")
        if self._market is None:
            self._market = self._investor.MarketData()
        return self._market

    def realtime(self) -> Any:
        if not self.authenticated:
            raise RuntimeError("authenticate() must succeed before realtime()")
        if self._realtime is None:
            self._realtime = self._investor.RealtimeDataConnection()
        return self._realtime

    def market_call(self, operation: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Rate-limit and execute one market-data operation."""
        self.market_limiter.acquire()
        return operation(*args, **kwargs)

    def quote(self, symbol: str) -> Any:
        return self.market_call(self.market_data().get_quote_symbol, symbol)

    def candlestick(self, symbol: str, interval: str, **kwargs: Any) -> Any:
        return self.market_call(self.market_data().get_candlestick, symbol, interval, **kwargs)

    def redacted_error(self, error: BaseException) -> str:
        return redact_error(error, (self.config.app_id, self.config.app_secret))

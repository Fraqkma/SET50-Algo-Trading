"""A small, interpretable long-only baseline strategy."""

from __future__ import annotations

import pandas as pd

from .base import Strategy


class BaselineStrategy(Strategy):
    """Trend/momentum baseline with a next-session execution convention.

    ``BUY`` requires positive 20-day momentum and ``Close`` above its 20-day
    SMA.  ``EXIT`` is emitted when either condition is false after features
    are available.  Earlier rows remain ``HOLD`` because the windows are not
    complete.  The strategy only emits signals; a future backtest must execute
    a signal no earlier than the next available trading row.
    """

    momentum_column: str = "momentum_20"
    moving_average_column: str = "sma_20"

    def generate_signal(self, market_data: pd.DataFrame) -> pd.Series:
        """Return one of ``BUY``, ``HOLD`` or ``EXIT`` for each feature date."""
        if market_data is None:
            raise ValueError("Feature data cannot be None.")
        required = {"close", self.momentum_column, self.moving_average_column}
        missing = required - set(market_data.columns)
        if missing:
            raise ValueError(f"Missing baseline feature columns: {sorted(missing)}")
        signals = pd.Series("HOLD", index=market_data.index, dtype="string", name="signal")
        ready = market_data[["close", self.momentum_column, self.moving_average_column]].notna().all(axis=1)
        buy = ready & (market_data[self.momentum_column] > 0) & (
            market_data["close"] > market_data[self.moving_average_column]
        )
        exit_signal = ready & ~buy
        signals.loc[buy] = "BUY"
        signals.loc[exit_signal] = "EXIT"
        return signals

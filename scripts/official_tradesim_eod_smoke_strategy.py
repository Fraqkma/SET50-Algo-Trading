"""Single-order limit fixture for the official simulator EOD cancellation check."""


class official_tradesim_eod_smoke_strategy:
    """Place one distant PTT limit buy and leave its residual for EOD handling."""

    def __init__(self, handler):
        self.handler = handler
        self.timeframe = "1min"
        self.submitted = False

    def on_data(self, bar):
        if self.submitted or bar.get("ShareCode") != "PTT":
            return
        # 0.2.6 rejects buys until the per-symbol tick stream has shown sell-side
        # volume. Waiting for one board lot keeps this fixture valid at placement.
        if self.handler.cum_sell_volume < 100:
            return
        price = float(bar["Close"])
        limit_price = max(0.01, price - 5.0)
        self.handler.create_order_to_limit(100, limit_price, "Buy", "PTT")
        self.submitted = True

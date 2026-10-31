"""One-order, offline 0.2.7 mechanics probe using actual local official ticks.

This deliberately has no signal or performance purpose. It submits at most one
small local simulator LIMIT/IOC request for PTT and never contacts a broker.
"""


class phase5_tick_mechanics_strategy:
    def __init__(self, handler):
        self.handler = handler
        self.timeframe = "1min"
        self.submitted = False

    def on_data(self, bar):
        if self.submitted or bar.get("ShareCode") != "PTT":
            return
        price = float(bar["Close"])
        # 2026-10-21's official tick ladder uses 0.25 THB around PTT prices.
        limit_price = round((price - 0.50) * 4) / 4
        self.submitted = True
        self.handler.create_order_to_limit(100, limit_price, "Buy", "PTT")

"""Limit-only fixture for testing TradeSim 0.2.6 partial fills and EOD residuals."""


class official_tradesim_partial_fill_smoke_strategy:
    """Submit one cash-affordable 2,000-board-lot PTT order after volume evidence."""

    def __init__(self, handler):
        self.handler = handler
        self.timeframe = "1min"
        self.submitted = False

    def on_data(self, bar):
        if self.submitted or bar.get("ShareCode") != "PTT":
            return
        quantity = 200_000
        if self.handler.cum_sell_volume < quantity:
            return
        self.handler.create_order_to_limit(quantity, float(bar["Close"]), "Buy", "PTT")
        self.submitted = True

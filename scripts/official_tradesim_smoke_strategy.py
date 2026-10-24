"""Order-free strategy used only to smoke-test the official simulator bridge."""


class official_tradesim_smoke_strategy:
    """Accept simulator callbacks while deliberately submitting no orders."""

    def __init__(self, handler):
        self.handler = handler
        self.timeframe = "1min"
        self.rows_seen = 0

    def on_data(self, bar):
        self.rows_seen += 1

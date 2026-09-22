# Settrade transaction-tick audit

Audit target: installed `settrade-v2==2.2.1` equity market-data surface.

## Classification

`PRICE_UPDATE_ONLY`

The installed SDK exposes these realtime equity subscriptions:

- `RealtimeDataConnection.subscribe_bid_offer(symbol, on_message)` — ten bid
  and ten ask price/volume levels.
- `RealtimeDataConnection.subscribe_price_info(symbol, on_message)` — price
  information such as last, high, low, market status, projected open fields,
  total value, and total volume.
- `RealtimeDataConnection.subscribe_candlestick(symbol, interval, on_message)`
  — interval candles.

The SDK does not expose an equity `subscribe_trade`, transaction, time-and-sales,
deal, execution-print, or ticker-by-trade method. The account `get_trades`
methods found in the package are account/trading surfaces and are not public
market transaction streams; the pilot does not initialize account APIs.

The prior bounded realtime probe observed BBO and price-info callbacks. BBO
payloads contained `bid_price1..10`, `ask_price1..10`, matching volume fields,
flags, and `symbol`. Price-info payloads contained `last`, high/low, market
status, projected-open fields, total value/volume, and `symbol`. No transaction
identity, per-trade quantity, aggressor side, or execution sequence was
observed. Price-info updates are therefore never persisted or labeled as trade
ticks.

No trade-tick collector, tick-derived bars, or trade charts are enabled. This is
intentional: there is no verified transaction-level source to preserve.

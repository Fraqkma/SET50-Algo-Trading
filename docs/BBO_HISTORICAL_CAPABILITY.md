# Historical Settrade BBO capability

## Determination

**`HISTORICAL_BBO_NOT_EXPOSED_BY_CURRENT_API`**

The installed `settrade-v2==2.2.1` source exposes a current quote method and a live `RealtimeDataConnection.subscribe_bid_offer(symbol)` WebSocket subscription to `proto/topic/bidofferv3/{symbol}`. The SDK's REST `MarketData` class exposes bounded candlestick and current-quote calls; it has no historical order-book/depth endpoint or BBO date-range method. No public historical trade-tape method is exposed either. `Equity.get_trades()` is account-scoped own-trade history, not a market-wide transaction tape and cannot reconstruct order-book snapshots. A live subscription is not evidence of remote history.

No historical BBO endpoint was available to probe, so no speculative endpoint was called. Current quote/BBO observations and live subscription capability do not imply historical retrieval.

## Local archive

The production local archive covers 2026-10-19 through 2026-10-28 across 50 current SET50 symbols. The retained collection audit counts 132,784 raw BBO callback events and 2,655,620 normalized depth rows. Each normalized snapshot carries 10 bid and 10 ask levels. Raw JSONL is 204,273,419 bytes; normalized CSV is 826,333,814 bytes; together approximately 1.03 GB, or about 129 MB per observed date on average. Oct 23 is a short partial observation. The detailed day spans and counts are retained in `reports/local_bbo_inventory.json`.

Raw callback timestamps are receipt times; normalized timestamps are collector retrieval times, not verified exchange event times. Event silence is not automatically an outage. Existing schema/quality reports identify ordering issues in one PTT ask ladder; source rows remain unchanged. There is no BBO reconstruction or synthetic depth.

## Retention

Keep BBO event-driven and date-partitioned when storage work is next scheduled; retain raw callbacks immutably, rebuild normalized snapshots from raw, and maintain daily file-size/event manifests. The current collector writes local production files and logs. Logged-out scheduling remains blocked by the Interactive task principal, so unattended BBO accumulation is not yet established.

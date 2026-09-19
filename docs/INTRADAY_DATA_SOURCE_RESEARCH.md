# SET50 Intraday Data-Source Research

Status: read-only planning research, dated 14 September 2026. This track is
isolated from the approved daily dataset: no data was downloaded, no probe was
made, and no collector or research-pipeline integration was implemented.

## Executive recommendation

Use **licensed SET Intraday Trading Data (Tick Data) through SET/SMART
Marketplace** as the only candidate primary source. SET documents SET trade
ticks, bids/offers, index ticks, historical requests, daily subscriptions, and
programmatic download; its data is for personal/internal use and cannot be
redistributed without separate permission. [SET Tick Data](https://www.set.or.th/app/online-data/tick-data?lang=en)

Start, subject to a human-approved licence and implementation decision, with
the current 20-symbol universe and **5-minute bars derived from licensed raw
ticks**, retaining the permitted source files. Include best bid/offer data when
the SET file specification confirms its level and timestamps. This produces
useful liquidity, volume, intraday-timing, and slippage diagnostics without
making 1-minute collection the default operational burden.

## Source comparison

The generated CSV records the detailed comparison. In short:

| Source | SET coverage | 1m / 5m / 15m | Tick / bid-ask / depth | Classification | Recommended use |
|---|---|---|---|---|---|
| SET Tick Data / SMART Marketplace | Verified | Derive from tick data | Yes / yes / levels need file-spec confirmation | A | Primary collection |
| EODHD | BK exchange listed; intraday per-symbol verification pending | Ticker-dependent | Not verified for BK | C | Limited future cross-check |
| Twelve Data | Thailand claim; per-symbol verification pending | API intervals offered | No documented SET tick/BBO feed | C | Lawful coverage probe/cross-check |
| Yahoo Finance/yfinance | Existing daily `.BK` path only | Unreliable for this purpose | No | D | Exclude from collection |
| TradingView | SET display/broker entitlement | Display, not approved collection API | No | D | Manual visual check only |
| Alpha Vantage | No SET-specific evidence | API intervals, coverage unverified | No SET evidence | D | Exclude |
| Polygon, Tiingo, Finnhub, Stooq | No documented usable SET intraday feed | Not established | Not established | D | Exclude/pending explicit vendor proof |

SET says its historical intraday product has SET tick data from September 2012,
offers trading-ticker and bids/offers variants, supports historical requests or
end-of-day subscription, and supplies online/API delivery. [SET Tick Data](https://www.set.or.th/app/online-data/tick-data?lang=en)
SMART Marketplace also identifies historical tick trades, bids/offers, and
real-time/delayed snapshots as separate products. [SMART Marketplace](https://www.set.or.th/th/services/connectivity-and-data/data/smart-marketplace)

EODHD’s public BK page confirms Thailand exchange code `BK`, MIC `XBKK`,
Asia/Bangkok timezone, and 1,296 active symbols, but does not prove intraday
availability for every one of this project’s 20 symbols. [EODHD BK exchange](https://eodhd.com/exchange/BK)
Its intraday documentation says non-US exchange coverage varies by ticker and
exchange, which is why it is only a cross-check candidate. [EODHD intraday documentation](https://eodhd.com/financial-academy/how-to-get-stocks-data-examples/how-to-get-stocks-intraday-historical-data-on-python)

Twelve Data supports the requested bar intervals and documents that intraday
depth varies by instrument and interval; its intraday data is unadjusted. That
does not independently establish coverage of the 20 SET50 names. [Twelve Data historical prices](https://support.twelvedata.com/en/articles/5656039-how-to-get-historical-prices), [price-adjustment policy](https://support.twelvedata.com/en/articles/5179064-are-the-prices-adjusted)

Yahoo’s documented offline historical-data download is a Gold feature and may
be absent for instruments because of licensing restrictions; it is not an
approved continuous collection source. [Yahoo Finance historical download help](https://help.yahoo.com/kb/account/download-historical-data-yahoo-finance-sln2311.html)
TradingView is a display/broker-entitlement route, not a public data-collection
API; its SET agreement also restricts furnishing market data to others.
[TradingView broker-data support](https://www.tradingview.com/support/solutions/43000479666-how-can-i-get-real-time-data-from-exchanges-that-i-have-already-purchased-with-my-broker/), [SET market-data agreement](https://s3.tradingview.com/exchange-agreements/set-market-data-agreement.pdf)

Polygon’s documented stock product is U.S. exchange data and Tiingo’s documented
equity universe is U.S. and Chinese markets, so neither is suitable for SET.
[Polygon stocks overview](https://polygon.io/docs/rest/stocks/overview), [Tiingo symbology](https://www.tiingo.com/documentation/appendix/symbology)

## Design answers

### 1-minute versus 5-minute

1-minute data is better only when studying short-lived quote/spread changes,
auction-adjacent behavior, or execution timing within a five-minute interval.
For the current three-observed-row, daily-driven strategy research, it is not
automatically more informative; it increases missing-bar, session, and storage
burden. Preserve licensed tick data if available, but start analysis with 5m
aggregation.

### Whether 15-minute is sufficient

15m is adequate for coarse volume/liquidity filters and broad intraday timing.
It is weak for realistic IOC limit-fill and slippage diagnostics because spreads,
quotes, and auctions can move materially inside a 15-minute bar. It is not a
substitute for bid/ask data. Use it only as a low-cost secondary aggregate.

### Highest-value additions over daily data

In descending order: bid/ask and spread observations; trade ticks or 1m/5m
OHLCV; auction/open/close flags; turnover and VWAP inputs; and then depth if the
official file provides a well-defined level schema. Those add information that a
daily OHLCV row cannot recover.

### Minimum practical dataset

Collect the current 20-symbol universe initially, not an inferred historical
SET50 universe. Require: raw licensed trade ticks or 5m OHLCV, volume/turnover,
session timestamps, source/retrieval timestamps, adjustment status, and best
bid/offer with sizes where available. Retain at least 12 months, subject to the
licence. Expand to all 50 only after collection reliability is demonstrated and
the licence permits it.

## Storage estimate

Assumptions: 21 observed sessions/month, 252/year, approximately 390 active
minute slots/session, and **100 compressed-columnar bytes per observed bar**.
No missing bars are manufactured. The CSV gives all 18 combinations.

| Symbols | Frequency | 1 month | 3 months | 1 year |
|---:|---|---:|---:|---:|
| 20 | 1m | 16.38 MB | 49.14 MB | 196.56 MB |
| 20 | 5m | 3.28 MB | 9.83 MB | 39.31 MB |
| 20 | 15m | 1.09 MB | 3.28 MB | 13.10 MB |
| 50 | 1m | 40.95 MB | 122.85 MB | 491.40 MB |
| 50 | 5m | 8.19 MB | 24.57 MB | 98.28 MB |
| 50 | 15m | 2.73 MB | 8.19 MB | 32.76 MB |

These are bar-storage estimates, not tick/order-book storage estimates. Raw
tick and quote files can be substantially larger and must be sized after SET
publishes the licensed file specification.

## Future schema and validation gates

Future records should have `timestamp`, `symbol`, OHLC, `volume`, `turnover`,
`vwap`, `bid`, `ask`, `bid_size`, `ask_size`, `source`, `retrieved_at`,
`timezone`, and `adjustment_status`. OHLC applies only to bars; bid/ask and size
fields require a quote source; turnover/VWAP may be source-supplied or derived.

Before any future import, validate duplicate timestamps, missing bars without
gap filling, session bounds, OHLC validity, volume anomalies, timezones, symbol
mappings, corporate-action boundaries, delayed/stale quotes, abnormal spreads,
and source outages. This is a proposed validation checklist, not a pipeline
change.

## Final answers and blockers

1. Best free/low-cost source: **none is verified enough for primary SET
   collection**. EODHD is the most credible low-cost future cross-check because
   it publicly lists BK, but needs a licensed per-symbol intraday probe.
2. Best official source: **SET Tick Data / SMART Marketplace**.
3. Best 1m/5m/15m OHLCV: **official SET tick data aggregated locally after
   licensing**; 5m is the recommended initial aggregate.
4. Best bid/ask/order-book source: **official SET Bids/Offers tick product**;
   available depth levels remain a contractual/file-spec question.
5. Automated continuous collection: technically feasible through SET’s licensed
   API/download route, but not authorised until product terms, credentials,
   rate limits, and retention rights are approved.
6. Recommended initial resolution: **5m**, retaining ticks if permitted.
7. Recommended initial universe: **the current 20 approved daily symbols**.
8. Recommended retention: **12 months minimum**.
9. Expected monthly storage: **about 3.28 MB for 20 symbols at 5m bars**, plus
   materially larger raw tick/quote files.
10. Blockers: SET price/product quote, licence, API terms, rate limits, exact
    bid/offer depth schema, timestamp convention, and raw/adjusted semantics.
11. Ready to build the collector next: **No**—a human must approve a licensed
    source and the unresolved technical terms first.

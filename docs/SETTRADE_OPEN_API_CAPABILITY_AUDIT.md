# Settrade Open API Capability Audit

Audit date: 2026-09-18. This audit uses the official `settrade-v2==2.2.1`
Python SDK and runtime credentials from the ignored `.env`. No credential value
is stored in reports or documentation and no order was submitted.

## Authentication and safety

`Investor(...)` authenticated successfully with the configured sandbox alias
(`BROKER_ID=SANDBOX`, `APP_CODE=SANDBOX`) and `MarketData()` initialized. The
client package changes the SDK environment only in memory for the sandbox UAT
alias; it never edits the user SDK config file. Account/equity interfaces are
not initialized by the collector. Orders placed: **0**.

## Historical daily findings

The initial date-only requests were malformed. The SDK requires ISO local
datetime parameters such as `2023-12-01T00:00:00`; date-only values return a
400 `TCHART-500` conversion error and must not be interpreted as missing data.
With correct parameters:

| PTT request | Result |
|---|---|
| 2026-01-01 through 2026-01-10 | 5 rows |
| 2025-01-01 through 2025-01-10 | 7 rows |
| 2024-01-01 through 2024-01-10 | 7 rows |
| 2023-12-01 through 2023-12-31 | 18 rows |
| 2023-01-01 through 2023-01-10 | empty |
| 2020, 2016, 2010 January windows | empty |

The earliest candle actually observed in the bounded boundary probe was
2023-12-01 (exchange-local date). This establishes recent history at least back
to December 2023, but does not claim the exact service retention boundary. The
API is therefore **RECENT_HISTORY_ONLY / CROSS_CHECK**, not a replacement for
the long Yahoo staging history. Settrade can cross-check overlapping recent
data; a source comparison found explicit OHLC/volume differences and retained
them as `MATERIAL_DIFFERENCE` rather than choosing a winner.

SDK candlestick responses use parallel arrays (`time`, `open`, `high`, `low`,
`close`, `volume`, `value`). Epoch timestamps were converted to UTC records and
compared using Asia/Bangkok exchange-local dates. `value` was returned as zero
in the observed samples, so the pipeline does not invent turnover.

## Intraday and realtime

The exact 20-symbol universe in `TASK.md` returned quote, daily, 1m, 5m, and
15m responses in the bounded capability pass. The collector smoke test stored
795 1m rows, derived 340 5m rows and 305 15m rows with zero validation issues.
The API returned non-empty recent 1m, 5m, and 15m samples for PTT. Session and
timezone semantics require continued metadata validation; the exchange-local
interpretation is documented as an assumption, not a corporate-action
adjustment.

A ten-second realtime test used four topics (bid/offer and price-info for PTT
and ADVANC) and received four events. Bid/offer payloads contained ten bid and
ten ask price/volume levels (`bid_price1..10`, `ask_price1..10`, and matching
volumes), so this is empirically **10-level depth**, not merely BBO. Price-info
payloads contained last, high, low, market status, projected open fields,
total value, and total volume. The SDK exposes no reconnect counter or durable
event sequence in the observed wrapper; reconnect handling is therefore
prepared in the collector boundary but remains an operational follow-up.

The test used four of the 35-topic pilot budget. The client uses 3 requests/sec
for general market polling and never intentionally tests a rate limit. No
rate-limit error occurred.

## Reference data and trading

The inspected official SDK exposes no non-account methods for current or
historical SET50 constituents, effective membership dates, security master,
ticker changes, delisted securities, listing dates, or corporate actions.
Historical SET50 membership remains externally blocked.

The equity trading surface requires account information. The pilot does not
initialize it. `SettradeTradingAdapter` rejects real submission and
`DryRunExecutor` serializes validated intentions with `submitted=false`; tests
prove the dry-run path cannot call an SDK order method.

## Classification

| Use | Classification | Reason |
|---|---|---|
| Long-term daily research | STAGING_ONLY | Retention and membership are insufficient |
| Recent daily | CROSS_CHECK | Non-empty recent data, source differences observed |
| Intraday bars | CROSS_CHECK | 1m/5m/15m responses observed, retention not characterized fully |
| Realtime quotes/depth | CROSS_CHECK | Live topics and 10 levels observed in a short sample |
| Execution validation | STAGING_ONLY | Useful quote/depth sample, no fill experiment performed |
| Historical SET50 membership | INSUFFICIENT_EVIDENCE | No SDK reference surface |

All Settrade data remains pilot/staging data. Approved daily data and manifests
were not changed.

# Settrade production cutover

## Configuration and isolation

The ignored `.env` is classified without printing credentials. Routing `013` / `ALGO_EQ` selects production. Existing pre-cutover data stays under `data/pilot/settrade`; production collector output is isolated under `data/pilot/settrade/production`. New collector rows carry environment/source provenance. A no-data checkpoint is not treated as a persisted market observation.

The marker is `reports/settrade_production_cutover.json`. Its recorded cutover boundary is **2026-10-16 19:12:02 Asia/Bangkok** (UTC timestamp in the JSON). The latest persisted pre-cutover sandbox observation was **2026-10-16 16:56:47 Asia/Bangkok**, from the `received_at` field of the PTTGC raw BBO event; its market timestamp was absent. The first successful production probe was a PTT quote during the smoke session beginning at the cutover timestamp; its exact response-receipt time was not captured, so the marker labels that timestamp as a session-start bound. First production auth exact receipt time is UNKNOWN. First persisted production market observation is UNKNOWN; the production collector wrote a checkpoint but no market rows. Git HEAD at inspection: `5c29ba0128155d50352ddd15a26cb0f9883d1627`; code was already dirty, so the exact collector build identity at cutover is UNKNOWN. New collector rows now include a SHA-256 collector source identity plus Git HEAD, broker, app code, and environment. No separate runtime release identifier exists.

Never merge the two roots without retaining the per-row source environment. No market data is interpolated or copied across the boundary.

## Verified capability evidence

The current installed `settrade-v2` version is 2.2.1. Its source exposes historical candles, quote, realtime bid/offer, and an `Investor.Equity(account_no)` factory. Equity methods include read-only account info, order list, portfolio and trade list, and separate place/change/cancel methods. The production probe verified authentication, quote, candle response, and a short live BBO subscription. It did not initialize Equity because no account number is configured.

| Capability | Production evidence | Sandbox comparison / status |
|---|---|---|
| Authentication | Verified success | Production KGI investor route authenticated |
| Historical candles | Daily PTT returned 7 rows in Jan 2025; sampled 1m request for 2026-10-01 returned zero | Methods existed in prior sandbox; production historical behavior is date/interval dependent |
| Current intraday | Latest bounded 1m response ended 2026-10-15 16:36 Bangkok and was stale at probe time | Did not prove a current-session response; recheck during market hours |
| Realtime quote | PTT quote verified | Market data existed in sandbox; no private account information is required |
| Realtime BBO | One PTT event, ten bid and ten ask levels; wrapper and normalized price/volume fields matched persisted sandbox schema | No material schema/depth difference observed in this sample |
| Account / portfolio / orders / deals | SDK methods available; production calls not made | `REQUIRES_ACCOUNT_NUMBER`; not verified for this account |
| Trading | place/change/cancel method names present in SDK | Inventory only; never invoked by readiness, collector, or UI |

The practical production gain is the potential to read private equity state through the investor account object, subject to an account number and entitlement. No such state was queried here. The observed market-data API remains broadly the same SDK surface; the bounded BBO comparison did not show a schema/depth change. Production candle freshness/history is not established as superior to sandbox from these observations.

The official [Settrade Open API reference](https://developer.settrade.com/open-api/api-reference) was opened during this task, but returned no crawlable endpoint content and official-domain searches did not yield indexed details. Therefore endpoint-specific claims above are based on installed SDK source and read-only production responses, not an independently verified documentation page. SDK files inspected: `settrade_v2/user.py`, `market.py`, `realtime.py`, and `equity.py`.

## Read-only operations

Activate the research environment and run:

```powershell
.\.venv\Scripts\Activate.ps1
.\.venv\Scripts\python.exe scripts\check_settrade_production_readiness.py
.\.venv\Scripts\python.exe scripts\check_settrade_collector_health.py
.\.venv\Scripts\python.exe scripts\probe_settrade_production.py
.\.venv\Scripts\python.exe scripts\audit_settrade_production_coverage.py
.\.venv\Scripts\python.exe scripts\refresh_current_set50_daily.py
.\.venv\Scripts\python.exe -m streamlit run ui\app.py
```

The readiness check authenticates and makes bounded market-data reads only. It inventories trading method names without calling them. The collector writes market data only. UI account state is labelled `READ ONLY — NO LIVE ORDER ACTIONS ENABLED` and requires account configuration before any account calls; the optional ignored `.env` key is `SETTRADE_ACCOUNT_NO`. That key is currently absent. Do not place the account number in source code or reports.

The daily refresh uses the same verified Yahoo tickers as the existing raw daily data. It downloads from each file's latest observed date, compares the overlap, appends only new dates, and records differing overlap fields without replacing the existing values. Unresolved identities are not guessed. A `PARTIAL` symbol result preserves its validation findings; the raw source rows remain unmodified except for appended dates.

The daily runner's deep health subprocess now defaults to a 60-second timeout (minimum 45, maximum 300), configurable with `SETTRADE_HEALTH_CHECK_TIMEOUT_SECONDS`. Nonzero health exits and invalid JSON remain failures.

## Coverage, refresh and limitations

`reports/settrade_production_smoke.json` contains bounded API observations. `reports/settrade_production_coverage_audit.json` separates sandbox and production paths and records per-day/per-dataset rows, symbols, timestamps, runtime evidence, and missing interval estimates. Days without source/runtime evidence and empty historical API responses remain UNKNOWN. BBO is callback-driven and no historical BBO retrieval was demonstrated; those events cannot be reconstructed from candle data. Historical repair is not attempted until API support and project policy are established. Existing stale daily OHLCV and exploratory market summaries are separately sourced; rebuilding the exploratory catalog does not refresh the upstream Yahoo source files.

Current-session candles and freshness should be rechecked during an open SET trading session. The after-close production smoke returned stale candles, so it cannot settle the previous sandbox `NO_DATA` issue. Never forward-fill or synthesize missing bars.

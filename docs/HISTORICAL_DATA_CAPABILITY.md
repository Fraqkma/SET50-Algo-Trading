# Historical market-data capability and recovery

Audit completed 2026-10-29 00:01 Bangkok time, before that day's 09:45 collector run; latest observed market bars remain 2026-10-28. All data sources remain separate; no organizer raw files were modified.

## Settrade Open API

The installed `settrade-v2==2.2.1` SDK exposes `MarketData.get_candlestick(symbol, interval, limit, start, end)` and `get_quote_symbol(symbol)`. Production probes have exercised `1m`, `5m`, `15m`, and `1d`; additional bounded calls show `1w` and `1mo` response support. `30m` and `60m` were not confirmed. The endpoint accepts bounded ranges and a row limit; the observed response count can be below the limit. PTT's 2026-01-01 to 2026-10-28 daily request returned 198 rows. Prior January 1-10 probes returned 5 rows for 2026, 7 for 2025, 7 for 2024, and none for the sampled 2023, 2022, 2020, 2018, 2016, and 2010 windows. Those empty windows are `API_NO_DATA` evidence for those specific requests, not proof of a universal retention cutoff.

Intraday API responses have also returned old requested windows (for example PTT 1m on 2026-10-21). Two verified append-only backfills added 53 and 121 bars to production normalized storage with zero conflicts. Broader intraday recovery remains constrained by sparse API availability and sampled empty responses. The production collector has 1m, 5m, and 15m observations for 50 symbols from 2026-10-19 through 2026-10-28; latest observation is 16:36 Bangkok on Oct 28.

Daily recovery completed for the current 50-symbol SET50 universe using one request per symbol at one request per second, from 2024-01-01 through 2026-10-28. The API returned 32,101 bars; 22,341 were appended and 9,760 already-present 2026 bars matched. There were no empty responses, errors, duplicate keys, conflicting OHLCV, or invalid OHLCV. The normalized daily file spans Bangkok dates 2024-01-02 to 2026-10-28 and is separate from intraday data. Raw API responses are retained append-only as 100 per-symbol request records across the initial 2026 pass and full-range recovery, with provenance. Details are in `reports/settrade_historical_recovery_manifest.json` and the preserved 2026 manifest.

The SDK exposes no historical SET50 membership/security-master endpoint. Current constituents are appropriate for live collection only. Existing approved daily research covers a partial universe of 20 symbols through 2026-09-04 and must not be described as survivorship-safe. Dividends, splits, and adjusted-versus-unadjusted conventions require source-specific checks.

## TradeSim and other research sources

The repository's official TradeSim history archive contains 492 files and 603,513 rows across 48 symbols, with coverage from 2023-09-21 through 2026-10-21. The official tick archive contains 13 files and 2,417,570 rows across the same 48 symbols, covering 13 trading dates from 2026-10-01 through 2026-10-21. These are simulator history/ticks, not Settrade historical BBO and not daily executable volume. Official benchmark history is retained separately. Approved Yahoo daily research data spans 2023-01-03 to 2026-09-04 for a partial 20-symbol universe; it has known PIT and survivorship limitations.

## Recovery policy and manifest

Daily 2026 data is recovered first for the current 50-symbol universe using one bounded API request per symbol, `limit=1000`, at one request per second. Checkpoint/resume is enabled. Raw responses are appended to a separate Settrade capture file; validated normalized rows are appended only when their `(symbol, interval, timestamp)` key is new. Conflicts are counted and never overwrite existing rows. Earlier annual probes are not silently reinterpreted as a retention boundary.

Per-request timestamps, requested ranges, returned ranges, status, retries, validation findings, persisted rows, existing rows, duplicate/conflict counts, and source are in `reports/settrade_historical_recovery_manifest.json`.

## Current-data quality

The 2026-10-28 current-market audit reports 50 symbols and no current-period malformed CSV records, duplicate keys, conflicting OHLCV, invalid OHLC, or negative-volume findings. Timestamp gaps remain `UNKNOWN`: an empty minute can mean no trade, API omission, aggregation behavior, or a session boundary. Existing legacy 5m/15m bad-row findings are preserved and were not repaired. Production 1m/5m/15m latest bars were 16:36 Bangkok on Oct 28. Daily Settrade rows are raw API OHLCV; adjusted-close semantics are unknown.

## Source comparison

Existing Settrade-versus-TradeSim comparisons cover overlapping intraday 1m/5m/15m timestamps only. Daily Settrade recovery must not be merged with Yahoo, TradeSim, or index history. Daily return comparisons remain exploratory until the recovered rows are audited against source dates, adjustment semantics, and PIT eligibility. No source is used to fill another.

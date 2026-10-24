# Settrade outage recovery and market-data gaps

## Collector behavior

The daily runner starts one isolated collector process per cycle. If a cycle fails, the runner classifies it as `AUTH_FAILURE`, `NETWORK_FAILURE`, `RATE_LIMIT`, or `API_FAILURE`. Authentication failures stop immediately. Other failures receive at most two runner retries with exponential waits of 5 and 10 seconds. Network failures are recorded as offline before the next collector process starts. A new process creates a fresh SDK session and registers its configured realtime subscriptions again. The retry loop is bounded and does not spin.

The runner writes timestamped collector states (`STARTING`, `LIVE`, `DEGRADED`, `OFFLINE`, `RECONNECTING`, `RECOVERED`, `MARKET_CLOSED`, `STOPPED`, and `ERROR`), PID, retry/reconnect counts, last disconnect category, delay, and latest successful request/callback timestamps in the next daily runtime summary. The health scan runs after a successful retry as it does after any successful cycle.

## Candle catch-up and checkpoints

For each symbol, the collector resumes the requested 1-minute range one minute after that symbol's last confirmed current-day candle checkpoint. It requests only the remaining Bangkok calendar-day range, validates returned records, filters out rows outside that request, and appends through the existing deterministic key deduplicator. This catches up the same day's missing tail after an interruption. The checkpoint retains its last confirmed timestamp when a response is empty or stale; it is never advanced based on an empty response. The next cycle continues from that checkpoint. Aggregated 5-minute and 15-minute bars are derived from the actual returned 1-minute rows and explicitly retain incomplete-bucket metadata.

Long gaps that exceed the endpoint's configured row limit may require more than one cycle. The collector does not assume the whole gap was recovered; coverage must be audited from persisted rows. If API data are not returned, the gap remains absent.

## BBO and quote gaps

BBO is an event-driven realtime subscription. Quiet periods by themselves do not prove a network failure, and the installed SDK has no verified historical BBO/depth endpoint. Missing BBO is therefore recorded as `BBO GAP — HISTORICAL RECOVERY NOT AVAILABLE`. The collector does not create BBO from candle rows. Realtime-only gaps remain gaps even after connectivity resumes.

## Gap and cause classifications

The recovery report separates persisted coverage from log/runtime evidence. Network outage labels require transport error evidence or explicit retry/reconnect telemetry; timestamps alone do not establish an outage. Other gaps remain `UNKNOWN`, `NO_CALLBACK_ACTIVITY`, or `NO_DATA` until evidence supports a cause. Weekend/closed periods are not treated as collection failures. The production cutover marker remains distinct from sandbox provenance.

`reports/settrade_gap_recovery.json` contains current-day dataset coverage, source/environment, per-symbol observation bounds, candle timestamp gaps, BBO event quiet-period interpretation, runtime/log evidence, day-by-day history, and recovery records. Compact reports are written beside it for current-day gaps, historical coverage, collector resilience, and UI features.

## Bounded manual recovery

Use `scripts/backfill_settrade_candles.py` to read one explicitly bounded production candle range. A probe writes a validation report but no market rows. `--apply` only consumes the matching previous probe, blocks the whole batch if any row is invalid or conflicts with a genuine row, appends new keys, records the request in `raw/candles/backfill.jsonl`, and leaves an audit in `reports/settrade_backfill_probe.json`. It does not rewrite existing rows, interpolate, or forward-fill. Never point this tool at BBO data.

## Dark research UI

Streamlit defaults to the dark theme in `.streamlit/config.toml`. The shared UI styles use slate backgrounds, restrained teal selection, and readable red/amber/green status colors. Market Overview provides a filterable/sortable SET50 watchlist and selectable daily-source heatmap. Candle Explorer has a source/environment toolbar, time range, local refresh, 60-second local-view auto-refresh, SMA 20/50, session VWAP when positive volume exists, symbol comparison, zoom/pan, and a Plotly reset-axes control. These view controls never authenticate or collect data. Collection Health shows production coverage, session/log evidence, gaps, source provenance, and current freshness. Existing navigation destinations remain under Workspace; pages without data are not represented as working tools.

## 2026-10-21 audit

The retained production log contains collection/SDK timestamps from 09:45 through later afternoon callback records. The post-close `settrade_daily_2026-10-21.json` summary is a separate 20:43 Asia/Bangkok invocation with `MARKET_CLOSED`; it is not the whole day's runtime record. No DNS, timeout, connection-reset, or authentication failure string was found in the day's collector log, so the user-reported internet interruption has no confirmed timestamp in retained evidence. The day remains `UNKNOWN` for outage cause.

The audit found persisted BBO and candle observations across the day. Two bounded PTT 1m requests recovered 174 genuine rows: 53 rows for 11:37–12:29 and 121 rows for 14:30–16:37 Bangkok. Both ranges had no prior rows, schema/price checks passed, and no conflicts were found. Raw and normalized BBO were not altered by recovery. Backfilled candle values keep production routing/source and collection timestamps in the normalized table, with each requested range and backfill time recorded in its probe report and the companion journal.

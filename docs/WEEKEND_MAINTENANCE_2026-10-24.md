# Weekend maintenance audit — 2026-10-24

## Window and coverage

The completed week was 2026-10-19 through 2026-10-23. Trading dates were Oct 19, 20, 21, and 22. Oct 23 was the SET holiday for H.M. King Chulalongkorn the Great Memorial Day ([SET holiday calendar](https://www.set.or.th/en/about/event-calendar/holiday?year=2026)); it is not classified as an outage.

| Date | Settrade production | Official TradeSim ticks/history | Finding |
|---|---|---|---|
| Oct 19 | BBO and 1m/5m/15m observed | Present | Cross-source overlap |
| Oct 20 | BBO and 1m/5m/15m observed | Present | 13 collector log errors and clock mismatch; exact cause/window unknown |
| Oct 21 | BBO and 1m/5m/15m observed | Present | Persisted session evidence conflicts with runtime `market_day=false`; audit now flags the contradiction |
| Oct 22 | BBO and 1m/5m/15m observed | Absent | Official archive cutoff; insufficient evidence for source comparison |
| Oct 23 | No candle session expected | Holiday | No outage |

## Settrade findings

| Date | Raw BBO events / symbols | Normalized depth rows | 1m rows | 5m rows | 15m rows |
|---|---:|---:|---:|---:|---:|
| Oct 19 | 20,215 / 50 | 404,300 | 5,000 | 1,375 | 848 |
| Oct 20 | 19,233 / 50 | 384,640 | 5,000 | 1,448 | 936 |
| Oct 21 | 20,249 / 50 | 404,980 | 5,174 | 1,289 | 720 |
| Oct 22 | 20,488 / 50 | 409,760 | 13,384 | 4,351 | 3,007 |

Raw BBO is event-driven; silence is not treated as a gap without evidence. The daily BBO session bounds and collector events are in `reports/weekend_data_maintenance.json`. Normalized data have production provenance; no suspicious row was deleted. Weekly candle rows had no malformed OHLC or duplicate keys reported. The configured session-grid comparison is a conservative coverage estimate: it does not account for no-trade bars. Daily OHLCV is absent from the Settrade pilot. The history-free 1m/5m datasets remain degraded/partial; 15m is healthier but still carries warnings.

Collector telemetry records no retries or reconnects on Oct 19–22. Oct 20 has 13 logged errors; per-run summary/log timestamps disagree on Oct 20–23. No exact outage is inferred. The Oct 21 `NON_TRADING_DAY` classification was a false classification caused by trusting a runtime flag despite persisted rows; the audit now reports `RUNTIME_MARKET_DAY_CONFLICT_WITH_DATA`.

## Official TradeSim archives and comparison

The local official archives passed ZIP integrity checks. SHA-256 values match the prior inventories; the archive manifests are unchanged. Official ticks and history are current through Oct 21. Tick rows contain repeated timestamps and exact duplicate records without trade/sequence identifiers; they are preserved as organizer data and are not force-deduplicated. No malformed/corrupt archive member was found.

The regenerated broad comparison has overlapping dates Oct 19–21. Across the official-history overlap, Settrade reports:

| Timeframe | Settrade rows | Official rows | Same-timestamp rows | Exact OHLCV matches | Divergent matched rows | Settrade-only | Official-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| 1m | 14,574 | 37,657 | 14,574 | 13,578 | 996 | 0 | 23,083 |
| 5m | 3,953 | 8,986 | 600 | 182 | 418 | 3,353 | 8,386 |
| 15m | 2,409 | 3,312 | 182 | 20 | 162 | 2,227 | 3,130 |

The comparison uses archive overlap and reports source-only rows; it does not force equality. Aggregation/session boundaries, incomplete buckets, no-trade-bar policy, adjustment semantics, or other source rules may explain differences; this audit does not attribute every divergence. Oct 22 is Settrade-only because the official archive snapshot stops at Oct 21, not evidence of an official feed outage.

## Gap and recovery decision

The persisted weekly gap audit was rerun. The current production API sample returned no historical rows for the tested request, and historical BBO retrieval is not verified; therefore no candle gap is classified as safely recoverable this maintenance. No backfill request was issued, no BBO was synthesized, and no TradeSim row was used to replace Settrade. The cumulative gap report contains prior backfill counts; **new rows appended this maintenance: 0**.

## Data-quality scorecard

| Dataset/area | Status |
|---|---|
| Settrade raw and normalized BBO | HEALTHY_WITH_WARNINGS |
| Settrade 1m | DEGRADED |
| Settrade 5m | DEGRADED |
| Settrade 15m | HEALTHY_WITH_WARNINGS |
| Settrade daily | UNKNOWN — absent from pilot |
| Official TradeSim ticks | HEALTHY_WITH_WARNINGS |
| Official TradeSim history | HEALTHY_WITH_WARNINGS |
| Provenance | HEALTHY |
| Collector telemetry | DEGRADED — clock conflicts and runtime contradictions |
| Cross-source diagnostics | HEALTHY_WITH_WARNINGS |

## Safe maintenance and next session

- Refreshed Settrade collection audit, gap report, official source comparison, and archive hash/integrity check.
- Fixed the audit classification so `market_day=false` cannot hide actual persisted observations.
- Did not modify organizer archives/raw files, market observations, or checkpoints; no backfill was applied.
- Before the next session, verify collector process/health and checkpoint state, confirm timestamps are normalized consistently to Asia/Bangkok, and inspect 1m/5m/15m freshness after close. Refresh organizer archives only after the next release and review hash deltas before ingestion.

Machine-readable evidence: [`weekend_data_maintenance.json`](../reports/weekend_data_maintenance.json). The read-only Competition Cockpit displays the week and scorecard.

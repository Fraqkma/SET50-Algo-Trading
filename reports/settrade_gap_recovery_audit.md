# Settrade gap and recovery audit

Read-only report from stored rows and local operational artifacts. No market data were created, rewritten, or recovered.

- Research repo: `D:\GitHub\SET50-Algo-Trading`
- Active Settrade data root: `D:\GitHub\SET50-Algo-Trading\data\pilot\settrade`
- Current free space on the data filesystem: 1017601835008 bytes
- Orders placed: 0

## Latest persisted observations

| Dataset | Earliest | Latest | Rows | Symbols | Last trading date | Freshness |
|---|---|---|---:|---:|---|---|
| raw_bbo | 2026-09-22T09:45:27.696470+07:00 | 2026-10-01T12:29:44.646636+07:00 | 18321 | 50 | 2026-10-01 | PARTIAL |
| normalized_bbo | 2026-09-22T09:45:27.696470+07:00 | 2026-10-01T12:29:44.646636+07:00 | 366420 | 50 | 2026-10-01 | PARTIAL |
| candles_1m | 2026-09-23T10:33:00+07:00 | 2026-10-01T12:29:00+07:00 | 2210 | 47 | 2026-10-01 | PARTIAL |
| candles_5m | 2026-09-23T10:33:00+07:00 | 2026-10-01T12:28:00+07:00 | 1202 | 47 | 2026-10-01 | PARTIAL |
| candles_15m | 2026-09-23T10:33:00+07:00 | 2026-10-01T12:28:00+07:00 | 1144 | 47 | 2026-10-01 | PARTIAL |
| historical_daily_ohlcv | 2023-01-03 | 2026-09-04 | 53843 | 62 | 2026-09-04 | STALE |
| exploratory_market_view | 2010-01-04 | 2026-09-18 | 160280 | 50 | 2026-09-18 | STALE |

## Previous disk-full incident

Classification: **UNKNOWN_NOT_CONFIRMED**. Exact start, end, and first affected timestamp are not established.

- No explicit ENOSPC, disk-full, zero-byte, or disk-guard critical event was found in the retained local evidence.
- The 2026-09-30 runtime summary records approximately 6.75 GiB free at start and end: below the 10 GiB warning threshold but above the 5 GiB critical threshold.
- The 2026-10-01 collection has genuine morning data but no persisted afternoon callbacks and no runtime summary; the exact stop cause is unknown.
- The previous C: checkout and its filesystem history are not available from this research checkout, so the earlier disk-full event cannot be timed from current local evidence.

## Date classification

- **confirmed_disk_full:** none evidenced
- **likely_disk_full:** none evidenced
- **collector_not_running:** 2026-10-05, 2026-10-06, 2026-10-07
- **weekdays_without_any_artifact_unknown:** 2026-10-02
- **partial_or_abnormal:** 2026-09-21, 2026-10-01
- **host_offline:** none evidenced
- **upstream_delay_or_no_data_dates:** 2026-09-23, 2026-09-25, 2026-09-28, 2026-09-29, 2026-09-30, 2026-10-01

## Trading-date collection coverage

| Date | Runner start/end | Raw BBO | Normalized depth rows | First/last BBO | Morning/afternoon | Candle rows (1m/5m/15m) | Classification |
|---|---|---:|---:|---|---|---|---|
| 2026-09-21 | 2026-09-21T09:45:13.528000+07:00 - 2026-09-21T23:28:58.870000+07:00 | 0 | 0 | none - none | none - none / none - none | 0/0/0 | ABNORMAL_TERMINATION |
| 2026-09-22 | 2026-09-22T09:45:08.133000+07:00 - 2026-09-22T17:02:28.896000+07:00 | 2647 | 52940 | 2026-09-22T09:45:27.696470+07:00 - 2026-09-22T16:56:28.299212+07:00 | 2026-09-22T09:45:27.696470+07:00 - 2026-09-22T11:19:12.578175+07:00 / 2026-09-22T14:30:45.014876+07:00 - 2026-09-22T16:56:28.299212+07:00 | 0/0/0 | VALID_DATA |
| 2026-09-23 | 2026-09-23T09:45:07.580000+07:00 - 2026-09-23T17:03:09.580000+07:00 | 2439 | 48780 | 2026-09-23T09:45:26.553221+07:00 - 2026-09-23T16:57:09.031400+07:00 | 2026-09-23T09:45:26.553221+07:00 - 2026-09-23T12:25:50.984316+07:00 / 2026-09-23T14:31:14.558215+07:00 - 2026-09-23T16:57:09.031400+07:00 | 1361/594/542 | VALID_DATA |
| 2026-09-24 | 2026-09-24T09:45:07.503000+07:00 - 2026-09-24T17:02:51.674000+07:00 | 6432 | 128640 | 2026-09-24T09:45:10.280444+07:00 - 2026-09-24T16:56:51.736025+07:00 | 2026-09-24T09:45:10.280444+07:00 - 2026-09-24T12:29:38.340907+07:00 / 2026-09-24T14:31:32.016669+07:00 - 2026-09-24T16:56:51.736025+07:00 | 0/0/0 | VALID_DATA |
| 2026-09-25 | 2026-09-25T09:45:07.191000+07:00 - 2026-09-25T17:02:35.659000+07:00 | 1240 | 24800 | 2026-09-25T09:45:09.727800+07:00 - 2026-09-25T16:56:35.327496+07:00 | 2026-09-25T09:45:09.727800+07:00 - 2026-09-25T12:28:25.887098+07:00 / 2026-09-25T14:30:52.970295+07:00 - 2026-09-25T16:56:35.327496+07:00 | 174/134/133 | VALID_DATA |
| 2026-09-28 | 2026-09-28T09:45:07.224000+07:00 - 2026-09-28T17:04:53.209000+07:00 | 1401 | 28020 | 2026-09-28T09:45:09.969806+07:00 - 2026-09-28T16:58:52.877589+07:00 | 2026-09-28T09:45:09.969806+07:00 - 2026-09-28T12:29:50.053295+07:00 / 2026-09-28T14:31:09.390454+07:00 - 2026-09-28T16:58:52.877589+07:00 | 198/131/130 | VALID_DATA |
| 2026-09-29 | 2026-09-29T09:45:07.830000+07:00 - 2026-09-29T17:03:07.427000+07:00 | 1685 | 33700 | 2026-09-29T09:45:14.779028+07:00 - 2026-09-29T16:57:07.139732+07:00 | 2026-09-29T09:45:14.779028+07:00 - 2026-09-29T12:29:54.366215+07:00 / 2026-09-29T14:31:11.736267+07:00 - 2026-09-29T16:57:07.139732+07:00 | 154/102/99 | VALID_DATA |
| 2026-09-30 | 2026-09-30T09:45:07.672000+07:00 - 2026-09-30T17:03:01.738000+07:00 | 1766 | 35320 | 2026-09-30T09:45:10.499458+07:00 - 2026-09-30T16:57:01.530376+07:00 | 2026-09-30T09:45:10.499458+07:00 - 2026-09-30T12:29:58.516805+07:00 / 2026-09-30T14:31:01.841610+07:00 - 2026-09-30T16:57:01.530376+07:00 | 198/151/150 | VALID_DATA |
| 2026-10-01 | 2026-10-01T09:45:07.254000+07:00 - 2026-10-01T13:52:46.658000+07:00 | 711 | 14220 | 2026-10-01T09:45:10.179561+07:00 - 2026-10-01T12:29:44.646636+07:00 | 2026-10-01T09:45:10.179561+07:00 - 2026-10-01T12:29:44.646636+07:00 / none - none | 125/90/90 | PARTIAL_SESSION_PROBABLE_COLLECTOR_OR_LOG_GAP |
| 2026-10-03 | 2026-10-03T17:41:38.686000+07:00 - 2026-10-03T17:41:38.686000+07:00 | 0 | 0 | none - none | none - none / none - none | 0/0/0 | LOG_ONLY_PARTIAL_OR_UNKNOWN |
| 2026-10-05 | 2026-10-05T09:45:05.318000+07:00 - 2026-10-05T09:45:05.318000+07:00 | 0 | 0 | none - none | none - none / none - none | 0/0/0 | LOG_ONLY_PARTIAL_OR_UNKNOWN |
| 2026-10-06 | 2026-10-06T09:45:05.442000+07:00 - 2026-10-06T09:45:05.442000+07:00 | 0 | 0 | none - none | none - none / none - none | 0/0/0 | LOG_ONLY_PARTIAL_OR_UNKNOWN |
| 2026-10-07 | 2026-10-07T09:45:05.287000+07:00 - 2026-10-07T09:45:05.287000+07:00 | 0 | 0 | none - none | none - none / none - none | 0/0/0 | LOG_ONLY_PARTIAL_OR_UNKNOWN |

## Candle date coverage

API availability counts reflect non-empty raw responses by symbol. The 5m and 15m series are local aggregates of contiguous observed 1m candles; no missing candle is filled.

### 1m

| Date | Rows | First candle | Last candle | Status | API non-empty symbols |
|---|---:|---|---|---|---:|
| 2026-09-23 | 1361 | 2026-09-23T10:33:00+07:00 | 2026-09-23T16:39:00+07:00 | SPARSE | 43 |
| 2026-09-25 | 174 | 2026-09-25T10:23:00+07:00 | 2026-09-25T16:28:00+07:00 | SPARSE | 27 |
| 2026-09-28 | 198 | 2026-09-28T09:56:00+07:00 | 2026-09-28T16:36:00+07:00 | SPARSE | 25 |
| 2026-09-29 | 154 | 2026-09-29T09:55:00+07:00 | 2026-09-29T16:37:00+07:00 | SPARSE | 20 |
| 2026-09-30 | 198 | 2026-09-30T09:56:00+07:00 | 2026-09-30T16:37:00+07:00 | SPARSE | 27 |
| 2026-10-01 | 125 | 2026-10-01T09:55:00+07:00 | 2026-10-01T12:29:00+07:00 | SPARSE | 32 |

### 5m

| Date | Rows | First candle | Last candle | Status | API non-empty symbols |
|---|---:|---|---|---|---:|
| 2026-09-23 | 594 | 2026-09-23T10:33:00+07:00 | 2026-09-23T16:39:00+07:00 | SPARSE | 43 |
| 2026-09-25 | 134 | 2026-09-25T10:23:00+07:00 | 2026-09-25T16:27:00+07:00 | SPARSE | 27 |
| 2026-09-28 | 131 | 2026-09-28T09:56:00+07:00 | 2026-09-28T16:36:00+07:00 | SPARSE | 25 |
| 2026-09-29 | 102 | 2026-09-29T09:55:00+07:00 | 2026-09-29T16:37:00+07:00 | SPARSE | 20 |
| 2026-09-30 | 151 | 2026-09-30T09:56:00+07:00 | 2026-09-30T16:37:00+07:00 | SPARSE | 27 |
| 2026-10-01 | 90 | 2026-10-01T09:55:00+07:00 | 2026-10-01T12:28:00+07:00 | SPARSE | 32 |

### 15m

| Date | Rows | First candle | Last candle | Status | API non-empty symbols |
|---|---:|---|---|---|---:|
| 2026-09-23 | 542 | 2026-09-23T10:33:00+07:00 | 2026-09-23T16:39:00+07:00 | PARTIAL | 43 |
| 2026-09-25 | 133 | 2026-09-25T10:23:00+07:00 | 2026-09-25T16:27:00+07:00 | SPARSE | 27 |
| 2026-09-28 | 130 | 2026-09-28T09:56:00+07:00 | 2026-09-28T16:36:00+07:00 | SPARSE | 25 |
| 2026-09-29 | 99 | 2026-09-29T09:55:00+07:00 | 2026-09-29T16:37:00+07:00 | SPARSE | 20 |
| 2026-09-30 | 150 | 2026-09-30T09:56:00+07:00 | 2026-09-30T16:37:00+07:00 | SPARSE | 27 |
| 2026-10-01 | 90 | 2026-10-01T09:55:00+07:00 | 2026-10-01T12:28:00+07:00 | SPARSE | 32 |


## File integrity

No zero-byte, malformed, duplicate, regressing, or truncated relevant files were found.

## Recovery

No historical BBO was reconstructed. No candle interval was re-downloaded during this audit. The retained evidence shows delayed or empty API responses for some symbol/date combinations, but does not establish that older intervals remain downloadable. Candle recoverability is therefore unverified; BBO intervals without original callbacks are unrecoverable from the retained local artifacts.

Confidence: HIGH for timestamps and row counts; LOW for historical incident causation because the old drive and earlier logs are unavailable.

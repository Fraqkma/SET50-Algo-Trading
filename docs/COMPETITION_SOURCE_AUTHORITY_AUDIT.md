# Competition Source and Authority Audit

**Verified:** 2026-10-31. **Competition period:** 2026-12-16 through 2027-01-15, Asia/Bangkok.

## Calendar

The SET 2026 and 2027 annual holiday calendars currently imply 21 expected sessions. Dec 31, 2026 and Jan 1, 2027 are holidays; weekends are excluded. The dated version and all 31 daily classifications are in [competition_calendar_verified.json](../reports/competition_calendar_verified.json). This is a current expected calendar, not a guarantee against later ad-hoc closures. Check the SET notices again before competition and final scoring. Source: [SET 2026 holiday calendar](https://www.set.or.th/en/about/event-calendar/holiday?year=2026) and [SET 2027 holiday calendar](https://www.set.or.th/th/about/event-calendar/holiday?year=2027).

## Available index history and official scored series

The source file `data/official/tradesim/history/benchmark/SET50.csv` contains 747 unique positive daily closes from 2023-09-21 through 2026-10-21. It is extracted from the organizer-provided `Daily_Ticks.zip` history member and has SHA-256 `cb302826aba0762dd111108c348f1fcab612a9971c4a1af71f62c79f35572267`; archive SHA-256 is `7c505a024bf75d2beba09d4edae3544b71ccbece76154085830ee9d4a5ce588d`. This is appropriate for source-labeled historical market-regime and benchmark-reference analyses. The KGI PDF defines the benchmark as SET50 **Price Index** (no dividends), sampled at daily closes (pages 1–3, 7). The available TradeSim history is not confirmed as the exact organizer scoring feed for the 2026 competition, and its future correction/revision policy is unknown. Do not claim equivalence.

## Official KGI scorecard PDF

File: `KGI_ALGO26_Performance_TH.pdf`; 18 pages; 5,014,707 bytes; SHA-256 `e2a7d549dfffd9691e077a09ba3e51d94a3da11da3da9433ba717039721d79f1`. All 18 pages were text-extracted and visually rendered/reviewed. The local text extractor was scoped to the research environment; no project dependency was added. Formula statements below use the PDF's mathematical definitions and were visually checked against the rendered pages:

| Metric/rule | PDF definition | Page |
|---|---|---:|
| Benchmark | SET50 Price Index, excludes dividends; return uses start/end daily closing values | 1–3 |
| Portfolio return | `(ending NAV − starting NAV) / starting NAV`; NAV includes holdings marked at daily close and remaining cash | 4 |
| Portfolio MDD | Largest peak-to-trough decline in daily closing NAV; recovery ends a drawdown episode | 5–6 |
| Excess return | Portfolio total return minus benchmark return, over the same dates and using closing prices | 7 |
| Calmar | Cumulative portfolio return divided by absolute percentage maximum drawdown | 8 |
| FIFO round trip | A lot is counted when its full quantity is closed under FIFO per symbol; partial sells match actual quantity; open lots are not complete | 9–10 |
| Average exposure | `sum(daily invested value) / sum(daily NAV)` across competition trading days; values use closing prices | 11–12 |
| Win rate | Profitable completed FIFO round trips divided by completed round trips; zero-PnL lots are neither wins nor losses | 13–14 |
| Expected payoff | `win rate × average gain − loss rate × average loss`, calculated only on completed round trips | 15–16 |
| Common Criteria | Portfolio MDD `< 1.5 × benchmark MDD`; at least 5 round trips; average exposure `≥ 50%`; expected payoff `> 0` | 18 |
| Award ranking | Best Alpha: portfolio return and excess return nonnegative; rank by excess return, Calmar, portfolio return. Best Risk Control: Calmar, excess return, lowest MDD. Most Active: round trips; Precision: win rate | 17–18 |

Page 16's worked arithmetic table lists 60 profitable and 40 losing trades, with gains 1,200 and losses 800, and displays expected payoff 400. Its printed expression `0.6 × 1200 − 0.4 × 800` equals 400; this example is consistent. The win-rate definition on pages 13–14 explicitly excludes zero-PnL completed round trips from both numerator and denominator. Qualification comparisons remain strict/non-strict exactly as shown above.

## Metric-window safeguards

`competition_metrics_for_period` in `src/competition/metrics.py` requires date-stamped daily records, explicit expected trading dates, matching canonical date window, complete NAV/index/exposure values, and known boundary treatment before returning window metrics. Its fail-closed incomplete path returns null metrics. The generic `competition_metrics` helper remains available for research sequences and must not be represented as an official-window score. Organizer boundary lots and exact NAV cutoff questions remain in `docs/QUESTIONS_FOR_ORGANIZER.md`.

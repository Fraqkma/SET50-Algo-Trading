# KGI ALGO26 official competition period

The confirmed inclusive competition period is **2026-12-16 through 2027-01-15**, in `Asia/Bangkok`. The single canonical source is [`config/competition.yaml`](../config/competition.yaml); its dates feed benchmark configuration, official metric scoping, score qualification, and the Competition Cockpit.

## Trading calendar and exposure

The period contains 21 expected SET trading days after excluding weekends and the SET holidays on 2026-12-31 and 2027-01-01. The official SET holiday pages for 2026 and 2027 were checked on 2026-10-30. Holiday notices can be amended, so refresh the calendar report before final scoring.

- 2026 calendar: <https://www.set.or.th/en/about/event-calendar/holiday?year=2026>
- 2027 calendar: <https://www.set.or.th/th/about/event-calendar/holiday?year=2027>
- Machine-readable generated dates: [`reports/competition_calendar.json`](../reports/competition_calendar.json)

Average exposure uses only the expected trading dates inside the inclusive competition period. It is unknown when a required date's NAV or invested value is missing. Weekend and holiday rows do not enter the denominator.

## Benchmark and scoring window

The benchmark is the SET50 Price Index, no dividends, using official daily closing values. Its configured date window is exactly Dec 16, 2026 through Jan 15, 2027. The exact organizer scoring file/API identity remains unresolved and is tracked in `QUESTIONS_FOR_ORGANIZER.md`. No future index values are created or inferred.

Official metrics may be labeled scoring-eligible only when the input run covers the exact canonical set of expected trading dates, contains complete daily inputs, has no unresolved FIFO boundary case, and proves continuous portfolio state across dates. The current TradeSim bridge creates a fresh portfolio each date, so its outputs remain simulator evidence and cannot populate official competition metrics. See `src/competition/period.py`, `competition_metrics_for_period()`, and the bridge scoring gate.

## Position and round-trip boundaries

FIFO lots opened before Dec 16, left open after Jan 15, or sold outside the inclusive period are tagged as boundary cases. Their treatment is not inferred. Metrics depending on unresolved round-trip treatment remain `UNKNOWN` until organizer guidance resolves whether pre-period holdings are allowed and how boundary lots are counted.

Pre-competition history can support warm-up and research, but only dates and fills assigned to the official scoring period enter score calculations.

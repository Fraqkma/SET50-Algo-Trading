# Questions for organizer

Confirmed competition period: 2026-12-16 through 2027-01-15 (inclusive), Asia/Bangkok. SET holidays were checked against the official 2026 and 2027 holiday pages and are recorded in `config/competition.yaml` and `reports/competition_calendar.json`.

## BLOCKING - competition boundary holdings and round-trips

- **Question:** Are positions opened before 2026-12-16 permitted in the competition portfolio? If so, how are their opening NAV/cost basis, invested exposure, and any sale during the competition treated? Does a position opened by 2027-01-15 but closed later count toward the completed FIFO Round-Trip requirement, Win Rate, or Expected Payoff?
- **Why it matters:** These rules affect starting NAV, daily exposure, FIFO round-trip counts, Common Criteria, and award eligibility.
- **Current assumption:** No boundary treatment is assumed. Cross-boundary lots are identified and the affected round-trip metrics remain UNKNOWN.
- **Impact if changed:** Portfolio return, exposure, realized P&L, minimum Round-Trip eligibility, Win Rate, Expected Payoff, and award readiness can all change.

## IMPORTANT - benchmark scoring series identity

- **Question:** Which exact official SET50 Price Index daily-close file or API series is the scoring source for 2026-12-16 through 2027-01-15, including any correction/revision policy?
- **Why it matters:** Benchmark return, benchmark maximum drawdown, excess return, and the Common Criteria drawdown threshold depend on the exact close series.
- **Current assumption:** Use the SET50 Price Index, no dividends, and official daily closes as specified; TradeSim benchmark data remain a cross-check until the scoring series is identified.
- **Impact if changed:** Benchmark metrics, Best Alpha eligibility/ranking, and the drawdown criterion may change.

## IMPORTANT - portfolio boundary valuation

- **Question:** At what exact time and price source is opening NAV set on 2026-12-16 and ending NAV set on 2027-01-15? Are same-day fills on either boundary included in the scored portfolio value and exposure?
- **Why it matters:** The confirmed dates identify the window, but do not settle whether boundary-day trading is included before or after each valuation point.
- **Current assumption:** Keep official scoring metrics UNKNOWN until valuation cutoffs and boundary-day fill treatment are confirmed. Daily closes are used only as the configured market reference, not as a substitute for an unspecified portfolio cutoff.
- **Impact if changed:** Portfolio return, maximum drawdown, exposure, and boundary trades can change.

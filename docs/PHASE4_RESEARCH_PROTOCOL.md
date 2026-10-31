# Proposed Phase 4 Research Protocol (Not Executed)

**Status:** protocol only. No new signal hypothesis was tested in this task.

## Objective and pre-registration

Primary objective remains balanced net risk-adjusted returns. Any next phase is limited to at most three economically distinct hypotheses, selected because the data support the mechanism. Each registration must state (a) mechanism and signed effect, (b) target estimand—single-stock residual alpha, cross-sectional ranking skill, or net portfolio effect—(c) fixed 1/2/3/5-session endpoints, and (d) net hurdle after commission, VAT, tick-size slippage sensitivity, and source-supported execution constraints. The 6–7% competition return remains aspirational, never a selection threshold.

No indicator/parameter grid. At most one frozen definition per hypothesis. Test the null that the effect is no larger than the stated cost hurdle; report gross, costs, net, and uncertainty separately.

## Design and dependence

- Use only rows admitted by the date-effective PIT gate. Join each feature using data available at its signal timestamp; never use later membership, vendor adjustment, or next-bar knowledge to create a signal.
- Match controls on signal date and, when sample permits, volatility, liquidity, sector, and market regime, with the pre-specified matching priority and balance diagnostics. No post-outcome matching.
- Separate date and symbol dependence using two-way clustered bootstrap or a justified multiway method; group overlapping 1–5 session outcome windows and purge/embargo overlapping events at split boundaries.
- Correct familywise error across the pre-registered primary hypotheses (Holm or stricter); secondary horizons/subgroups are descriptive only.
- Split chronologically into development, validation, and genuinely unseen holdout. No already reviewed 2023–2026 daily history may be called unseen. Keep prospective Nov/Dec 2026 Settrade collection untouched until the hypothesis, code, and decision thresholds are frozen; use only for source-specific validation if its semantics are adequate.

## Power and stop rules

Before the outcome run, compute MDE/power against the cost hurdle using effective date-symbol clusters, overlap blocks, expected event incidence, and conservative variance. Event count alone is insufficient. If effective independent blocks cannot support 80% power at two-sided familywise alpha 0.05 for the minimum economically meaningful effect, stop without outcome search and collect more time/source coverage. Require adequate event counts across at least 10 symbols and 20 dates plus acceptable balance; these are minimum gates, not power proof. Stop on failed provenance, leakage, benchmark date alignment, sample adequacy, or cost hurdle. No promotion with an interval spanning the hurdle.

## Source and execution sufficiency

Daily-bar-only hypotheses may support signal diagnostics and daily-mark portfolio baselines; they cannot establish BBO, auction fills, IOC fill rate, or queue position. Tick studies require validated source timestamps, symbol identity, complete relevant sessions, and aligned strategy order times. TradeSim 0.2.7 fixture checks establish mechanics only. Keep Yahoo approved PIT, organizer daily history, Settrade production, and organizer tick studies as separate datasets unless a documented security/action reconciliation is completed in advance.

## Portfolio construction gate

3/5/8-name equal-weight comparisons may proceed only after a signal passes G1 and source, cost, and validation gates. They are risk/implementation diagnostics, not independent alpha tests. Enforce long-only, capital, board-lot, fees/VAT and one adverse SET tick per fill where the source supports a fill model. Report exposure, daily close NAV drawdown, FIFO completed round trips, and payoff, without tuning to qualification thresholds. Historical SET50 MDD distributions and the strict 1.5× condition are scenarios; no future drawdown cap is guaranteed.

## Untouched holdout rule

Hash the frozen protocol, code, config, and source manifests before any next run. Record every attempted hypothesis. Do not read or summarize prospective holdout outcomes before the freeze. If the sample is underpowered or source quality fails, report `NO_TEST` and do not promote a candidate.

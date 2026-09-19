# Larger Comparable-Block OOS Research

This is a fixed-parameter extension of the existing Design A versus Design C
walk-forward study. It does not modify either strategy, feature, execution,
eligibility, or portfolio rule.

## Pre-specified block design

The approved data contain 898 observed union trading rows. The design uses the
first **250 observed rows** as initial expanding research history, followed by
**80 observed rows per OOS block**. The 250-row history is materially longer
than the 50-row longest feature warm-up and is roughly a year of observed
trading, while 80 rows provide multiple three-row rebalances without making the
study dominated by a very short episode.

This produces eight equal 80-row paired blocks (250 + 8 × 80 = 890 rows). The
remaining eight observed rows are a deterministic terminal remainder shorter
than one complete block. They are reported as unused rather than analyzed as a
shorter block. This rule was chosen from data geometry and comparability, not
from returns.

Each block resets to THB 10,000,000. For a block ending at date `t`, approved
raw rows are truncated at `t` before features are built; only rows in the OOS
interval are passed to the engine. No future row can affect a feature, signal,
selection, execution, or valuation.

## Dependence and statistical status

The eight blocks are paired A/C experiments, but they are not guaranteed to be
independent. Expanding research histories overlap, market conditions can be
serially related, and all blocks share the same historical universe and fixed
execution model. More blocks increase descriptive coverage but do not magically
create independent samples. Daily observations inside a block are not counted
as independent tests.

The pre-registered exact paired test is not run by this workflow. Human approval
is required first to determine whether the resulting eight blocks meet the
protocol's intended conditions for an inferential comparison.

## Outputs

Run `python scripts/run_larger_oos.py` to produce:

- `reports/larger_oos_results.json`
- `reports/larger_oos_results.csv`
- `reports/larger_oos_report.md`

The JSON contains every block's A and C metrics, paired differences, costs,
fills/non-fills, valuation completeness, and eligibility exclusions. It also
records the terminal remainder policy and whether an inferential test was run.

This is OOS evidence only; it is not optimization and does not establish
strategy superiority by itself.

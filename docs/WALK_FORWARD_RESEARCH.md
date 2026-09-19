# Deterministic Walk-Forward Research

This workflow is a fixed-parameter out-of-sample evaluation of the existing
Design A reference and Design C comparison. It does not tune momentum windows,
Top N, rebalance frequency, execution assumptions, or any other strategy rule.

## Fold rule

The approved data contain 898 observed union trading rows. Folds use the first
400 observed rows as the initial research history and the next 120 observed rows
as OOS. The research window expands by one OOS block each time; the final fold
uses the remaining rows (18 rows). Calendar gaps are preserved because the rule
is based on observed rows, not fabricated calendar dates.

Each fold resets to THB 10,000,000. This makes fold results independent and
auditable; the aggregate return is a documented compounded proxy, not a single
continuous portfolio result.

For each fold, raw approved data are truncated at that fold's OOS end before
features are built. Only rows in the OOS interval are passed to the event-ordered
engine. Thus research history can warm up causal features, while no later row can
influence a signal or execution.

## Unchanged strategy and execution

Both designs use the existing historical SET50 membership gate, valuation-gap
policy, boundary exits, Design A filter, three-observed-row schedule, full
replacement, equal weights, and LIMIT/IOC one-tick execution model. Design C
only ranks qualifying Design A candidates by `momentum_20` and selects Top 10.

## Outputs

Run `python scripts/run_walk_forward.py` to produce:

- `reports/walk_forward_results.json`
- `reports/walk_forward_results.csv`
- `reports/walk_forward_report.md`

Metrics are reported per strategy and fold, including returns, costs, turnover,
fills/non-fills, drawdown, valuation completeness, and rebalance count. Aggregate
statistics include mean, median, population standard deviation, positive-fold
fraction, and compounded independent-fold net return.

The result is diagnostic OOS evidence. It is not parameter optimization and does
not establish strategy superiority from return alone.

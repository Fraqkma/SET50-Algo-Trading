# Design C Comparative Backtest

`Design C` is the controlled cross-sectional comparison to the Design A
reference. It uses the same approved research loader, historical SET50 gate,
feature frames, three-observed-row schedule, full replacement, equal weighting,
boundary exits, and LIMIT/IOC execution model. The only strategy difference is
that qualifying Design A candidates are ranked by `momentum_20` and capped at
Top 10.

Run:

```text
python scripts/run_design_c_comparison.py
```

The script writes Design C JSON/Markdown, orders, selections, and snapshots,
plus `reports/design_a_vs_c_comparison.json` and `.md`. It also records how often
fewer than ten candidates qualified and the per-signal symbol-set differences.

The output is descriptive research evidence. A higher or lower return does not
establish superiority; no parameter optimization, OOS tuning, or Design C
modification is performed by this workflow.

# Design A Backtest Report

This is the first fixed-assumption research run; no optimization or OOS testing was performed.

- `design`: `A`
## research_period
- `start`: `2023-01-03`
- `end`: `2026-09-04`
- `observations`: `898`
- `approved_symbols_loaded`: `20`
- `starting_capital`: `10000000`
- `final_equity`: `2881303.363244797241866051837`
- `gross_return`: `-0.5894018801035329474163400004`
- `net_return`: `-0.7118696636755202758133948163`
- `volatility`: `0.08539205721260267`
- `maximum_drawdown`: `-0.7575565538426281729301119431`
- `turnover`: `72.90182961604103125010704`
- `commission`: `1144558.724971844190626680528`
- `vat`: `80119.11074802909334386763696`
- `total_fees`: `1224677.835719873283970548159`
- `slippage`: `4765765.1700000000000000`
- `trade_count`: `1363`
- `unique_symbols_traded`: `18`
- `rebalance_count`: `298`
- `fills`: `1363`
- `non_fills`: `641`
- `valuation_gaps`: `[]`
- `valuation_complete`: `True`
- `complete_valuation_snapshots`: `898`
- `incomplete_valuation_snapshots`: `0`
## unvalued_positions
- `boundary_exit_events`: `2`
- `boundary_exit_fills`: `2`
- `boundary_exit_non_fills`: `0`
- `boundary_exit_symbols`: `['BGRIM', 'CENTEL']`
## data_exclusions
## eligibility_exclusions
- `GULF_PRE_MERGER_CONTINUITY_BOUNDARY`: `182`
- `OUTSIDE_SET50_MEMBERSHIP_PERIOD`: `1178`
- `OUTSIDE_APPROVED_DATA_RANGE`: `122`
## execution_assumptions
- `order_type`: `LIMIT`
- `validity`: `IOC`
- `commission_rate`: `0.00157`
- `vat_rate`: `0.07`
- `buy_request`: `next_session_open_plus_one_tick`
- `sell_request`: `next_session_open_minus_one_tick`
- `fill_rule`: `requested_price_inside_low_high`
- `tick_mapping`: `scripts/run_design_a_backtest.py:set_tick_size`
- `benchmark`: `Design A is the reference; no separate benchmark series was run.`

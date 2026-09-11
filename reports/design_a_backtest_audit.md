# Design A Backtest Audit

## Executive summary

Recommendation: **PASS**. Mechanical accounting checks pass; historical-universe boundary exits prevent post-membership valuation.

## Accounting reconciliation

```json
{
  "starting_cash": "10000000",
  "buy_notional": "368793669.8557228209876169",
  "sell_notional": "360224626.3046874915134535",
  "fees": "1224677.835719873283970548165",
  "recalculated_ending_cash": "206278.613244797241866051835",
  "reported_ending_cash": "206278.6132447972418660518373",
  "residual": "-2.3E-21",
  "matches_within_decimal_tolerance": true
}
```

## Slippage analysis

```json
{
  "reported_slippage": "4765765.1700000000000000",
  "recalculated_monetary_impact": "4765765.1700000000000000",
  "buy_monetary_impact": "2395336.1600000000000000",
  "sell_monetary_impact": "2370429.0100000000000000",
  "theoretical_price_impact_ticks": "1363.00000000000000",
  "filled_order_count": 1363,
  "requested_prices_match_one_adverse_tick": true,
  "fills_inside_low_high": true,
  "one_tick_each_filled_order": true,
  "slippage_non_negative": true,
  "deducted_via_execution_price_not_separate_cash_charge": true,
  "double_count_detected": false
}
```

## Fee/VAT analysis

```json
{
  "commission_rate": "0.00157",
  "vat_rate": "0.07",
  "recalculated_commission": "1144558.724971844190626680528",
  "recalculated_vat": "80119.11074802909334386763696",
  "recalculated_total_fees": "1224677.835719873283970548165",
  "reported_total_fees": "1224677.835719873283970548159",
  "commission_plus_vat_equals_total": true,
  "commission_vat_rounding_residual": "6E-21",
  "based_on_executed_notional": true,
  "fees_non_negative": true,
  "deducted_once_via_cash_reconciliation": true
}
```

## Turnover analysis

```json
{
  "definition": "sum(filled executed notional) / starting capital; buys and sells both included",
  "buy_notional": "368793669.8557228209876169",
  "sell_notional": "360224626.3046874915134535",
  "total_notional": "729018296.1604103125010704",
  "recalculated_turnover": "72.90182961604103125010704",
  "reported_turnover": "72.90182961604103125010704",
  "matches_report": true
}
```

## Non-fill analysis

```json
{
  "total": 641,
  "by_reason": {
    "IOC_LIMIT_NOT_FILLED": 504,
    "INSUFFICIENT_CASH": 136,
    "DATA_UNAVAILABLE": 1
  },
  "by_symbol": {
    "LH": 50,
    "PTTGC": 40,
    "TOP": 58,
    "CENTEL": 33,
    "GLOBAL": 28,
    "HMPRO": 41,
    "OSP": 50,
    "SCGP": 51,
    "KTB": 63,
    "COM7": 23,
    "BGRIM": 16,
    "MTC": 27,
    "IVL": 36,
    "BDMS": 36,
    "RATCH": 50,
    "GULF": 7,
    "KKP": 14,
    "TIDLOR": 17,
    "THAI": 1
  },
  "by_side": {
    "BUY": 440,
    "SELL": 201
  }
}
```

## Portfolio reconciliation

```json
{
  "expected_final_positions": {
    "IVL": 27941,
    "PTTGC": 15833,
    "KKP": 6038,
    "TIDLOR": 28561
  },
  "reported_final_positions": {
    "IVL": 27941,
    "KKP": 6038,
    "PTTGC": 15833,
    "TIDLOR": 28561
  },
  "matches_final_positions": true
}
```

## Valuation-gap analysis

```json
{
  "symbols": {},
  "example_dates": {},
  "no_forward_fill": true
}
```

## Execution timing

```json
{
  "all_fills_after_signal_or_approved_boundary_exception": true,
  "all_selections_after_signal": true,
  "same_day_fills": 2,
  "same_day_boundary_exceptions": 2
}
```

## Eligibility exclusions

```json
{
  "GULF_PRE_MERGER_CONTINUITY_BOUNDARY": 182,
  "OUTSIDE_SET50_MEMBERSHIP_PERIOD": 1178,
  "OUTSIDE_APPROVED_DATA_RANGE": 122
}
```

## Sanity checks

```json
{
  "cash_never_negative": true,
  "positions_never_negative": true,
  "fills_inside_low_high": true,
  "one_tick_each_filled_order": true,
  "fees_non_negative": true,
  "slippage_non_negative": true,
  "cash_reconciliation_passes": true,
  "position_reconciliation_passes": true,
  "timing_passes": true,
  "nonfills_zero_cash_effect": true
}
```

## Bugs found

- NON_FILL records previously omitted side; fixed mechanically before this audit and regression-tested.

## Limitations, not bugs

- Valuation gaps make snapshots explicitly INCOMPLETE; equity and return/risk metrics are unavailable rather than calculated from a partial value.
- LIMIT/IOC bar-range fill and injected tick-band mapping are explicit research assumptions.
- High turnover and one-tick adverse pricing can dominate returns under the fixed model.

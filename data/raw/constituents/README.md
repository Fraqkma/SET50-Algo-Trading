# Historical SET50 constituent data

This directory must contain one or more CSV files describing historical SET50 membership.

Required schema:

```csv
effective_from,effective_to,symbol
2025-01-01,2025-06-30,AOT
2025-01-01,2025-06-30,ADVANC
2025-07-01,2025-12-31,ADVANC
2025-07-01,2025-12-31,CPALL
```

The project intentionally does not hard-code a fixed SET50 list for all dates. This data is used to determine which Yahoo Finance tickers are required for a historical backtest window.

If official SET50 constituent files are later provided by the competition, they can replace this research dataset without changing the pipeline contract.

# Official TradeSim 0.2.5 integration

## Runtime source and setup

The authoritative local package is `tradeSim0.2.5.zip` at the repository root.
It passed ZIP integrity checking and contains 534 members, including
`TradingSimulation.ipynb`, `requirements.txt`, `tradeSim/`, the strategy template,
two examples, SET50 symbol data, daily/intraday history, and tick data. It is
extracted to the ignored `tools/kgi_tradesim/` directory. The research environment
is `.venv` (Python 3.14.7); official TradeSim requires its separate
`.venv-kgi313` with **exactly Python 3.13.0**.

Archive SHA-256: `9f9e972f9df082bcd0739588f241a318243db06f5d0837290d4bc8593bfb5ed7`
(14,858,491 bytes; 222,042,917 bytes uncompressed). Version evidence is the
archive filename and required package layout; the package does not expose an
internal version constant. The official archive remains local and is ignored by
Git as a setup source.

Run `scripts/setup_kgi_tradesim.ps1` after installing Python 3.13.0. The script
checks the exact interpreter before creating the environment and installs only
the archive's pinned `requirements.txt`. This machine currently exposes Python
3.13.16 but not 3.13.0, so environment setup and TradeSim execution are blocked
until the exact patch release is available. The research environment is not
changed. No package is installed using a substitute interpreter.

The `--check` diagnostic inventories the archive, extracted runtime, exact
interpreter, requirements/import status, practice data, and strategy templates.
It reports `BLOCKED` when the required runtime is unavailable and does not
install packages. At this audit, `.venv-kgi313` is absent; dependency
installation, TradeSim imports under the competition interpreter, and notebook
imports have not been verified. The named 08/10/2026 workshop PDF and
`KGI_ALGO26_Performance_TH.pdf` are not present in this workspace. The archive
contains `docs/WORKSHOP_CODE.md`, which supplements source/notebook inspection
but does not replace the missing competition PDFs.

## Notebook flow and local bridge

The workshop notebook flow is: imports; load one tick file and parse
`TradeDateTime`; group rows per symbol; set team/strategy and fresh-start policy;
initialize `TradeSim.tradeSim(team, current_date=...)`; import a module whose file
and class names match; instantiate a `StrategyHandler` per symbol; choose
`with_visual`; process each symbol's rows, match order books and update market
prices; flush transaction/error logs; create transaction summary; finalize/save
daily summary and portfolio; display portfolio metrics and holdings. Its
multi-day cell creates a new simulator and handlers per date in ascending order.

The research CLI is `scripts/run_official_tradesim.py`. It uses only the local
extraction and launches `.venv-kgi313/Scripts/python.exe` as a subprocess. It
does not import TradeSim into Python 3.14. `--list-dates` is usable without the
official environment. Once Python 3.13.0 and the archive requirements are
installed:

```powershell
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --check
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --list-dates
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --date 2026-09-09
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --date 2026-09-09 --date 2026-09-10
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --compare research.json official.json
```

The default strategy is the archive's unmodified `Example_strategy.py`; a
candidate can be supplied with `--strategy path\to\StrategyName.py`, with a
matching class name. Outputs are retained under ignored
`artifacts/official_tradesim_runs/<run-id>/`, including stdout, stderr, normalized
JSON, copied simulator result files, and strategy source/hash. Each run uses a
unique TradeSim owner/run ID and starts fresh. Repeating `--date` in ascending
order within one CLI invocation follows the notebook's carry behavior: saved cash,
holdings, and portfolio snapshots move across dates, while handler state and
unfilled order books reset each day. Separate CLI invocations are independent.

The checked tick inventory is recorded in
[`reports/tradesim_025_practice_data_inventory.json`](../reports/tradesim_025_practice_data_inventory.json):
16 files from 2026-09-09 through 2026-09-30, 48 SET50 symbols per day, about 203.7 MB,
137,706–316,891 rows per file. Each file contains only the date in its filename;
all symbols matched the bundled SET50 list, and timestamps, prices, and volumes
passed the structural checks. Recorded
coverage spans 09:55–16:37 each day, so the local checks found no obvious
truncated session. This does not certify completeness against an external feed.

The tick files total 203,668,125 bytes. They cover 16 practice dates from
2026-09-09 through 2026-09-30, with 48 symbols per date. Filenames carry the
trading date; tick timestamps are naive local values. October 16 is an
intentional production cutover partial day and is not used to judge the
TradeSim practice-session inventory.

## Observed runtime facts from the 0.2.5 source

- A simulator object loads/saves cash, holdings, and daily snapshots through its
  owner portfolio JSON. The notebook creates fresh StrategyHandler instances per
  symbol each day, so instance state resets; strategy state is not automatically
  persisted.
- Each daily simulator has a new in-memory order book. Resting limit orders that
  did not fill are therefore not carried to the next day. This is source-code
  behavior, pending runtime smoke verification.
- `Order.py` validates the bundled SET50 symbol list and 100-share board lots;
  `Execution.py` checks cash for buys and held quantity for sells. The strategy
  interface exposes `create_order_to_limit` and `create_order_at_market`, with
  no validity/IOC parameter. Pending limit orders can rest intraday. Exact
  runtime behavior still needs the 3.13.0 smoke test.
- Order creation checks a buy quantity against cumulative tick sell volume, and
  a sell quantity against cumulative tick buy volume. Reviewed execution fills a
  matched order's full requested quantity; no partial-fill quantity is emitted
  by this source path. FIFO still accepts partial actual fill records so a future
  simulator version with partials can be accounted for without inventing fills.
- The reviewed code does not gate order submission by an explicit exchange
  session clock; it processes rows supplied by the selected tick CSV. Session
  restrictions require confirmation from the newest workshop/rules material.
- `CommissionService.py` uses 0.157% commission plus 7% VAT. Its slippage is a
  price-bucket schedule, not an explicit generic one-tick API. Limit fills do
  not apply market slippage; market fills use one bucket step.
- The bundled `Example_strategy.py` calls `create_order_at_market`. This conflicts
  with the competition constraint in the repository instructions limiting orders
  to Limit and Market-to-Limit IOC. The example is retained only as an official
  package smoke fixture; it is not a compliant strategy recommendation.

These are observations from code, not a replacement for the missing newest
workshop PDF. Any conflict with the 08/10/2026 workshop or performance PDF must
be resolved in favor of those documents and recorded explicitly.

## Accounting and metrics foundation

`src/competition/metrics.py` supplies FIFO per-symbol lot accounting, close-based
portfolio/benchmark return and drawdown, excess return, Calmar, average exposure,
completed-lot Win Rate/Expected Payoff, Common Criteria PASS/FAIL/UNKNOWN, and a
descriptive award-readiness view. Buy lots may coexist; only actual sell fill
quantity is matched, FIFO. A round-trip is complete only when an individual buy
lot has been fully closed. Partial fills are recorded by actual quantity; open
lots can cross days. Accounting is separate from order eligibility.

ADD_TO_POSITION_RULE remains **UNCONFIRMED** as a competition rule. TradeSim's
FIFO portfolio structure permits multiple open lots by symbol, which does not
establish organizer permission. The supplied brief does not prohibit pyramiding.

The referenced `KGI_ALGO26_Performance_TH.pdf` was not found in this workspace.
The user-supplied task description specifies Common Criteria and FIFO semantics;
those are implemented. However, the exact PDF formula for Calmar, treatment of
breakeven round-trips, NAV base, and every award/ranking detail remain provisional
until the authoritative PDF can be inspected. TradeSim 0.2.5 source currently
defines Return as NAV vs fixed THB 10,000,000, Max DD from daily finalized NAV
peaks/troughs, Calmar as return divided by max drawdown, exposure as the mean of
daily invested/NAV, and excludes breakeven round-trips from Win Rate/Payoff.
Potential discrepancy: the source's `save_summary_csv` computes some measures
from simulator portfolio state; it has not been verified against the missing
performance document.

Additional direct summary-source observations: portfolio return is final NAV
versus fixed THB 10,000,000. Portfolio max drawdown uses daily finalized NAV
peak/trough values; benchmark return and drawdown use daily benchmark closes
from the selected start date through the simulation date. Average exposure is
the arithmetic mean of each day's invested value divided by that day's NAV.
FIFO lots become complete only when fully sold; realized lot P&L includes the
simulator's fee-adjusted buy cost and sell proceeds, while break-even lots are
excluded from Win Rate and Expected Payoff. TradeSim writes Calmar as zero when
drawdown is zero; the research metrics helper preserves it as null because the
ratio is undefined. This discrepancy remains explicit pending the Performance
PDF. If benchmark data has fewer than two closes, the simulator returns 0.0 for
benchmark return; that fallback also needs confirmation against the PDF.

## Research comparison and next task boundary

The existing research backtester remains unchanged and is always labeled
`RESEARCH_BACKTEST`; this bridge labels official results
`OFFICIAL_TRADESIM_0_2_5`. Returns/costs/fills/turnover/timing/ending NAV need not
match because tick-level official matching, order validity, price buckets, and
daily portfolio state differ from research assumptions. Unknown values remain
null. No final strategy selection, award optimization, competition cockpit, or
real order placement is part of this foundation.

Portable Python interfaces now live in `src/competition/core/`: market input,
features, signals, portfolio/risk policy, order intent, and execution adapter
contracts. FIFO accounting remains in `src/competition/metrics.py`; the
TradeSim subprocess boundary remains in `src/competition/tradesim_bridge/`.
These modules have no Streamlit or notebook dependency and do not import
TradeSim into the research interpreter. They are contracts only; no final
strategy, portfolio policy, or live execution implementation is selected.

## Current source audit

`Strategy_template` requires a same-named strategy module/class, subclass
initialization with a handler, and `on_data(bar)`. The callback receives
`ShareCode`, `Timestamp`, `Open`, `High`, `Low`, `Close`, and `Volume`; it is a
live-updating aggregated bar. The handler exposes portfolio reads, historical
data, limit/market order creation, open-order reads and cancel methods. The
workshop multi-day cell creates a handler per symbol per day. Strategy instance
state resets each day; saved portfolio cash and holdings load when
`fresh_start=False`.

Relevant handler calls found in the implementation are
`check_port_has_stock(symbol, volume)`, `get_stock_by_symbol(symbol)`,
`get_total_stock_volume_by_symbol(symbol)`, `get_all_stocks_info()`,
`get_portfolio_info()`, `get_cash_balance()`, `get_roi()`,
`get_historical_data(symbol, n, timeframe="1D")`,
`create_order_to_limit(volume, price, side, symbol)`,
`create_order_at_market(volume, side, symbol)`, `get_open_orders(symbol=None)`,
`cancel_order(order_number)`, and `cancel_all_orders(symbol=None)`. Cancel calls
only alter the simulator's local paper order book.

Directly observed execution facts:

- The bundled SET50 symbol list and 100-share increments are validated. Buy
  checks include cash and cumulative opposing-side tick volume; sells check
  held shares and cumulative opposing-side tick volume. Sell holdings are
  validated again at fill time.
- The inspected order validator has no explicit positive-quantity guard; its
  board-lot check applies only when quantity is positive. The portable
  `OrderIntent` rejects nonpositive quantities before an engine adapter.
- The handler exposes Limit and Market only. It has no Market-to-Limit or IOC
  argument. Limit orders can rest during the day; their book is in-memory and
  resets with the next daily simulator.
- A new limit order can fill at a current quote within its limit; a resting
  limit fills at its limit when crossed. Auction flags do not fill limit orders.
- Matched fills use the full order quantity. The reviewed path emits no partial
  fills. No explicit exchange-session gate or limit-price tick rounding was
  identified in the inspected order path.
- Market fills apply a price-bucket increment with thresholds
  2/5/10/25/100/200/400 and increments 0.01/0.02/0.05/0.10/0.25/0.50/1.00/2.00.
  Limit execution does not use this market-slippage calculation. Fees are
  0.157% commission plus 7% VAT. The bridge derives fees from actual fill
  prices/quantities because transaction logs have no explicit fee columns.
- Multiple same-symbol lots can coexist in the simulator portfolio. That is
  implementation behavior, not competition permission: `ADD_TO_POSITION_RULE
  = UNCONFIRMED`.

The supplied example uses Market orders, conflicting with the repository's
Limit / Market-to-Limit IOC rule. Keep it as an official simulator smoke fixture
only; it is not a compliant strategy recommendation.

The bridge stores per-run metadata, strategy source/hash, tick file sizes and
hashes, archive identity, stdout/stderr, official raw outputs, and normalized
results in `artifacts/official_tradesim_runs/<run-id>/`. The comparison command
reports per-dimension results for signals, orders, fills, non-fills, prices,
fees, turnover, holdings, and returns. Missing inputs stay UNKNOWN; differences
are not attributed to a cause without evidence. No official run has been
produced because exact Python 3.13.0 is unavailable.

When raw fill rows and official fee constants are available, normalized
Round-Trips, Win Rate, and Expected Payoff are rebuilt from the independent FIFO
ledger and compared with TradeSim's summary values. Qualification uses the FIFO
count/payoff, includes a value/threshold/status/explanation for each criterion,
and records any simulator-summary mismatch as a warning.

## Organizer version update (2026-10-22)

TradeSim 0.2.6 is the organizer-designated competition simulator. The local
archive and side-by-side extraction are documented in
[TradeSim 0.2.6 final readiness](TRADESIM_026_READINESS.md). The existing 0.2.5
extraction remains at the compatibility path. Do not run either version until
`.venv-kgi313` is verified as exact Python 3.13.0. `--check` currently reports
`BLOCKED` because the launcher resolves 3.13.16, so 0.2.6 has not been promoted
to the active preferred runtime.

The 0.2.6 bridge schema 4 retains actual fill rows and normalizes order-level
requested/filled/canceled quantity, fill timestamps/prices, and final status
when the runner captures an EOD residual. The runner explicitly snapshots then
cancels remaining local simulator orders at day end; this does not carry orders
overnight and does not interact with a broker. Runtime behavior remains
unobserved until the exact interpreter is available.

## Current official dataset and runtime status (2026-10-22)

This section supersedes earlier statements in this guide that runtime execution or official historical data were unavailable. TradeSim 0.2.6 is the designated package; its exact Python 3.13.0 runtime, package requirements, and imports now pass `scripts/run_official_tradesim.py --check`. `Daily_Ticks.zip` has been preserved at the repository root and copied unchanged with its two nested ZIPs under `data/official/tradesim/archives/`. Extracted data are isolated under `data/official/tradesim/{history,ticks,daily_ticks}/`; the whole data tree is git-ignored.

The official tick archive contains 13 dates from 2026-10-01 through 2026-10-21 (48 symbols/date, 2,417,570 rows). History contains 492 files / 603,513 rows spanning 2023-09-21 through 2026-10-21. See the machine-readable inventories and cross-source comparison in `reports/tradesim_official_daily_ticks_package.json`, `reports/tradesim_official_history_inventory.json`, `reports/tradesim_official_tick_inventory.json`, and `reports/tradesim_vs_settrade_data_comparison.json`. The official loader preserves CSV order and repeated tick rows, adds an explicit sequence number and provenance, and treats source timestamps as naive Bangkok exchange time.

Run official data only when explicitly requested; there is no fallback to practice data:

```powershell
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --check
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --list-official-data
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --data-source official --date 2026-10-21 --strategy scripts\official_tradesim_smoke_strategy.py
```

Runtime smoke evidence includes one-day and multi-day no-order runs, a 200,000-share limit-order fixture that generated 87 actual fills, and an end-of-day cancellation fixture. These are simulator-only checks, not strategy performance claims. The packaged example strategy generated Market orders during an earlier exploratory simulator run; those outputs are retained as evidence, but that example is not competition-rule compliant and must not be used as a competition strategy. No brokerage order was placed.

Practice ticks cover Sep 9?30 and official ticks start Oct 1, so the archives extend rather than overlap; the 0.2.5 and 0.2.6 practice data remain intact. Ten standalone outer-archive daily CSVs are byte-identical to matching nested tick archive files. Tick files contain repeated exact rows and repeated symbol/timestamp values with no trade ID or sequence field; preserve them as supplied and do not deduplicate. Official history docs describe prices as corporate-action adjusted, while Settrade production adjustment status is unknown. Candle comparisons therefore remain diagnostic; neither source is used to fill the other's gaps.


For a new organizer package, place it at the root as `Daily_Ticks.zip`, then run:

```powershell
.\.venv\Scripts\python.exe scripts\ingest_official_daily_ticks.py
.\.venv\Scripts\python.exe scripts\compare_official_tradesim_sources.py
.\.venv\Scripts\python.exe scripts\run_official_tradesim.py --list-official-data
```

Ingestion is idempotent and refuses to overwrite conflicting extracted files. Refresh inventories and comparisons only from organizer-provided archives; review changed hashes and coverage before replay.

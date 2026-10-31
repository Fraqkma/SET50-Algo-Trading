# TradeSim 0.2.6 final readiness audit

Audit date: 2026-10-22 (Asia/Bangkok)  
Repository: `D:\GitHub\SET50-Algo-Trading`  
Branch / HEAD: `main` / `5c29ba0128155d50352ddd15a26cb0f9883d1627`

## Outcome

The organizer-designated simulator is TradeSim 0.2.6. Its local archive is intact
and extracted at `tools/kgi_tradesim/0.2.6`. Python 3.13.0 runtime validation is
BLOCKED: `py -0p` lists Python 3.13.16 and 3.14.7, and `py -3.13` resolves to
3.13.16. No `.venv-kgi313` exists. Do not run the official simulator under the
research environment or substitute 3.13.16. The report therefore leaves the
active preferred runtime unset until exact-version validation passes.

The pre-existing 0.2.5 extraction remains in its original unversioned
`tools/kgi_tradesim/` compatibility location. Its original ZIP is not present,
so the source comparison uses that preserved extraction as the baseline; the
baseline cannot be represented with an archive hash. The 0.2.6 archive and
source comparison are recorded in `reports/tradesim_version_comparison.json`.

## Archive and version evidence

| Field | Result |
|---|---|
| Archive | `tradeSim0.2.6.zip` |
| Absolute path | `D:\GitHub\SET50-Algo-Trading\tradeSim0.2.6.zip` |
| Size | 15,785,706 bytes |
| SHA-256 | `38e928e62190204d4f2edde4aa8ce2d324d08e99ba6caa2ffab30b94a568389a` |
| ZIP integrity | PASS (`testzip()` returned no corrupt member) |
| Members / top-level | 535; `TradingSimulation.ipynb`, `docs`, `marketInfo`, `requirements.txt`, `requirements-optional.txt`, `strategy`, `tradeSim` |
| Version evidence | Archive filename and complete `docs/CHANGELOG.md` section `0.2.6` |
| Extraction | `tools/kgi_tradesim/0.2.6` (side-by-side; no overwrite) |
| 0.2.5 retention | Existing extracted tree retained at `tools/kgi_tradesim/` |

There is no local `tradeSim0.2.5.zip`, `tradeSim_history.zip`, or
`tradeSim_ticks.zip`. The extraction contains the 0.2.5 practice ticks. The 0.2.6
archive includes 16 tick CSVs, dates 2026-09-09 through 2026-09-30, 48 symbols
per day, 0 invalid timestamp rows, 0 invalid market rows, and no out-of-universe
symbols. Tick CSVs are naive local market time; provenance is labeled as
`TRADESIM_0_2_6_PRACTICE`, with file paths and hashes in the inventory command.

## Source comparison

The extracted 0.2.5 source is a compatibility baseline, not the missing original
ZIP. The following package files differ in the source comparison:

- `tradeSim/Execution.py`
- `tradeSim/Order.py`
- `tradeSim/Portfolio.py`
- `tradeSim/Stock.py`
- `tradeSim/StrategyHandler.py`
- `tradeSim/Strategy_runner.py`
- `tradeSim/TradeSim.py`
- `tradeSim/TransactionLog.py`
- `docs/CHANGELOG.md` (added in 0.2.6)

Requirements are byte-identical between the preserved baseline extraction and
0.2.6: no additions, removals, or version changes. Strategy templates/examples,
notebook, fee constants, and summary-metric source are unchanged in the
comparison. Practice daily/intraday files differ because the archive data was
refreshed. `Execution.py` changes include limit matching and per-tick volume
caps; `TradeSim.py` and `StrategyHandler.py` track volume by symbol; `Order.py`
tracks remaining quantity/fill counts; portfolio/stock code combines fills for
the same buy order into one lot; transaction logging writes one row per fill.

## 0.2.6 matching semantics

The official changelog and extracted source agree on these behaviors:

- A resting buy limit fills only when a trade is below the limit; a resting sell
  fills only when a trade is above the limit. Touching the price does not fill.
- Each eligible fill is capped by that tick's volume, floored to a 100-share
  lot. Orders are processed in placement order and share the tick's available
  quantity. Quantity below one lot does not fill.
- A new limit that is immediately marketable retains its immediate matching
  behavior and price improvement, but its fill is also capped by tick volume.
- An order's unfilled remainder remains open intraday. At the close the remainder
  is canceled; filled shares remain in the portfolio. A fresh daily simulator
  starts with an empty order book, so pending orders do not carry overnight.
- A partial order logs one transaction row per fill under the same order number.
  `get_open_orders()` reports remaining quantity. One buy order's pieces make
  one portfolio lot and one round-trip when fully sold.
- `create_order_to_limit(volume, price, side, symbol)` keeps its four-argument
  signature; strategies that assume full immediate fills need retesting.
- Market-order source behavior and commission/VAT constants are unchanged.
  Commission is 0.157%, VAT is 7% of commission. Market execution uses the
  unchanged price-bucket slippage function; limits do not use market slippage.

Evidence is labeled `CHANGELOG DOCUMENTED` and `SOURCE IMPLEMENTED`; runtime
observation is still `NOT OBSERVED`. Same-symbol separate buy orders remain
separate lots in source. This is not evidence that the competition permits
adding to a position.

## Runtime and regression status

`scripts/run_official_tradesim.py --check` reports `BLOCKED` with
`MISSING_EXACT_VERSION`; imports and dependency checks are `NOT_CHECKED`. The
installed Python is x64 Python 3.13.16, not the required 3.13.0. Requirements
were not installed because the exact environment is unavailable. The existing
research `.venv` was not modified. No `.venv-kgi313` was created from a
different interpreter.

No one-day run, three-day run, resting-limit partial-fill fixture, EOD
cancellation simulation, market regression, immediate-limit regression, or
`create_order_to_limit` runtime comparison was executed. The source-level
fixtures and bridge were updated to record EOD residual cancellations and
multiple actual fills; FIFO and qualification consume fill rows only. These
claims still need runtime confirmation under exact Python 3.13.0.

Normalized result schema 4 represents per-fill IDs/timestamps/prices, requested,
filled, remaining and canceled quantities, final status, multiple fills per
order, pending/canceled orders, fees, NAV, positions, and raw artifact paths.
Where original requested volume cannot be recovered from fills or a captured
pending order, it remains null rather than being invented.

## Official history/tick workflow

The official `docs/get_historical_data.md` says `tradeSim_history.zip` contains
daily and intraday OHLCV plus the SET50 symbol list through the latest closed
trading day; it is refreshed weekday mornings. `tradeSim_ticks.zip` contains
market ticks for each weekday from 2026-10-01 through the latest closed day and
is refreshed on the same schedule. Both should be placed locally without
overwriting either the original version archive or another source. Do not use
Windows “Extract All” into the shared runtime path; inspect and validate first.

Run the read-only archive inventory:

```powershell
.\.venv\Scripts\python.exe scripts\inspect_official_tradesim_data.py
.\.venv\Scripts\python.exe scripts\inspect_official_tradesim_data.py --archive .\tradeSim_history.zip
.\.venv\Scripts\python.exe scripts\inspect_official_tradesim_data.py --extract-source-data
```

The inventory reports archive SHA-256, integrity, CSV paths, schemas, rows,
symbols, timestamp bounds, duplicate symbol/timestamp rows, per-file hashes,
and the timezone assumption. `--extract-source-data` extracts only `marketInfo/`
into a source-specific `data/raw/tradesim_official_history/<sha256>/` or
`data/raw/tradesim_official_ticks/<sha256>/` location; it refuses overwrite and
does not mix these files into `SETTRADE_PRODUCTION` datasets.

Current status is `OFFICIAL_HISTORY_ARCHIVE_NOT_PRESENT`; no missing data was
fabricated. The only available official practice source is
`TRADESIM_0_2_6_PRACTICE`.

Market-source labels and a non-persisting, duplicate-key-safe comparison helper
are available in `src/competition/data_sources.py`. Matching dates/symbols can
be compared across OHLCV values and timestamps; divergent and one-sided records
remain separate in the result. The helper never writes or overwrites a dataset.

For each weekday archive refresh: place the organizer ZIP in the workspace;
run the inspector to discover/hash it; validate ZIP and CSV schemas; inventory
dates, symbols, rows, timestamp bounds, duplicates, and hashes; extract only
`marketInfo/` to the archive-hash-keyed, source-specific path if desired; record
its latest date; then run market-data quality checks. Keep prior hash paths and
all `SETTRADE_PRODUCTION` files separate.

## Results page and bridge

The Streamlit destination is explicitly titled “OFFICIAL TRADESIM 0.2.6 ·
Results” and shows the archive hash, extraction path, runtime readiness, adapter
status, tick inventory, run version, fill/partial-fill counts, fees, NAV, order
residuals, fills, warnings, and raw artifact location. Saved-run details appear
when a saved run exists. Seven older retained artifacts identify TradeSim 0.2.3
in their metadata; they remain labeled with that version and are not reclassified.
No 0.2.6 run artifact exists because runtime validation is blocked. The page
remains read-only and does not start simulations.

Version comparison and operational records:

- `reports/tradesim_version_comparison.json`
- `reports/tradesim_026_final_readiness.json`
- `artifacts/official_tradesim_runs/<run-id>/` (created by a future run)

## Commands after exact Python 3.13.0 is available

Install/register the exact interpreter first; do not use the research `.venv` or
assume `py -3.13` is exact (currently it resolves to 3.13.16). Use the absolute
executable path printed by a verified Python 3.13.0 interpreter:

```powershell
py -0p
$python3130 = 'C:\Path\To\Verified\Python3130\python.exe'
& $python3130 -c "import sys; print(sys.executable); print(sys.version)"
& $python3130 -m venv .venv-kgi313
.\.venv-kgi313\Scripts\python.exe -m pip install -r .\tools\kgi_tradesim\0.2.6\requirements.txt
.\.venv-kgi313\Scripts\python.exe scripts\run_official_tradesim.py --check
.\.venv-kgi313\Scripts\python.exe scripts\run_official_tradesim.py --list-dates
.\.venv-kgi313\Scripts\python.exe scripts\run_official_tradesim.py --date 2026-09-09
.\.venv-kgi313\Scripts\python.exe scripts\run_official_tradesim.py --date 2026-09-09 --date 2026-09-10 --date 2026-09-11
```

The first two smoke commands use the official example strategy only as an engine
smoke fixture. Its market orders conflict with the competition rules in
`AGENTS.md`; do not treat it as a compliant strategy. Runtime checks must also
cover immediate/resting limit behavior, partial fills and EOD cancellation,
market fills, FIFO lots, qualification metrics, and the competition's permitted
order types. Resolve the rule mismatch with organizer documentation before any
strategy validation that assumes Market-to-Limit/IOC is available.

## Readiness decision

- TradeSim 0.2.6 fully ready for strategy validation: **NO** (exact runtime and
  runtime regressions remain unverified).
- Decision Support + Competition State Machine ready to proceed with
  simulator-coupled implementation: **NO** until exact runtime and order-rule
  semantics are verified. Contract/design work can proceed without choosing a
  strategy.
- Final strategy selected or optimized: **NO**.
- Data fabricated: **NO**.
- Real orders placed: **0**.
- Commit or push: **NO**.
- Separate official KGI submission repository accessed: **NO**.

## Superseding verification update (2026-10-22)

The earlier `BLOCKED` runtime assessment and statements that official history/tick archives were absent are superseded. Python 3.13.0 is installed at the side-by-side runtime path, `.venv-kgi313` has been provisioned from it with the official 0.2.6 requirements, and `scripts/run_official_tradesim.py --check` reports READY. Official data have been extracted into `data/official/tradesim/` with archive hashes and inventories. The comparison report covers practice dates and Settrade 1m/5m/15m; daily Settrade comparison is unavailable because no comparable production daily series was present.

One-day and multi-day official-data smoke runs succeeded; partial fills and end-of-day cancellation were also observed using isolated simulator fixtures. This validates the bridge/runtime path, not strategy profitability or full compliance of the package example strategy. Official tick duplicate rows remain untouched. The original archives are unchanged.

Current commands: `scripts/run_official_tradesim.py --check`, `--list-official-data`, and explicit `--data-source official`. See the current status and source-selection details in [the integration guide](OFFICIAL_TRADESIM_INTEGRATION.md).


## TradeSim 0.2.7 migration update (2026-10-28)

TradeSim 0.2.7 is the validated preferred competition simulator; 0.2.6 is deprecated for scoring and retained for historical reproduction. See [0.2.7 readiness](TRADESIM_027_READINESS.md) and `reports/tradesim_027_execution_semantics.json`. Runtime evidence covers IOC matching, volume caps, cancellations, fees, auctions, valid ticks, tick-table transition, FIFO and one-/multi-day smoke runs.

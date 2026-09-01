# AGENTS.md

## Project: SET50 Algo Trading Competition

This repository contains a Python-only algorithmic trading system for a SET50 stock
trading competition.

The primary goals are:
1. Select eligible SET50 stocks using systematic, reproducible rules.
2. Generate buy/sell signals.
3. Manage a long-only portfolio under the competition constraints.
4. Backtest strategies realistically.
5. Produce orders that comply with the competition's allowed order types and costs.
6. Keep research, backtesting, portfolio/risk logic, and execution logic separated.

---

# 1. Competition Rules — NON-NEGOTIABLE

The following rules come from the official competition briefing supplied by the team.
Treat them as hard constraints. Never write code that intentionally violates them.

## 1.1 Universe

- The tradable universe is stocks in the SET50 index.
- Stock-selection logic must only select eligible SET50 stocks.
- Do not introduce assets outside the permitted SET50 universe.
- The system should make the eligible universe explicit rather than hiding it inside
  strategy code.

## 1.2 Programming Language

- Trading strategies must be written in Python only.
- Target Python version: Python 3.13 or newer.
- Keep production/trading logic in `.py` files.
- Jupyter notebooks may be used for research, exploration, visualization, and
  analysis, but the actual trading strategy must remain reproducible as Python
  source code.

## 1.3 Starting Capital

- Initial cash balance: THB 10,000,000.
- No additional capital may be added during the competition.
- The system must never create money artificially.
- Selling a position returns cash to the portfolio; this is normal portfolio activity
  and is not considered adding capital.
- Never allow cash or equity to become positive through an accounting bug.
- Portfolio accounting must maintain a clear distinction between:
  - cash
  - market value of holdings
  - realized P&L
  - unrealized P&L
  - fees
  - total equity

## 1.4 Long-Only

- Short selling is prohibited.
- Never generate an order that sells more shares than are currently held.
- A sell signal for an empty position must result in no order.
- Position quantity must never become negative.
- Borrowing/leverage must not be introduced unless the competition rules explicitly
  allow it.

## 1.5 Minimum Stock Coverage

- By the end of the competition, the strategy must have traded at least 5 distinct
  stock names.
- Track the number of unique stock symbols actually traded.
- This is different from the number of orders or number of trades.
- The system should expose a metric such as `unique_symbols_traded`.
- Backtests should report whether this requirement is satisfied.

## 1.6 Allowed Order Types

Only these order types are permitted:

- Limit Order
- Market-to-Limit Order with IOC (Immediate-Or-Cancel) validity

Do not introduce:
- Market orders
- Stop orders
- Stop-limit orders
- GTC orders
- Other order types

unless the competition organizer explicitly changes the rules.

The execution layer must represent order type and validity explicitly.

## 1.7 Commission and VAT

Every buy/sell transaction must account for:

- Commission: 0.157% of order value.
- VAT: 7% of the commission.
- No minimum commission fee.

The effective combined charge is:

`0.157% × 1.07 = 0.16799%`

Do not silently apply the fee twice.

Keep commission and VAT as separate fields in the transaction record so the
calculation can be audited.

Example conceptual calculation:

```text
order_value = executed_price * quantity

commission = order_value * 0.00157
vat = commission * 0.07
total_fees = commission + vat

buy_cash_change = order_value + total_fees
sell_cash_change = order_value - total_fees
```

The exact execution-price and fill rules belong in the execution/backtest layer.

## 1.8 Slippage

- Assume slippage of 1 tick size.
- Slippage must be applied consistently in the backtest/execution model.
- Do not use an arbitrary fixed THB percentage as a substitute for tick slippage.
- Tick size must be represented explicitly and should be derived according to the
  applicable SET price/tick-size rule for the stock price.
- The strategy itself should not secretly change the slippage assumption.

Keep the following concepts separate:

```text
signal price
requested order price
simulated execution price
slippage
```

---

# 2. Required Architecture

Use a layered architecture. Do not put all trading logic into `main.py`.

Recommended structure:

```text
SET50-Algo-Trading/
│
├── AGENTS.md
├── README.md
├── requirements.txt
├── .gitignore
├── .env.example
│
├── config/
│   ├── config.yaml
│   └── trading_hours.yaml
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── features/
│
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_feature_analysis.ipynb
│   ├── 03_strategy_research.ipynb
│   └── 04_backtest_analysis.ipynb
│
├── src/
│   ├── __init__.py
│   │
│   ├── data/
│   │   ├── __init__.py
│   │   ├── loader.py
│   │   ├── cleaner.py
│   │   └── features.py
│   │
│   ├── strategies/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── baseline.py
│   │   └── ensemble.py
│   │
│   ├── backtest/
│   │   ├── __init__.py
│   │   ├── engine.py
│   │   ├── metrics.py
│   │   └── transaction_cost.py
│   │
│   ├── risk/
│   │   ├── __init__.py
│   │   ├── position_sizing.py
│   │   ├── risk_manager.py
│   │   └── limits.py
│   │
│   ├── execution/
│   │   ├── __init__.py
│   │   ├── broker.py
│   │   ├── order_manager.py
│   │   └── paper_trader.py
│   │
│   └── utils/
│       ├── __init__.py
│       ├── logger.py
│       └── time.py
│
├── tests/
│   ├── test_data.py
│   ├── test_strategy.py
│   ├── test_backtest.py
│   ├── test_risk.py
│   └── test_execution.py
│
├── results/
│   ├── backtests/
│   ├── reports/
│   └── figures/
│
└── main.py
```

The initial implementation should create the structure and interfaces first.
Do not prematurely implement a sophisticated strategy.

---

# 3. Responsibilities of Each Layer

## `src/data/`

Responsible for:

- Loading market data.
- Validating columns and timestamps.
- Cleaning malformed data.
- Handling missing values explicitly.
- Creating reusable features.
- Providing a consistent DataFrame/data model to strategies.

Data code must not place orders.

## `src/strategies/`

Responsible for:

- Stock selection.
- Signal generation.
- Strategy parameters.
- Strategy-specific calculations.

A strategy should answer:

```text
Which stocks should be traded?
What signal does each stock currently have?
```

A strategy should NOT directly manipulate cash or send broker orders.

Use an abstract base class where appropriate.

Example conceptual interface:

```python
class Strategy(ABC):
    @abstractmethod
    def generate_signal(self, data):
        ...
```

## `src/backtest/`

Responsible for:

- Historical simulation.
- Portfolio/equity calculation.
- Order simulation.
- Transaction costs.
- Slippage.
- Performance metrics.
- Trade logs.

Backtests must be event/time ordered.

Never use future information to determine an earlier trade.

## `src/risk/`

Responsible for:

- Position sizing.
- Maximum position limits.
- Portfolio exposure.
- Cash checks.
- Drawdown controls.
- Daily loss controls if required by the strategy.
- Validating that an order is safe before execution.

Risk management is a hard gate before an order reaches execution.

Example flow:

```text
Signal
  ↓
Position Sizing
  ↓
Risk Checks
  ↓
Order Validation
  ↓
Execution
```

## `src/execution/`

Responsible for:

- Creating valid competition orders.
- Enforcing allowed order types.
- Enforcing IOC validity where required.
- Checking available cash.
- Checking available holdings before selling.
- Translating approved orders into the competition API/interface.
- Recording order status and fills.

Execution code must never invent fills.

## `src/utils/`

Reusable infrastructure only:

- Logging.
- Time/date helpers.
- Common validation.
- Configuration helpers.

---

# 4. Portfolio Accounting Rules

The portfolio engine must be deterministic and auditable.

Track at minimum:

```text
cash
positions
average_cost
market_value
realized_pnl
unrealized_pnl
commission
vat
total_fees
equity
```

For each transaction, record:

```text
timestamp
symbol
side
quantity
requested_price
executed_price
order_type
validity
order_value
commission
vat
total_fees
slippage
```

Never use floating-point arithmetic carelessly for money.

Where practical:
- use integer quantities for shares;
- use Decimal or carefully controlled numeric handling for monetary values;
- round only at clearly defined financial boundaries.

---

# 5. Strategy and Backtest Integrity

## No Lookahead Bias

A strategy must never use information that would not have been known at the
time of the decision.

Examples of prohibited behavior:

- Using today's closing price to place an order that supposedly occurred before
  today's close.
- Using future returns to create a feature.
- Normalizing the complete dataset before a historical walk-forward test.
- Using future portfolio information to determine a past position size.

Always make the decision timestamp and execution timestamp explicit.

## No Data Leakage

Feature generation, scaling, model fitting, and parameter selection must respect
the chronological order of the data.

If machine learning is introduced later:

```text
Train → Validate → Test
```

must remain strictly time ordered.

## Avoid Survivorship Bias

When historical SET50 membership is available, use the historical constituent
universe appropriate for each date rather than blindly using today's SET50 members
for old periods.

If historical membership data is not available, document that limitation instead
of pretending the backtest is unbiased.

## Out-of-Sample Testing

Do not judge a strategy only on the data used to tune it.

Prefer:

```text
Train
  ↓
Validation
  ↓
Out-of-Sample Test
  ↓
Final evaluation
```

For time-series strategies, walk-forward evaluation is preferred.

---

# 6. Performance Metrics

Do not optimize only for raw profit.

The backtest/reporting layer should support metrics such as:

- Total Return
- Final Equity
- Annualized Return
- Volatility
- Sharpe Ratio
- Sortino Ratio
- Maximum Drawdown
- Calmar Ratio
- Win Rate
- Profit Factor
- Average Trade P&L
- Number of Trades
- Turnover
- Total Commission
- Total VAT
- Total Fees
- Unique Symbols Traded

Always show:

```text
Gross P&L
Fees
Net P&L
```

A strategy is not considered successful merely because gross P&L is positive.

---

# 7. Stock Selection

Stock selection is one of the required competition presentation topics.

Keep stock-selection logic modular so the team can test factors such as:

- Momentum
- Relative strength
- Volume/liquidity
- Volatility
- Trend
- Mean reversion
- Fundamental factors, if permitted by the available data
- Market regime
- Cross-sectional ranking

Do not hard-code a final factor model before testing it.

Every factor should have:
- clear definition;
- data source;
- calculation timestamp;
- parameter/configuration;
- test result.

---

# 8. Portfolio Management

Portfolio management is separate from stock selection.

Stock selection answers:

```text
What should we own?
```

Portfolio management answers:

```text
How much should we own?
When should we rebalance?
How much cash should remain?
How should capital be distributed?
```

Do not let a single signal blindly spend all available capital.

Portfolio allocation must respect:
- available cash;
- current positions;
- position limits;
- order quantity;
- transaction costs;
- slippage;
- long-only constraint.

---

# 9. Risk Management

Risk management is a required competition presentation topic.

At minimum, design the system so it can support:

- Maximum position size
- Maximum portfolio exposure
- Cash reserve
- Maximum loss per trade
- Maximum daily loss
- Drawdown protection
- Volatility-aware position sizing
- Concentration limits

Risk controls must be implemented as enforceable checks, not just comments.

A rejected order should be logged with the reason.

Example:

```text
REJECTED:
symbol=ABC
reason=insufficient_cash
```

---

# 10. Configuration

Do not hard-code competition constants throughout the source code.

Use configuration for:

```yaml
initial_capital: 10000000

fees:
  commission_rate: 0.00157
  vat_rate: 0.07

execution:
  slippage_ticks: 1
  allowed_order_types:
    - LIMIT
    - MARKET_TO_LIMIT
  validity:
    - IOC

constraints:
  long_only: true
  minimum_unique_symbols: 5
```

The source code should read these values from configuration.

Do not silently change official competition parameters.

---

# 11. Dependencies

Prefer a small, justified dependency set.

Recommended baseline:

- numpy
- pandas
- scipy
- statsmodels
- scikit-learn
- numba
- matplotlib
- plotly
- pyyaml
- python-dotenv
- pydantic
- pytest
- jupyter

A backtesting framework such as vectorbt may be added if useful, but the project
must not become dependent on a framework's hidden assumptions about fills,
slippage, commissions, or portfolio accounting.

When adding a package:
1. Confirm it is actually needed.
2. Add it to `requirements.txt`.
3. Document its purpose.
4. Avoid adding large libraries for functionality that is trivial to implement.

---

# 12. Environment and Secrets

Never commit:

```text
.env
API keys
access tokens
passwords
private credentials
personal account information
```

Use:

```text
.env.example
```

for variable names only.

Example:

```text
API_KEY=
API_SECRET=
```

The real `.env` must remain ignored by Git.

---

# 13. Logging

Use structured logging rather than scattered `print()` statements.

Logs should make it possible to understand:

```text
signal generated
→ order created
→ risk check
→ order submitted
→ fill/rejection
→ portfolio updated
```

Never log secrets.

---

# 14. Testing Requirements

Before a strategy is considered usable, test:

### Data
- Missing data
- Duplicate timestamps
- Invalid prices
- Invalid quantities

### Portfolio
- Buy
- Sell
- Full liquidation
- Partial liquidation
- Insufficient cash
- Attempted short sell

### Fees
- Commission
- VAT
- Total fees

### Execution
- Limit order
- Market-to-limit IOC
- Slippage
- Invalid order type
- Invalid order quantity

### Risk
- Position limit
- Exposure limit
- Cash limit
- Drawdown/loss limit

### Strategy
- Signal correctness
- No lookahead
- Empty data
- Missing feature values

Tests should be deterministic.

---

# 15. Coding Style

- Use Python 3.13+.
- Follow PEP 8.
- Use type hints for public functions and important data structures.
- Prefer small functions with one responsibility.
- Avoid global mutable state.
- Avoid magic numbers.
- Use descriptive variable/function names.
- Add docstrings to important public classes/functions.
- Keep business logic separate from I/O.
- Do not put API calls directly inside strategy classes.
- Do not put plotting code inside trading/execution code.
- Do not duplicate fee/risk calculations across modules.

---

# 16. Git Rules

Use small, meaningful commits.

Recommended commit examples:

```text
feat: add market data loader
feat: add baseline momentum strategy
feat: add portfolio accounting
feat: add risk checks
feat: add execution order model
test: add commission calculation tests
test: add long-only portfolio tests
refactor: separate strategy from execution
docs: update backtest methodology
```

Never commit:
- `.env`
- credentials
- huge raw datasets unless explicitly required
- generated cache files
- `__pycache__`
- `.venv`

---

# 17. Initial Development Order

Do NOT begin by building a complicated AI/ML strategy.

Implement in this order:

1. Repository structure
2. Configuration
3. Data model/loading
4. Portfolio/accounting model
5. Transaction cost model
6. Execution/order model
7. Risk checks
8. Backtest engine
9. Performance metrics
10. Simple baseline strategy
11. Tests
12. Walk-forward evaluation
13. More advanced strategies
14. ML/ensemble only if justified by out-of-sample results

The baseline must be reproducible before adding complexity.

---

# 18. Definition of Done

A feature is not complete merely because it runs.

It should have:

- clear responsibility;
- type-safe/reasonable interfaces;
- tests where appropriate;
- no hidden competition-rule violations;
- deterministic behavior where possible;
- logging for important state transitions;
- documentation when assumptions matter.

The system should always be able to answer:

```text
Why did we buy this stock?
Why did we sell it?
How many shares did we trade?
At what price?
What fees were charged?
What slippage was applied?
How much cash remained?
What risk check allowed/rejected the order?
```

---

# 19. Priority Rule

When there is a conflict between:
1. strategy performance,
2. code convenience,
3. competition rules,

the competition rules always win.

Never "optimize" by changing the rules.

When a requirement is ambiguous, isolate the assumption in configuration or a
clearly documented module rather than silently making it part of the strategy.

---

# 20. Important Presentation Topics

The competition requires the team to explain:

### Stock Selection
- What factors are used to choose stocks?
- Why are those factors expected to work?
- How were they tested?

### Portfolio Management
- How capital is allocated.
- How positions are rebalanced.
- Why the portfolio is diversified or concentrated.

### Risk Management
- Position limits.
- Exposure control.
- Drawdown/loss protection.
- Transaction-cost awareness.
- Why the strategy remains robust under adverse conditions.

The implementation should make these concepts visible and measurable so that the
final presentation can be backed by actual results.

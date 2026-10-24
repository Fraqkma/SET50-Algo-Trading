# SET50 Research Foundation: Phase 2 Market Microstructure

**Status:** Research-only foundation
**Date:** 2026-09-22
**Scope:** SET/SET50 order interaction, execution, liquidity, and transaction-cost concepts

This document explains market-microstructure concepts needed before feature,
signal, strategy, or backtest work. It does not change production behavior, define
a trading strategy, create a signal, estimate a fill model, or claim profitability.

## 1. Research question and boundary

The research question is:

> What market-microstructure concepts must be understood to simulate execution and
> transaction cost for a long-only SET50 system without unrealistic assumptions?

Project constraints used as context:

- SET/SET50 universe.
- Initial capital: THB 10,000,000.
- No additional capital.
- Long-only; no short selling.
- Minimum five distinct symbols.
- Allowed order types: Limit and Market-to-Limit IOC, as specified by the project.
- Commission: 0.157%.
- VAT: 7% of commission.
- Slippage: one tick.

These are supplied project constraints. They are not empirical measurements of
SET50 execution.

The previous project observations of approximately THB 4.7M in slippage and THB
1.2M in transaction costs are treated only as **historical project observations**.
They are motivation for studying execution. They are not evidence that SET50
normally has costs of those amounts, and this document does not infer their cause.

## 2. Official SET market-model evidence

The official SET materials describe a centralized automatic order-matching process
that uses price-then-time priority. SET's trading-method description says orders are
queued and arranged by the best price and then time; its English description also
states that the system continuously matches the first buy and sell orders in the
queue. [SET trading methods](https://www.set.or.th/en/market/information/trading-procedure/trading-methods)

SET's order-type documentation states that a limit order specifies a price, a market
order seeks the best available price and may match across price levels, and a
market-to-limit order initially executes only at the current best market price. It
also states how unmatched quantity is handled. [SET order types](https://www.set.or.th/en/market/information/trading-procedure/order-types)

SET's published research material describes a centralized limit order book, price-
then-time matching, visible best bid/offer and depth information, and continuous
matching. [SET-CMRI working paper](https://media.set.or.th/common/research/630.pdf)

These sources describe market rules and mechanisms. They do not provide the actual
historical order-book path, queue position, or fill probability for a particular
project order.

## 3. Bid

The **bid** is a displayed buy interest: the price and quantity a participant is
willing to buy under the order's conditions. The highest displayed bid is the best
bid.

Example for an eligible SET50 stock:

```text
Best bid: 100.50 THB for 8,000 shares
```

A sell order that is executable against this level may trade at 100.50, subject to
the order type, queue, available quantity, and venue rules. A long-only portfolio
selling a held position usually interacts with bids; a buy order does not execute at
the bid merely because the bid is visible.

## 4. Ask

The **ask**, or offer, is displayed sell interest: the price and quantity a
participant is willing to sell under the order's conditions. The lowest displayed
ask is the best ask.

Example:

```text
Best ask: 100.75 THB for 5,000 shares
```

A buy order that is executable against this level may trade at 100.75, subject to
available quantity and priority. A long-only portfolio buying shares normally
crosses the ask, while selling normally reaches the bid.

## 5. Bid-ask spread

For a displayed best bid and ask:

```text
spread_abs = ask - bid
spread_pct = (ask - bid) / reference_price
```

If the best bid is 100.50 and best ask is 100.75:

```text
absolute spread = 0.25 THB
```

The spread is an implicit execution cost when an investor crosses from one side of
the market to the other. It is not the same as commission and is not automatically
visible in daily OHLCV.

- **Tight spread:** usually lower price concession for a small executable order.
- **Wide spread:** larger crossing cost and greater uncertainty around a fair or
  mid-market price.
- **Liquid-looking stock:** may have a tighter spread and more displayed depth, but
  this must be measured rather than assumed from its SET50 label.
- **Illiquid-looking stock:** may have sparse depth, wider spread, and larger price
  movement for a given order size.

For a long-only strategy, buys commonly pay the ask and sells commonly receive the
bid. Repeated turnover can therefore pay the spread repeatedly even when the daily
close appears unchanged.

## 6. Order book and market depth

An order book is the set of queued buy and sell orders organized by price. A simple
illustration is:

```text
ASK / offers
101.00       5,000 shares
100.90       3,000 shares
100.80       2,000 shares

---------------------------

100.70       4,000 shares
100.60       6,000 shares
100.50       8,000 shares
BID / buys
```

For a buy order:

1. An aggressive order may interact with the lowest ask first.
2. If its quantity exceeds the displayed quantity at that level, it may continue to
   another price level only if the order type permits it.
3. A passive limit order may join the bid/ask queue and wait for an opposite order.
4. Its result depends on price priority, time priority, cancellations, new orders,
   pauses, and the available opposite-side quantity.

**Depth is not daily volume.** Visible order-book depth is quantity currently
displayed at price levels; daily volume is quantity traded over a completed period.
Available liquidity is the quantity that can actually execute under a specified
order and time constraint. Executable liquidity can be less than displayed depth.

## 7. Market order

A market order specifies quantity but not a limit price. SET describes it as an
order to buy or sell at the best available price. SET also states that it can match
at more than one price level and that unmatched quantity is automatically cancelled.

Properties:

- Usually higher fill probability than a non-marketable limit order when opposing
  liquidity exists.
- Price uncertainty: the eventual price is not fixed by the order itself.
- Slippage risk rises when the book is thin, volatile, or smaller than the order.
- A sufficiently large order can consume multiple ask or bid levels and create
  market impact.
- It is different from the project's explicit Market-to-Limit order.

Daily OHLCV cannot reveal which price levels a historical market order consumed.
Any daily backtest using a single close as a market-order fill is an execution
assumption, not an observed order-book fact.

## 8. Limit order

A limit order specifies both quantity and a price constraint.

- Buy limit: execute only at the limit price or better.
- Sell limit: execute only at the limit price or better for the seller.
- The price constraint reduces price uncertainty but does not guarantee a fill.
- A non-marketable limit can wait in the queue, be partially filled, or expire/cancel.

Example:

```text
Current best ask = 100.00
Buy limit        = 99.50
```

Possible outcomes include:

1. No fill: price never reaches 99.50 or available sellers do not reach the order.
2. Partial fill: some quantity trades at 99.50, with the remainder waiting or
   cancelling according to the validity condition.
3. Full fill: enough sell interest reaches the order and the order's time in force
   allows it to remain active.
4. The order is cancelled, rejected, or expires before a fill.

The project must not treat “submitted” as “filled.” A future execution model must
represent order status, filled quantity, remaining quantity, and cancellation.

## 9. IOC / FAK condition

IOC means **Immediate-Or-Cancel**: attempt to match immediately; cancel any
unmatched remainder. In SET's newer trading-system terminology, the condition was
renamed from IOC to **Fill and Kill (FAK)**. The official SET criteria document
states that FAK/IOC matches immediately and cancels any quantity left unmatched.
[SET revised trading criteria](https://media.set.or.th/set/Documents/2023/Jan/revised_trading_criteria_SET_EN.pdf)

For this project, “IOC” should be retained as the project vocabulary unless the
broker/venue interface specifies the current label `FAK`. The implementation must
verify the actual interface rather than assume that every venue uses the same name.

IOC/FAK is not Good-Till-Cancelled:

```text
Order arrives -> immediate matching attempt -> filled quantity kept
                                      -> unmatched quantity cancelled
```

Partial fill is allowed under IOC/FAK: the matched part remains executed and the
unmatched remainder is cancelled. If no quantity can match immediately, the entire
order is cancelled.

## 10. Market-to-Limit IOC

SET defines Market-to-Limit as an order with no specified price that is allowed to
execute only at the current best market price: the lowest offer for a buy or highest
bid for a sell. If quantity remains unmatched, SET describes it as being converted
to a limit order at the last executed price. [SET order types](https://www.set.or.th/en/market/information/trading-procedure/order-types)

The official criteria also state that Market-to-Limit can be combined with FAK
(the current name for IOC). [SET revised trading criteria](https://media.set.or.th/set/Documents/2023/Jan/revised_trading_criteria_SET_EN.pdf)

For the project's `Market-to-Limit IOC` label, the conceptual sequence is:

1. Submit a Market-to-Limit order with quantity and side, but no user limit price.
2. It attempts to execute at the current best opposing price level only.
3. Any quantity that cannot execute is subject to the IOC/FAK condition and is
   cancelled immediately. Without IOC/FAK, the remainder would be converted to a
   limit order at the last executed price under SET's rule.
4. The result can be full fill, partial fill plus cancellation, or no fill.

This is different from a plain market order because a market order may match across
multiple price levels, while Market-to-Limit is restricted to the best current
level. It is different from a plain limit order because the investor does not set
the initial limit price; the first executable price is taken from the current best
opposite side.

### Important venue-version boundary

The project brief uses “Market-to-Limit IOC,” while current SET materials use FAK
for the renamed IOC condition. Exact broker or Settrade request fields, rejection
rules, and acknowledgement semantics must be verified against the applicable
interface specification before any execution code is changed. This document does
not infer those fields.

## 11. Queue priority

SET's automatic matching uses price-then-time priority:

1. Better price has priority.
2. At the same price, earlier accepted order time has priority.

Example:

```text
Bid 100.00
Existing queued orders: 10,000 shares
Our new order:           2,000 shares
Incoming seller:         5,000 shares
```

Under price-time priority, the existing 10,000 shares are ahead of the new order.
The incoming 5,000 shares may be consumed by orders ahead of ours, leaving our
order with no fill. The exact result depends on the full queue and any intervening
cancellations or executions.

Displayed depth does not disclose our exact queue position unless order-level data
and order-entry timestamps are available.

## 12. Partial fill

If an order is 10,000 shares and only 3,000 shares are executable under its price,
side, queue, and validity conditions:

```text
requested quantity = 10,000
filled quantity    =  3,000
remaining quantity =  7,000
```

The accounting consequences are:

- Position changes by 3,000 shares, not 10,000.
- Cash changes by the executed value plus applicable buy fees, not the requested
  notional.
- The remaining 7,000 shares are either cancelled, remain queued, or become a
  limit remainder according to order type and validity.
- IOC/FAK cancels the 7,000-share remainder immediately.
- Commission and VAT apply to executed value under the project cost rule; no fill
  means no executed notional for that order.

An execution record must therefore preserve requested quantity and filled quantity
as separate fields.

## 13. Fill probability

Fill probability is the probability that a submitted order executes under a stated
time window and order condition. It is not determined by the daily close alone.

Relevant factors include:

- distance between limit price and current bid/ask;
- spread and price level;
- queue position and order-entry time;
- displayed and hidden opposing liquidity;
- order size relative to available liquidity;
- volatility and price movement;
- time available before expiry or cancellation;
- trading activity, pauses, and venue rules.

This document does not propose a numerical fill-probability model. Without order,
quote, and trade data, a numerical probability would be an unsupported assumption.

## 14. Liquidity

Liquidity is multi-dimensional. It can involve:

- trading volume;
- traded value and turnover;
- bid-ask spread;
- visible depth at multiple levels;
- replenishment and cancellation activity;
- price impact for a specified order size;
- ability to execute within a time constraint.

Volume alone is insufficient. A stock can show high daily volume but have a wide
spread or thin depth at the moment of the order. Conversely, visible depth can be
large while actual executable liquidity changes rapidly.

For SET50 research, liquidity measures must be time-aligned and should not use a
full-day volume value to justify a fill that supposedly occurred before the day
ended.

## 15. Market impact

Market impact is the price movement or price concession caused by our own order's
interaction with available liquidity.

- **Temporary impact:** price concession associated with executing now and potentially
  reversing as liquidity replenishes.
- **Permanent impact:** longer-lasting information or imbalance effect associated
  with the order or market response.

Impact generally depends on order size, depth, spread, volatility, participation
rate, and market conditions. The project must not create a quantitative impact
model without supporting order-book/trade evidence. A one-tick slippage setting is a
project assumption, not proof that every order has one tick of impact.

## 16. Slippage

Slippage is the difference between a declared reference/expected price and the
actual executed price. The sign convention must be declared.

For a buy, using expected price as the benchmark:

```text
expected buy price = 100.00
actual buy price   = 100.20
buy slippage       = +0.20 THB adverse
```

For a sell, receiving less than the benchmark is adverse. Positive/negative labels
must therefore identify both side and convention; otherwise a “positive slippage”
number is ambiguous.

The project rule of **one tick slippage** is an execution assumption/constraint. It
must be interpreted using the applicable SET tick size at the relevant price level;
it is not evidence that all SET50 orders experience exactly one tick.

Slippage is distinct from commission:

- Commission is an explicit fee calculated from executed order value.
- Slippage is an execution-price difference relative to a benchmark.

## 17. Transaction cost decomposition

```text
Transaction Cost
├── Commission                  explicit
├── VAT on commission           explicit
├── Bid-ask spread              implicit
├── Slippage                    implicit / execution assumption
├── Market impact               implicit
└── Other applicable fees       only if sourced and applicable
```

Explicit costs are directly charged or specified. Implicit costs arise from the
execution path or opportunity lost when an order does not execute. Spread, slippage,
and impact must not be silently folded into commission.

Do not add exchange, broker, tax, borrowing, or other charges unless the applicable
competition or broker source explicitly requires them. This project is long-only,
so borrow cost is not a default cost component.

### Project commission example

For a THB 1,000,000 executed trade:

```text
commission = 1,000,000 × 0.00157 = 1,570.00 THB
VAT        = 1,570.00 × 0.07    =   109.90 THB
explicit total                  = 1,679.90 THB
```

This excludes spread, slippage, market impact, and any other fee not specified by
the project. It does not change the project commission constraint.

## 18. Tick size and trading units

SET publishes price-dependent minimum movements for securities. The current SET
price-band/tick-size page lists the following schedule for ordinary securities:

| Market price level (THB) | Tick size (THB) |
|---:|---:|
| Less than 2 | 0.01 |
| 2 to less than 5 | 0.02 |
| 5 to less than 10 | 0.05 |
| 10 to less than 25 | 0.10 |
| 25 to less than 100 | 0.25 |
| 100 to less than 200 | 0.50 |
| 200 to less than 400 | 1.00 |
| 400 and above | 2.00 |

Source: [SET price bands and tick sizes](https://www.set.or.th/en/market/information/trading-procedure/price-bands-and-tick-sizes), accessed 2026-09-22.

The applicable tick must be determined at the relevant price and date. A fixed
THB amount is not a valid substitute for “one tick” across all SET50 securities.
Rules may change, so a production or execution implementation must verify the
effective schedule before use.

Trading quantity also has a unit rule. SET states that a board lot is generally 100
shares, while a security priced at THB 500 or more for six consecutive months can
have a 50-share board lot. [SET trading units](https://www.set.or.th/en/market/information/trading-procedure/trading-units)

This matters for order quantity validation and for interpreting partial fills. It
does not imply that every historical security used the same lot rule at every date.

## 19. VWAP

Volume Weighted Average Price is:

```text
VWAP = sum(price × volume) / sum(volume)
```

VWAP can be used as an execution benchmark when the relevant intraday trade prices
and volumes are available. It differs from the daily close because it reflects the
volume-weighted path of executed trades, not just the final reported price.

With only daily OHLCV, exact intraday VWAP is unavailable. A typical-price proxy or
other estimate would be an assumption and must be labelled as such. Daily volume
does not tell us how volume was distributed across prices or time.

## 20. Daily OHLCV limitations

Daily OHLCV provides:

```text
Open, High, Low, Close, Volume
```

It does not directly provide:

- bid and ask at the decision time;
- spread;
- order-book depth by price level;
- queue position;
- whether our order filled and when;
- partial-fill quantity;
- cancellations and replenishment;
- the intraday execution path;
- exact VWAP without intraday trades.

The research record must separate:

```text
Observed data       = what the source actually reports
Execution assumption = what the experiment assumes happened between observations
```

Using `Close`, `Open`, `High`, or `Low` as an execution price is not automatically
wrong, but it must be justified for the order timing and labelled as an assumption.
For example, a daily high is not proof that a buy limit was filled at the high.

## 21. Execution-price assumptions

| Reference | Appropriate use | Strength | Main limitation |
|---|---|---|---|
| Close | End-of-day descriptive return or a close-based decision convention | Simple and reproducible | May be unavailable at the claimed order time; no spread/fill path |
| Next open | Next-session execution proxy after a prior-close signal | Preserves basic chronology | Does not reveal opening auction fill, spread, or queue |
| Bid | Sell-side reference or observed executable buy-side boundary depending on context | Uses a quote when available | Requires timestamped quote data and correct side |
| Ask | Buy-side reference when buying immediately | Uses a quote when available | Requires timestamped quote data and correct side |
| Mid | Mark-to-market or spread-neutral comparison reference | Useful analytical benchmark | Usually not an executable price |
| VWAP | Intraday execution benchmark | Incorporates traded volume | Requires intraday trades; daily OHLCV is insufficient for exact VWAP |
| Limit price | Maximum buy / minimum sell constraint | Represents order intent | Does not prove a fill |
| Simulated execution price | Controlled experiment under declared rules | Makes assumptions explicit | It is a model, not observed historical execution |

No method is declared “best” in this foundation. Suitability depends on the
research question, timing, available data, and the order type being represented.

## 22. Lookahead and execution timing

The timing must be consistent with Phase 1:

```text
Signal generated at t
        -> order submitted after signal
        -> execution at the declared permitted time
```

Conservative daily example:

```text
Close(t) -> calculate signal after t close -> submit next session
```

Incorrect example:

```text
Signal at t uses Close(t+1)
```

The close of `t` can be used only if the strategy explicitly waits until that close
is available. If the model claims same-day execution before the close, it cannot use
the final close or any indicator calculated from it.

## 23. Execution assumptions versus empirical evidence

### Assumptions acceptable for a controlled research experiment

- one-tick slippage because it is an explicit project constraint;
- next-open execution after a declared close signal when only daily data exists;
- a declared partial-fill rule used as a sensitivity scenario;
- a declared no-fill rule when the required quote/order-book evidence is absent.

### Claims that require empirical evidence

- actual spread for a specific symbol and time;
- queue position or fill probability;
- IOC/FAK fill rate;
- Market-to-Limit price path;
- market impact at a specified order size;
- exact intraday VWAP;
- whether a daily high/low was executable for the project's order.

If the required evidence is unavailable, report the limitation. Do not convert an
assumption into an observed fact.

## 24. Research implications for the project

Before any future execution-aware experiment:

1. Preserve historical point-in-time SET50 membership and security identity.
2. Declare signal and execution timestamps.
3. Keep requested, filled, and cancelled quantity separate.
4. Keep explicit fees separate from spread, slippage, and impact.
5. Use the correct price-dependent tick size for a one-tick assumption.
6. Do not infer quote, depth, queue, or fill facts from daily OHLCV.
7. Verify the applicable Settrade/venue order-field semantics before implementation.
8. Report all assumptions and perform sensitivity analysis only under a pre-declared
   methodology; do not tune assumptions to improve a result.

## 25. Research boundary

This document is research-only. It does not modify source code, strategy code,
feature code, backtest code, optimization code, data pipelines, historical
universes, Yahoo mappings, Research Dataset Gate, or production behavior. It does
not download market data or create trading signals.

## References

- [SET - Order types](https://www.set.or.th/en/market/information/trading-procedure/order-types)
- [SET - Revised trading criteria, English PDF](https://media.set.or.th/set/Documents/2023/Jan/revised_trading_criteria_SET_EN.pdf)
- [SET - Trading methods](https://www.set.or.th/en/market/information/trading-procedure/trading-methods)
- [SET - Price bands and tick sizes](https://www.set.or.th/en/market/information/trading-procedure/price-bands-and-tick-sizes)
- [SET - Trading units](https://www.set.or.th/en/market/information/trading-procedure/trading-units)
- [SET-CMRI Working Paper 1/2016](https://media.set.or.th/common/research/630.pdf)
- [Phase 1: SET50 Research Methodology](SET50_RESEARCH_METHODOLOGY.md)
- [Project SET50 parameter research](../set50_parameter_research.md)

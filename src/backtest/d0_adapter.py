"""Isolated execution adapter for the fixed D0 persistence diagnostic."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal
from typing import Mapping
import pandas as pd
from src.backtest.engine import ExecutionPolicy, _bar, _buy_budget_price, _market_value, _non_fill, _target_quantity, _union_dates
from src.backtest.transaction_cost import calculate_transaction_costs
from src.execution.order_manager import OrderSide
from src.strategies.d0_turnover_control import qualification_state

@dataclass
class D0ExecutionAdapter:
    initial_cash: Decimal = Decimal("10000000")
    max_positions: int = 10
    commission_rate: Decimal = Decimal("0.00157")
    vat_rate: Decimal = Decimal("0.07")

    def run(
        self,
        market_data: Mapping[str, pd.DataFrame],
        gate: object,
        policy: ExecutionPolicy,
        execution_start: pd.Timestamp | None = None,
    ) -> dict[str, object]:
        frames = {
            s: f.copy() if {"entry_confirmed", "exit_confirmed"}.issubset(f.columns) else qualification_state(f)
            for s, f in market_data.items()
        }
        dates = _union_dates(frames)
        cash, positions, pending, orders, snapshots = self.initial_cash, {}, {}, [], []
        for i, date in enumerate(dates):
            if execution_start is not None and date < pd.Timestamp(execution_start):
                continue
            for signal, symbol, side, qty in pending.pop(date, []):
                bar = _bar(frames[symbol], date); decision = gate.assess(symbol, date.date())
                if not decision.eligible: orders.append(_non_fill(signal,date,symbol,side,decision.reason or "INELIGIBLE",event_quantity=qty)); continue
                requested = policy.requested_price(OrderSide(side), bar["open"]) if bar else None; executed = policy.fill_price(OrderSide(side), requested, bar["low"], bar["high"]) if bar else None
                if executed is None: orders.append(_non_fill(signal,date,symbol,side,"IOC_LIMIT_NOT_FILLED",requested,event_quantity=qty)); continue
                costs = calculate_transaction_costs(executed * qty, self.commission_rate, self.vat_rate)
                if side == "BUY" and cash < executed*qty + costs.total_fees: orders.append(_non_fill(signal,date,symbol,side,"INSUFFICIENT_CASH",requested,event_quantity=qty)); continue
                if side == "SELL" and positions.get(symbol,0) < qty: orders.append(_non_fill(signal,date,symbol,side,"INSUFFICIENT_HOLDINGS",requested,event_quantity=qty)); continue
                before_cash, before_pos = cash, positions.get(symbol,0)
                if side == "BUY": cash -= executed*qty + costs.total_fees; positions[symbol]=before_pos+qty
                else: cash += executed*qty-costs.total_fees; positions[symbol]=before_pos-qty; positions.pop(symbol,None) if positions.get(symbol)==0 else None
                orders.append({"signal_date":signal,"execution_date":date,"symbol":symbol,"side":side,"quantity":qty,"status":"FILLED","reason": "ENTRY_CONFIRMED" if side=="BUY" else "EXIT_CONFIRMED","requested_price":requested,"executed_price":executed,"commission":costs.commission,"vat":costs.vat,"total_fees":costs.total_fees,"slippage":abs(executed-bar["open"])*qty,"cash_before":before_cash,"cash_after":cash,"position_before":before_pos,"position_after":positions.get(symbol,0)})
            for symbol, frame in frames.items():
                row = frame.loc[frame.index == date]
                if row.empty or i+1 >= len(dates): continue
                r=row.iloc[0]; held=positions.get(symbol,0)>0; boundary=held and getattr(gate,"membership_end",lambda *_:None)(symbol,date.date())==date.date(); exit_sig=bool(r.exit_confirmed) or boundary; entry_sig=bool(r.entry_confirmed) and not held
                next_orders = pending.setdefault(dates[i + 1], [])
                already_pending = {(p[1], p[2]) for p in next_orders}
                if exit_sig and held and (symbol, "SELL") not in already_pending:
                    next_orders.append((date, symbol, "SELL", positions[symbol]))
                elif entry_sig and (symbol, "BUY") not in already_pending and len(positions) + sum(p[2] == "BUY" for p in next_orders) < self.max_positions:
                    b=_bar(frame,dates[i+1])
                    if b:
                        next_orders.append((date, symbol, "BUY", _target_quantity(
                            self.initial_cash / Decimal(self.max_positions),
                            _buy_budget_price(policy.requested_price(OrderSide.BUY, b["open"]), self.commission_rate, self.vat_rate),
                        )))
            mv,gaps,_=_market_value(positions,frames,date,gate=gate); snapshots.append({"date":date,"equity":cash+mv if not gaps else None,"positions":len(positions),"cash":cash})
        filled=[o for o in orders if isinstance(o,dict)]; final=next((s["equity"] for s in reversed(snapshots) if s["equity"] is not None), self.initial_cash); fees=sum((o["total_fees"] for o in filled),Decimal(0)); slip=sum((o["slippage"] for o in filled),Decimal(0))
        return {"final_equity":str(final),"gross_return":str((final-self.initial_cash+fees)/self.initial_cash),"net_return":str((final-self.initial_cash)/self.initial_cash),"turnover":str(sum((o["executed_price"]*o["quantity"] for o in filled),Decimal(0))/self.initial_cash),"commission":str(sum((o["commission"] for o in filled),Decimal(0))),"vat":str(sum((o["vat"] for o in filled),Decimal(0))),"total_fees":str(fees),"slippage":str(slip),"fills":len(filled),"non_fills":len(orders)-len(filled),"orders":orders,"snapshots":snapshots}

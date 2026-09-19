"""Run the isolated, fixed D0 turnover-control diagnostic."""
from __future__ import annotations
import json,sys
from decimal import Decimal
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.data.research import load_approved_market_data
from src.data.features import build_features
from src.data.eligibility import MarketDataEligibilityGate
from src.strategies.d0_turnover_control import qualification_state
from src.backtest.d0_adapter import D0ExecutionAdapter
from src.backtest.engine import ExecutionPolicy, _bar, _buy_budget_price, _market_value, _non_fill, _target_quantity, _union_dates
from src.execution.order_manager import OrderSide
from scripts.run_design_a_backtest import set_tick_size

CAPITAL=Decimal("10000000")
POLICY=ExecutionPolicy(tick_size=set_tick_size)

def run():
    gate=MarketDataEligibilityGate(ROOT); manifest=pd.read_csv(ROOT/"data/processed/approved_market_data_manifest.csv"); states={}
    for s in manifest.set_symbol.astype(str).str.upper():
        try: states[s]=qualification_state(build_features(load_approved_market_data(s,gate=gate)))
        except (FileNotFoundError,ValueError): pass
    rows=[]
    for s,x in states.items():
        for ts,r in x.iterrows():
            rows.append({"date":ts.date(),"symbol":s,"qualifies_raw_design_a":bool(r.qualifies_raw_design_a),"qualifying_streak":int(r.qualifying_streak),"failing_streak":int(r.failing_streak),"d0_entry_confirmed":bool(r.entry_confirmed),"d0_exit_confirmed":bool(r.exit_confirmed),"order_generated":False,"order_reason":"","slot_available":""})
    execution = D0ExecutionAdapter().run({s: x for s, x in states.items()}, gate, POLICY)
    pd.DataFrame(rows).to_csv(ROOT/"reports/d0_signal_churn.csv",index=False)
    pd.DataFrame([{"metric":"signal_observations","design_a":"n/a","design_d0":len(rows)},{"metric":"confirmed_entries","design_a":"n/a","design_d0":sum(r["d0_entry_confirmed"] for r in rows)},{"metric":"confirmed_exits","design_a":"n/a","design_d0":sum(r["d0_exit_confirmed"] for r in rows)}]).to_csv(ROOT/"reports/d0_cost_comparison.csv",index=False)
    report={"status":"EXECUTED_DIAGNOSTIC","design":"D0","rules":{"entry_persistence_rows":2,"exit_persistence_rows":2,"max_positions":10,"ranking_replacement":False},"observations":len(rows),"symbols":len(states),"execution":{k:v for k,v in execution.items() if k not in ("orders","snapshots")},"production_mutated":False}
    (ROOT/"reports/d0_execution_results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    order_rows = []
    for event in execution["orders"]:
        if isinstance(event, dict): order_rows.append({k: str(v) for k,v in event.items()})
        else: order_rows.append({"symbol": event.symbol, "side": event.side, "status": event.status, "reason": event.reason or ""})
    pd.DataFrame(order_rows).to_csv(ROOT/"reports/d0_execution_orders.csv", index=False)
    pd.DataFrame(execution["snapshots"]).to_csv(ROOT/"reports/d0_portfolio_diagnostics.csv", index=False)
    pd.DataFrame([{ "metric": k, "value": v } for k,v in report["execution"].items()]).to_csv(ROOT/"reports/d0_vs_a_comparison.csv", index=False)
    (ROOT/"docs/D0_EXECUTION_EVALUATION.md").write_text("# D0 Execution Evaluation\n\nD0 completed an isolated execution run using the existing LIMIT/IOC, one-tick, fee, VAT, eligibility, and valuation primitives. The production A/C engine was not modified.\n\nThe result is diagnostic only; Design A comparison and walk-forward adapter outputs require review of the generated reports.\n", encoding="utf-8")
    (ROOT/"reports/d0_research_decision.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    (ROOT/"reports/d0_backtest_comparison.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    decision = {"classification":"DIAGNOSTIC_ONLY","conclusion":"Human approval required before any next-design change.","production_mutated":False,"d0_net_return":execution["net_return"],"d0_fills":execution["fills"],"d0_turnover":execution["turnover"],"walk_forward":"NOT_RUN"}
    (ROOT/"reports/d0_execution_decision.json").write_text(json.dumps(decision, indent=2), encoding="utf-8")
    return report
if __name__=="__main__": run()

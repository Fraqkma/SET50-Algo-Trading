"""Descriptive transaction-cost and one-tick slippage attribution."""
from __future__ import annotations
import json
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]

def _events(design):
    f=pd.read_csv(ROOT/f"reports/design_{design.lower()}_backtest_orders.csv")
    f=f[f.status.eq("FILLED")].copy(); f.insert(0,"design",design)
    for c in ["order_value","slippage","commission","vat","total_fees","requested_price","executed_price","quantity"]: f[c]=pd.to_numeric(f.get(c,0),errors="coerce").fillna(0)
    f["date"]=pd.to_datetime(f.execution_date,errors="coerce"); f["year"]=f.date.dt.year; f["month"]=f.date.dt.to_period("M").astype(str)
    f["tick_size"]=np.where(f.quantity>0,f.slippage/f.quantity,np.nan); f["slippage_bps"]=np.where(f.order_value>0,f.slippage/f.order_value*10000,np.nan); f["fee_total"]=f.commission+f.vat; f["transaction_cost"]=f.fee_total+f.slippage
    f["price_bucket"]=pd.cut(f.executed_price,[-np.inf,5,10,25,50,100,np.inf],labels=["<5","5-10","10-25","25-50","50-100",">100"])
    f["notional_bucket"]=pd.qcut(f.order_value,4,labels=["Q1","Q2","Q3","Q4"],duplicates="drop")
    f["reason_class"]=f.reason.fillna("NORMAL").map(lambda x:"BOUNDARY_EXIT" if str(x).startswith("UNIVERSE_BOUNDARY") else "NORMAL_STRATEGY")
    return f

def _agg(f, keys):
    g=f.groupby(keys,dropna=False).agg(fills=("symbol","size"),notional=("order_value","sum"),slippage=("slippage","sum"),avg_slippage=("slippage","mean"),median_slippage=("slippage","median"),fees=("fee_total","sum"),transaction_cost=("transaction_cost","sum")).reset_index(); g["slippage_bps"]=np.where(g.notional>0,g.slippage/g.notional*10000,np.nan); return g

def run():
    f=pd.concat([_events("A"),_events("C")],ignore_index=True); f.to_csv(ROOT/"reports/slippage_event_attribution.csv",index=False)
    _agg(f,["symbol"]).to_csv(ROOT/"reports/slippage_by_symbol.csv",index=False); _agg(f,["month"]).to_csv(ROOT/"reports/slippage_by_month.csv",index=False); _agg(f,["side"]).to_csv(ROOT/"reports/slippage_by_side.csv",index=False)
    _agg(f,["design","year","month","side","reason_class","price_bucket","notional_bucket"]).to_csv(ROOT/"reports/slippage_cost_concentration.csv",index=False)
    top=f.nlargest(max(1,int(np.ceil(len(f)*.1))),"slippage"); top5=f.groupby("symbol").slippage.sum().nlargest(5)
    report={"status":"DESCRIPTIVE_ONLY","fills":len(f),"total_slippage":float(f.slippage.sum()),"total_fees":float(f.fee_total.sum()),"total_transaction_cost":float(f.transaction_cost.sum()),"per_design":{d:{"fills":int((f.design==d).sum()),"slippage":float(f.loc[f.design==d,"slippage"].sum()),"fees":float(f.loc[f.design==d,"fee_total"].sum()),"transaction_cost":float(f.loc[f.design==d,"transaction_cost"].sum())} for d in ("A","C")},"top_10_percent_slippage_share":float(top.slippage.sum()/f.slippage.sum()),"top_5_symbol_slippage_share":float(top5.sum()/f.slippage.sum()),"buy_sell_slippage":f.groupby("side").slippage.sum().to_dict(),"price_bucket_slippage_bps":_agg(f,["price_bucket"])[["price_bucket","slippage_bps"]].to_dict("records"),"counterfactuals":{"zero_slippage_net_return_delta":float(f.slippage.sum()),"zero_fees_net_return_delta":float(f.fee_total.sum()),"zero_both_delta":float(f.transaction_cost.sum()),"turnover_reduction_25pct_cost_saved":float(f.transaction_cost.sum()*.25),"turnover_reduction_50pct_cost_saved":float(f.transaction_cost.sum()*.5),"turnover_reduction_75pct_cost_saved":float(f.transaction_cost.sum()*.75)},"limitations":["order logs do not deterministically link non-fill retries to later fills","qualification/ranking reason is not recorded on every order","feature/liquidity joins require a separate timestamp-level event map"],"production_mutated":False}
    (ROOT/"reports/transaction_cost_root_causes.json").write_text(json.dumps(report,indent=2,default=str),encoding="utf-8")
    (ROOT/"docs/TRANSACTION_COST_SLIPPAGE_ANALYSIS.md").write_text("# Transaction-cost and slippage analysis\n\nThis report is descriptive and uses existing A/C filled-order logs only. It does not alter execution assumptions or strategy logic. Total cost is dominated by repeated one-tick slippage across high turnover; precise retry causality is not identifiable from the current logs.\n",encoding="utf-8")
    return report
if __name__=="__main__": run()

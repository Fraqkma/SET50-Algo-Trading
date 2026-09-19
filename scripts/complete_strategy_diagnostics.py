"""Complete descriptive diagnostics from existing approved A/C artifacts.

No strategy parameters are changed and no official backtest outputs are
overwritten.  The runner uses approved 2023-2026 prices and existing order and
selection logs only.
"""
from __future__ import annotations
import csv, json, math, sys
from collections import defaultdict, deque
from pathlib import Path
import numpy as np
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.data.research import load_approved_market_data
from src.data.features import build_features

SYMBOLS=["BDMS","BGRIM","CENTEL","COM7","GLOBAL","HMPRO","IVL","KKP","KTB","LH","MTC","OSP","PTTGC","RATCH","SCGP","THAI","TOP"]
HORIZONS=[1,3,5,10,20]

def lot_rows(design: str) -> pd.DataFrame:
    orders=pd.read_csv(ROOT/f"reports/design_{design.lower()}_backtest_orders.csv")
    orders["execution_date"]=pd.to_datetime(orders["execution_date"],errors="coerce")
    orders["quantity"]=pd.to_numeric(orders["quantity"],errors="coerce").fillna(0).astype(int)
    orders["executed_price"]=pd.to_numeric(orders["executed_price"],errors="coerce")
    orders["order_value"]=pd.to_numeric(orders["order_value"],errors="coerce").fillna(0)
    queues=defaultdict(deque); rows=[]; lot=0
    for _,o in orders.sort_values(["execution_date"]).iterrows():
        if o.get("status")!="FILLED": continue
        symbol=str(o["symbol"]); qty=int(o["quantity"])
        if o["side"]=="BUY":
            lot+=1; queues[symbol].append({"lot_id":lot,"qty":qty,"entry":o})
        elif o["side"]=="SELL":
            remaining=qty
            while remaining and queues[symbol]:
                entry=queues[symbol][0]; used=min(remaining,entry["qty"]); remaining-=used; entry["qty"]-=used
                gross=(float(o["executed_price"])-float(entry["entry"]["executed_price"]))*used
                fees=float(o.get("total_fees",0))+float(entry["entry"].get("total_fees",0)); slip=float(o.get("slippage",0))+float(entry["entry"].get("slippage",0))
                rows.append({"lot_id":entry["lot_id"],"symbol":symbol,"entry_signal_date":entry["entry"].get("signal_date",""),"entry_execution_date":entry["entry"]["execution_date"],"exit_signal_date":o.get("signal_date",""),"exit_execution_date":o["execution_date"],"entry_price":entry["entry"]["executed_price"],"exit_price":o["executed_price"],"quantity":used,"holding_rows":int((o["execution_date"]-entry["entry"]["execution_date"]).days),"exit_reason":"SELL","gross_pnl":gross,"fees":fees,"slippage":slip,"net_pnl":gross-fees})
                if entry["qty"]==0: queues[symbol].popleft()
    return pd.DataFrame(rows)

def feature_rows() -> pd.DataFrame:
    out=[]
    for s in SYMBOLS:
        f=load_approved_market_data(s); x=build_features(f); close=x["close"]
        x["momentum_60"]=close.pct_change(60); x["momentum_120"]=close.pct_change(120)
        x["close_gt_sma20"]=close>x["sma_20"]; x["close_gt_sma50"]=close>x["sma_50"]; x["sma20_gt_sma50"]=x["sma_20"]>x["sma_50"]
        for h in HORIZONS: x[f"fwd_{h}d"]=close.shift(-h)/close-1
        for name in ["momentum_20","momentum_60","momentum_120","close_gt_sma20","close_gt_sma50","sma20_gt_sma50","volatility_20","volume_ratio_20"]:
            cols=[name]+[f"fwd_{h}d" for h in HORIZONS]; v=x[cols].dropna()
            for h in HORIZONS:
                z=v[[name,f"fwd_{h}d"]]; row={"symbol":s,"feature":name,"horizon_days":h,"sample_size":len(z),"pearson":z.iloc[:,0].corr(z.iloc[:,1]),"spearman":z.iloc[:,0].rank().corr(z.iloc[:,1].rank())}
                if x[name].dtype==bool or str(x[name].dtype)=="bool": row.update({"true_mean":z.loc[z[name],z.columns[1]].mean(),"false_mean":z.loc[~z[name],z.columns[1]].mean()})
                else: row.update({"true_mean":"","false_mean":""})
                out.append(row)
    return pd.DataFrame(out)

def run()->dict:
    all_lots=[]
    for d in ("A","C"):
        lots=lot_rows(d); lots.insert(0,"design",d); all_lots.append(lots)
    lot=pd.concat(all_lots,ignore_index=True) if all_lots else pd.DataFrame()
    buckets=pd.cut(lot["holding_rows"],[-1,2,5,10,20,10**9],labels=["1-2","3-5","6-10","11-20",">20"]) if len(lot) else []
    hold=[]
    if len(lot):
        lot["bucket"]=buckets
        for (d,b),g in lot.groupby(["design","bucket"],observed=True):
            returns=g.net_pnl/(g.entry_price*g.quantity)
            hold.append({"design":d,"bucket":str(b),"count":len(g),"win_rate":float((g.net_pnl>0).mean()),"gross_pnl":g.gross_pnl.sum(),"net_pnl":g.net_pnl.sum(),"average_return":float(returns.mean()),"median_return":float(returns.median()),"fees":g.fees.sum(),"slippage":g.slippage.sum()})
    feat=feature_rows(); feat.to_csv(ROOT/"reports/feature_future_return_relationships.csv",index=False)
    pd.DataFrame(hold).to_csv(ROOT/"reports/strategy_holding_duration.csv",index=False)
    cost={}
    for d in ("A","C"):
        r=json.loads((ROOT/f"reports/design_{d.lower()}_backtest_report.json").read_text())
        cost[d]={"round_trip_cost_drag_fraction":(float(r["total_fees"])+float(r["slippage"])) / 10000000,"median_completed_trade_cost":float(lot.loc[lot.design==d,"fees"].add(lot.loc[lot.design==d,"slippage"]).median()) if len(lot) else None,"total_fees":r["total_fees"],"slippage":r["slippage"]}
    pd.DataFrame([{"design":d,**v} for d,v in cost.items()]).to_csv(ROOT/"reports/cost_break_even_analysis.csv",index=False)
    (ROOT/"reports/cost_break_even_analysis.json").write_text(json.dumps(cost, indent=2), encoding="utf-8")
    selections=pd.read_csv(ROOT/"reports/design_c_backtest_selections.csv"); selections["selected_count"]=selections.selected_symbols.fillna("").map(lambda x: len([z for z in str(x).split(",") if z]))
    pd.DataFrame([{"comparison":"C_selected_vs_A_qualified_not_selected","horizon_days":h,"mean_selected":"","mean_not_selected":"","sample_size_selected":int(selections.selected_count.sum()),"sample_size_not_selected":"","status":"INSUFFICIENT_EVIDENCE: qualified candidate set was not persisted"} for h in HORIZONS]).to_csv(ROOT/"reports/design_c_selection_quality.csv",index=False)
    pd.DataFrame([{"metric":"selection_dates","value":len(selections)},{"metric":"mean_selected_count","value":selections.selected_count.mean()},{"metric":"two_row_persistence_proxy","value":"not identifiable: qualification sets absent"}]).to_csv(ROOT/"reports/signal_churn_diagnostics.csv",index=False)
    payload={"status":"DESCRIPTIVE_ONLY","holding_duration_rows":len(hold),"lot_count":len(lot),"feature_rows":len(feat),"cost_break_even":cost,"limitations":["qualified-but-not-selected candidate sets are absent from existing logs","holding rows use calendar-day deltas, not engine observed-row indices","no overlapping-return inferential claims"],"production_mutated":False}
    (ROOT/"reports/strategy_diagnostic_completion.json").write_text(json.dumps(payload,indent=2,default=str),encoding="utf-8")
    (ROOT/"docs/STRATEGY_DIAGNOSTIC_COMPLETION.md").write_text("# Strategy diagnostic completion\n\nDiagnostics replay existing approved Design A/C orders only. Results are descriptive; no strategy logic or official backtest outputs were changed. Qualified candidate sets are not present in the original logs, so selected-versus-qualified and true qualification persistence remain unidentifiable.\n",encoding="utf-8")
    return payload

if __name__=="__main__": run()

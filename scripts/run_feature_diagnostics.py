"""Descriptive feature diagnostics on approved daily data; no strategy run."""
from __future__ import annotations
import json
from pathlib import Path
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.research import load_approved_market_data
from src.data.features import build_features

SYMBOLS = ["BDMS","BGRIM","CENTEL","COM7","GLOBAL","HMPRO","IVL","KKP","KTB","LH","MTC","OSP","PTTGC","RATCH","SCGP","THAI","TOP"]

def run() -> dict:
    rows=[]
    for symbol in SYMBOLS:
        frame=load_approved_market_data(symbol)
        feat=build_features(frame, momentum_window=20)
        close=feat["close"]
        feat["momentum_60"]=close.pct_change(60)
        feat["momentum_120"]=close.pct_change(120)
        feat["close_gt_sma20"]=close > feat["sma_20"]
        feat["close_gt_sma50"]=close > feat["sma_50"]
        feat["sma20_gt_sma50"]=feat["sma_20"] > feat["sma_50"]
        for name in ["momentum_20","momentum_60","momentum_120","close_gt_sma20","close_gt_sma50","sma20_gt_sma50","volatility_20","volume_sma_20","volume_ratio_20"]:
            if name in feat:
                valid=feat[[name,"daily_return"]].dropna()
                future=(close.shift(-5)/close-1.0).loc[valid.index]
                rows.append({"symbol":symbol,"feature":name,"observations":int(len(valid)),
                             "mean":float(valid[name].mean()) if len(valid) else None,
                             "return_correlation":float(valid[name].corr(valid["daily_return"])) if len(valid)>1 else None,
                             "forward_5d_mean":float(future.mean()) if len(future) else None,
                             "positive_forward_5d_rate":float((future>0).mean()) if len(future) else None,
                             "classification":"INSUFFICIENT_EVIDENCE" if len(valid)<100 else "DIAGNOSTIC_ONLY"})
    payload={"status":"DESCRIPTIVE_ONLY","rows":rows,"parameters":{"momentum_window":20,"short_window":20,"long_window":50,"volatility_window":20,"volume_window":20},"production_mutated":False}
    (ROOT/"reports/feature_diagnostics.json").write_text(json.dumps(payload,indent=2),encoding="utf-8")
    pd.DataFrame(rows).to_csv(ROOT/"reports/feature_diagnostics.csv",index=False)
    (ROOT/"docs/FEATURE_DIAGNOSTICS.md").write_text("# Feature diagnostics\n\nThese are descriptive correlations on approved daily data only; no feature or strategy parameters were changed and no backtest was run.\n",encoding="utf-8")
    return payload
if __name__=="__main__": run()

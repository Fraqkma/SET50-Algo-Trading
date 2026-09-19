"""Persist qualification and candidate observability without changing A/C runs."""
from __future__ import annotations
import json, sys
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from src.data.research import load_approved_market_data
from src.data.features import build_features
from src.data.eligibility import MarketDataEligibilityGate
from src.strategies.cross_sectional import rank_time_series_candidates

def load_frames():
    manifest=pd.read_csv(ROOT/"data/processed/approved_market_data_manifest.csv")
    gate=MarketDataEligibilityGate(ROOT); frames={}
    for s in manifest.set_symbol.astype(str).str.upper():
        try: frames[s]=build_features(load_approved_market_data(s,gate=gate))
        except (FileNotFoundError,ValueError): pass
    return frames,gate

def qualification(frames,gate):
    rows=[]
    for symbol,frame in frames.items():
        streak=0; previous=False
        for ts,row in frame.iterrows():
            date=ts.date(); eligible=gate.assess(symbol,date).eligible
            momentum=row.get("momentum_20"); close=row.get("close"); sma=row.get("sma_20")
            feature_available=bool(pd.notna(momentum) and pd.notna(close) and pd.notna(sma))
            qualifies=bool(eligible and feature_available and float(close)>float(sma) and float(momentum)>0)
            if qualifies: streak+=1
            else: streak=0
            transition="ENTER" if qualifies and not previous else "EXIT" if previous and not qualifies else "STAY_QUALIFIED" if qualifies else "STAY_UNQUALIFIED"
            rows.append({"date":date,"symbol":symbol,"eligible":eligible,"feature_available":feature_available,"momentum_20":momentum,"close":close,"sma_20":sma,"qualifies_design_a":qualifies,"previous_qualifies_design_a":previous,"qualification_transition":transition,"qualification_streak":streak})
            previous=qualifies
    return pd.DataFrame(rows)

def candidates(frames,gate):
    selected=pd.read_csv(ROOT/"reports/design_c_backtest_selections.csv")
    selected["date"]=pd.to_datetime(selected.signal_date).dt.date
    sets={d:set(str(v).split("|") if pd.notna(v) else []) for d,v in zip(selected.date,selected.selected_symbols)}
    out=[]
    for date,symbols in sets.items():
        ranked=rank_time_series_candidates(frames,date,top_n=len(frames),gate=gate)
        count=len(ranked)
        for _,r in ranked.iterrows():
            symbol=r.symbol; close=frames[symbol]["close"]
            idx=[x.date() for x in close.index]
            pos=idx.index(date) if date in idx else -1
            item={"date":date,"symbol":symbol,"momentum_20":r.momentum_20,"rank":int(r["rank"]),"selected_by_design_c":symbol in symbols,"candidate_count":count}
            for h in (1,3,5,10,20): item[f"forward_return_{h}d"]=(float(close.iloc[pos+h]/close.iloc[pos]-1) if pos>=0 and pos+h<len(close) else None)
            out.append(item)
    return pd.DataFrame(out)

def run():
    frames,gate=load_frames(); q=qualification(frames,gate); c=candidates(frames,gate)
    q.to_csv(ROOT/"reports/design_a_qualification_state.csv",index=False); c.to_csv(ROOT/"reports/design_c_candidate_set.csv",index=False)
    summary={"status":"DESCRIPTIVE_ONLY","symbols":len(frames),"qualification_rows":len(q),"candidate_rows":len(c),"production_mutated":False,"limitations":["persistence is diagnostic only; production strategy unchanged","future returns are labels and never used in ranking"]}
    (ROOT/"reports/observability_diagnostic_replay.json").write_text(json.dumps(summary,indent=2,default=str),encoding="utf-8")
    return summary
if __name__=="__main__": run()

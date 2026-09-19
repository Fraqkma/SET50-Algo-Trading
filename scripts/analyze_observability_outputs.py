"""Summarize the persisted observability replay descriptively."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]; H=[1,3,5,10,20]
def run():
    c=pd.read_csv(ROOT/"reports/design_c_candidate_set.csv"); q=pd.read_csv(ROOT/"reports/design_a_qualification_state.csv")
    rows=[]
    for h in H:
        col=f"forward_return_{h}d"
        for label,g in c.assign(group=c.selected_by_design_c.map({True:"selected",False:"qualified_not_selected"})).groupby("group"):
            v=pd.to_numeric(g[col],errors="coerce").dropna(); rows.append({"group":label,"horizon_days":h,"sample_size":len(v),"mean":v.mean(),"median":v.median(),"hit_rate":(v>0).mean(),"q25":v.quantile(.25),"q50":v.quantile(.5),"q75":v.quantile(.75),"rank_spearman":g.loc[v.index,"rank"].corr(v,method="spearman") if len(v)>1 else None})
    pd.DataFrame(rows).to_csv(ROOT/"reports/design_c_selection_quality_complete.csv",index=False)
    transitions=q.qualification_transition.value_counts(); q["streak_bucket"]=pd.cut(q.qualification_streak,[-1,1,2,3,10**9],labels=["1-row","2-row","3-10"," >10"])
    persistence=pd.DataFrame([{"metric":"qualification_rows","value":len(q)},{"metric":"enter_count","value":int((q.qualification_transition=="ENTER").sum())},{"metric":"exit_count","value":int((q.qualification_transition=="EXIT").sum())},{"metric":"one_row_qualification_streaks","value":int(((q.qualification_transition=="ENTER") & (q.qualification_streak==1)).sum())},{"metric":"two_row_persistence_proxy","value":"requires signal replay; state is now available"}]); persistence.to_csv(ROOT/"reports/signal_persistence_complete.csv",index=False)
    t=q.qualification_transition.value_counts().rename_axis("transition").reset_index(name="count"); t.to_csv(ROOT/"reports/turnover_mechanism_decomposition.csv",index=False)
    summary={"status":"DESCRIPTIVE_ONLY","candidate_rows":len(c),"qualification_rows":len(q),"one_row_entries":int(((q.qualification_transition=="ENTER")&(q.qualification_streak==1)).sum()),"enter_count":int((q.qualification_transition=="ENTER").sum()),"exit_count":int((q.qualification_transition=="EXIT").sum()),"limitations":["persistence-2 turnover simulation is not a production change and requires a separate signal-to-order replay","candidate forward returns overlap and are descriptive"]}
    (ROOT/"reports/observability_analysis_summary.json").write_text(json.dumps(summary,indent=2),encoding="utf-8"); return summary
if __name__=="__main__": run()

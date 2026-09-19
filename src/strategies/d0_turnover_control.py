"""Fixed two-row persistence turnover-control signal state for D0."""
from __future__ import annotations
import pandas as pd

def qualification_state(frame: pd.DataFrame) -> pd.DataFrame:
    x=frame.copy(); raw=(x["momentum_20"]>0)&(x["close"]>x["sma_20"])&x[["momentum_20","close","sma_20"]].notna().all(axis=1)
    x["qualifies_raw_design_a"]=raw; x["qualifying_streak"]=raw.astype(int).groupby((~raw).cumsum()).cumsum(); x["failing_streak"]=(~raw).astype(int).groupby(raw.cumsum()).cumsum()
    x["entry_confirmed"]=x["qualifying_streak"]>=2; x["exit_confirmed"]=x["failing_streak"]>=2
    return x

class D0TurnoverControl:
    """No-ranking replacement policy; fixed two-row entry/exit persistence."""
    max_positions=10
    def state(self, frame: pd.DataFrame) -> pd.DataFrame: return qualification_state(frame)

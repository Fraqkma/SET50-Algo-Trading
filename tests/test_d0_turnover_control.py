import pandas as pd
from src.strategies.d0_turnover_control import qualification_state

def test_two_row_entry_and_exit_persistence():
    x=pd.DataFrame({"momentum_20":[1,1,-1,-1],"close":[2,2,1,1],"sma_20":[1,1,2,2]})
    s=qualification_state(x)
    assert s.entry_confirmed.tolist()==[False,True,False,False]
    assert s.exit_confirmed.tolist()==[False,False,False,True]

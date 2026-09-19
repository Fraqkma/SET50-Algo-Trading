from scripts.analyze_transaction_costs import _agg
import pandas as pd


def test_aggregation_is_deterministic():
    frame=pd.DataFrame({"symbol":["A","A"],"order_value":[10.,20.],"slippage":[1.,2.],"fee_total":[.1,.2],"transaction_cost":[1.1,2.2]})
    out=_agg(frame,["symbol"])
    assert out.iloc[0].fills == 2
    assert out.iloc[0].slippage == 3

from scripts.run_d0_backtest import run

def test_d0_runner_is_isolated():
    result=run()
    assert result["design"]=="D0"
    assert result["production_mutated"] is False

from scripts.complete_strategy_diagnostics import HORIZONS


def test_fixed_forward_horizons():
    assert HORIZONS == [1, 3, 5, 10, 20]

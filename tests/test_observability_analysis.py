from scripts.analyze_observability_outputs import H


def test_requested_horizons_are_fixed():
    assert H == [1, 3, 5, 10, 20]

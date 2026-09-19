from scripts.run_feature_diagnostics import SYMBOLS


def test_feature_diagnostic_universe_is_fixed():
    assert len(SYMBOLS) == len(set(SYMBOLS))
    assert "BDMS" in SYMBOLS and "TOP" in SYMBOLS

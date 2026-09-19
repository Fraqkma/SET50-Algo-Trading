from scripts.run_strategy_root_cause_analysis import _run


def test_existing_reports_are_read_only_diagnostics():
    result = _run("A")
    assert result["design"] == "A"
    assert result["fills"] >= 0

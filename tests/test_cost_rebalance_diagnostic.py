from __future__ import annotations

import json
from pathlib import Path


def test_cost_diagnostic_has_fixed_scenarios_and_both_designs() -> None:
    report = json.loads(
        (Path(__file__).resolve().parents[1] / "reports" / "design_a_c_cost_rebalance_diagnostic.json").read_text()
    )
    assert set(report["cost_sensitivity"]) == {"official", "zero_transaction_cost", "fee_only", "slippage_only"}
    assert set(report["frequency_sensitivity"]) == {
        "every_1_observed_row", "every_3_observed_rows", "every_5_observed_rows_weekly_style", "every_10_observed_rows"
    }
    for family in ("cost_sensitivity", "frequency_sensitivity"):
        assert all(set(value) >= {"Design A", "Design C"} for value in report[family].values())


def test_zero_cost_diagnostic_improves_net_return_without_changing_base_reference() -> None:
    report = json.loads(
        (Path(__file__).resolve().parents[1] / "reports" / "design_a_c_cost_rebalance_diagnostic.json").read_text()
    )
    for design in ("Design A", "Design C"):
        official = float(report["cost_sensitivity"]["official"][design]["net_return"])
        zero = float(report["cost_sensitivity"]["zero_transaction_cost"][design]["net_return"])
        assert zero > official
    assert report["cost_sensitivity"]["official"]["Design A"]["final_equity"] == "2881303.363244797241866051837"

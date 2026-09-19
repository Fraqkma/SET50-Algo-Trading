import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_protocol_is_preregistered_and_uses_fold_net_return():
    protocol = json.loads((ROOT / "reports" / "statistical_comparison_protocol.json").read_text(encoding="utf-8"))
    assert protocol["status"] == "preregistered"
    assert protocol["primary_comparison"] == "Design C minus Design A"
    assert protocol["primary_metric"] == "fold_level_net_return_difference"
    assert protocol["unit_of_comparison"] == "paired_walk_forward_fold"
    assert protocol["formal_inferential_test"] is None


def test_protocol_does_not_claim_current_superiority():
    text = (ROOT / "docs" / "STATISTICAL_COMPARISON_PROTOCOL.md").read_text(encoding="utf-8")
    assert "insufficient evidence to establish superiority" in text
    assert "No inferential result is reported" in text
    assert "two-sided alpha = 0.05" in text


def test_walk_forward_results_match_registered_fold_count():
    results = json.loads((ROOT / "reports" / "walk_forward_results.json").read_text(encoding="utf-8"))
    protocol = json.loads((ROOT / "reports" / "statistical_comparison_protocol.json").read_text(encoding="utf-8"))
    assert len(results["folds"]) == protocol["fold_count"] == 5
    assert len([r for r in results["fold_results"] if r["design"] == "A"]) == 5
    assert len([r for r in results["fold_results"] if r["design"] == "C"]) == 5

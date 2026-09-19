from decimal import Decimal

import pandas as pd

from scripts.run_walk_forward import aggregate_metrics, build_expanding_folds


def test_expanding_folds_are_chronological_and_non_overlapping():
    dates = pd.date_range("2020-01-01", periods=898, freq="D")
    folds = build_expanding_folds(dates, initial_research_observations=400, oos_observations=120)
    assert len(folds) == 5
    assert folds[0].research_observations == 400
    assert folds[0].oos_observations == 120
    for previous, current in zip(folds, folds[1:]):
        assert current.research_end == previous.oos_end
        assert current.oos_start > current.research_end
        assert current.research_observations == previous.research_observations + previous.oos_observations
    assert sum(f.oos_observations for f in folds) == 498


def test_fold_builder_rejects_invalid_sizes():
    dates = pd.date_range("2020-01-01", periods=10, freq="D")
    for kwargs in ({"initial_research_observations": 0}, {"oos_observations": 0}):
        try:
            build_expanding_folds(dates, **kwargs)
        except ValueError:
            pass
        else:
            raise AssertionError("invalid fold size was accepted")


def test_aggregate_metrics_is_deterministic_and_documents_compounding():
    rows = [
        {"net_return": "0.10", "final_equity": "11000000"},
        {"net_return": "-0.05", "final_equity": "9500000"},
    ]
    first = aggregate_metrics(rows)
    second = aggregate_metrics(rows)
    assert first == second
    assert first["positive_fold_fraction"] == 0.5
    assert abs(float(first["compounded_independent_fold_net_return"]) - 0.045) < 1e-12

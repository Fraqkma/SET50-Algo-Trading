import pandas as pd

from scripts.run_larger_oos import OOS_BLOCK, INITIAL_HISTORY, build_larger_oos_folds


def test_larger_oos_has_equal_sized_non_overlapping_blocks():
    dates = pd.date_range("2020-01-01", periods=898, freq="D")
    folds, remainder = build_larger_oos_folds(dates)
    assert INITIAL_HISTORY == 250
    assert OOS_BLOCK == 80
    assert len(folds) == 8
    assert all(fold.oos_observations == OOS_BLOCK for fold in folds)
    assert len(remainder) == 1
    assert remainder[0].oos_observations == 8
    for previous, current in zip(folds, folds[1:]):
        assert current.research_end == previous.oos_end
        assert current.oos_start > current.research_end
        assert current.research_observations == previous.research_observations + OOS_BLOCK


def test_larger_oos_does_not_use_future_dates_in_fold_boundaries():
    dates = pd.date_range("2020-01-01", periods=898, freq="D")
    folds, _ = build_larger_oos_folds(dates)
    for fold in folds:
        assert fold.research_end < fold.oos_start
        assert fold.oos_end <= dates[-1].date().isoformat()
        assert fold.research_observations + fold.oos_observations <= 890


def test_larger_oos_block_count_is_deterministic():
    dates = pd.date_range("2020-01-01", periods=898, freq="D")
    first = build_larger_oos_folds(dates)
    second = build_larger_oos_folds(dates)
    assert first == second

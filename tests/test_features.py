from __future__ import annotations

import pandas as pd
import pytest

from src.data.features import build_features
from src.strategies.baseline import BaselineStrategy


def _prices(count: int = 60) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=count, freq="D")
    close = pd.Series(range(100, 100 + count), index=index, dtype=float)
    return pd.DataFrame({"Close": close, "Volume": 1_000.0}, index=index)


def test_features_are_causal_and_keep_warmup_missing_values() -> None:
    source = _prices()
    features = build_features(source)
    assert pd.isna(features.iloc[0]["daily_return"])
    assert pd.isna(features.iloc[19]["momentum_20"])
    assert pd.notna(features.iloc[20]["momentum_20"])
    assert features.iloc[20]["momentum_20"] == pytest.approx(20 / 100)

    changed_future = source.copy()
    changed_future.iloc[-1, changed_future.columns.get_loc("Close")] = 10_000
    changed_features = build_features(changed_future)
    columns = ["daily_return", "momentum_20", "sma_20", "sma_50", "volatility_20"]
    pd.testing.assert_frame_equal(features.loc[features.index[:-1], columns], changed_features.loc[features.index[:-1], columns])


def test_features_do_not_repair_missing_or_duplicate_input() -> None:
    missing = _prices(5)
    missing.loc[missing.index[2], "Close"] = None
    with pytest.raises(ValueError, match="Close contains missing"):
        build_features(missing)

    duplicate = pd.concat([_prices(2), _prices(1)])
    with pytest.raises(ValueError, match="duplicate dates"):
        build_features(duplicate)


def test_volume_features_are_computed_without_filling() -> None:
    features = build_features(_prices(25))
    assert {"volume_sma_20", "volume_ratio_20"}.issubset(features.columns)
    assert pd.isna(features.iloc[18]["volume_sma_20"])
    assert features.iloc[19]["volume_ratio_20"] == pytest.approx(1.0)


def test_baseline_signal_rules_are_deterministic() -> None:
    features = build_features(_prices())
    signals = BaselineStrategy().generate_signal(features)
    assert set(signals.iloc[:20]) == {"HOLD"}
    assert signals.iloc[20] == "BUY"


def test_baseline_rejects_unfeatured_input() -> None:
    with pytest.raises(ValueError, match="Missing baseline feature"):
        BaselineStrategy().generate_signal(pd.DataFrame({"close": [1.0]}))

from __future__ import annotations

import pandas as pd
import pytest

from src.data.features import FeatureContext, build_features
from src.strategies.baseline import BaselineStrategy


def _prices(count: int = 60) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=count, freq="D")
    close = pd.Series(range(100, 100 + count), index=index, dtype=float)
    adjusted_close = close.copy()
    return pd.DataFrame(
        {
            "Close": close,
            "Adj Close": adjusted_close,
            "Volume": 1_000.0,
            "Dividends": 0.0,
            "Stock Splits": 0.0,
        },
        index=index,
    )


def _context(
    *,
    data_status: str = "USE",
    pit_membership: object = "SET50:eligible",
    information_cutoff: str = "2024-12-31 23:59:59",
) -> FeatureContext:
    return FeatureContext(
        security_id="TEST_SECURITY",
        pit_membership=pit_membership,
        identity_status="VERIFIED",
        data_status=data_status,
        information_cutoff=information_cutoff,
        source_data="tests/test_features.py",
    )


def test_features_are_causal_and_keep_warmup_missing_values() -> None:
    source = _prices()
    features = build_features(source, context=_context())
    assert pd.isna(features.iloc[0]["daily_return"])
    assert pd.isna(features.iloc[19]["momentum_20"])
    assert pd.notna(features.iloc[20]["momentum_20"])
    assert features.iloc[20]["momentum_20"] == pytest.approx(20 / 100)

    changed_future = source.copy()
    changed_future.iloc[-1, changed_future.columns.get_loc("Close")] = 10_000
    changed_features = build_features(changed_future, context=_context())
    columns = ["daily_return", "momentum_20", "sma_20", "sma_50", "volatility_20"]
    pd.testing.assert_frame_equal(features.loc[features.index[:-1], columns], changed_features.loc[features.index[:-1], columns])


def test_features_do_not_repair_missing_or_duplicate_input() -> None:
    missing = _prices(5)
    missing.loc[missing.index[2], "Close"] = None
    with pytest.raises(ValueError, match="Close contains missing"):
        build_features(missing, context=_context())

    duplicate = pd.concat([_prices(2), _prices(1)])
    with pytest.raises(ValueError, match="duplicate dates"):
        build_features(duplicate, context=_context())


def test_volume_features_are_computed_without_filling() -> None:
    features = build_features(_prices(25), context=_context())
    assert {"volume_sma_20", "volume_ratio_20"}.issubset(features.columns)
    assert pd.isna(features.iloc[18]["volume_sma_20"])
    assert features.iloc[19]["volume_ratio_20"] == pytest.approx(1.0)


def test_baseline_signal_rules_are_deterministic() -> None:
    features = build_features(_prices(), context=_context())
    signals = BaselineStrategy().generate_signal(features)
    assert set(signals.iloc[:20]) == {"HOLD"}
    assert signals.iloc[20] == "BUY"


def test_baseline_rejects_unfeatured_input() -> None:
    with pytest.raises(ValueError, match="Missing baseline feature"):
        BaselineStrategy().generate_signal(pd.DataFrame({"close": [1.0]}))


def test_price_features_use_adjusted_close_and_preserve_raw_columns() -> None:
    source = _prices(3)
    source["Adj Close"] = [100.0, 200.0, 400.0]
    original = source.copy(deep=True)
    features = build_features(source, context=_context())

    assert features.iloc[1]["daily_return"] == pytest.approx(1.0)
    assert features["price_representation"].eq("adjusted_close").all()
    pd.testing.assert_frame_equal(source, original)
    pd.testing.assert_series_equal(features["close"], original["Close"], check_names=False)


def test_feature_output_contains_context_and_timestamp_metadata() -> None:
    features = build_features(_prices(3), context=_context())

    assert features["security_id"].eq("TEST_SECURITY").all()
    assert features["pit_membership"].eq("SET50:eligible").all()
    assert features["identity_status"].eq("VERIFIED").all()
    assert features["data_status"].eq("USE").all()
    assert features["data_timestamp"].equals(features.index.to_series())
    assert features["feature_timestamp"].equals(features.index.to_series())
    assert features["information_cutoff"].eq(pd.Timestamp("2024-12-31 23:59:59")).all()


def test_missing_pit_context_is_rejected() -> None:
    with pytest.raises(ValueError, match="FeatureContext"):
        build_features(_prices())


def test_ineligible_pit_context_is_rejected() -> None:
    with pytest.raises(ValueError, match="PIT membership"):
        build_features(_prices(), context=_context(pit_membership=False))


def test_status_contract_preserves_flags_and_blocks_unresolved_values() -> None:
    flagged = build_features(_prices(25), context=_context(data_status="USE_WITH_FLAG"))
    assert flagged["data_status"].eq("USE_WITH_FLAG").all()
    assert pd.notna(flagged.iloc[-1]["momentum_20"])

    unavailable = build_features(_prices(25), context=_context(data_status="SOURCE_NEEDED"))
    assert unavailable["data_status"].eq("SOURCE_NEEDED").all()
    assert unavailable["momentum_20"].isna().all()


def test_target_and_label_columns_are_rejected() -> None:
    source = _prices()
    source["future_return"] = 0.0
    with pytest.raises(ValueError, match="unsupported|target|label"):
        build_features(source, context=_context())


def test_corporate_action_metadata_limitation_is_explicit() -> None:
    source = _prices(2).drop(columns=["Dividends", "Stock Splits"])
    features = build_features(source, context=_context())

    assert features["corporate_action_metadata_status"].eq("UNAVAILABLE").all()

from __future__ import annotations

import pandas as pd
import pytest

from src.data.features import FeatureContext, build_features


def _fixture(count: int = 60) -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=count, freq="D")
    adjusted = pd.Series(range(100, 100 + count), index=index, dtype=float)
    volume = pd.Series(range(10, 10 + count), index=index, dtype=float)
    return pd.DataFrame(
        {
            "Close": adjusted * 10,
            "Adj Close": adjusted,
            "Volume": volume,
            "Dividends": 0.0,
            "Stock Splits": 0.0,
        },
        index=index,
    )


def _context(**overrides: object) -> FeatureContext:
    values: dict[str, object] = {
        "security_id": "TEST_SECURITY",
        "pit_membership": "SET50:eligible",
        "identity_status": "VERIFIED",
        "data_status": "USE",
        "information_cutoff": "2024-12-31 23:59:59",
        "source_data": "synthetic-validation-fixture",
    }
    values.update(overrides)
    return FeatureContext(**values)


def test_all_feature_formulas_and_warmups_are_aligned() -> None:
    source = _fixture()
    features = build_features(source, context=_context())
    row = features.iloc[20]
    expected_returns = pd.Series(source["Adj Close"].pct_change().iloc[1:21].to_numpy())

    assert row["daily_return"] == pytest.approx(120 / 119 - 1)
    assert row["momentum_20"] == pytest.approx(120 / 100 - 1)
    assert row["sma_20"] == pytest.approx(sum(range(101, 121)) / 20)
    assert pd.isna(features.iloc[19]["momentum_20"])
    assert pd.notna(features.iloc[20]["momentum_20"])
    assert pd.isna(features.iloc[48]["sma_50"])
    assert pd.notna(features.iloc[49]["sma_50"])
    trend_row = features.iloc[49]
    assert trend_row["trend_20_50"] == pytest.approx(trend_row["sma_20"] / trend_row["sma_50"] - 1)
    assert row["volatility_20"] == pytest.approx(expected_returns.std(ddof=0))
    assert row["volume_sma_20"] == pytest.approx(sum(range(11, 31)) / 20)
    assert row["volume_ratio_20"] == pytest.approx(30 / (sum(range(11, 31)) / 20))


def test_price_features_all_use_adjusted_close_not_raw_close() -> None:
    source = _fixture()
    features = build_features(source, context=_context())

    assert features.iloc[20]["daily_return"] == pytest.approx(120 / 119 - 1)
    assert features.iloc[20]["sma_20"] == pytest.approx(sum(range(101, 121)) / 20)
    assert features.iloc[20]["momentum_20"] == pytest.approx(0.2)
    assert features["price_representation"].eq("adjusted_close").all()


def test_unresolved_identity_is_unavailable_and_never_merged() -> None:
    features = build_features(
        _fixture(25),
        context=_context(identity_status="UNSUPPORTED_PREDECESSOR_SUCCESSOR"),
    )

    assert features["momentum_20"].isna().all()
    assert features["validity_status"].eq("IDENTITY_UNRESOLVED").all()


def test_timestamp_boundary_rejects_future_information() -> None:
    with pytest.raises(ValueError, match="timestamps"):
        build_features(
            _fixture(3),
            context=_context(information_cutoff="2023-12-31 23:59:59"),
        )


def test_deterministic_values_and_metadata() -> None:
    source = _fixture()
    first = build_features(source, context=_context())
    second = build_features(source, context=_context())
    pd.testing.assert_frame_equal(first, second)


def test_per_row_pit_and_status_fail_closed() -> None:
    source = _fixture(3)
    context = _context(
        pit_membership=pd.Series(["SET50:eligible", False, "SET50:eligible"], index=source.index),
        data_status=pd.Series(["USE", "SOURCE_NEEDED", "USE_WITH_FLAG"], index=source.index),
    )
    features = build_features(source, context=context)

    assert pd.notna(features.iloc[0]["daily_return"]) is False
    assert pd.isna(features.iloc[1]["daily_return"])
    assert features.iloc[1]["validity_status"] == "INELIGIBLE"
    assert features.iloc[2]["data_status"] == "USE_WITH_FLAG"

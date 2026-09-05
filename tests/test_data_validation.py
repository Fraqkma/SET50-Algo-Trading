from __future__ import annotations

import pandas as pd

from src.data.validator import validate_market_data


def test_missing_data_is_detected() -> None:
    df = pd.DataFrame(
        {
            "open": [10.0, None, 11.0],
            "high": [11.0, 12.0, 12.0],
            "low": [9.0, 10.0, 10.5],
            "close": [10.5, 11.5, 12.5],
            "volume": [1000, 1500, 2000],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )

    result = validate_market_data(df)
    assert result["is_valid"] is False
    assert any("missing" in issue.lower() for issue in result["issues"])


def test_negative_prices_and_invalid_volume_are_rejected() -> None:
    df = pd.DataFrame(
        {
            "open": [10.0, -1.0, 11.0],
            "high": [11.0, 12.0, 12.0],
            "low": [9.0, 10.0, 10.5],
            "close": [10.5, 11.5, 12.5],
            "volume": [1000, 0, 2000],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-03"]),
    )

    result = validate_market_data(df)
    assert result["is_valid"] is False
    assert any("price" in issue.lower() or "volume" in issue.lower() for issue in result["issues"])


def test_raw_path_generation() -> None:
    from src.data.yahoo_loader import build_raw_price_path

    path = build_raw_price_path("AOT")
    assert path.name == "AOT.BK.parquet"
    assert "data/raw/prices" in str(path)

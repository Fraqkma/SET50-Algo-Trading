import pandas as pd
import pytest

from src.competition.data_sources import (
    SETTRADE_PRODUCTION,
    TRADESIM_OFFICIAL_HISTORY,
    compare_market_sources,
)


def test_source_comparison_keeps_matches_differences_and_missing_rows_separate():
    left = pd.DataFrame([
        {"symbol": "PTT", "timestamp": "2026-10-20", "close": 30.0, "volume": 100},
        {"symbol": "AOT", "timestamp": "2026-10-20", "close": 55.0, "volume": 200},
    ])
    right = pd.DataFrame([
        {"symbol": "PTT", "timestamp": "2026-10-20", "close": 30.0, "volume": 100},
        {"symbol": "AOT", "timestamp": "2026-10-20", "close": 54.5, "volume": 200},
        {"symbol": "BBL", "timestamp": "2026-10-20", "close": 150.0, "volume": 300},
    ])
    result = compare_market_sources(left, right,
        left_source=SETTRADE_PRODUCTION,
        right_source=TRADESIM_OFFICIAL_HISTORY,
        values=("close", "volume"))
    assert result["counts"] == {"MATCH": 1, "DIVERGENCE": 1, "LEFT_ONLY": 0, "RIGHT_ONLY": 1}
    assert result["persisted_data_modified"] is False
    assert next(row for row in result["rows"] if row["symbol"] == "AOT")["differences"] == ["close"]


def test_source_comparison_rejects_ambiguous_or_duplicate_rows():
    frame = pd.DataFrame([{"symbol": "PTT", "timestamp": "d", "close": 30}])
    with pytest.raises(ValueError, match="distinct source labels"):
        compare_market_sources(frame, frame, left_source=SETTRADE_PRODUCTION,
                               right_source=SETTRADE_PRODUCTION)
    duplicate = pd.concat([frame, frame], ignore_index=True)
    with pytest.raises(ValueError, match="duplicate comparison keys"):
        compare_market_sources(duplicate, frame, left_source=SETTRADE_PRODUCTION,
                               right_source=TRADESIM_OFFICIAL_HISTORY)

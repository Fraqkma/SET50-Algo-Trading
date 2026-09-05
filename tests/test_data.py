"""Tests for the market data loading and cleaning pipeline."""

from __future__ import annotations

import pandas as pd

from src.data.cleaner import clean_market_data
from src.data.yahoo_loader import download_set50_data, normalize_yahoo_symbol


def test_symbol_normalization() -> None:
    assert normalize_yahoo_symbol("AOT") == "AOT.BK"
    assert normalize_yahoo_symbol("AOT.BK") == "AOT.BK"
    assert normalize_yahoo_symbol("CPALL") == "CPALL.BK"


def test_clean_market_data_keeps_expected_columns() -> None:
    data = pd.DataFrame(
        {
            "Open": [10.0, 11.0],
            "High": [11.0, 12.0],
            "Low": [9.0, 10.0],
            "Close": [10.5, 11.5],
            "Adj Close": [10.4, 11.4],
            "Volume": [1000, 1200],
        },
        index=pd.to_datetime(["2024-01-01", "2024-01-02"]),
    )

    cleaned = clean_market_data(data)
    assert {"open", "high", "low", "close", "adjusted_close", "volume"}.issubset(cleaned.columns)
    assert cleaned.index.is_monotonic_increasing


def test_downloader_skips_existing_file(tmp_path, monkeypatch) -> None:
    """When a symbol is already cached locally, the downloader should not re-download it."""
    from src import data as data_package

    data_package.PROJECT_ROOT = tmp_path

    raw_dir = tmp_path / "data" / "raw" / "prices"
    raw_dir.mkdir(parents=True, exist_ok=True)
    existing = raw_dir / "AOT.BK.parquet"
    existing.write_bytes(b"cached")

    calls = []

    def fake_download(*args, **kwargs):
        calls.append((args, kwargs))
        return pd.DataFrame({"Close": [10.0]})

    monkeypatch.setattr("yfinance.download", fake_download)

    done = download_set50_data("2024-01-01", "2024-03-31", force=False, project_root=tmp_path)
    assert done["successful_symbols"] == []
    assert calls == []
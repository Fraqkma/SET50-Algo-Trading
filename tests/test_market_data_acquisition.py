from __future__ import annotations

import tempfile
from pathlib import Path

import pandas as pd

from src.data.market_data_acquisition import (
    acquire,
    historical_universe,
    normalize_download_frame,
    validate_raw_frame,
    verified_mapping,
    valid_existing_file,
)


def test_historical_universe_and_date_range():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        path = Path(directory) / "historical_set50.csv"
        pd.DataFrame(
            {
                "symbol": ["BBB", "AAA", "AAA"],
                "effective_from": ["2023-07-01", "2023-01-01", "2024-01-01"],
                "effective_to": ["2023-12-31", "2023-06-30", "2024-06-30"],
            }
        ).to_csv(path, index=False)
        symbols, start, end = historical_universe(path)
    assert symbols["symbol"].tolist() == ["AAA", "BBB"]
    assert start.isoformat() == "2023-01-01"
    assert end.isoformat() == "2024-06-30"


def test_verified_mapping_filters_unresolved():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        path = Path(directory) / "audit.csv"
        pd.DataFrame(
            {
                "SET Symbol": ["AAA", "BBB"],
                "Yahoo Ticker": ["AAA.BK", "BBB.BK"],
                "Status": ["VERIFIED", "NOT_FOUND"],
            }
        ).to_csv(path, index=False)
        verified, unresolved = verified_mapping(path)
    assert verified["Yahoo Ticker"].tolist() == ["AAA.BK"]
    assert unresolved["SET Symbol"].tolist() == ["BBB"]


def test_timezone_normalization_and_required_actions():
    index = pd.date_range("2024-01-01", periods=2, tz="UTC")
    source = pd.DataFrame(
        {
            "Open": [1, 2], "High": [2, 3], "Low": [0.5, 1.5],
            "Close": [1.5, 2.5], "Adj Close": [1.5, 2.5], "Volume": [10, 20],
        }, index=index
    )
    result = normalize_download_frame(source, "AAA.BK")
    assert result["Date"].tolist() == ["2024-01-01", "2024-01-02"]
    assert result["Dividends"].tolist() == [0.0, 0.0]
    assert result["Stock Splits"].tolist() == [0.0, 0.0]
    assert validate_raw_frame(result) == []


def test_ohlc_validation_reports_anomalies_without_cleaning():
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-02", "2024-01-01"], "Open": [2, 2], "High": [1, 3],
            "Low": [2, 1], "Close": [2, 2], "Volume": [-1, 3],
        }
    )
    issues = validate_raw_frame(frame)
    assert "dates are not sorted" in issues
    assert "High < Low" in issues
    assert any(issue.startswith("High below Open/Close by") for issue in issues)
    assert "negative volume" in issues
    assert frame.loc[0, "High"] == 1


def test_ohlc_validation_allows_small_relative_rounding_difference():
    frame = pd.DataFrame(
        {
            "Date": ["2024-01-01"], "Open": [100.00], "High": [99.95],
            "Low": [99.00], "Close": [99.90], "Volume": [10],
        }
    )
    assert validate_raw_frame(frame) == []


def test_banpu_known_suspension_gap_is_whitelisted():
    frame = pd.DataFrame(
        {
            "Date": ["2026-07-16", "2026-08-04"], "Open": [10, 10],
            "High": [10, 10], "Low": [10, 10], "Close": [10, 10], "Volume": [1, 1],
        }
    )
    assert validate_raw_frame(frame, symbol="BANPU") == []


def test_resume_validation_rejects_malformed_file():
    with tempfile.TemporaryDirectory(dir=Path.cwd()) as directory:
        path = Path(directory) / "AAA.BK.csv"
        pd.DataFrame({"Date": ["2024-01-01"], "Open": [1]}).to_csv(path, index=False)
        valid, _, issues = valid_existing_file(path)
    assert not valid
    assert any("missing required columns" in issue for issue in issues)


def _write_gate2_inputs(project_root: Path) -> None:
    constituents = project_root / "data" / "processed" / "constituents"
    constituents.mkdir(parents=True)
    pd.DataFrame(
        {
            "symbol": ["AAA", "BBB"],
            "effective_from": ["2024-01-01", "2024-01-01"],
            "effective_to": ["2024-01-31", "2024-01-31"],
        }
    ).to_csv(constituents / "historical_set50.csv", index=False)
    (project_root / "reports").mkdir()
    pd.DataFrame(
        {
            "SET Symbol": ["AAA", "BBB"],
            "Yahoo Ticker": ["AAA.BK", "BBB.BK"],
            "Status": ["VERIFIED", "VERIFIED"],
        }
    ).to_csv(project_root / "reports" / "yahoo_ticker_audit.csv", index=False)


def _download_frame() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Open": [1.0], "High": [2.0], "Low": [1.0], "Close": [1.5],
            "Adj Close": [1.5], "Volume": [10.0], "Dividends": [0.0],
            "Stock Splits": [0.0],
        },
        index=pd.DatetimeIndex(["2024-01-02"], name="Date"),
    )


def test_acquire_isolates_failed_ticker(tmp_path):
    _write_gate2_inputs(tmp_path)
    requested = []

    def downloader(**kwargs):
        requested.append(kwargs["tickers"])
        if kwargs["tickers"] == "AAA.BK":
            raise RuntimeError("temporary network failure")
        return _download_frame()

    records = acquire(tmp_path, sleep_seconds=0, retries=0, downloader=downloader)

    assert requested == ["AAA.BK", "BBB.BK"]
    assert [record.status for record in records] == ["FAILED", "SUCCESS"]
    assert (tmp_path / "data" / "raw" / "market_data" / "BBB_BK.csv").exists()


def test_acquire_skips_valid_existing_file(tmp_path):
    _write_gate2_inputs(tmp_path)
    output = tmp_path / "data" / "raw" / "market_data"
    output.mkdir(parents=True)
    _download_frame().reset_index().assign(Date=lambda frame: frame["Date"].dt.strftime("%Y-%m-%d")).to_csv(
        output / "AAA_BK.csv", index=False
    )

    def unexpected_download(**kwargs):
        raise AssertionError(f"unexpected download for {kwargs['tickers']}")

    records = acquire(tmp_path, sleep_seconds=0, retries=0, downloader=unexpected_download)

    assert records[0].status == "SUCCESS"
    assert "resume" in records[0].error

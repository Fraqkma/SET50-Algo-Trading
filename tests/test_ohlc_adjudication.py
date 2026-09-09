from __future__ import annotations

import csv
from pathlib import Path

from src.data.ohlc_adjudication import find_ohlc_anomalies


def test_adjudication_records_each_envelope_breach(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    raw = tmp_path / "data" / "raw"
    reports.mkdir()
    raw.mkdir(parents=True)
    _write_csv(reports / "market_data_remediation.csv", [{
        "set_symbol": "AAA", "yahoo_ticker": "AAA.BK", "raw_file": "data/raw/AAA.csv",
        "issue_classification": "OHLC_ANOMALY",
    }])
    _write_csv(raw / "AAA.csv", [
        {"Date": "2024-01-02", "Open": "10", "High": "9", "Low": "8", "Close": "10", "Volume": "1"},
        {"Date": "2024-01-03", "Open": "10", "High": "11", "Low": "11", "Close": "10", "Volume": "1"},
    ])
    findings = find_ohlc_anomalies(tmp_path)
    assert [item.violated_rule for item in findings] == ["HIGH_BELOW_OPEN_OR_CLOSE", "LOW_ABOVE_OPEN_OR_CLOSE"]
    assert {item.approval_decision for item in findings} == {"NEEDS_REVIEW"}
    assert all(item.classification == "YAHOO_VENDOR_DATA_ISSUE_SUSPECTED" for item in findings)


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

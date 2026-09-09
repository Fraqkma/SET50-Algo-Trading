from __future__ import annotations

from pathlib import Path

from src.data.market_data_remediation import classify_acquisition_record, write_research_readiness_reports


def test_success_is_approved_without_silent_promotion() -> None:
    record = classify_acquisition_record(_row("AAA", "SUCCESS"))
    assert record.approval_status == "APPROVED"
    assert record.issue_classification == "NONE"
    assert record.approved_from == "2024-01-01"


def test_readiness_manifest_contains_only_explicitly_approved_rows(tmp_path: Path) -> None:
    reports = tmp_path / "reports"
    reports.mkdir()
    _write_csv(reports / "market_data_acquisition.csv", [
        _row("AAA", "SUCCESS"), _row("BBB", "PARTIAL", "High below Open/Close"),
    ])
    records = write_research_readiness_reports(tmp_path)
    assert len(records) == 2
    manifest = (tmp_path / "data" / "processed" / "approved_market_data_manifest.csv").read_text()
    assert "AAA" in manifest
    assert "BBB" not in manifest


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    import csv
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def test_ohlc_anomaly_requires_review() -> None:
    record = classify_acquisition_record(_row("AAA", "PARTIAL", "High below Open/Close by 1.00"))
    assert record.approval_status == "NEEDS_REVIEW"
    assert "OHLC_ANOMALY" in record.issue_classification
    assert "YAHOO_VENDOR_DATA_ISSUE_SUSPECTED" in record.issue_classification


def test_gulf_is_approved_only_for_observed_post_merger_range() -> None:
    record = classify_acquisition_record(_row("GULF", "PARTIAL", "missing reference trading dates", "2025-04-03", "2026-09-04"))
    assert record.approval_status == "APPROVED_WITH_KNOWN_GAP"
    assert record.approved_from == "2025-04-03"


def test_tidlor_is_approved_only_after_corporate_action_gap() -> None:
    record = classify_acquisition_record(_row("TIDLOR", "PARTIAL_KNOWN_GAP", "missing reference trading dates", "2025-05-16", "2026-09-04"))
    assert record.approval_status == "APPROVED_WITH_KNOWN_GAP"
    assert record.approved_from == "2025-05-16"


def test_banpu_remains_reviewable_when_suspension_has_other_warnings() -> None:
    record = classify_acquisition_record(_row("BANPU", "PARTIAL", "High below Open/Close; missing reference trading dates"))
    assert record.approval_status == "NEEDS_REVIEW"
    assert "KNOWN_SUSPENSION" in record.issue_classification


def test_intuch_is_rejected_without_guessed_replacement() -> None:
    record = classify_acquisition_record(_row("INTUCH", "NO_DATA"))
    assert record.approval_status == "REJECTED"
    assert "TICKER_IDENTITY_ISSUE" in record.issue_classification


def _row(symbol: str, status: str, findings: str = "", start: str = "2024-01-01", end: str = "2024-12-31") -> dict[str, str]:
    return {"SET Symbol": symbol, "Yahoo Ticker": f"{symbol}.BK", "Status": status,
            "Source": "Yahoo Finance", "Output File": f"data/raw/market_data/{symbol}.csv",
            "Validation Issues": findings, "Actual First Date": start, "Actual Last Date": end}

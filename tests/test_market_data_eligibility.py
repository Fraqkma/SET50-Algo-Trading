from __future__ import annotations

import csv
from pathlib import Path

import pytest

from src.data.eligibility import MarketDataEligibilityGate


@pytest.fixture
def gate_root(tmp_path: Path) -> Path:
    constituents = tmp_path / "data" / "processed" / "constituents"
    reports = tmp_path / "reports"
    raw = tmp_path / "data" / "raw" / "market_data"
    constituents.mkdir(parents=True)
    reports.mkdir()
    raw.mkdir(parents=True)
    _write_csv(constituents / "historical_set50.csv", [
        {"symbol": "AAA", "effective_from": "2024-01-01", "effective_to": "2024-12-31"},
        {"symbol": "INTUCH", "effective_from": "2024-01-01", "effective_to": "2025-06-30"},
        {"symbol": "GULF", "effective_from": "2024-01-01", "effective_to": "2025-12-31"},
        {"symbol": "BANPU", "effective_from": "2026-01-01", "effective_to": "2026-12-31"},
        {"symbol": "FLAG", "effective_from": "2024-01-01", "effective_to": "2024-12-31"},
        {"symbol": "NOMAP", "effective_from": "2024-01-01", "effective_to": "2024-12-31"},
        {"symbol": "MISSING", "effective_from": "2024-01-01", "effective_to": "2024-12-31"},
    ])
    _write_csv(reports / "yahoo_ticker_audit.csv", [
        {"SET Symbol": "AAA", "Yahoo Ticker": "AAA.AUDITED", "Status": "VERIFIED"},
        {"SET Symbol": "INTUCH", "Yahoo Ticker": "INTUCH.AUDITED", "Status": "NOT_FOUND"},
        {"SET Symbol": "GULF", "Yahoo Ticker": "GULF.AUDITED", "Status": "VERIFIED"},
        {"SET Symbol": "BANPU", "Yahoo Ticker": "BANPU.AUDITED", "Status": "VERIFIED"},
        {"SET Symbol": "FLAG", "Yahoo Ticker": "FLAG.AUDITED", "Status": "VERIFIED"},
        {"SET Symbol": "NOMAP", "Yahoo Ticker": "", "Status": "NOT_FOUND"},
        {"SET Symbol": "MISSING", "Yahoo Ticker": "MISSING.AUDITED", "Status": "VERIFIED"},
    ])
    _write_csv(reports / "market_data_acquisition.csv", [
        _acquisition("AAA", "SUCCESS", "data/raw/market_data/explicit_aaa.csv"),
        _acquisition("INTUCH", "NO_DATA", ""),
        _acquisition("GULF", "PARTIAL", "data/raw/market_data/explicit_gulf.csv", "missing historical coverage"),
        _acquisition("BANPU", "PARTIAL", "data/raw/market_data/explicit_banpu.csv", "High below Open/Close"),
        _acquisition("FLAG", "PARTIAL", "data/raw/market_data/explicit_flag.csv", "invalid OHLC"),
        _acquisition("NOMAP", "NO_DATA", ""),
        _acquisition("MISSING", "SUCCESS", "data/raw/market_data/not_present.csv"),
    ])
    _write_csv(reports / "market_data_remediation.csv", [
        _approval("AAA", "APPROVED"),
        _approval("INTUCH", "REJECTED"),
        _approval("GULF", "APPROVED", "2025-04-03", "2025-12-31"),
        _approval("BANPU", "NEEDS_REVIEW"),
        _approval("FLAG", "NEEDS_REVIEW"),
        _approval("NOMAP", "REJECTED"),
        _approval("MISSING", "APPROVED"),
    ])
    _write_csv(tmp_path / "data" / "processed" / "approved_market_data_manifest.csv", [
        _manifest("AAA", "APPROVED"), _manifest("GULF", "APPROVED_WITH_KNOWN_GAP", "2025-04-03", "2025-12-31"),
        _manifest("MISSING", "APPROVED"),
    ])
    _write_csv(raw / "explicit_aaa.csv", [{"Date": "2024-06-03", "Open": "1"}])
    _write_csv(raw / "explicit_gulf.csv", [{"Date": "2025-04-03", "Open": "1"}])
    _write_csv(raw / "explicit_banpu.csv", [{"Date": "2026-08-04", "Open": "1"}])
    _write_csv(raw / "explicit_flag.csv", [{"Date": "2024-06-03", "Open": "1"}])
    return tmp_path


def test_valid_historical_member_date_resolves_explicit_audited_file(gate_root: Path) -> None:
    decision = MarketDataEligibilityGate(gate_root).assess("AAA", "2024-06-03")
    assert decision.eligible
    assert decision.reason is None
    assert decision.yahoo_ticker == "AAA.AUDITED"
    assert decision.raw_file == gate_root / "data" / "raw" / "market_data" / "explicit_aaa.csv"


def test_date_outside_membership_is_excluded(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("AAA", "2025-01-01").reason == "OUTSIDE_SET50_MEMBERSHIP_PERIOD"


def test_unknown_symbol_is_excluded(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("UNKNOWN", "2024-06-03").reason == "UNKNOWN_SET_SYMBOL"


def test_unavailable_yahoo_mapping_is_excluded(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("NOMAP", "2024-06-03").reason == "YAHOO_MAPPING_UNAVAILABLE"


def test_missing_raw_data_file_is_excluded(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("MISSING", "2024-06-03").reason == "RAW_FILE_MISSING"


def test_known_coverage_gap_is_excluded_without_forward_fill(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("AAA", "2024-06-04").reason == "DATE_NOT_IN_RAW_DATA"


def test_banpu_known_suspension_is_excluded_before_gap_filling(gate_root: Path) -> None:
    assert MarketDataEligibilityGate(gate_root).assess("BANPU", "2026-07-20").reason == "BANPU_KNOWN_SUSPENSION"


def test_intuch_gulf_continuity_boundaries_preserve_identities(gate_root: Path) -> None:
    gate = MarketDataEligibilityGate(gate_root)
    assert gate.assess("INTUCH", "2025-04-01").reason == "INTUCH_POST_MERGER_IDENTITY_RETIRED"
    assert gate.assess("INTUCH", "2025-03-31").reason == "YAHOO_MAPPING_UNAVAILABLE"
    assert gate.assess("GULF", "2025-03-31").reason == "GULF_PRE_MERGER_CONTINUITY_BOUNDARY"
    approved = gate.assess("GULF", "2025-04-03")
    assert approved.eligible
    assert approved.acquisition_status == "PARTIAL"


def test_invalid_or_flagged_acquisition_data_is_excluded(gate_root: Path) -> None:
    decision = MarketDataEligibilityGate(gate_root).assess("FLAG", "2024-06-03")
    assert decision.reason == "APPROVAL_STATUS_NEEDS_REVIEW"
    assert decision.validation_issues == "invalid OHLC"


def test_gate_never_guesses_ticker_or_constructs_bk_filename(gate_root: Path) -> None:
    decision = MarketDataEligibilityGate(gate_root).assess("AAA.BK", "2024-06-03")
    assert decision.reason == "UNKNOWN_SET_SYMBOL"


def _acquisition(symbol: str, status: str, output_file: str, issues: str = "") -> dict[str, str]:
    return {"SET Symbol": symbol, "Source": "Yahoo Finance via yfinance", "Status": status,
            "Output File": output_file, "Validation Issues": issues}


def _approval(symbol: str, status: str, approved_from: str = "", approved_to: str = "") -> dict[str, str]:
    return {"set_symbol": symbol, "approval_status": status, "approved_from": approved_from, "approved_to": approved_to}


def _manifest(symbol: str, status: str, approved_from: str = "2024-01-01", approved_to: str = "2024-12-31") -> dict[str, str]:
    return {"set_symbol": symbol, "approval_status": status, "approved_from": approved_from, "approved_to": approved_to}


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

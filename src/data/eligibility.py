"""Date-aware approval gate for historical SET50 market data.

This module is the sole policy boundary that future feature and backtest code
must use before reading a raw market-data file.  It only reads the existing
constituent, ticker-audit, acquisition-report, and raw CSV artifacts; it never
downloads, cleans, fills, or modifies data.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from .market_data_remediation import APPROVED_STATUSES


ROOT = Path(__file__).resolve().parents[2]
INTUCH_GULF_EFFECTIVE_DATE = date(2025, 4, 1)
BANPU_SUSPENSION_START = date(2026, 7, 17)
BANPU_SUSPENSION_END = date(2026, 8, 3)


@dataclass(frozen=True)
class EligibilityDecision:
    """Auditable result of a market-data eligibility check."""

    symbol: str
    requested_date: date
    eligible: bool
    reason: str | None
    source: str | None = None
    raw_file: Path | None = None
    yahoo_ticker: str | None = None
    audit_status: str | None = None
    acquisition_status: str | None = None
    validation_issues: str | None = None


class MarketDataEligibilityGate:
    """Resolve whether one SET symbol has approved raw data on one date.

    Approved means the symbol was a SET50 constituent on that date, has an
    explicitly VERIFIED Yahoo mapping, has a SUCCESS acquisition record, and
    has an explicit raw CSV path containing that date.  PARTIAL, NO_DATA, and
    other non-success acquisition states are excluded rather than repaired.
    """

    def __init__(self, project_root: str | Path = ROOT) -> None:
        self.project_root = Path(project_root).resolve()
        self._constituents = self._read_csv(
            self.project_root / "data" / "processed" / "constituents" / "historical_set50.csv",
            {"symbol", "effective_from", "effective_to"},
        )
        self._audit = self._index_rows(
            self._read_csv(
                self.project_root / "reports" / "yahoo_ticker_audit.csv",
                {"SET Symbol", "Yahoo Ticker", "Status"},
            ),
            "SET Symbol",
        )
        self._acquisition = self._index_rows(
            self._read_csv(
                self.project_root / "reports" / "market_data_acquisition.csv",
                {"SET Symbol", "Source", "Status", "Output File"},
            ),
            "SET Symbol",
        )
        self._approval = self._index_rows(
            self._read_csv(
                self.project_root / "reports" / "market_data_remediation.csv",
                {"set_symbol", "approval_status", "approved_from", "approved_to"},
            ),
            "set_symbol",
        )
        self._manifest = self._index_rows(
            self._read_csv(
                self.project_root / "data" / "processed" / "approved_market_data_manifest.csv",
                {"set_symbol", "approval_status", "approved_from", "approved_to"},
            ),
            "set_symbol",
        )
        self._raw_date_cache: dict[Path, set[date]] = {}

    def assess(self, symbol: str, requested_date: str | date | datetime) -> EligibilityDecision:
        """Return the deterministic eligibility decision for ``(symbol, date)``."""
        normalized_symbol = str(symbol).strip().upper()
        target_date = self._parse_date(requested_date)
        memberships = [row for row in self._constituents if row["symbol"].strip().upper() == normalized_symbol]
        if not memberships:
            return self._exclude(normalized_symbol, target_date, "UNKNOWN_SET_SYMBOL")
        if not any(self._is_active(row, target_date) for row in memberships):
            return self._exclude(normalized_symbol, target_date, "OUTSIDE_SET50_MEMBERSHIP_PERIOD")

        # Identity boundaries are applied before provider/data checks.  They
        # never rewrite membership symbols or fabricate continuity price data.
        if normalized_symbol == "INTUCH" and target_date >= INTUCH_GULF_EFFECTIVE_DATE:
            return self._exclude(normalized_symbol, target_date, "INTUCH_POST_MERGER_IDENTITY_RETIRED")
        if normalized_symbol == "GULF" and target_date < INTUCH_GULF_EFFECTIVE_DATE:
            return self._exclude(normalized_symbol, target_date, "GULF_PRE_MERGER_CONTINUITY_BOUNDARY")
        if normalized_symbol == "BANPU" and BANPU_SUSPENSION_START <= target_date <= BANPU_SUSPENSION_END:
            return self._exclude(normalized_symbol, target_date, "BANPU_KNOWN_SUSPENSION")

        audit = self._audit.get(normalized_symbol)
        if audit is None:
            return self._exclude(normalized_symbol, target_date, "YAHOO_AUDIT_RECORD_MISSING")
        if audit["Status"] != "VERIFIED":
            return self._exclude(
                normalized_symbol, target_date, "YAHOO_MAPPING_UNAVAILABLE", audit_status=audit["Status"]
            )

        acquisition = self._acquisition.get(normalized_symbol)
        if acquisition is None:
            return self._exclude(
                normalized_symbol, target_date, "ACQUISITION_RECORD_MISSING",
                yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"],
            )
        approval = self._approval.get(normalized_symbol)
        if approval is None:
            return self._exclude(
                normalized_symbol, target_date, "APPROVAL_RECORD_MISSING",
                source=acquisition["Source"], yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"],
                acquisition_status=acquisition["Status"], validation_issues=acquisition.get("Validation Issues") or None,
            )
        if approval["approval_status"] not in APPROVED_STATUSES:
            return self._exclude(
                normalized_symbol, target_date, f"APPROVAL_STATUS_{approval['approval_status']}",
                source=acquisition["Source"], yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"],
                acquisition_status=acquisition["Status"], validation_issues=acquisition.get("Validation Issues") or None,
            )
        manifest = self._manifest.get(normalized_symbol)
        if manifest is None or manifest["approval_status"] not in APPROVED_STATUSES:
            return self._exclude(
                normalized_symbol, target_date, "APPROVED_MANIFEST_RECORD_MISSING", source=acquisition["Source"],
                yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"], acquisition_status=acquisition["Status"],
            )
        if not self._within_approved_range(manifest, target_date):
            return self._exclude(
                normalized_symbol, target_date, "OUTSIDE_APPROVED_DATA_RANGE", source=acquisition["Source"],
                yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"], acquisition_status=acquisition["Status"],
            )

        raw_file = self._reported_raw_file(acquisition["Output File"])
        if raw_file is None or not raw_file.is_file():
            return self._exclude(
                normalized_symbol, target_date, "RAW_FILE_MISSING", source=acquisition["Source"],
                yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"],
                acquisition_status=acquisition["Status"], raw_file=raw_file,
            )
        if not self._contains_date(raw_file, target_date):
            return self._exclude(
                normalized_symbol, target_date, "DATE_NOT_IN_RAW_DATA", source=acquisition["Source"],
                yahoo_ticker=audit["Yahoo Ticker"], audit_status=audit["Status"],
                acquisition_status=acquisition["Status"], raw_file=raw_file,
            )
        return EligibilityDecision(
            symbol=normalized_symbol, requested_date=target_date, eligible=True, reason=None,
            source=acquisition["Source"], raw_file=raw_file, yahoo_ticker=audit["Yahoo Ticker"],
            audit_status=audit["Status"], acquisition_status=acquisition["Status"],
            validation_issues=acquisition.get("Validation Issues") or None,
        )

    def approved_manifest_record(self, symbol: str) -> dict[str, str] | None:
        """Return the explicit manifest record used to locate approved data."""
        return self._manifest.get(str(symbol).strip().upper())

    def approved_raw_file(self, symbol: str) -> Path | None:
        """Resolve the manifest's explicit raw path without assuming its first date is a member date."""
        record = self.approved_manifest_record(symbol)
        if record is None or record.get("approval_status") not in APPROVED_STATUSES:
            return None
        reported = record.get("raw_file", "")
        if not reported:
            return None
        candidate = (self.project_root / Path(reported)).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(f"Approved raw path escapes project root: {reported}") from exc
        return candidate

    def membership_end(self, symbol: str, requested_date: str | date | datetime) -> date | None:
        """Return the active historical SET50 membership end for a date."""
        normalized_symbol = str(symbol).strip().upper()
        target_date = self._parse_date(requested_date)
        periods = sorted(
            (
                date.fromisoformat(row["effective_from"]),
                date.fromisoformat(row["effective_to"]),
            )
            for row in self._constituents
            if row["symbol"].strip().upper() == normalized_symbol
        )
        for index, (start, end) in enumerate(periods):
            if not start <= target_date <= end:
                continue
            contiguous_end = end
            for next_start, next_end in periods[index + 1:]:
                if next_start > contiguous_end + timedelta(days=1):
                    break
                contiguous_end = max(contiguous_end, next_end)
            return contiguous_end
        return None

    @staticmethod
    def _read_csv(path: Path, required_columns: set[str]) -> list[dict[str, str]]:
        if not path.is_file():
            raise FileNotFoundError(f"Eligibility input is missing: {path}")
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            columns = set(reader.fieldnames or [])
            missing = required_columns - columns
            if missing:
                raise ValueError(f"Eligibility input {path} is missing columns: {sorted(missing)}")
            return [{key: (value or "").strip() for key, value in row.items()} for row in reader]

    @staticmethod
    def _index_rows(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
        indexed: dict[str, dict[str, str]] = {}
        for row in rows:
            normalized_key = row[key].strip().upper()
            if normalized_key in indexed:
                raise ValueError(f"Eligibility input has duplicate {key}: {normalized_key}")
            indexed[normalized_key] = row
        return indexed

    @staticmethod
    def _parse_date(value: str | date | datetime) -> date:
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(str(value).strip())
        except ValueError as exc:
            raise ValueError("requested_date must be an ISO date (YYYY-MM-DD)") from exc

    @staticmethod
    def _is_active(row: dict[str, str], target_date: date) -> bool:
        return date.fromisoformat(row["effective_from"]) <= target_date <= date.fromisoformat(row["effective_to"])

    @staticmethod
    def _within_approved_range(approval: dict[str, str], target_date: date) -> bool:
        start, end = approval.get("approved_from", ""), approval.get("approved_to", "")
        return (not start or target_date >= date.fromisoformat(start)) and (not end or target_date <= date.fromisoformat(end))

    def _reported_raw_file(self, reported_path: str) -> Path | None:
        if not reported_path:
            return None
        candidate = (self.project_root / Path(reported_path)).resolve()
        try:
            candidate.relative_to(self.project_root)
        except ValueError as exc:
            raise ValueError(f"Reported raw path escapes project root: {reported_path}") from exc
        return candidate

    def _contains_date(self, raw_file: Path, target_date: date) -> bool:
        if raw_file in self._raw_date_cache:
            return target_date in self._raw_date_cache[raw_file]
        dates: set[date] = set()
        with raw_file.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if "Date" not in (reader.fieldnames or []):
                return False
            for row in reader:
                try:
                    dates.add(date.fromisoformat((row.get("Date") or "").strip()))
                except ValueError:
                    continue
        self._raw_date_cache[raw_file] = dates
        return target_date in dates

    @staticmethod
    def _exclude(symbol: str, target_date: date, reason: str, **details: object) -> EligibilityDecision:
        return EligibilityDecision(symbol=symbol, requested_date=target_date, eligible=False, reason=reason, **details)

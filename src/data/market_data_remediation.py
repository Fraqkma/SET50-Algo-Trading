"""Reproducible approval records for immutable Gate 2 raw market data."""

from __future__ import annotations

import csv
import argparse
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
APPROVAL_STATUSES = {"APPROVED", "APPROVED_WITH_KNOWN_GAP", "REJECTED", "NEEDS_REVIEW"}
APPROVED_STATUSES = {"APPROVED", "APPROVED_WITH_KNOWN_GAP"}


@dataclass(frozen=True)
class ApprovalRecord:
    """A deterministic, auditable decision derived from Gate 1 and Gate 2 reports."""

    set_symbol: str
    yahoo_ticker: str
    raw_file: str
    acquisition_status: str
    validation_findings: str
    affected_dates_or_ranges: str
    issue_classification: str
    evidence_source: str
    approval_status: str
    reason: str
    approved_from: str = ""
    approved_to: str = ""


def classify_acquisition_record(record: dict[str, str]) -> ApprovalRecord:
    """Classify one acquisition row without modifying raw data or reports."""
    symbol = record["SET Symbol"].strip().upper()
    status = record["Status"].strip()
    findings = record.get("Validation Issues", "").strip()
    raw_file = record.get("Output File", "").strip()
    dates = _date_range(record)
    evidence = "reports/market_data_acquisition.csv; reports/yahoo_ticker_audit.csv"

    if status == "SUCCESS":
        return _record(
            record, "NONE", evidence, "APPROVED", "No acquisition validation findings were recorded.",
            approved_from=record.get("Actual First Date", "").strip(), approved_to=record.get("Actual Last Date", "").strip(),
        )
    if symbol == "INTUCH":
        return _record(
            record, "MISSING_YAHOO_DATA;CORPORATE_ACTION_ISSUE;TICKER_IDENTITY_ISSUE", evidence,
            "REJECTED", "Yahoo mapping/data is unavailable; retain INTUCH only as the pre-merger identity.",
        )
    if symbol == "GULF":
        return _record(
            record, "INSUFFICIENT_HISTORICAL_COVERAGE;CORPORATE_ACTION_ISSUE", evidence,
            "APPROVED_WITH_KNOWN_GAP",
            "Approved only for the observed post-merger GULF series; no pre-merger history is inferred.",
            approved_from=record.get("Actual First Date", "").strip(),
            approved_to=record.get("Actual Last Date", "").strip(),
            dates=dates,
        )
    if symbol == "TIDLOR":
        return _record(
            record, "INSUFFICIENT_HISTORICAL_COVERAGE;CORPORATE_ACTION_ISSUE", evidence,
            "APPROVED_WITH_KNOWN_GAP",
            "Approved only from the observed Tidlor Holdings series start; the pre-2025-05-16 entity gap remains excluded.",
            approved_from=record.get("Actual First Date", "").strip(),
            approved_to=record.get("Actual Last Date", "").strip(),
            dates=dates,
        )
    if symbol == "BANPU":
        return _record(
            record, "KNOWN_SUSPENSION;OHLC_ANOMALY;INSUFFICIENT_HISTORICAL_COVERAGE", evidence,
            "NEEDS_REVIEW", "Suspension is documented, but the OHLC anomaly and trailing coverage gap require review.", dates=dates,
        )
    if status == "PARTIAL" and _has_ohlc_anomaly(findings):
        return _record(
            record, "OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED", evidence + "; reports/ohlc_anomaly_adjudication.csv", "NEEDS_REVIEW",
            "Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.", dates=dates,
        )
    if status == "NO_DATA":
        return _record(record, "MISSING_YAHOO_DATA", evidence, "REJECTED", "No usable provider data was acquired.", dates=dates)
    return _record(record, "UNKNOWN_UNRESOLVED", evidence, "NEEDS_REVIEW", "No deterministic approval rule covers this acquisition state.", dates=dates)


def generate_approval_records(project_root: str | Path = ROOT) -> list[ApprovalRecord]:
    """Return one deterministic approval record per acquisition report row."""
    root = Path(project_root).resolve()
    with (root / "reports" / "market_data_acquisition.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    required = {"SET Symbol", "Yahoo Ticker", "Status", "Source", "Output File"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Acquisition report is missing required approval inputs.")
    return [classify_acquisition_record({key: (value or "").strip() for key, value in row.items()}) for row in rows]


def write_approval_reports(project_root: str | Path = ROOT) -> list[ApprovalRecord]:
    """Write deterministic approval CSV/Markdown artifacts; raw files are never touched."""
    root = Path(project_root).resolve()
    records = generate_approval_records(root)
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    csv_path = reports / "market_data_remediation.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0])))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    counts = {status: sum(record.approval_status == status for record in records) for status in sorted(APPROVAL_STATUSES)}
    lines = ["# Market Data Remediation and Approval Report", "", "## Approval status"]
    lines += [f"- {status}: {counts[status]}" for status in sorted(counts)]
    lines += ["", "## Non-success acquisition decisions"]
    for record in records:
        if record.acquisition_status != "SUCCESS":
            lines.append(f"- `{record.set_symbol}` — {record.approval_status}: {record.issue_classification}. {record.reason}")
    lines += ["", "Raw files were not changed. No gaps were filled and no PARTIAL row was automatically promoted."]
    (reports / "market_data_remediation.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return records


def write_research_readiness_reports(project_root: str | Path = ROOT) -> list[ApprovalRecord]:
    """Write the final all-symbol readiness report and approved-date manifest."""
    root = Path(project_root).resolve()
    records = generate_approval_records(root)
    processed = root / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    manifest_fields = ["set_symbol", "yahoo_ticker", "raw_file", "approval_status", "approved_from", "approved_to", "issue_classification", "reason"]
    approved = [record for record in records if record.approval_status in APPROVED_STATUSES]
    if any(not record.approved_from or not record.approved_to for record in approved):
        raise ValueError("Every approved symbol must have an explicit approved date range.")
    with (processed / "approved_market_data_manifest.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=manifest_fields)
        writer.writeheader()
        for record in approved:
            payload = asdict(record)
            writer.writerow({field: payload[field] for field in manifest_fields})
    counts = {status: sum(record.approval_status == status for record in records) for status in sorted(APPROVAL_STATUSES)}
    lines = ["# Final Research-Data Readiness", "", "This report is derived from the acquisition, remediation, and OHLC adjudication records. Raw Yahoo files were not modified and no OHLC values were repaired or fabricated.", "", "## Status counts"]
    lines += [f"- {status}: {counts[status]}" for status in sorted(counts)]
    lines += ["", "## Symbol decisions"]
    for record in records:
        lines.append(f"- `{record.set_symbol}` — {record.approval_status}; range={record.approved_from or 'none'} to {record.approved_to or 'none'}; classification={record.issue_classification}; reason={record.reason}")
    lines += ["", "## Downstream manifest", "", "Only `APPROVED` and `APPROVED_WITH_KNOWN_GAP` rows appear in `data/processed/approved_market_data_manifest.csv`. Consumers must still pass each date through `MarketDataEligibilityGate`.", "", "Feature engineering and backtesting are not started."]
    (root / "reports" / "research_data_readiness.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    with (root / "reports" / "research_data_readiness.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(records[0])))
        writer.writeheader()
        writer.writerows(asdict(record) for record in records)
    return records


def _record(
    acquisition: dict[str, str], classification: str, evidence: str, approval: str, reason: str,
    approved_from: str = "", approved_to: str = "", dates: str | None = None,
) -> ApprovalRecord:
    if approval not in APPROVAL_STATUSES:
        raise ValueError(f"Unknown approval status: {approval}")
    return ApprovalRecord(
        set_symbol=acquisition["SET Symbol"].strip().upper(), yahoo_ticker=acquisition.get("Yahoo Ticker", "").strip(),
        raw_file=acquisition.get("Output File", "").strip(), acquisition_status=acquisition["Status"].strip(),
        validation_findings=acquisition.get("Validation Issues", "").strip(),
        affected_dates_or_ranges=dates if dates is not None else _date_range(acquisition),
        issue_classification=classification, evidence_source=evidence, approval_status=approval, reason=reason,
        approved_from=approved_from, approved_to=approved_to,
    )


def _date_range(record: dict[str, str]) -> str:
    start, end = record.get("Actual First Date", "").strip(), record.get("Actual Last Date", "").strip()
    return f"{start} to {end}" if start and end else "No acquired data range"


def _has_ohlc_anomaly(findings: str) -> bool:
    return "High below Open/Close" in findings or "Low above Open/Close" in findings


def main() -> None:
    """Generate approval artifacts from the current acquisition report."""
    parser = argparse.ArgumentParser(description="Generate immutable raw-data remediation approvals.")
    parser.add_argument("--project-root", default=ROOT)
    args = parser.parse_args()
    records = write_approval_reports(args.project_root)
    write_research_readiness_reports(args.project_root)
    for status in sorted(APPROVAL_STATUSES):
        print(f"{status}: {sum(record.approval_status == status for record in records)}")


if __name__ == "__main__":
    main()

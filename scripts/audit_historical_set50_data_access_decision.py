"""Build the read-only SET50 historical-data access decision package."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
AUDIT_DATE = "2026-09-12"

ROUTES = [
    {"route": "SET Historical Data Request", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/historical", "official": True, "membership": "Potentially, must confirm requested constituent package", "reference_data": "Equity trading/statistics and company information; scope/product confirmation required", "access": "One-time request/licensed delivery", "assessment": "MOST_SUITABLE_INITIAL_ROUTE"},
    {"route": "SET Historical Data Request Service", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/data-request", "official": True, "membership": "Potentially through a tailored official request", "reference_data": "Historical equity data/statistics; exact security-master fields must be confirmed", "access": "Request and commercial terms", "assessment": "COMPLEMENTARY_REQUEST_ROUTE"},
    {"route": "SETSMART Corporate/Advance/Multi Market", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/web-based", "official": True, "membership": "Historical security/index functions may be available by product", "reference_data": "Historical securities, issuer information, announcements and statistics; depth depends on subscription", "access": "Authenticated subscription", "assessment": "POSSIBLE_IF_PRODUCT_CONFIRMED"},
    {"route": "SMART Marketplace API", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace", "official": True, "membership": "Reference/index data may be available through an API product; exact endpoint unknown", "reference_data": "Reference data and corporate actions", "access": "Authenticated/licensed API", "assessment": "POSSIBLE_API_ROUTE"},
    {"route": "SET End-of-Day service", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/end-of-day", "official": True, "membership": "Index/weight or tracker files may cross-check constituents; complete historical membership uncertain", "reference_data": "Official EOD/index and corporate-action-related files", "access": "Product access/licensing", "assessment": "CROSS_CHECK_ONLY_UNTIL_CONFIRMED"},
]

FIELDS = [
    {"field": "index_name", "priority": "REQUIRED", "reason": "Distinguishes SET50 from SET100 and other indices."},
    {"field": "effective_start_date", "priority": "REQUIRED", "reason": "Prevents boundary ambiguity and lookahead."},
    {"field": "effective_end_date", "priority": "REQUIRED", "reason": "Defines the valid membership interval."},
    {"field": "historical_symbol", "priority": "REQUIRED", "reason": "Preserves the symbol published at the historical date."},
    {"field": "security_identifier", "priority": "REQUIRED", "reason": "Resolves identity across ticker changes and prevents ticker-only joins."},
    {"field": "issuer_security_name", "priority": "REQUIRED", "reason": "Audits issuer and instrument identity."},
    {"field": "membership_status", "priority": "REQUIRED", "reason": "Separates active, removed, replacement and boundary records."},
    {"field": "revision_or_boundary_date", "priority": "REQUIRED", "reason": "Captures between-period changes and corrections."},
    {"field": "corporate_action_reference_id", "priority": "HIGHLY_DESIRABLE", "reason": "Links mergers, amalgamations, listings and delistings."},
    {"field": "listing_delisting_dates", "priority": "HIGHLY_DESIRABLE", "reason": "Constrains price eligibility and listing boundaries."},
    {"field": "source_provenance_and_revision", "priority": "REQUIRED", "reason": "Makes the delivered extract auditable and reproducible."},
    {"field": "isin_or_exchange_security_code", "priority": "HIGHLY_DESIRABLE", "reason": "Independent identity key when tickers change."},
    {"field": "corporate_action_adjustment_factors", "priority": "OPTIONAL", "reason": "Needed only if supplied as part of a separately defined price policy."},
]

CHECKLIST = [
    ("coverage", "Provide all 22 canonical half-year SET50 snapshots from 2016 H1 through 2026 H2, with index name and effective start/end dates."),
    ("revisions", "Identify all between-period revisions, replacement events, corrections and superseded files."),
    ("security_master", "Provide historical security identifiers, exchange codes, issuer/security names and ticker history."),
    ("identity_events", "Document ticker changes, mergers/amalgamations, successors, delistings, relistings and listing dates."),
    ("membership_rows", "State whether each row is a member, replacement, removal or boundary record and provide the effective date."),
    ("provenance", "Provide source URL/product name, extraction date, file version, revision number and correction history."),
    ("licensing", "Confirm that internal quantitative research, audit retention and derived research reports are permitted."),
    ("delivery", "Specify format, schema, encoding, date/time convention, missing-value convention and checksum/versioning."),
]


def payload() -> dict:
    return {
        "status": "READ_ONLY_PRE_ACQUISITION_DECISION",
        "prepared_at": AUDIT_DATE,
        "routes": [dict(row, retrieved_at=AUDIT_DATE) for row in ROUTES],
        "minimum_dataset_fields": FIELDS,
        "request_checklist": [{"category": category, "request": request} for category, request in CHECKLIST],
        "acceptance_criteria": [
            "All 22 canonical periods are represented.",
            "Effective dates and index name are explicit.",
            "Security identity is explicit or resolvable with official identifiers.",
            "Between-period revisions and corrections are documented.",
            "Source provenance, version and licensing are preserved.",
            "TRUE/TRUEE/DTAC, GULF/INTUCH/GULFI, TIDLOR, BANPU/BANPUU, SCB/SCBB, TMB/TTB and MRDIYT reconcile without synthetic continuity.",
        ],
        "rejection_criteria": [
            "Missing canonical periods or implicit effective dates.",
            "Ticker-only identity with no authoritative security mapping.",
            "Unexplained revisions, between-period changes or corporate-action boundaries.",
            "Unknown provenance, unverifiable corrections, or unsuitable licensing.",
            "Requirement to infer membership from current constituents or to fabricate continuity.",
        ],
        "membership_only_consequence": "Membership lists alone are insufficient for price acquisition; obtain a separate official security master covering identifiers, names, ticker history, listing/delisting and corporate actions before mapping prices.",
        "recommended_route": "SET Historical Data Request, with an explicit request for the membership plus security-reference bundle; use SETSMART/SMART Marketplace as alternatives or cross-checks if their product scope is confirmed.",
        "ready_for_price_acquisition": False,
        "bulk_price_data_downloaded": False,
        "production_data_modified": False,
    }


def write_outputs(data: dict) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_set50_data_access_decision.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    with (REPORT_DIR / "historical_set50_data_request_checklist.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["category", "request"])
        writer.writeheader()
        writer.writerows(data["request_checklist"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = payload()
    if args.write:
        write_outputs(data)
    print(json.dumps({"routes": len(data["routes"]), "fields": len(data["minimum_dataset_fields"]), "ready": data["ready_for_price_acquisition"]}, indent=2))


if __name__ == "__main__":
    main()

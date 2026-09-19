"""Emit a deterministic, read-only audit of pre-2023 SET50 membership access.

This script intentionally performs no network requests and never constructs a
constituent list.  It records only the period metadata publicly exposed by the
official SET archive and the legitimate access routes identified in the audit.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
AUDIT_DATE = "2026-09-12"
ARCHIVE_URL = "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100"

PERIODS = [f"{year} H{half}" for year in range(2016, 2023) for half in (1, 2)]

SOURCES = [
    {"name": "SET50/SET100 constituent archive", "url": ARCHIVE_URL, "retrieval_date": AUDIT_DATE, "official": True, "supports": "Public period index for 2016 H1 through 2022 H2; download links require member login."},
    {"name": "SET Information Services", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/main", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Official historical-data, SETSMART, reference-data and corporate-action service catalogue."},
    {"name": "SET Historical Data Request", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/historical", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Legitimate one-time historical-data request route; exact constituent package must be confirmed."},
    {"name": "SET Historical Data Request Service", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/data-request", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Official request/contact route for historical equity data and statistics."},
    {"name": "SETSMART / web-based data services", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/web-based", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Authenticated SETSMART products; historical depth depends on subscribed product."},
    {"name": "SET SMART Marketplace", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/smart-marketplace", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Authenticated API marketplace including reference data and corporate actions."},
    {"name": "SET End-of-Day service", "url": "https://www.set.or.th/en/services/connectivity-and-data/data/end-of-day", "retrieval_date": AUDIT_DATE, "official": True, "supports": "Official EOD/index files; constituent/weight files may be an alternative reference, subject to product access."},
]

IDENTITIES = [
    {"case": "TRUE / TRUEE / DTAC", "identity_status": "VERIFIED_NON_CONTINUITY", "impact": "Keep predecessor and post-amalgamation securities separate; snapshot symbols must be used as published."},
    {"case": "GULF / INTUCH / GULFI", "identity_status": "VERIFIED_NON_CONTINUITY", "impact": "Preserve merger and suspension boundaries; do not backfill post-event GULF."},
    {"case": "TIDLOR", "identity_status": "VERIFIED_NON_CONTINUITY", "impact": "NTL and replacement TIDLOR require separate identities and effective dates."},
    {"case": "BANPU / BANPUU", "identity_status": "VERIFIED_NON_CONTINUITY", "impact": "Use exact date-effective symbols; no inferred continuity."},
    {"case": "SCB / SCBB", "identity_status": "REQUIRES_MAPPING_POLICY", "impact": "Keep bank and holding-company raw series separate pending policy."},
    {"case": "TMB / TTB", "identity_status": "VERIFIED_CONTINUITY_WITH_TICKER_CHANGE", "impact": "Date-effective ticker mapping only; preserve historical symbol in membership."},
    {"case": "MRDIYT", "identity_status": "VERIFIED_LISTING_BOUNDARY", "impact": "No membership or price observations before its listing date."},
]


def _row(period: str) -> dict:
    year, half = period.split()
    y = int(year)
    h = int(half[1])
    start = f"{y:04d}-{'01-01' if h == 1 else '07-01'}"
    end = f"{y:04d}-{'06-30' if h == 1 else '12-31'}"
    return {
        "period": period,
        "effective_from": start,
        "effective_to": end,
        "official_archive_url": f"{ARCHIVE_URL}#{period.replace(' ', '-')}",
        "official_source_status": "OFFICIAL_ARCHIVE_PERIOD_LISTED",
        "publicly_accessible": True,
        "file_bytes_publicly_accessible": False,
        "authentication_required": True,
        "legitimate_alternative": "SET Historical Data Request or licensed SETSMART/reference-data extract",
        "independently_verifiable": False,
        "acquisition_status": "ACCESS_REQUIRED",
        "identity_status": "REVIEW_REQUIRED",
        "price_data_readiness": "NOT_READY",
        "remaining_blocker": "Authenticated/licensed official constituent file and row-level verification",
        "human_approval_required": True,
    }


def payload() -> dict:
    rows = [_row(period) for period in PERIODS]
    return {
        "status": "READ_ONLY_ACCESS_AUDIT",
        "retrieved_at": AUDIT_DATE,
        "required_snapshot_count": len(PERIODS),
        "snapshots": rows,
        "sources": SOURCES,
        "identity_cross_reference": IDENTITIES,
        "officially_verified_membership": [],
        "official_source_identified_access_restricted": PERIODS,
        "secondary_evidence_only": [],
        "unverified_constituent_lists": PERIODS,
        "official_source_identified_count": len(PERIODS),
        "accessible_without_authentication_count": 0,
        "requiring_legitimate_set_access_count": len(PERIODS),
        "period_metadata_unverified_count": 0,
        "constituent_list_verified_count": 0,
        "licensed_extract_would_resolve_membership_blocker": True,
        "licensed_extract_conditions": "Must contain official half-year rows, effective dates, revisions/provenance, and security identifiers.",
        "ready_for_full_historical_price_acquisition": False,
        "bulk_price_data_downloaded": False,
        "raw_data_modified": False,
        "approved_manifest_modified": False,
        "eligibility_rules_modified": False,
        "synthetic_membership_constructed": False,
    }


def write_outputs(data: dict) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_set50_membership_access_audit.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    fields = list(data["snapshots"][0])
    with (REPORT_DIR / "historical_set50_membership_access_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data["snapshots"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write JSON and CSV reports")
    args = parser.parse_args()
    data = payload()
    if args.write:
        write_outputs(data)
    print(json.dumps({"snapshots": len(data["snapshots"]), "official_source_identified": data["official_source_identified_count"], "ready": data["ready_for_full_historical_price_acquisition"]}, indent=2))


if __name__ == "__main__":
    main()

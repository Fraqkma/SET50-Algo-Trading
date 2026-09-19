"""Generate the deterministic, pre-acquisition SET50 data request specification."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"

PERIODS = [f"{year} H{half}" for year in range(2016, 2027) for half in (1, 2)]

REQUEST_FIELDS = [
    ("index_name", "REQUIRED", "SET50 identifier for every row"),
    ("effective_start_date", "REQUIRED", "Start of membership validity"),
    ("effective_end_date", "REQUIRED", "End of membership validity"),
    ("historical_symbol", "REQUIRED", "Published symbol at the effective date"),
    ("security_identifier", "REQUIRED", "Authoritative exchange/security identifier"),
    ("issuer_security_name", "REQUIRED", "Issuer and instrument name"),
    ("membership_status", "REQUIRED", "Member, replacement, removal, or boundary status"),
    ("revision_boundary_date", "REQUIRED", "Between-review change or correction date"),
    ("source_provenance", "REQUIRED", "Product, version, extraction date, checksum or equivalent"),
    ("isin_exchange_code", "HIGHLY_DESIRABLE", "Independent identity key"),
    ("listing_delisting_dates", "HIGHLY_DESIRABLE", "Tradability boundaries"),
    ("ticker_name_change_history", "HIGHLY_DESIRABLE", "Date-effective historical names and tickers"),
    ("corporate_action_reference", "HIGHLY_DESIRABLE", "Merger, amalgamation, split, rights and successor references"),
    ("corporate_action_factors", "OPTIONAL", "Only if supplied with documented semantics"),
]

CHECKLIST = [
    ("membership_coverage", "Confirm all 22 canonical SET50 half-year periods from 2016 H1 through 2026 H2."),
    ("between_review_changes", "Provide all between-period additions, removals, replacements, corrections and superseded versions."),
    ("security_master", "Provide authoritative identifiers, exchange codes, issuer/security names and date-effective mappings."),
    ("corporate_actions", "Document ticker/name changes, mergers, amalgamations, successors, delistings, relistings, splits and rights events."),
    ("price_semantics", "State whether prices are raw or adjusted, and whether splits, rights, dividends or other actions are reflected."),
    ("execution_suitability", "Confirm whether OHLCV is suitable for historical OHLC execution backtesting and whether raw execution fields are available."),
    ("price_corporate_actions", "Provide the associated corporate-action record or explain how every adjustment is represented."),
    ("provenance", "Provide source URL/product, retrieval/extraction date, schema version, file version and correction history."),
    ("licensing", "State one-time and recurring cost, internal research rights, retention rights, derived-report rights and redistribution restrictions."),
    ("delivery", "Specify file/API format, date convention, timezone, missing-value convention, encoding, checksums and delivery schedule."),
]

ACCEPTANCE = [
    "All 22 canonical periods are present and labelled SET50.",
    "Every membership row has explicit effective dates and an authoritative identity or resolvable official mapping.",
    "Between-review revisions, corrections and superseded records are documented.",
    "The seven audited identity cases reconcile without ticker-only inference or synthetic continuity.",
    "Price semantics are explicit; raw execution OHLC is separated from adjusted analytical fields.",
    "Corporate-action records and listing/delisting boundaries are preserved.",
    "Provenance, versioning, checksums and licensing terms are retained with the immutable delivery.",
]

REJECTION = [
    "Any missing canonical period, implicit boundary, or unexplained replacement.",
    "Ticker-only identity or current-constituent substitution for historical members.",
    "Unclear raw/adjusted price semantics or adjusted values presented as execution OHLC.",
    "Missing corporate-action, listing/delisting, revision or correction information needed to explain a boundary.",
    "Unverifiable provenance, missing checksums/versioning, or licensing that does not permit the intended internal research use.",
]


def payload() -> dict:
    return {
        "status": "PRE_ACQUISITION_REQUEST_SPECIFICATION",
        "canonical_periods": PERIODS,
        "period_count": len(PERIODS),
        "requested_fields": [{"field": field, "priority": priority, "purpose": purpose} for field, priority, purpose in REQUEST_FIELDS],
        "request_checklist": [{"category": category, "request": request} for category, request in CHECKLIST],
        "acceptance_criteria": ACCEPTANCE,
        "rejection_criteria": REJECTION,
        "licensing_cost_status": "UNRESOLVED_UNTIL_SET_QUOTE",
        "permitted_research_usage_status": "UNRESOLVED_UNTIL_SET_LICENSE_TERMS",
        "price_acquisition_requested_now": False,
        "data_downloaded": False,
        "production_data_modified": False,
        "ready_for_import": False,
    }


def write_outputs(data: dict) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_set50_data_request_spec.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
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
    print(json.dumps({"periods": data["period_count"], "fields": len(data["requested_fields"]), "ready_for_import": data["ready_for_import"]}, indent=2))


if __name__ == "__main__":
    main()

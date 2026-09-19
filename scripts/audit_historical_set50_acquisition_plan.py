"""Build a deterministic, non-acquiring plan for historical SET50 extension."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONSTITUENTS = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"
REPORT_DIR = ROOT / "reports"
DOC = ROOT / "docs" / "HISTORICAL_SET50_ACQUISITION_PLAN.md"
SET_ARCHIVE_URL = "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100"
TARGET_START = "2016-01-01"
TARGET_END = "2026-09-04"


def required_snapshots() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for year in range(2016, 2027):
        rows.append({"period": f"{year} H1", "effective_from": f"{year}-01-01" if year != 2024 else "2024-01-02", "effective_to": f"{year}-06-30"})
        rows.append({"period": f"{year} H2", "effective_from": f"{year}-07-01", "effective_to": f"{year}-12-31"})
    return rows


IDENTITY_CASES: list[dict[str, str]] = [
    {"historical_symbol": "TRUE", "modern_symbol": "TRUE", "identity": "new True Corporation after TRUEE/DTAC amalgamation", "transition": "2023-03", "issue": "amalgamation and new listing", "continuity": "NO_UNAPPROVED_SPLICE", "human_approval": "YES"},
    {"historical_symbol": "TRUEE", "modern_symbol": "TRUE", "identity": "predecessor True Corporation", "transition": "2023-02 to 2023-03", "issue": "temporary symbol then delisting", "continuity": "NO_UNAPPROVED_SPLICE", "human_approval": "YES"},
    {"historical_symbol": "DTAC", "modern_symbol": "TRUE", "identity": "Total Access Communication predecessor", "transition": "2023-03", "issue": "amalgamation and delisting", "continuity": "NO_UNAPPROVED_SPLICE", "human_approval": "YES"},
    {"historical_symbol": "GULF", "modern_symbol": "GULF", "identity": "Gulf Energy predecessor / successor boundary", "transition": "2025-03 to 2025-04", "issue": "GULFI/INTUCH amalgamation and suspension", "continuity": "BOUNDARY_REQUIRED", "human_approval": "YES"},
    {"historical_symbol": "GULFI", "modern_symbol": "GULF", "identity": "Gulf Development post-amalgamation security", "transition": "2025-04", "issue": "ticker and issuer boundary", "continuity": "BOUNDARY_REQUIRED", "human_approval": "YES"},
    {"historical_symbol": "INTUCH", "modern_symbol": "GULF", "identity": "Intouch Holdings predecessor", "transition": "2025-04", "issue": "amalgamation and delisting/transfer", "continuity": "NO_UNAPPROVED_SPLICE", "human_approval": "YES"},
    {"historical_symbol": "TIDLOR", "modern_symbol": "TIDLOR", "identity": "Ngern Tid Lor to TIDLOR Holdings", "transition": "2025-05", "issue": "holding-company replacement under same ticker", "continuity": "BOUNDARY_REQUIRED", "human_approval": "YES"},
    {"historical_symbol": "BANPU", "modern_symbol": "BANPUU", "identity": "Banpu security", "transition": "2026", "issue": "temporary/revised symbol around amalgamation", "continuity": "UNRESOLVED", "human_approval": "YES"},
    {"historical_symbol": "BANPUU", "modern_symbol": "BANPU", "identity": "Banpu temporary/revised security", "transition": "2026", "issue": "temporary symbol and delisting notice", "continuity": "UNRESOLVED", "human_approval": "YES"},
    {"historical_symbol": "MRDIYT", "modern_symbol": "MRDIYT", "identity": "MR. D.I.Y. Holding Thailand", "transition": "2025-11", "issue": "new listing; no pre-listing history", "continuity": "NO_PRELISTING_DATA", "human_approval": "YES"},
    {"historical_symbol": "SCB", "modern_symbol": "SCB", "identity": "SCB X / Siam Commercial Bank corporate transition", "transition": "2021-2022", "issue": "company-name and holding-company transition; ticker continuity needs issuer evidence", "continuity": "REVIEW_REQUIRED", "human_approval": "YES"},
    {"historical_symbol": "TTB", "modern_symbol": "TTB", "identity": "TMBThanachart Bank following TMB/Thanachart combination", "transition": "2019-2020", "issue": "bank merger/name transition", "continuity": "REVIEW_REQUIRED", "human_approval": "YES"},
]


def read_symbols(path: Path = CONSTITUENTS) -> list[str]:
    with path.open(newline="", encoding="utf-8") as handle:
        symbols = {row["symbol"].strip() for row in csv.DictReader(handle) if row.get("symbol", "").strip()}
    return sorted(symbols | {case["historical_symbol"] for case in IDENTITY_CASES})


def build_matrix(symbols: list[str]) -> list[dict[str, str]]:
    case_by_symbol = {case["historical_symbol"]: case for case in IDENTITY_CASES}
    rows = []
    for symbol in symbols:
        case = case_by_symbol.get(symbol)
        if case:
            identity_status = "REVIEW_REQUIRED"
            continuity = case["continuity"]
            concern = case["issue"]
        else:
            identity_status = "UNREVIEWED_HISTORICAL_IDENTITY"
            continuity = "NOT_ESTABLISHED"
            concern = "historical issuer, rename, delisting, and corporate actions not yet audited"
        rows.append({
            "symbol": symbol,
            "required_start": TARGET_START,
            "required_end": TARGET_END,
            "candidate_sources": "SET licensed historical data; licensed secondary source; Yahoo/yfinance cross-check only",
            "expected_availability": "UNKNOWN_PENDING_OFFICIAL_SNAPSHOT" if symbol not in {"ADVANC", "BANPU", "PTT", "TRUE"} else "PILOT_PARTIAL_ONLY",
            "source_limitations": "SET access/authentication and licensing unresolved; secondary symbol coverage unverified",
            "adjusted_raw_status": "UNVERIFIED",
            "corporate_action_concerns": concern,
            "acquisition_status": "NOT_STARTED",
            "validation_status": "NOT_STARTED",
            "identity_status": identity_status,
            "continuity_status": continuity,
            "human_approval_required": "YES",
        })
    return rows


def build_payload() -> dict[str, Any]:
    symbols = read_symbols()
    return {
        "status": "PLANNING_ONLY",
        "target_start": TARGET_START,
        "target_end": TARGET_END,
        "required_snapshot_count": len(required_snapshots()),
        "required_snapshots": required_snapshots(),
        "official_source": SET_ARCHIVE_URL,
        "official_access_status": "PUBLIC_ARCHIVE_LISTED_MEMBER_AUTH_REQUIRED",
        "observed_repository_symbol_count": len(read_symbols()),
        "observed_repository_and_known_identity_symbols": symbols,
        "identity_cases": IDENTITY_CASES,
        "symbol_matrix": build_matrix(symbols),
        "acquisition_performed": False,
        "approved_manifest_modified": False,
        "raw_data_modified": False,
        "eligibility_gate_modified": False,
        "backtest_run": False,
    }


def write_outputs(payload: dict[str, Any]) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_set50_acquisition_plan.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    fields = list(payload["symbol_matrix"][0])
    with (REPORT_DIR / "historical_set50_symbol_matrix.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(payload["symbol_matrix"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="write planning reports; never acquires data")
    args = parser.parse_args()
    payload = build_payload()
    if args.write:
        write_outputs(payload)
    print(json.dumps({"required_snapshot_count": payload["required_snapshot_count"], "symbol_count": payload["observed_repository_symbol_count"], "acquisition_performed": False}, indent=2))


if __name__ == "__main__":
    main()

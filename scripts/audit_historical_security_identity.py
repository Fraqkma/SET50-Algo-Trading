"""Emit a read-only, source-backed security-identity audit."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "reports"
AUDIT_DATE = "2026-09-12"

SOURCES = [
    {"name": "SET TRUE/DTAC amalgamation notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256345950&symbol=SET", "official": True, "supports": "TRUEE and DTAC deleted; new TRUE added to SET50 effective 2023-03-02"},
    {"name": "SET new TRUE listing notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=16776256332630&symbol=TRUE", "official": True, "supports": "TRUE listing, trading date, and transfer of assets and obligations after amalgamation"},
    {"name": "SET GULF/INTUCH suspension notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=94876500&symbol=INTUCH", "official": True, "supports": "GULF and INTUCH suspension, GULF to GULFI ticker transition"},
    {"name": "SET post-amalgamation GULF inclusion notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=95454300&symbol=GULF", "official": True, "supports": "GULF Development inclusion effective 2025-04-02 after GULFI/INTUCH amalgamation"},
    {"name": "SET TIDLOR listing notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=96648700&symbol=SET", "official": True, "supports": "TIDLOR Holdings listed in place of Ngern Tid Lor effective 2025-05-15"},
    {"name": "SET BANPU/BPP suspension notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105437300&symbol=BANPUU", "official": True, "supports": "BANPU ticker changed to BANPUU and trading suspension during amalgamation"},
    {"name": "SET BANPUU/BPP delisting notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=105587000&symbol=BPP", "official": True, "supports": "BANPUU and BPP delisted; BANPU relisted after amalgamation"},
    {"name": "SET SCB/SCBB restructuring notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2022049146&symbol=SCB", "official": True, "supports": "SCB X listed in place of SCBB; SCBB delisted effective 2022-04-27"},
    {"name": "SET TMB/TTB name and ticker notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=2021051542&symbol=TTB", "official": True, "supports": "TMB renamed TMBThanachart and ticker changed TMB to TTB effective 2021-05-12"},
    {"name": "SET MRDIYT listing notice", "url": "https://www.set.or.th/en/market/news-and-alert/newsdetails?id=99345900&symbol=MRDIYT", "official": True, "supports": "MRDIYT first listed and traded 2025-11-05"},
    {"name": "SET constituent archive", "url": "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100", "official": True, "supports": "Public archive index and period structure; file downloads require member authentication"},
]

CASES = [
    {"case": "TRUE / TRUEE / DTAC", "historical_identity": "TRUEE and DTAC predecessor securities; new True Corporation security TRUE", "transition": "Amalgamation registered 2023-03-01; SET50 change effective 2023-03-02; TRUE traded 2023-03-03", "continuity_status": "VERIFIED_NON_CONTINUITY", "price_treatment": "Keep TRUEE, DTAC, and TRUE OHLCV separate; no synthetic splice; any economic-return bridge requires approved corporate-action policy", "membership_treatment": "Use TRUEE/DTAC before the effective boundary and TRUE after it; do not backfill the new TRUE into earlier snapshots", "confidence": "VERIFIED", "human_approval": "YES", "bias_risk": "Survivorship and lookahead if new TRUE is used in pre-2023 membership"},
    {"case": "GULF / INTUCH / GULFI", "historical_identity": "GULF Energy, INTUCH, temporary GULFI, then GULF Development", "transition": "Suspension 2025-03-21 to 2025-04-02; post-amalgamation GULF inclusion effective 2025-04-02", "continuity_status": "VERIFIED_NON_CONTINUITY", "price_treatment": "Keep pre-event GULF, INTUCH/GULFI, and post-event GULF boundary-separated; preserve suspension; no synthetic splice", "membership_treatment": "Apply historical member symbol in each effective snapshot; post-event GULF is not evidence of prior INTUCH membership", "confidence": "VERIFIED", "human_approval": "YES", "bias_risk": "Lookahead and fabricated continuity around merger and suspension"},
    {"case": "TIDLOR", "historical_identity": "Ngern Tid Lor (NTL) predecessor and TIDLOR Holdings replacement under ticker TIDLOR", "transition": "TIDLOR listed/traded in place of NTL effective 2025-05-15", "continuity_status": "VERIFIED_NON_CONTINUITY", "price_treatment": "Keep NTL and TIDLOR raw series separate; a 1:1 share-swap bridge is not permission to join OHLCV", "membership_treatment": "Use NTL before 2025-05-15 and TIDLOR after the effective boundary", "confidence": "VERIFIED", "human_approval": "YES", "bias_risk": "Survivorship and false performance continuity if the current TIDLOR file is backfilled"},
    {"case": "BANPU / BANPUU", "historical_identity": "Banpu security temporarily renamed BANPUU during BANPU/BPP amalgamation, then BANPU relisted", "transition": "BANPUU effective during 2026-07-17 suspension; BANPUU/BPP delisted 2026-07-31; BANPU traded 2026-08-04 onward", "continuity_status": "VERIFIED_NON_CONTINUITY", "price_treatment": "Keep BANPU, BANPUU, and post-event BANPU separate at raw-data level; corporate-action adjustment requires explicit policy", "membership_treatment": "Use the exact symbol published in each effective SET50 snapshot; do not infer BANPUU membership from a change notice", "confidence": "VERIFIED", "human_approval": "YES", "bias_risk": "Lookahead if post-amalgamation BANPU is used before its effective listing"},
    {"case": "MRDIYT", "historical_identity": "MR. D.I.Y. Holding (Thailand) Public Company Limited", "transition": "First listed and traded 2025-11-05", "continuity_status": "VERIFIED_NON_CONTINUITY", "price_treatment": "Use only from listing/trading date; no pre-listing price history", "membership_treatment": "Membership can begin only in snapshots effective after listing", "confidence": "VERIFIED", "human_approval": "NO_FOR_BOUNDARY; YES_FOR_APPROVAL", "bias_risk": "Lookahead/survivorship if pre-listing observations are fabricated"},
    {"case": "SCB", "historical_identity": "SCB X (SCB) holding company replaced SCBB (The Siam Commercial Bank)", "transition": "SCB listed and SCBB delisted 2022-04-27 through restructuring/share swap", "continuity_status": "REQUIRES_MAPPING_POLICY", "price_treatment": "Keep SCBB and SCB raw series separate; SET used the last SCBB price for limits, which is not proof of OHLCV continuity", "membership_treatment": "Use SCBB before and SCB after the effective boundary unless official snapshot states otherwise", "confidence": "VERIFIED", "human_approval": "YES", "bias_risk": "False continuity and lookahead if holding-company history is treated as bank history"},
    {"case": "TTB", "historical_identity": "TMB Bank renamed TMBThanachart Bank; ticker TMB changed to TTB", "transition": "Name and ticker change effective 2021-05-12", "continuity_status": "VERIFIED_CONTINUITY_WITH_TICKER_CHANGE", "price_treatment": "A date-effective ticker mapping is plausible; do not adjust OHLCV unless separate corporate-action evidence requires it", "membership_treatment": "Map TMB before 2021-05-12 and TTB after; preserve the historical published symbol", "confidence": "VERIFIED", "human_approval": "YES_FOR_DATA_MAPPING", "bias_risk": "Missing or duplicated observations at the ticker boundary"},
]


def payload() -> dict:
    return {"status": "READ_ONLY_AUDIT", "retrieved_at": AUDIT_DATE, "cases": CASES, "sources": SOURCES, "bulk_price_acquisition": False, "approved_manifest_modified": False, "raw_data_modified": False, "eligibility_gate_modified": False, "strategy_or_backtest_modified": False}


def write_outputs(data: dict) -> None:
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_security_identity_audit.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
    fields = ["case", "historical_identity", "transition", "continuity_status", "price_treatment", "membership_treatment", "confidence", "human_approval", "bias_risk"]
    with (REPORT_DIR / "historical_security_identity_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(data["cases"])


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    data = payload()
    if args.write:
        write_outputs(data)
    print(json.dumps({"cases": len(data["cases"]), "sources": len(data["sources"]), "bulk_price_acquisition": False}, indent=2))


if __name__ == "__main__":
    main()

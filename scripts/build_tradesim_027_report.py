"""Publish local migration evidence only after exact-runtime fixtures pass."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.competition.tradesim_bridge.runtime import inspect_archive, runtime_source_hash
from src.competition.tradesim_bridge.versioning import write_comparison_report

EVIDENCE = ROOT / "reports/migration_027/20261028T111305Z"
FIXTURES = ROOT / "artifacts/tradesim_027_validation/20261028-r3"


def read(path: Path) -> dict:
    data = path.read_bytes()
    return json.loads(data.decode("utf-16" if data.startswith((b"\xff\xfe", b"\xfe\xff")) else "utf-8-sig"))


def write(name: str, report: dict) -> None:
    (ROOT / "reports" / name).write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")


def main() -> None:
    archive = inspect_archive(ROOT / "tradeSim0.2.7.zip")
    matrices = {v: read(FIXTURES / v / "matrix.json") for v in ("0.2.6", "0.2.7")}
    current = matrices["0.2.7"]
    check = read(EVIDENCE / "runtime_check_027.json")
    smokes = [read(EVIDENCE / name) for name in ("smoke_one_day.json", "smoke_multi_day.json")]
    if not (archive["integrity"] == "PASS" and check["status"] == "READY"
            and current["all_checks_pass"] and all(run["status"] == "success" for run in smokes)):
        raise RuntimeError("Runtime validation incomplete; preference unchanged")
    warnings = [
        "Cross-symbol limits wait for their own-symbol tick. Placed differs from Timestamp in the observed delayed fill, contradicting the changelog's always-equal statement.",
        "Daily bars cannot reproduce exact-event tick volume. Research V1 remains an approximation.",
        "Qualification/award formulas still require the authoritative performance criteria.",
    ]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(), "status": "READY_WITH_WARNINGS",
        "runtime_validated": True, "organizer_designated_version": "0.2.7", "preferred_version": "0.2.7",
        "archive_sha256": archive["sha256"], "archive": archive,
        "runtime_source_sha256": runtime_source_hash(ROOT / "tools/kgi_tradesim/0.2.7"),
        "runtime_check": check, "requirements_changes": [], "pip_check": "PASS",
        "all_pinned_versions_match": True, "dependency_installations": [],
        "fixture_report": str((FIXTURES / "0.2.7/matrix.json").relative_to(ROOT)),
        "fixture_checks": current["checks"], "official_smokes": smokes,
        "preserved_versions": {"0.2.5": "tools/kgi_tradesim (legacy extraction)",
                               "0.2.6": "tools/kgi_tradesim/0.2.6; root ZIP absent at baseline"},
        "warnings": warnings, "real_orders_placed": 0,
    }
    write("tradesim_027_readiness.json", report)
    comparison = write_comparison_report(ROOT)
    source_diff = comparison["comparison_026_to_027"]
    source_diff["classified_changes"] = {
        name: "DATA" if name.startswith("marketInfo/") else "DOCUMENTATION_ONLY" if name.startswith("docs/")
        else "VALIDATION" if name.endswith("Order.py") else "BEHAVIORAL"
        for name in source_diff["changed_files"] + source_diff["added_files"]
    }
    source_diff["fee_constants"] = "UNCHANGED: commission=0.00157; VAT=0.07; CommissionService changed pricing, not rates"
    source_diff["additional_source_changes"] = [
        "Result directories support university/team separation in TradeSim, Portfolio, TransactionLog, PortSummarize.",
        "Cross-symbol Market request explicitly rejects instead of silently mispricing/vanishing.",
        "Index-symbol validation has a descriptive error; index history remains readable.",
        "Tick tables load from validated JSON and fail if unavailable; simulation date selects the table.",
        "Bundled daily/intraday history refreshed through Oct 21; practice ticks and benchmark remain through Sep 30.",
        "Notebook and strategy templates/examples unchanged; public strategy signatures unchanged.",
    ]
    comparison["regression_matrix"] = {v: str((FIXTURES / v / "matrix.json").relative_to(ROOT)) for v in matrices}
    comparison["fixture_caveat"] = "Use r3 matrices: earlier exploratory 0.2.6 custom-folder probe did not capture its default result path; retained, not authoritative. r3 uses isolated cwd and default result for both versions."
    write("tradesim_version_comparison.json", comparison)
    semantics = {
        "version": "0.2.7", "archive_sha256": archive["sha256"],
        "authority": {"ORGANIZER_ANNOUNCED": "User supplied announcement in TASK_current_data_and_tradesim_027_migration.md",
                      "CHANGELOG_DOCUMENTED": "tools/kgi_tradesim/0.2.7/docs/CHANGELOG.md section 0.2.7 (read completely)",
                      "SOURCE_IMPLEMENTED": ["Execution.py", "Order.py", "CommissionService.py", "tick_size.json", "TradeSim.py"],
                      "RUNTIME_OBSERVED": report["fixture_report"]},
        "order_mapping": {"Limit": "LIMIT / IOC", "Market": "MARKET_TO_LIMIT / IOC (organizer 0.2.7 API alias only)"},
        "checks": current["checks"], "tick_ladders": current["tick_ladders"],
        "tick_table_source": "tools/kgi_tradesim/0.2.7/tradeSim/tick_size.json",
        "future_date_test": "2026-11-15 and 2026-11-16 controlled simulator dates; not real future observations",
        "discrepancies": [warnings[0]], "cross_symbol_evidence": current["cross_symbol"],
        "residual_representation": "Official object remaining_volume is not zeroed on cancel and may already exclude daily-cap quantity. Bridge uses requested minus actual filled as canceled; pending=0 after attempt.",
        "cash_policy": "Acceptance checks full requested cash/holdings before volume clipping; fees apply only to fills.",
        "auction_policy": "Any Flag other than Buy/Sell cannot fill; OPEN1_E/OPEN2_E/ATC included.",
        "legacy_rule_mismatch": "RESOLVED_FOR_027: official API documentation explicitly identifies Market-to-Limit IOC; generic market orders remain prohibited outside this mapping.",
        "cases_by_version": {v: m["cases"] for v, m in matrices.items()},
        "fifo": current["fifo_shared_tick"], "real_orders_placed": 0,
    }
    write("tradesim_027_execution_semantics.json", semantics)
    impact = {"research_model_preserved": "RESEARCH_EXECUTION_V1", "v2_created": False,
              "reason": "Daily OHLCV lacks executable volume at the exact event; do not substitute daily volume or fabricate BBO.",
              "historical_artifacts_rewritten": False, "parameter_tuning": False,
              "candidate_impact": {
                  "Trend20": {"classification": "ALPHA_FAILURE", "action": "Remain rejected; gross -59.04% under V1; no automatic retest."},
                  "Breakout20": {"classification": "ALPHA_FAILURE", "action": "Remain rejected; gross -33.95% under V1; no automatic retest."},
                  "RelativeStrength": {"classification": "ALPHA_FAILURE", "action": "Remain rejected; gross -57.52% under V1; no automatic retest."},
                  "MeanRev5": {"classification": "MIXED", "factors": ["COST_SENSITIVE", "EXECUTION_MODEL_SENSITIVE"], "action": "Remain rejected; possible predeclared sensitivity only, not promotion."},
                  "Round2_H6": {"classification": "MIXED", "factors": ["COST_SENSITIVE", "EXECUTION_MODEL_SENSITIVE"], "action": "Remain rejected; near-zero gross and negative net; no OOS survivor."}},
              "comparability": "0.2.6 fills are not 0.2.7 scoring results; changed resting, tick cap, slippage, auctions and validation alter realized paths. V1 results remain valid only under their original declared assumptions.",
              "next_research": "Pre-register a bounded execution-sensitivity study on observed official ticks with unchanged signals and parameters; require human choice before V2 adoption or candidate reruns.",
              "final_strategy_selected": False}
    write("research_execution_model_027_impact.json", impact)
    print(json.dumps({"preferred": "0.2.7", "checks": len(current["checks"]), "status": report["status"]}))


if __name__ == "__main__":
    main()

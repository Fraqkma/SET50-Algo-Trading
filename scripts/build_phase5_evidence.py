"""Build source-faithful Phase 5 audit snapshots from preserved Phase 3/4 evidence."""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def read(relative: str):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def write(relative: str, payload) -> None:
    path = ROOT / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")


def main() -> None:
    now = datetime.now(timezone.utc).isoformat()
    task = ROOT / "TASK_PHASE5_PIT_UNLOCK_EXECUTION_AND_RESEARCH.md"
    pit = read("reports/phase4_pit_universe_eligibility.json")
    phase3 = read("reports/research_phase3_summary.json")
    source_files = [
        "AGENTS.md", "TASK_PHASE5_PIT_UNLOCK_EXECUTION_AND_RESEARCH.md",
        "KGI_ALGO26_Performance_TH.pdf",
        "reports/phase4_pit_universe_eligibility.json", "reports/phase3_run_reconciliation.json",
        "reports/research_phase3_summary.json",
        "reports/research_holding_horizon_curve.json", "reports/phase4_nonpromotional_baselines.json",
        "reports/competition_benchmark_risk_envelope.json",
        "reports/competition_calendar_verified.json", "reports/tradesim_027_readiness.json",
        "reports/tradesim_027_execution_semantics.json", "reports/settrade_scheduler_status.json",
        "reports/runtime/settrade_daily_2026-10-30.json", "logs/settrade/daily-2026-10-30.log",
        "config/phase4_research_direction_lock.json", "config/phase5_preregistration.json",
        "scripts/phase5_tick_mechanics_strategy.py", "data/official/tradesim/ticks/ticks/2026-10-21.csv",
        "tests/test_phase5_evidence.py", "tests/test_settrade_daily_health_timeout.py", "ui/app.py",
        "scripts/build_phase5_evidence.py",
    ]
    hashes = {p: sha(ROOT / p) for p in source_files if (ROOT / p).is_file()}
    git_head = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    git_branch = subprocess.check_output(["git", "branch", "--show-current"], cwd=ROOT, text=True).strip()
    porcelain = subprocess.check_output(["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"], cwd=ROOT)
    run_provenance = {"git_head": git_head, "branch": git_branch, "dirty_worktree_status_sha256_at_report_build": hashlib.sha256(porcelain).hexdigest(), "observed_pre_edit_porcelain_entry_count": 201, "pre_edit_status_fingerprint": "NOT_CAPTURED_BEFORE_EDITS", "python_version": sys.version}
    symbols = pit["symbols"]
    new_approved = 0
    new_obs = 0
    coverage = {
        "schema_version": 1, "generated_at_utc": now, "source_report": "reports/phase4_pit_universe_eligibility.json",
        "source_sha256": hashes["reports/phase4_pit_universe_eligibility.json"],
        "original_phase3_event_symbols": 18, "phase4_manifest_approved_records": 20,
        "phase4_approved_within_phase3_sample": 18, "phase4_needs_review": 42,
        "rejected_identity_records": 1, "newly_approved_pit_symbols": new_approved,
        "newly_approved_pit_symbol_date_observations": new_obs,
        "coverage_scope": "Per-symbol/per-membership-interval/source facts inherited from the complete Phase 4 audit; no source-union or current-universe-to-PIT promotion.",
        "symbols": symbols,
        "source_lanes": {
            "approved_yahoo_pit": "18 event-panel names; 20 approved records including THAI/MRDIYT with 48 observations each (below 55-row feature warmup); cutoff 2026-09-04.",
            "official_tradesim_daily": "49 daily files including SET50; 2023-09-21 through 2026-10-21; separate panel pending per-security adjustment/action/identity verification.",
            "settrade_production": "Current-universe production observations; not historical PIT admissible; source-specific only.",
            "organizer_ticks": "13 sessions; execution-only evidence, not daily PIT coverage."
        },
        "resolution": "No newly approved symbol-date observations. 42 NEEDS_REVIEW records retain their symbol-specific Phase 4 exact_gate_reason and exclusion reasons; 1 rejected INTUCH identity remains separate. Existing archive availability cannot establish adjustment basis, issuer identity, or PIT source eligibility.",
        "source_hashes": hashes
    }
    coverage["run_provenance"] = run_provenance
    write("reports/phase5_pit_coverage_matrix.json", coverage)

    holdout = {
        "schema_version": 1, "generated_at_utc": now,
        "source_cutoffs": {"approved_yahoo_pit": "2026-09-04", "official_tradesim_daily_and_index": "2026-10-21", "collector_evidence_observed_through": "2026-10-30"},
        "blocks": [
            {"dates": "2023-01-03 through 2026-09-04", "status": "PREVIOUSLY_SEEN_DIAGNOSTIC", "reason": "Phase 3/4 signal definitions, outcomes, source comparisons, benchmark and holding distributions already inspected."},
            {"dates": "2026-09-05 through 2026-10-30", "status": "PREVIOUSLY_SEEN_DIAGNOSTIC", "reason": "Official history/source comparisons and Oct collector evidence were inspected; stock PIT coverage/identity is not newly approved."},
            {"dates": "2026-10-31 onward", "status": "PROSPECTIVE_ONLY", "reason": "No complete future market session and no outcome evidence available at freeze; preserve future data untouched if a frozen protocol becomes eligible."},
            {"dates": "Unverified historical source/identity intervals", "status": "UNAVAILABLE", "reason": "No verified PIT membership plus source/corporate-action/security identity chain."}
        ],
        "genuinely_independent_oos_exists": False, "effective_time_clusters": None, "effective_symbol_clusters": None,
        "overlap_adjusted_sample_size": None, "minimum_detectable_effect": None,
        "power_status": "NOT_ESTIMABLE_FOR_NEW_SCREEN: no newly admitted sample and no untouched outcome block; existing Phase 3/4 clustered intervals remain descriptive only.",
        "previously_seen_phase3_h5_cluster_diagnostics": {
            hypothesis: {
                "matched_events": summary.get("matched_event_count_h5"), "unique_symbols": summary.get("unique_symbols_h5"),
                "unique_dates": summary.get("unique_dates_h5"), "adjacent_same_symbol_events_within_7_days": summary.get("adjacent_same_symbol_events_within_7_days"),
                "kish_effective_date_clusters": summary.get("horizons", {}).get("5", {}).get("effective_date_clusters_kish"),
                "kish_effective_symbol_clusters": summary.get("horizons", {}).get("5", {}).get("effective_symbol_clusters_kish"),
                "clustered_95ci_uplift": summary.get("horizons", {}).get("5", {}).get("ci95"),
                "95ci_width_percentage_points": (lambda ci: None if not ci else (ci[1] - ci[0]) * 100)(summary.get("horizons", {}).get("5", {}).get("ci95")),
                "rough_80pct_mde_percentage_points": (lambda ci: None if not ci else (ci[1] - ci[0]) * 0.5 * 1.70 * 100)(summary.get("horizons", {}).get("5", {}).get("ci95")),
                "mde_note": "Normal-equivalent rough approximation from clustered 95% CI half-width, conservatively scaled for four primary tests; descriptive only, not a new power calculation."
            } for hypothesis, summary in phase3.get("hypothesis_summaries", {}).items()
        },
        "no_lookahead": "No holdout outcomes were used to define or tune a new hypothesis; new alpha screen deferred.", "source_hashes": hashes, "run_provenance": run_provenance
    }
    write("reports/phase5_data_holdout_audit.json", holdout)

    repro = {
        "schema_version": 1, "generated_at_utc": now, "status": "RECONCILED_WITH_QUARANTINED_VARIANTS",
        "canonical_phase3_status": "NO_SIGNAL_PASSED_PROMOTION_GATE", "candidate_shortlist_for_human_review": [],
        "phase3_cohorts": {"S3-A": 45, "S3-B": 724, "S3-C": 2269, "S3-D": 486},
        "reconciliation": [
            {"variant": "S3-A_BOOTSTRAP", "status": "HISTORICAL_INTERVAL_METHOD_DRIFT", "action": "Retain original conclusions; regenerated Phase 4 seed intervals are not interchangeable."},
            {"variant": "S3-B_ENDPOINT", "status": "INCOMPATIBLE", "action": "Next-open/close-to-close benchmark endpoint remains separate from original close-to-close definition."},
            {"variant": "S3-C_CONTROLS", "status": "INCOMPATIBLE", "action": "Direction-aligned same-symbol/year non-gap controls remain separate from same-date cross-section."},
            {"variant": "S3-D_EVENT_BOOK", "status": "UNRESOLVED_SINGLE_EVENT", "action": "One-event provenance discrepancy quarantined; do not silently reconcile by outcome."}
        ],
        "canonical_reproduction_seeds": {"phase3_final_primary": 20261030, "phase4_holding_curve": "20261101 plus fixed horizon offsets", "phase3_bootstrap_replications": 10000, "phase4_holding_bootstrap_replications": 10000},
        "existing_result": "All four fail G1; all 32 Phase 4 horizon uplift tests Holm-adjusted p=1 in existing scenarios; tick stress erased positive point estimates; no independently eligible OOS.",
        "cost_fields": {"fee_only_net": "distinct from one-tick stress", "one_tick_per_side_stress": "sensitivity, not calibrated fill", "benchmark_relative_uplift": "source/date aligned only", "executable_long_only_net_pnl": "not established from daily bars"},
        "deterministic_reproduction": "Prior event IDs and hashes retained in Phase 3 outputs. This Phase 5 audit did not rerun or overwrite Phase 3/4 results.", "source_hashes": hashes, "run_provenance": run_provenance
    }
    write("reports/phase5_reproducibility.json", repro)

    mechanic_source = read("reports/tradesim_027_execution_semantics.json")
    readiness = read("reports/tradesim_027_readiness.json")
    mechanics = {
        "schema_version": 1, "generated_at_utc": now, "classification": "RESEARCH_ONLY_MECHANICAL_FEASIBILITY",
        "version": "0.2.7", "python": "3.13.0", "runtime_validated": readiness.get("runtime_validated"),
        "archive_sha256": readiness.get("archive_sha256"), "runtime_source_sha256": readiness.get("runtime_source_sha256"),
        "observed_fixture_checks": mechanic_source.get("checks", {}),
        "controlled_scenarios": ["no fill/close limit", "partial IOC fill and canceled remainder", "tick-volume cap", "invalid tick rejection", "auction exclusion", "cash/position constraints", "FIFO partial close", "cross-symbol delayed tick", "pre/post 2026-11-16 tick ladder"],
        "official_local_tick_dates_available": 13, "real_tick_order_run_this_phase": {"run_id": "20261030T185523Z_c0474a64", "date": "2026-10-21", "source_tick_sha256": hashes.get("data/official/tradesim/ticks/ticks/2026-10-21.csv"), "requests": 1, "accepted_orders": 0, "fills": 0, "result": "REJECTED_IN_SIMULATOR", "reason": "buy volume exceeded cumulative sell volume in the official daily tick sequence", "classification": "mechanical feasibility only; one data-date case; not fill-rate evidence"},
        "known_runtime_discrepancy": "Cross-symbol limit can fill on the first later own-symbol tick; actual fill Timestamp differs from Placed despite changelog wording.",
        "qualification": "Mechanical fixtures do not establish historical or competition execution, fill probability, alpha, or Common Criteria.",
        "real_broker_orders_placed": 0, "source_hashes": hashes, "run_provenance": run_provenance
    }
    write("reports/phase5_official_tick_mechanics.json", mechanics)

    feasibility = read("reports/phase4_nonpromotional_baselines.json")
    risk_envelope = read("reports/competition_benchmark_risk_envelope.json")
    feasibility.update({"phase5_generated_at_utc": now, "competition_period": "2026-12-16 through 2027-01-15", "expected_sessions": 21,
                        "award_objective": {"primary": "Best Alpha", "secondary": "Best Risk Control"},
                        "common_criteria_status": "CONDITIONAL_OR_UNKNOWN", "unknown_fields": ["organizer scoring benchmark/revisions", "actual tick-level fills and volume", "boundary-day NAV/fills", "cross-boundary FIFO eligibility", "expected payoff from completed FIFO lots"],
                        "source_specific_benchmark_21_session_rolling_mdd": risk_envelope,
                        "no_strategy_portfolio": "No signal passed G1; no strategy-specific 3/5/8 position optimization or official replay was run.",
                        "source_hashes": hashes, "run_provenance": run_provenance})
    write("reports/phase5_competition_feasibility.json", feasibility)

    collector = {
        "schema_version": 1, "generated_at_utc": now, "oct30": {
            "task_last_result": 1, "runner_status": "FAILED_AFTER_RETRY_LIMIT", "startup": "READY",
            "runtime_seconds": 8466.48, "rotation_generations": 21, "one_minute_rows_written": 5314,
            "bbo_events_written": 9689, "orders_placed": 0,
            "cause": "Local health subprocess exceeded its 60-second timeout on three checks; collector cycles themselves exited 0 before health checks. No evidence the runner was deadlocked; it continued to collect and checkpoint while health checks timed out.",
            "fix_status": "Default bounded health timeout raised to 180 seconds (minimum 90, maximum 300); nonzero errors and runner exit behavior preserved; focused tests required."},
        "oct29": "PARTIAL_COLLECTION; later daily recovery 50/50 does not prove original scheduled invocation.",
        "logged_out_runtime": "UNATTENDED_CONFIGURED_NOT_RUNTIME_VALIDATED; Password logon metadata and interactive_only=false were directly rechecked in Task Scheduler; no proof of run in logged-out session.",
        "task_metadata_recheck": {"enabled": True, "state": "Ready", "logon_type": "Password", "interactive_only": False, "evidence": "Read-only Get-ScheduledTask query during Phase 5 audit; no task settings changed."},
        "nov2": {"status": "NOV2_NOT_YET_OBSERVABLE", "scheduled_local": "2026-11-02 09:45 Asia/Bangkok", "command": ".\\.venv\\Scripts\\python.exe scripts\\check_settrade_collector_readonly.py --target-date 2026-11-02"},
        "source_hashes": hashes, "run_provenance": run_provenance
    }
    write("reports/phase5_collector_diagnostics.json", collector)
    write("reports/phase5_signal_screen.json", {"status": "NEW_ALPHA_SCREEN_DEFERRED", "reason": "Zero newly approved PIT symbol-date observations and no genuinely untouched observed outcome block; running a screen would recycle seen outcomes or rely on unverified source joins.", "hypothesis_count": 0, "candidate_shortlist_for_human_review": [], "preregistration": "config/phase5_preregistration.json", "source_hashes": hashes})

    registry = read("reports/experiment_registry.json")
    experiment_id = "PHASE5_PIT_UNLOCK_EXECUTION_AND_RESEARCH_20261031"
    registry["experiments"] = [x for x in registry.get("experiments", []) if x.get("experiment_id") != experiment_id]
    registry["experiments"].append({"experiment_id": experiment_id, "hypothesis_id": "PIT_UNLOCK_AND_MECHANICAL_READINESS", "status": "DATA_GATED_NO_CANDIDATE", "engine": "PHASE5_AUDIT_AND_0.2.7_MECHANICS", "source_data": "Phase 3/4 evidence, source-specific archives and Oct 30 collector logs; no merged stock return panel", "parameters": "No alpha hypothesis screened; preregistration frozen in config/phase5_preregistration.json", "metrics_artifacts": ["reports/phase5_pit_coverage_matrix.json", "reports/phase5_data_holdout_audit.json", "reports/phase5_reproducibility.json", "reports/phase5_official_tick_mechanics.json", "reports/phase5_competition_feasibility.json", "reports/phase5_collector_diagnostics.json", "reports/phase5_signal_screen.json"], "source_hashes": hashes, "notes": "No new PIT approval or independent OOS. Mechanical evidence only; no strategy promotion."})
    registry["phase5_status"] = {"experiment_id": experiment_id, "status": "RESEARCH_ONLY_DATA_GATED", "decision_report": "docs/PHASE5_DECISION_REPORT.md", "candidate_shortlist_for_human_review": []}
    write("reports/experiment_registry.json", registry)

    (ROOT / "docs/PHASE5_PIT_DATA_UNLOCK.md").write_text(
        "# Phase 5 PIT Data Unlock\n\nNo newly approved PIT symbol-date observations were added. The Phase 4 matrix remains the complete per-symbol audit: 63 date-effective candidates, 42 `NEEDS_REVIEW`, 20 approved manifest records (18 overlapping the Phase 3 sample), and 1 rejected INTUCH identity. The event panel remains 18 names; THAI and MRDIYT remain below the 55-observation event warmup. The 42 cases retain their exact individual gate and exclusion reasons in [the machine-readable matrix](../reports/phase5_pit_coverage_matrix.json).\n\nOfficial TradeSim daily history (49 files including SET50) and Settrade production data remain separate source lanes. Neither was promoted into PIT stock outcomes because per-security adjustment, identity, corporate-action, source authorization, or historical membership evidence is incomplete. Current-universe data do not create historical PIT membership. No paid backfill was made.\n\n**Newly approved PIT symbols = 0; newly approved symbol-date observations = 0.**\n", encoding="utf-8")
    (ROOT / "docs/PHASE5_RESEARCH_REPRODUCIBILITY.md").write_text(
        "# Phase 5 Research Reproducibility\n\nCanonical Phase 3 status remains `NO_SIGNAL_PASSED_PROMOTION_GATE`; `CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW = []`. Existing S3-A bootstrap drift, S3-B endpoint mismatch, S3-C control definition, and S3-D one-event provenance discrepancy remain explicitly separate/quarantined in [the reconciliation JSON](../reports/phase5_reproducibility.json). Phase 4's 32 Holm-adjusted contrasts remain historical seen-data diagnostics, not new confirmation.\n\nThe interval through 2026-10-30 is `PREVIOUSLY_SEEN_DIAGNOSTIC`; later periods are prospective only. No genuinely independent OOS block exists at this freeze. New alpha screening is deferred because no new PIT-approved observations or untouched outcomes are available.\n", encoding="utf-8")
    (ROOT / "docs/PHASE5_TICK_EXECUTION_FEASIBILITY.md").write_text(
        "# Phase 5 Official Tick Execution Feasibility\n\nTradeSim 0.2.7 is runtime validated in exact Python 3.13.0. Preserved fixtures cover tick volume clipping, IOC remainder cancellation, no-fill close limits, invalid ticks, auctions, FIFO partial sells, cross-symbol delay, and the 2026-11-16 tick-ladder change. A single offline LIMIT request driven by the actual 2026-10-21 official tick file was rejected because requested buy volume exceeded cumulative eligible sell volume. It produced zero accepted orders and zero fills. Tick source SHA-256 and run ID are in [machine evidence](../reports/phase5_official_tick_mechanics.json).\n\nThese are mechanical checks, not a measured fill rate or alpha evidence. The one-date probe is not market-wide evidence; no strategy replay was run because no signal passed G1. Daily OHLCV cannot establish IOC fills. Cross-symbol timestamp behavior differs from changelog wording and remains disclosed.\n", encoding="utf-8")
    (ROOT / "docs/PHASE5_COLLECTOR_READINESS.md").write_text(
        "# Phase 5 Collector Readiness\n\nOct 30's collector completed 21 rotations and persisted 5,314 1m rows and 9,689 BBO events before it failed after three local health subprocess timeouts at 60 seconds. Collection subprocesses exited 0; the evidence supports a slow health scan as the observed cause, not a stuck collector. Default timeout is now 180 seconds (bounded 90–300), with failure propagation preserved.\n\nOct 29 remains `PARTIAL_COLLECTION`. The Task Scheduler task was directly rechecked as enabled/Ready with Password logon and `interactive_only=false`, but actual unattended execution remains `UNATTENDED_CONFIGURED_NOT_RUNTIME_VALIDATED`. Nov 2 is `NOV2_NOT_YET_OBSERVABLE`. Read-only check after 09:45 Bangkok: `'.\\.venv\\Scripts\\python.exe scripts\\check_settrade_collector_readonly.py --target-date 2026-11-02'`. See [diagnostics](../reports/phase5_collector_diagnostics.json).\n", encoding="utf-8")
    (ROOT / "docs/PHASE5_DECISION_REPORT.md").write_text(
        "# Phase 5 Decision Report\n\n## Decision\n\nPhase 3/4 conclusions remain unchanged: `NO_SIGNAL_PASSED_PROMOTION_GATE`; `CANDIDATE_SHORTLIST_FOR_HUMAN_REVIEW = []`. Phase 5 added no PIT-approved observations and found no genuinely untouched historical outcome block. `NEW_ALPHA_SCREEN_DEFERRED`. No strategy selected.\n\n## Evidence\n\n- PIT: 18 Phase 3 event symbols and 20 approved manifest rows; 42 candidate identities remain individually `NEEDS_REVIEW`, one INTUCH identity is rejected. Net Phase 5 approvals: zero symbols and zero symbol-date observations.\n- Holdout: all historical outcomes through the observed Oct 30 evidence window are previously seen diagnostics; Oct 31 onward is prospective. Independent OOS does not exist. Effective power/MDE for a new screen is therefore not estimable.\n- Reproducibility: incompatible S3-A/B/C/D definitions remain separately labeled. Existing Phase 3/4 rejection status is preserved.\n- TradeSim 0.2.7: exact Python 3.13.0 runtime is validated; existing fixtures cover IOC/volume/FIFO/ladder mechanics. A one-order official-tick probe was rejected by the local simulator's cumulative-volume constraint and created zero fills. Neither this probe nor the fixtures estimate fill rates or alpha.\n- KGI scoring PDF: all 18 pages were extracted and read directly. SHA-256: `e2a7d549dfffd9691e077a09ba3e51d94a3da11da3da9433ba717039721d79f1`. Verified Common Criteria are Portfolio MDD `< 1.5×` benchmark MDD, at least 5 FIFO-completed round trips, average daily close exposure `≥ 50%`, and expected payoff `> 0`. Best Alpha adds nonnegative portfolio return and excess return; ranks by excess return, Calmar, portfolio return. Best Risk Control ranks by Calmar, excess return, then lowest MDD.\n- Competition feasibility: Phase 4 non-promotional 21-session rolling baseline remains the only feasibility baseline. 5 FIFO round trips and 50% exposure cannot be confirmed from daily bars or assumed fills. Common Criteria stay `CONDITIONAL_OR_UNKNOWN`. Best Alpha remains primary, Best Risk Control secondary.\n- Collector: Oct 30 cycles persisted data but failed after repeated 60-second health subprocess timeouts. The bounded default is increased to 180 seconds, with failure propagation preserved. Logged-out execution remains configuration-only; Nov 2 is not yet observable.\n\n## Human decisions and organizer questions\n\n`HUMAN_DECISIONS_REQUIRED: NONE`. The only outstanding policy questions remain in [QUESTIONS_FOR_ORGANIZER.md](QUESTIONS_FOR_ORGANIZER.md): official benchmark/revision, boundary NAV/fill cutoff, and cross-boundary FIFO lot eligibility.\n\n## Next actions\n\n1. Preserve new prospective PIT evidence and resolve each source/identity case only with dated primary provenance.\n2. Run the read-only Nov 2 collector check after its scheduled time and validate persisted market-time coverage.\n3. Keep TradeSim mechanics and signal research separate until a signal has newly qualified PIT coverage and an untouched chronological evaluation block.\n", encoding="utf-8")


if __name__ == "__main__":
    main()

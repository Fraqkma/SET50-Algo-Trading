"""Run frozen Phase 3 hypotheses and benchmark risk envelope diagnostics."""
from __future__ import annotations

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.eligibility import MarketDataEligibilityGate
from src.data.research import load_approved_market_data
from src.research.phase3_final import (
    holm_adjust, kish_effective_clusters, prepare_daily_features,
    g1_promotion_gate,
    rolling_benchmark_drawdowns, summarize_risk_envelope,
    two_way_pigeonhole_bootstrap,
)


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> None:
    gate = MarketDataEligibilityGate(ROOT)
    manifest_path = ROOT / "data/processed/approved_market_data_manifest.csv"
    manifest = pd.read_csv(manifest_path)
    frames: dict[str, pd.DataFrame] = {}
    source_paths: set[Path] = set()
    for row in manifest.itertuples(index=False):
        if not str(row.approval_status).startswith("APPROVED"):
            continue
        try:
            frame = load_approved_market_data(row.set_symbol, gate=gate)
        except (ValueError, FileNotFoundError):
            continue
        if len(frame) >= 55 and {"open", "high", "low", "close", "volume"}.issubset(frame.columns):
            frames[row.set_symbol] = prepare_daily_features(frame)
            path = gate.approved_raw_file(row.set_symbol)
            if path:
                source_paths.add(path)
    source_hashes_by_symbol = {symbol: sha(gate.approved_raw_file(symbol)) for symbol in frames}

    bench_path = ROOT / "data/official/tradesim/history/benchmark/SET50.csv"
    benchmark = pd.read_csv(bench_path)
    benchmark["Date"] = pd.to_datetime(benchmark.Date).dt.normalize()
    benchmark = benchmark.drop_duplicates("Date").set_index("Date").sort_index()
    benchmark_close = pd.to_numeric(benchmark.Close, errors="coerce")
    benchmark_features = pd.DataFrame(index=benchmark.index)
    benchmark_features["close"] = benchmark_close
    benchmark_features["sma50"] = benchmark_close.rolling(50, min_periods=50).mean()
    benchmark_features["return20"] = benchmark_close.pct_change(20)

    def benchmark_return(start_date: pd.Timestamp, end_date: pd.Timestamp) -> float | None:
        start_value = benchmark_close.get(start_date)
        end_value = benchmark_close.get(end_date)
        if pd.isna(start_value) or pd.isna(end_value) or not start_value:
            return None
        return float(end_value / start_value - 1)

    rows: list[dict] = []
    def provenance(symbol: str, decision_date: pd.Timestamp) -> dict[str, str]:
        b = benchmark_features.reindex([decision_date]).iloc[0] if decision_date in benchmark_features.index else None
        if b is None or pd.isna(b.sma50) or pd.isna(b.return20):
            regime = "UNKNOWN"
        else:
            regime = "POSITIVE" if b.close > b.sma50 and b.return20 >= 0 else "OTHER"
        return {"data_source": "approved_market_data_manifest.csv / approved raw daily CSV",
                "source_file": str(gate.approved_raw_file(symbol).relative_to(ROOT)),
                "source_sha256": source_hashes_by_symbol[symbol],
                "pit_state": "APPROVED", "market_regime": regime}
    all_dates = sorted(set().union(*(set(f.index) for f in frames.values())))
    for symbol, f in frames.items():
        raw_close = pd.to_numeric(f.close, errors="coerce")
        adj_close = pd.to_numeric(f.adjusted_close, errors="coerce") if "adjusted_close" in f else raw_close
        adj_open = f.open * (adj_close / raw_close)
        for i, date in enumerate(f.index):
            # load_approved_market_data already applied the PIT gate per row.
            if i < 55 or i + 5 >= len(f):
                continue
            vol_ratio = f.volume_ratio20.iloc[i]
            event = {
                "S3-A": bool(pd.notna(f.atr10_pct.iloc[i]) and pd.notna(f.prior20_atr10_pct.iloc[i]) and pd.notna(f.adjusted_prior20_high.iloc[i]) and pd.notna(vol_ratio) and f.atr10_pct.iloc[i] <= .8 * f.prior20_atr10_pct.iloc[i] and adj_close.iloc[i] > f.adjusted_prior20_high.iloc[i] and vol_ratio >= 1.5),
                "S3-D": bool(pd.notna(vol_ratio) and vol_ratio >= 2 and f.return1.iloc[i] > .005),
            }
            # S3-B is assessed cross-sectionally below.
            for hid in ("S3-A", "S3-D"):
                for h in (1, 2, 3, 5):
                    if i + h >= len(f):
                        continue
                    ret = float(adj_close.iloc[i + h] / adj_open.iloc[i + 1] - 1)
                    benchmark_cc = benchmark_return(date, f.index[i + h])
                    rows.append({"hypothesis": hid, "symbol": symbol, "date": date.date().isoformat(), "h": h,
                                 "event": event[hid], "return": ret, "known_at": "SESSION_CLOSE_DATE_ONLY",
                                 "benchmark_close_return_signal_to_end": benchmark_cc,
                                 "benchmark_relative_return": ret - benchmark_cc if benchmark_cc is not None else None,
                                 "benchmark_relative_reference": "stock next-open-to-horizon-close minus benchmark signal-close-to-end-close",
                                 "atr10_pct": float(f.atr10_pct.iloc[i]) if pd.notna(f.atr10_pct.iloc[i]) else None,
                                 "prior20_atr10_pct": float(f.prior20_atr10_pct.iloc[i]) if pd.notna(f.prior20_atr10_pct.iloc[i]) else None,
                                 "volume_ratio20": float(vol_ratio) if pd.notna(vol_ratio) else None,
                                 "momentum20": float(f.momentum20.iloc[i]) if pd.notna(f.momentum20.iloc[i]) else None,
                                 **provenance(symbol, date)})
            # Gap events are observable at next open, but no open fill is assumed.
            gap = float(f.open.iloc[i + 1] / raw_close.iloc[i] - 1) if raw_close.iloc[i] else np.nan
            if np.isfinite(gap):
                aligned = 1 if gap > 0 else -1
                is_gap = abs(gap) >= .01
                for h in (1, 2, 3, 5):
                    if i + 1 + h >= len(f):
                        continue
                    outcome = aligned * float(adj_close.iloc[i + 1 + h] / adj_close.iloc[i + 1] - 1)
                    unaligned = float(adj_close.iloc[i + 1 + h] / adj_close.iloc[i + 1] - 1)
                    benchmark_cc = benchmark_return(f.index[i + 1], f.index[i + 1 + h])
                    rows.append({"hypothesis": "S3-C", "symbol": symbol, "date": f.index[i + 1].date().isoformat(),
                                 "h": h, "event": is_gap, "return": outcome, "return_unaligned": unaligned, "gap_pct": gap,
                                 "benchmark_close_return_signal_to_end": benchmark_cc,
                                 "benchmark_relative_return": unaligned - benchmark_cc if benchmark_cc is not None else None,
                                 "direction_aligned_benchmark_relative_return": outcome - aligned * benchmark_cc if benchmark_cc is not None else None,
                                 "benchmark_relative_reference": "gap-session-close-to-horizon-close minus benchmark gap-session-close-to-end-close",
                                 "known_at": "OPEN_PRINT_TIME_UNAVAILABLE", "momentum20": float(f.momentum20.iloc[i]) if pd.notna(f.momentum20.iloc[i]) else None,
                                 "volume_ratio20": float(vol_ratio) if pd.notna(vol_ratio) else None,
                                 **provenance(symbol, f.index[i + 1])})

    raw = pd.DataFrame(rows)
    # Compute S3-B with only dates having at least ten simultaneously eligible names.
    b_rows: list[dict] = []
    panel: dict[pd.Timestamp, list[tuple[str, pd.Series, pd.DataFrame]]] = {}
    for symbol, f in frames.items():
        for i, date in enumerate(f.index):
            # The panel is built only from rows returned by the date-aware gate.
            if i < 55 or i + 5 >= len(f):
                continue
            b = benchmark_features.reindex([date]).iloc[0]
            panel.setdefault(date, []).append((symbol, f.iloc[i], f.iloc[i:i + 6]))
    for date, members in panel.items():
        if len(members) < 10 or date not in benchmark_features.index:
            continue
        b = benchmark_features.loc[date]
        if pd.isna(b.sma50) or pd.isna(b.return20) or b.close <= b.sma50 or b.return20 < 0:
            continue
        momentum = [(s, float(row.momentum20)) for s, row, _ in members if pd.notna(row.momentum20) and row.momentum20 > 0]
        if not momentum:
            continue
        cutoff = np.quantile([v for _, v in momentum], .8)
        evset = {s for s, m in momentum if m >= cutoff}
        for symbol, row, hist in members:
            f = frames[symbol]
            idx = f.index.get_loc(date)
            adj = f.adjusted_close if "adjusted_close" in f else f.close
            for h in (1, 2, 3, 5):
                if idx + h >= len(f):
                    continue
                stock_ret = float(adj.iloc[idx + h] / adj.iloc[idx] - 1)
                bd = benchmark_close.reindex([date, f.index[idx + h]]).dropna()
                rel = stock_ret - (float(bd.iloc[-1] / bd.iloc[0] - 1) if len(bd) == 2 else np.nan)
                b_rows.append({"hypothesis": "S3-B", "symbol": symbol, "date": date.date().isoformat(), "h": h,
                               "event": symbol in evset, "return": rel, "known_at": "SESSION_CLOSE_DATE_ONLY",
                               "momentum20": float(row.momentum20) if pd.notna(row.momentum20) else None,
                               **provenance(symbol, date)})
    if b_rows:
        raw = pd.concat([raw, pd.DataFrame(b_rows)], ignore_index=True)

    summaries: dict[str, dict] = {}
    primary_ps: dict[str, float | None] = {}
    for hid in ("S3-A", "S3-B", "S3-C", "S3-D"):
        sub = raw[raw.hypothesis == hid]
        e = sub[sub.event].copy()
        controls = sub[~sub.event].copy()
        horizons: dict[str, dict] = {}
        diffs_primary: list[float] = []
        d_primary: list[str] = []
        s_primary: list[str] = []
        for h in (1, 2, 3, 5):
            ev = e[e.h == h]
            co = controls[controls.h == h]
            diffs: list[float] = []
            ds: list[str] = []
            ss: list[str] = []
            for _, evrow in ev.iterrows():
                if hid == "S3-C":
                    eligible = co[(co.symbol == evrow["symbol"]) & (pd.to_datetime(co.date).dt.year == pd.Timestamp(evrow["date"]).year)]
                    control_mean = float((eligible["return_unaligned"] * np.sign(evrow["gap_pct"])).mean()) if not eligible.empty else np.nan
                else:
                    eligible = co[co.date == evrow["date"]]
                    control_mean = float(eligible["return"].mean()) if not eligible.empty else np.nan
                if eligible.empty or not np.isfinite(evrow["return"]):
                    continue
                diffs.append(float(evrow["return"] - control_mean))
                ds.append(evrow["date"]); ss.append(evrow["symbol"])
            matched_control_mean = float(np.mean([float(e.loc[(e.symbol == symbol) & (e.date == day) & (e.h == h), "return"].iloc[0]) - diff for symbol, day, diff in zip(ss, ds, diffs)])) if diffs else None
            boot = two_way_pigeonhole_bootstrap(diffs, ds, ss, seed=20261030) if h == 5 else {"mean": float(np.mean(diffs)) if diffs else None, "ci95": None, "p_two_sided_centered": None}
            horizons[str(h)] = {
                "raw_events": int(len(ev)), "matched_events": len(diffs),
                "symbols": int(ev.symbol.nunique()), "dates": int(ev.date.nunique()),
                "event_mean": float(ev["return"].mean()) if len(ev) else None,
                "event_median": float(ev["return"].median()) if len(ev) else None,
                "hit_rate_direction_aligned": float((ev["return"] > 0).mean()) if len(ev) else None,
                "control_mean_matched": matched_control_mean,
                "mean_uplift": boot.get("mean"), "ci95": boot.get("ci95"),
                "p_two_sided_centered": boot.get("p_two_sided_centered"),
                "effective_date_clusters_kish": kish_effective_clusters(ds),
                "effective_symbol_clusters_kish": kish_effective_clusters(ss),
                "event_q10_q90": [float(ev["return"].quantile(.1)), float(ev["return"].quantile(.9))] if len(ev) else None,
            }
            if h == 5:
                diffs_primary, d_primary, s_primary = diffs, ds, ss
        p = horizons["5"]["p_two_sided_centered"]
        primary_ps[hid] = p
        event_primary = e[e.h == 5]
        adequate = (len(diffs_primary) >= 30 and event_primary.symbol.nunique() >= 10 and event_primary.date.nunique() >= 20)
        ci = horizons["5"]["ci95"]
        pass_g1 = bool(adequate and ci and ci[0] > 0 and p is not None)
        summaries[hid] = {
            "status": "G1_PASS_REQUIRES_G2_G3" if pass_g1 else ("REJECTED_INADEQUATE_OR_NONPOSITIVE_EVIDENCE"),
            "g0": "PASS_WITH_PARTIAL_PIT_PANEL_AND_DATE_ONLY_SEMANTICS" if len(e) else "NO_EVENTS",
            "g1_adequacy": adequate, "raw_event_count_h5": len(event_primary),
            "matched_event_count_h5": len(diffs_primary), "unique_symbols_h5": int(event_primary.symbol.nunique()),
            "unique_dates_h5": int(event_primary.date.nunique()),
            "unique_pairs_h5": int(event_primary[["symbol", "date"]].drop_duplicates().shape[0]) if len(event_primary) else 0,
            "adjacent_same_symbol_events_within_7_days": int(sum((pd.Timestamp(b)-pd.Timestamp(a)).days <= 7 for _, g in event_primary.groupby("symbol") for a,b in zip(sorted(g.date)[:-1], sorted(g.date)[1:]))),
            "horizons": horizons,
        }
        slice_rows = []
        for label, start, end in (("2023-09-21_to_2024-12-31", "2023-09-21", "2024-12-31"),
                                  ("2025", "2025-01-01", "2025-12-31"),
                                  ("2026_to_2026-09-04", "2026-01-01", "2026-09-04")):
            mask = (pd.to_datetime(event_primary.date) >= start) & (pd.to_datetime(event_primary.date) <= end)
            subset = event_primary.loc[mask]
            matched_mask = [(start <= day <= end) for day in d_primary]
            slice_diffs = [value for value, include in zip(diffs_primary, matched_mask) if include]
            slice_rows.append({"slice": label, "seen_not_oos": True, "events": int(len(subset)),
                               "symbols": int(subset.symbol.nunique()), "dates": int(subset.date.nunique()),
                               "event_mean": float(subset["return"].mean()) if len(subset) else None,
                               "matched_uplift_mean": float(np.mean(slice_diffs)) if slice_diffs else None,
                               "matched_count": len(slice_diffs)})
        summaries[hid]["chronological_slices"] = slice_rows
    adjusted = holm_adjust(primary_ps)
    for hid in summaries:
        summaries[hid]["holm_adjusted_p_h5"] = adjusted[hid]
        ci = summaries[hid]["horizons"]["5"]["ci95"]
        summaries[hid]["holm_gate_pass"] = g1_promotion_gate(
            matched_events=summaries[hid]["matched_event_count_h5"],
            symbols=summaries[hid]["unique_symbols_h5"], dates=summaries[hid]["unique_dates_h5"],
            ci95=ci, holm_adjusted_p=adjusted[hid],
        )
        if not summaries[hid]["holm_gate_pass"]:
            summaries[hid]["status"] = "REJECTED_G1_NOT_MET"

    windows = rolling_benchmark_drawdowns(benchmark.reset_index().rename(columns={"index": "Date"}))
    risk = summarize_risk_envelope(windows)
    risk.update({"status": "BENCHMARK_AWARE_RISK_ENVELOPE", "source": str(bench_path.relative_to(ROOT)),
                 "benchmark_sha256": sha(bench_path), "exploratory_pre_freeze_calculation_disclosed": True,
                 "official_scoring_feed_and_revision_policy": "UNCONFIRMED"})
    (ROOT / "reports/competition_benchmark_risk_envelope.json").write_text(json.dumps(risk, indent=2), encoding="utf-8")

    run_at = datetime.now(timezone.utc).isoformat()
    prereg = ROOT / "docs/RESEARCH_PHASE3_PRE_REGISTRATION_FINAL.md"
    config = ROOT / "config/research_phase3_hypotheses_final.json"
    head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    status = subprocess.run(["git", "status", "--porcelain=v1", "-z"], cwd=ROOT, capture_output=True).stdout
    code_paths = [ROOT / "scripts/run_phase3_final_research.py", ROOT / "scripts/build_phase3_execution_sensitivity.py", ROOT / "src/research/phase3_final.py",
                  ROOT / "src/data/research.py", ROOT / "src/data/eligibility.py"]
    paths = [manifest_path, ROOT / "data/processed/constituents/historical_set50.csv", bench_path, prereg, config, *sorted(source_paths)]
    summary = {
        "schema_version": 1, "engine": "RESEARCH_DIAGNOSTIC", "run_timestamp_utc": run_at,
        "git_head": head, "worktree_dirty": bool(status), "worktree_porcelain_entries_at_run": status.count(b"\0"),
        "pre_registration_sha256": sha(prereg), "hypothesis_config_sha256": sha(config),
        "code_hashes": {str(p.relative_to(ROOT)): sha(p) for p in code_paths},
        "worktree_porcelain_sha256_at_run": hashlib.sha256(status).hexdigest(),
        "python_version": platform.python_version(), "hypothesis_summaries": summaries,
        "holm_adjusted_p_values": adjusted, "risk_envelope": "reports/competition_benchmark_risk_envelope.json",
        "data": {"approved_symbols": sorted(frames), "partial_pit_panel": True,
                 "sample_start": str(min(x.index.min() for x in frames.values()).date()),
                 "sample_end": str(max(x.index.max() for x in frames.values()).date()),
                 "source_hashes": {str(p.relative_to(ROOT)): sha(p) for p in paths}},
        "gates": {"g0": "PASS_WITH_LIMITATIONS", "g1": "PASS" if any(v["holm_gate_pass"] for v in summaries.values()) else "FAIL_ALL",
                  "g2": "NOT_RUN_NO_G1_SURVIVOR", "g3": "NOT_RUN_NO_G1_SURVIVOR", "g4": "NOT_RUN_NO_G1_SURVIVOR"},
        "promotion_summary": "NO_SIGNAL_PASSED_PROMOTION_GATE" if not any(v["holm_gate_pass"] for v in summaries.values()) else "SIGNAL_REQUIRES_FURTHER_GATES",
        "position_count_study": "NOT_RUN_AFTER_G1_REJECTION" if not any(v["holm_gate_pass"] for v in summaries.values()) else "PENDING_G3",
        "execution_sensitivity": "reports/execution_sensitivity_027_fixed_fill_arithmetic.json",
        "cost_assumptions": {"commission_rate": 0.00157, "vat_rate": 0.07, "combined_side_rate": 0.0016799,
                             "baseline_slippage": "one adverse SET tick per filled side; prior V1 fills",
                             "stress": "1.5x baseline fees plus one additional adverse tick; fixed-fill arithmetic only"},
        "limitations": ["All approved stock history was previously inspected; no untouched OOS claim.",
                        "Approved PIT panel is partial, not full historical SET50.",
                        "Daily bars cannot establish fill probabilities, spread, depth, or IOC fill size.",
                        "Official scoring benchmark feed/revision policy is unconfirmed.",
                        "Historical rolling windows overlap and are not independent."]
    }
    out = ROOT / "reports/research_phase3_summary.json"
    out.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    raw[raw.event].to_json(ROOT / "reports/research_phase3_event_outcomes.jsonl", orient="records", lines=True, force_ascii=False)
    registry_path = ROOT / "reports/experiment_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    experiment_id = "PHASE3_FINAL_DIRECTION_ADDENDUM_20261030"
    if not any(item.get("experiment_id") == experiment_id for item in registry.get("experiments", [])):
        registry.setdefault("experiments", []).append({
            "experiment_id": experiment_id, "hypothesis_id": "S3-A/S3-B/S3-C/S3-D",
            "status": summary["promotion_summary"], "engine": "RESEARCH_DIAGNOSTIC",
            "generated_at_utc": run_at, "git_head": head, "dirty_worktree": True,
            "dirty_entries_at_run": summary["worktree_porcelain_entries_at_run"],
            "dirty_status_sha256": summary["worktree_porcelain_sha256_at_run"],
            "pre_registration_sha256": summary["pre_registration_sha256"],
            "hypothesis_config_sha256": summary["hypothesis_config_sha256"],
            "source_hashes": summary["data"]["source_hashes"], "code_hashes": summary["code_hashes"],
            "python_version": platform.python_version(), "period": summary["data"],
            "costs": summary["cost_assumptions"], "execution_model": "signal diagnostic; no fills; separate fixed-fill arithmetic sensitivity",
            "metrics_artifacts": ["reports/research_phase3_summary.json", "reports/research_phase3_event_outcomes.jsonl",
                                  "reports/competition_benchmark_risk_envelope.json", "reports/execution_sensitivity_027_fixed_fill_arithmetic.json"],
            "test_status": "POST_RUN_VALIDATION_PENDING",
            "notes": "All four frozen signals failed G1 after clustered CI/Holm; no portfolio construction or TradeSim candidate replay."
        })
    registry["latest_phase3_run"] = {"git_head": head, "run_date": run_at[:10],
                                      "preregistration": str(prereg.relative_to(ROOT)),
                                      "summary": str(out.relative_to(ROOT)),
                                      "promotion_summary": summary["promotion_summary"],
                                      "experiment_id": experiment_id}
    registry_path.write_text(json.dumps(registry, indent=2), encoding="utf-8")
    print(json.dumps({k: {"status": v["status"], "events": v["raw_event_count_h5"], "matched": v["matched_event_count_h5"], "uplift": v["horizons"]["5"]["mean_uplift"], "ci95": v["horizons"]["5"]["ci95"], "holm_p": v["holm_adjusted_p_h5"]} for k, v in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()

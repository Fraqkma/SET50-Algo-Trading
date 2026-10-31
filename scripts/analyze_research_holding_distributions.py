"""Exploratory fixed-horizon diagnostics on the frozen Phase 3 event cohorts."""
from __future__ import annotations

import hashlib
import json
import sys
from functools import lru_cache
from collections import Counter
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.eligibility import MarketDataEligibilityGate
from src.data.research import load_approved_market_data
from src.research.phase3_final import prepare_daily_features, kish_effective_clusters
from src.research.holding_period import (
    align_directional_return, cluster_bootstrap, holm_adjust, passage_counts,
)
from scripts.run_design_a_backtest import set_tick_size

HORIZONS = (1, 2, 3, 4, 5, 7, 10, 15)
HYPOTHESES = ("S3-A", "S3-B", "S3-C", "S3-D")
FEE_PER_SIDE = 0.00157 * 1.07
ROUND_TRIP_FEE = 2 * FEE_PER_SIDE
SEED = 20261101


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=100_000)
def _tick(price_text: str) -> float:
    return float(set_tick_size(Decimal(price_text)))


def tick_cost(raw_entry: float, raw_exit: float) -> float:
    entry_tick = _tick(str(raw_entry))
    exit_tick = _tick(str(raw_exit))
    return entry_tick / raw_entry + exit_tick / raw_exit


def net_return(frame: pd.DataFrame, entry_i: int, exit_i: int,
               entry_kind: str, *, stress_tick: bool) -> tuple[float, float]:
    raw_entry = float(frame.iloc[entry_i].open if entry_kind == "open" else frame.iloc[entry_i].close)
    raw_exit = float(frame.iloc[exit_i].close)
    adj_close = frame.adjusted_close if "adjusted_close" in frame else frame.close
    factor_entry = float(adj_close.iloc[entry_i] / frame.close.iloc[entry_i])
    adj_entry = raw_entry * factor_entry
    adj_exit = float(adj_close.iloc[exit_i])
    gross = adj_exit / adj_entry - 1
    costs = ROUND_TRIP_FEE + (tick_cost(raw_entry, raw_exit) if stress_tick else 0.0)
    return gross, gross - costs


def outcome(frame: pd.DataFrame, signal_i: int, h: int, hypothesis: str,
            *, stress_tick: bool) -> tuple[float, float] | None:
    if hypothesis == "S3-C":
        entry_i, exit_i, entry_kind = signal_i, signal_i + h, "close"
    else:
        entry_i, exit_i, entry_kind = signal_i + 1, signal_i + h, "open"
    if exit_i >= len(frame) or entry_i >= len(frame):
        return None
    return net_return(frame, entry_i, exit_i, entry_kind, stress_tick=stress_tick)


def subtract_benchmark_return(result: tuple[float, float] | None, frame: pd.DataFrame,
                              signal_i: int, h: int, benchmark_close: pd.Series
                              ) -> tuple[float, float] | None:
    """Express S3-B stock outcome relative to the sourced index over signal-to-exit closes."""
    if result is None:
        return None
    start = frame.index[signal_i]
    end_i = signal_i + h
    if end_i >= len(frame):
        return None
    end = frame.index[end_i]
    start_value = benchmark_close.get(start)
    end_value = benchmark_close.get(end)
    if pd.isna(start_value) or pd.isna(end_value) or not start_value:
        return None
    benchmark_return = float(end_value / start_value - 1)
    return result[0] - benchmark_return, result[1] - benchmark_return


def event_flag(hypothesis: str, frame: pd.DataFrame, i: int,
               gap_events: set[tuple[str, str]]) -> bool:
    symbol = str(frame.attrs.get("symbol", ""))
    date = frame.index[i].date().isoformat()
    if hypothesis == "S3-C":
        return (symbol, date) in gap_events
    if hypothesis == "S3-B":
        return False
    f = frame
    vol_ratio = f.volume_ratio20.iloc[i]
    if pd.isna(vol_ratio):
        return False
    if hypothesis == "S3-A":
        return bool(pd.notna(f.atr10_pct.iloc[i]) and pd.notna(f.prior20_atr10_pct.iloc[i])
                    and pd.notna(f.adjusted_prior20_high.iloc[i])
                    and f.atr10_pct.iloc[i] <= .8 * f.prior20_atr10_pct.iloc[i]
                    and f.adjusted_close.iloc[i] > f.adjusted_prior20_high.iloc[i]
                    and vol_ratio >= 1.5)
    return bool(vol_ratio >= 2 and f.return1.iloc[i] > .005)


def main() -> None:
    gate = MarketDataEligibilityGate(ROOT)
    manifest = pd.read_csv(ROOT / "data/processed/approved_market_data_manifest.csv")
    frames: dict[str, pd.DataFrame] = {}
    for row in manifest.itertuples(index=False):
        if not str(row.approval_status).startswith("APPROVED"):
            continue
        try:
            frame = load_approved_market_data(row.set_symbol, gate=gate)
        except (ValueError, FileNotFoundError):
            continue
        if len(frame) >= 55 and {"open", "high", "low", "close", "volume"}.issubset(frame.columns):
            f = prepare_daily_features(frame)
            f.attrs["symbol"] = row.set_symbol
            frames[row.set_symbol] = f

    frozen_path = ROOT / "reports/research_phase3_event_outcomes.jsonl"
    frozen = pd.read_json(frozen_path, lines=True)
    frozen5 = frozen[frozen.h == 5]
    frozen_pairs = {h: set(zip(g.symbol.astype(str), g.date.astype(str)))
                    for h, g in frozen5.groupby("hypothesis")}
    frozen_gap_sign = {(str(r.symbol), pd.Timestamp(r.date).date().isoformat()):
                       (1 if float(r.gap_pct) >= 0 else -1)
                       for r in frozen5[frozen5.hypothesis == "S3-C"].itertuples()}
    gap_pairs = frozen_pairs.get("S3-C", set())
    if set(frozen_gap_sign) != gap_pairs:
        raise RuntimeError("Frozen S3-C dates do not align to stored gap directions.")
    all_gap_pairs: set[tuple[str, str]] = set()
    for sym, frame in frames.items():
        for gap_i in range(56, len(frame)):
            prior_close = float(frame.close.iloc[gap_i - 1])
            if prior_close <= 0:
                continue
            gap = float(frame.open.iloc[gap_i] / prior_close - 1)
            if abs(gap) >= 0.01:
                all_gap_pairs.add((sym, frame.index[gap_i].date().isoformat()))
    # The frozen H=5 rows define the canonical event cohort. No thresholds are changed.
    benchmark_path = ROOT / "data/official/tradesim/history/benchmark/SET50.csv"
    benchmark = pd.read_csv(benchmark_path)
    benchmark["Date"] = pd.to_datetime(benchmark.Date).dt.normalize()
    bench_close = benchmark.drop_duplicates("Date").set_index("Date").Close.astype(float).sort_index()

    all_results: dict[str, dict[str, list[dict[str, object]]]] = {}
    horizon_curve: dict[str, object] = {}
    p_registry: dict[str, dict[str, float | None]] = {"fee_only": {}, "one_tick_each_side": {}}

    for hid in HYPOTHESES:
        if hid not in frozen_pairs:
            frozen_pairs[hid] = set()
        event_pairs = frozen_pairs[hid]
        # S3-B frozen event dates are kept fixed. The eligible cross-section is reconstructed
        # only to provide its original same-date non-event controls.
        events_by_date: dict[str, set[str]] = {}
        for sym, date in event_pairs:
            events_by_date.setdefault(date, set()).add(sym)
        return_cache: dict[str, dict[tuple[str, str, int], tuple[float, float]]] = {
            "fee_only": {}, "one_tick_each_side": {}}
        event_rows: list[dict[str, object]] = []
        pair_rows: dict[str, list[dict[str, object]]] = {"fee_only": [], "one_tick_each_side": []}

        if hid == "S3-C":
            candidate_pairs = set(event_pairs)
            # Same-symbol/year non-gap control dates are generated from eligible rows.
            years = {(sym, pd.Timestamp(date).year) for sym, date in event_pairs}
            for sym, f in frames.items():
                for year in {y for s, y in years if s == sym}:
                    for i, date in enumerate(f.index):
                        ds = date.date().isoformat()
                        if date.year == year and (sym, ds) not in all_gap_pairs and i >= 55:
                            candidate_pairs.add((sym, ds))
        else:
            candidate_pairs = set(event_pairs)
            event_dates = {date for _, date in event_pairs}
            for sym, f in frames.items():
                for date in event_dates:
                    ts = pd.Timestamp(date)
                    if ts in f.index:
                        i = f.index.get_loc(ts)
                        if i >= 55:
                            candidate_pairs.add((sym, date))

        for sym, ds in sorted(candidate_pairs):
            f = frames.get(sym)
            if f is None:
                continue
            ts = pd.Timestamp(ds)
            if ts not in f.index:
                continue
            i = f.index.get_loc(ts)
            is_event = (sym, ds) in event_pairs
            if hid == "S3-B":
                is_event = sym in events_by_date.get(ds, set())
                # Controls remain PIT-eligible peers at the frozen event date.
            elif hid == "S3-C":
                is_event = (sym, ds) in gap_pairs
            elif i < 55 or event_flag(hid, f, i, gap_pairs) != is_event:
                # Drop any recomputation mismatch rather than silently changing cohort/controls.
                continue
            event_record = None
            if is_event:
                event_record = {"hypothesis": hid, "symbol": sym, "date": ds,
                                "net_path_fee_only": [], "net_path_one_tick": [], "horizons": {}}
                event_rows.append(event_record)
            for cost_name, stress in (("fee_only", False), ("one_tick_each_side", True)):
                ret_by_h: dict[int, tuple[float, float]] = {}
                for h in HORIZONS:
                    result = outcome(f, i, h, hid, stress_tick=stress)
                    if hid == "S3-B":
                        result = subtract_benchmark_return(result, f, i, h, bench_close)
                    if result is not None:
                        ret_by_h[h] = result
                        return_cache[cost_name][(sym, ds, h)] = result
                if event_record:
                    path_key = "net_path_one_tick" if stress else "net_path_fee_only"
                    path = []
                    for h in range(1, 16):
                        path_outcome = outcome(f, i, h, hid, stress_tick=stress)
                        if hid == "S3-B":
                            path_outcome = subtract_benchmark_return(path_outcome, f, i, h, bench_close)
                        if path_outcome is None:
                            path.append(None)
                        elif hid == "S3-C":
                            direction = frozen_gap_sign.get((sym, ds), 1)
                            path.append(align_directional_return(*path_outcome, direction)[1])
                        else:
                            path.append(path_outcome[1])
                    event_record[path_key] = path
                    for h in HORIZONS:
                        event_record["horizons"].setdefault(str(h), {})[cost_name] = {
                            "gross": (align_directional_return(*ret_by_h[h], frozen_gap_sign.get((sym, ds), 1))[0]
                                      if hid == "S3-C" else ret_by_h[h][0]),
                            "net": (align_directional_return(*ret_by_h[h], frozen_gap_sign.get((sym, ds), 1))[1]
                                    if hid == "S3-C" else ret_by_h[h][1])} if h in ret_by_h else None

        cache_by_date: dict[str, dict[tuple[str, int], list[tuple[str, float]]]] = {}
        cache_by_symbol_year: dict[str, dict[tuple[str, int, int], list[tuple[str, float, float]]]] = {}
        for cache_cost in ("fee_only", "one_tick_each_side"):
            cache_by_date[cache_cost] = {}
            cache_by_symbol_year[cache_cost] = {}
            for (csym, cdate, ch), (cgross, cnet) in return_cache[cache_cost].items():
                cache_by_date[cache_cost].setdefault((cdate, ch), []).append((csym, cnet))
                if (csym, cdate) not in all_gap_pairs:
                    cache_by_symbol_year[cache_cost].setdefault(
                        (csym, pd.Timestamp(cdate).year, ch), []).append((cdate, cgross, cnet))

        # Assemble horizon statistics and matched effects using per-event matched controls.
        hyp_summary: dict[str, object] = {"canonical_frozen_h5_event_count": len(event_pairs),
            "events_with_any_horizon": len(event_rows), "unique_symbols": len({r["symbol"] for r in event_rows}),
            "unique_dates": len({r["date"] for r in event_rows}), "horizons": {}}
        for h in HORIZONS:
            h_summary: dict[str, object] = {"sessions": h, "cost_scenarios": {}}
            for cost_name, stress in (("fee_only", False), ("one_tick_each_side", True)):
                event_values: list[float] = []
                gross_values: list[float] = []
                dates: list[str] = []
                symbols: list[str] = []
                diffs: list[float] = []
                diff_dates: list[str] = []
                diff_symbols: list[str] = []
                controls_used = 0
                for r in event_rows:
                    outcome_row = r["horizons"].get(str(h), {}).get(cost_name)
                    if outcome_row is None:
                        continue
                    net = float(outcome_row["net"])
                    gross_values.append(float(outcome_row["gross"]))
                    event_values.append(net)
                    dates.append(str(r["date"])); symbols.append(str(r["symbol"]))
                    ds, sym = str(r["date"]), str(r["symbol"])
                    controls: list[float] = []
                    if hid == "S3-C":
                        candidates = cache_by_symbol_year[cost_name].get(
                            (sym, pd.Timestamp(ds).year, h), [])
                        direction = frozen_gap_sign.get((sym, ds), 1)
                        controls = [align_directional_return(gross, net, direction)[1]
                                    for _, gross, net in candidates]
                    else:
                        for csym, cnet in cache_by_date[cost_name].get((ds, h), []):
                            if csym in events_by_date.get(ds, set()):
                                continue
                            controls.append(cnet)
                    if controls:
                        controls_used += len(controls)
                        diffs.append(net - float(np.mean(controls)))
                        diff_dates.append(ds); diff_symbols.append(sym)
                event_boot = cluster_bootstrap(event_values, dates, symbols, seed=SEED + h)
                uplift_boot = cluster_bootstrap(diffs, diff_dates, diff_symbols, seed=SEED + h + 100)
                p_registry[cost_name][f"{hid}_H{h}"] = uplift_boot.get("p_two_sided_centered")
                arr = np.asarray(event_values, dtype=float)
                gross_arr = np.asarray(gross_values, dtype=float)
                h_summary["cost_scenarios"][cost_name] = {
                    "n_observed": len(arr), "matched_n": len(diffs),
                    "symbols": len(set(symbols)), "event_dates": len(set(dates)),
                    "effective_date_clusters_kish": kish_effective_clusters(dates),
                    "effective_symbol_clusters_kish": kish_effective_clusters(symbols),
                    "gross_mean": float(gross_arr.mean()) if len(arr) else None,
                    "net_mean": float(arr.mean()) if len(arr) else None,
                    "net_median": float(np.median(arr)) if len(arr) else None,
                    "net_quantiles_p10_p25_p50_p75_p90": [float(v) for v in np.quantile(arr, [.1,.25,.5,.75,.9])] if len(arr) else None,
                    "net_std": float(arr.std(ddof=1)) if len(arr) > 1 else None,
                    "fraction_positive_net": float((arr > 0).mean()) if len(arr) else None,
                    "net_mean_ci95_two_way_cluster": event_boot.get("ci95"),
                    "matched_control_mean_uplift": uplift_boot.get("mean"),
                    "matched_control_uplift_ci95_two_way_cluster": uplift_boot.get("ci95"),
                    "matched_control_uplift_p_unadjusted": uplift_boot.get("p_two_sided_centered"),
                    "control_observations_used": controls_used,
                    "adjustment": "none yet; Holm will be applied across all 32 horizons per cost scenario",
                }
            hyp_summary["horizons"][str(h)] = h_summary
        all_results[hid] = {"events": event_rows, "summary": hyp_summary}
        horizon_curve[hid] = hyp_summary

    adjusted = {cost: holm_adjust(values) for cost, values in p_registry.items()}
    for hid in HYPOTHESES:
        for h in HORIZONS:
            for cost in ("fee_only", "one_tick_each_side"):
                stats = horizon_curve[hid]["horizons"][str(h)]["cost_scenarios"][cost]
                key = f"{hid}_H{h}"
                stats["matched_control_uplift_p_holm_32_tests"] = adjusted[cost].get(key)

    # First-passage curves use close-marked net returns only. Intraday order is unavailable.
    objectives = (0.01, 0.02)
    adverse = (-0.01, -0.02)
    passage: dict[str, object] = {"definition": "first eligible daily close at which a hypothetical round-trip net return crosses the threshold",
        "thresholds_net_return": {}, "by_hypothesis": {}, "event_paths": {}}
    for hid in HYPOTHESES:
        evs = all_results[hid]["events"]
        passage["by_hypothesis"][hid] = {}
        passage["event_paths"][hid] = [{"symbol": r["symbol"], "event_date": r["date"],
            "net_close_return_by_session_fee_only": r["net_path_fee_only"],
            "net_close_return_by_session_one_tick": r["net_path_one_tick"]} for r in evs]
        for cost in ("fee_only", "one_tick_each_side"):
            path_key = "net_path_one_tick" if cost == "one_tick_each_side" else "net_path_fee_only"
            rows = [{"net_path": r[path_key], "date": r["date"], "symbol": r["symbol"]} for r in evs]
            for threshold in (*objectives, *adverse, 0.0):
                key = f"{cost}:{threshold:+.1%}"
                competing = -0.01 if threshold >= 0 else 0.01
                passage["by_hypothesis"][hid][key] = passage_counts(
                    rows, threshold, HORIZONS, competing_threshold=competing,
                    replications=2_000, seed=SEED + HYPOTHESES.index(hid) * 1_000
                    + int(abs(threshold) * 10_000) + (100 if cost == "one_tick_each_side" else 0))
    passage["thresholds_net_return"] = {"positive_objectives": list(objectives),
        "adverse_boundaries": list(adverse), "first_positive": 0.0,
        "selection_note": "predeclared descriptive levels, not fitted to maximize outcomes"}

    metadata = {"schema_version": 1, "experiment_id": "PHASE4_HOLDING_DISTRIBUTION_REUSED_PHASE3_20261031",
        "run_timestamp_utc": datetime.now(timezone.utc).isoformat(), "classification": "EXPLORATORY_REUSED_HISTORY_NOT_CONFIRMATORY",
        "frozen_phase3_event_source": "reports/research_phase3_event_outcomes.jsonl", "canonical_event_rule": "unique hypothesis/symbol/date rows present at H=5; Phase 3 final event cohort",
        "horizons_trading_sessions": list(HORIZONS), "session_counting": "entry session is H=1; observed eligible rows, no calendar-day arithmetic",
        "entry_exit": {"S3-A/S3-D": "signal at close t; hypothetical adjusted next-session open entry; close at t+H; H=1 exits entry-session close",
                       "S3-B": "signal at close t; next-session open entry; close at t+H; H=1 exits next-session close; outcome subtracts official TradeSim-history SET50 price-index close-to-close return from t through t+H",
                       "S3-C": "gap observed after open; hypothetical entry at gap-session close (not an open fill); close H observed sessions later"},
        "source": "approved PIT daily stock rows only; no Settrade/TradeSim stock OHLCV blended; official TradeSim price-index series used as S3-B relative-return baseline",
        "source_hashes": {"phase3_event_outcomes": sha(frozen_path), "approved_manifest": sha(ROOT / "data/processed/approved_market_data_manifest.csv"),
                          "constituents": sha(ROOT / "data/processed/constituents/historical_set50.csv"),
                          "benchmark": sha(benchmark_path), "phase3_preregistration": sha(ROOT / "docs/RESEARCH_PHASE3_PRE_REGISTRATION_FINAL.md"),
                          "hypothesis_config": sha(ROOT / "config/research_phase3_hypotheses_final.json"),
                          "phase4_direction_lock": sha(ROOT / "config/phase4_research_direction_lock.json")},
        "costs": {"commission_rate": 0.00157, "vat_rate_on_commission": 0.07, "two_sided_fee_rate": ROUND_TRIP_FEE,
                  "one_tick_each_side": "adverse one SET tick at raw entry and exit, using scripts/run_design_a_backtest.py tick schedule; OHLC proxy only, not a fill model",
                  "returns_are": "daily-bar adjusted-price estimates; no BBO, queue, executable volume, or IOC fill probabilities"},
        "controls": {"S3-A/S3-B/S3-D": "same-date PIT-eligible non-event securities; exact frozen events retained",
                     "S3-C": "same symbol and calendar year, eligible non-gap observations; control returns direction-aligned to event gap"},
        "uncertainty": "10,000 two-way date/symbol pigeonhole bootstrap; seed=20261101 plus horizon/cost offsets; small symbol-cluster count limits reliability; Holm across 32 horizon tests within each cost scenario",
        "reuse_and_oos": "Every source observation used here has been inspected in prior research; no independent OOS. Chronological slices and horizon reanalysis do not create new confirmation.",
        "promotion": "No Phase 3 rejection is reopened; this distribution cannot pass G1 or promote a signal.",
        "promotion_status": "NO_SIGNAL_PASSED_PROMOTION_GATE",
        "candidate_shortlist_for_human_review": [],
        "new_data_purchases_thb": 0,
        "real_orders_placed": 0,
        "horizon_curve": horizon_curve}
    out_path = ROOT / "reports/research_holding_horizon_curve.json"
    out_path.write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    passage_path = ROOT / "reports/research_time_to_outcome_distribution.json"
    passage["metadata"] = {k: metadata[k] for k in ("experiment_id", "classification", "horizons_trading_sessions", "entry_exit", "costs", "source_hashes", "reuse_and_oos")}
    passage_path.write_text(json.dumps(passage, indent=2, allow_nan=False), encoding="utf-8")
    print(json.dumps({hid: {h: {c: {k: v for k, v in d.items() if k in ("n_observed", "matched_n", "net_mean", "matched_control_mean_uplift", "matched_control_uplift_ci95_two_way_cluster", "matched_control_uplift_p_holm_32_tests")}
        for c, d in row["cost_scenarios"].items()} for h, row in hyp["horizons"].items()} for hid, hyp in horizon_curve.items()}, indent=2))


if __name__ == "__main__":
    main()

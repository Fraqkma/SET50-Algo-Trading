"""Run the frozen Phase 3 daily-bar event screen; diagnostic only."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.eligibility import MarketDataEligibilityGate
from src.data.research import load_approved_market_data


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    gate = MarketDataEligibilityGate(ROOT)
    manifest = pd.read_csv(ROOT / "data/processed/approved_market_data_manifest.csv")
    frames: dict[str, pd.DataFrame] = {}
    for row in manifest.itertuples(index=False):
        if str(row.approval_status).startswith("APPROVED"):
            try:
                frame = load_approved_market_data(row.set_symbol, gate=gate)
            except (ValueError, FileNotFoundError):
                continue
            if len(frame) >= 55:
                frames[row.set_symbol] = frame

    events: list[dict] = []
    controls: list[dict] = []
    for symbol, frame in frames.items():
        raw_close = pd.to_numeric(frame["close"], errors="coerce")
        close = pd.to_numeric(frame["adjusted_close"], errors="coerce") if "adjusted_close" in frame else raw_close
        adjustment = close / raw_close
        high = pd.to_numeric(frame["high"], errors="coerce") * adjustment
        low = pd.to_numeric(frame["low"], errors="coerce") * adjustment
        open_ = pd.to_numeric(frame["open"], errors="coerce") * adjustment
        raw_open = pd.to_numeric(frame["open"], errors="coerce")
        volume = pd.to_numeric(frame["volume"], errors="coerce")
        tr = pd.concat([high - low, (high - close.shift()).abs(), (low - close.shift()).abs()], axis=1).max(axis=1)
        atr10 = tr.rolling(10, min_periods=10).mean() / close
        prior20_atr = atr10.shift(10).rolling(20, min_periods=20).mean()
        prior_high = high.shift().rolling(20, min_periods=20).max()
        prior_volume = volume.shift().rolling(20, min_periods=20).mean()
        ret = close.pct_change()
        for i in range(len(frame)):
            day = frame.index[i]
            if i < 55 or i + 6 >= len(frame):
                continue
            if not gate.assess(symbol, day.date()).eligible:
                continue
            common = {
                "symbol": symbol, "signal_date": day.date().isoformat(),
                "signal_timestamp": day.isoformat() + "T16:00:00+07:00",
                "entry_date": frame.index[i + 1].date().isoformat(),
                "source": "approved_market_data_manifest.csv / approved raw daily CSV",
                "entry_reference": "next observed session open reference; hypothetical only, not an executable fill",
            }
            forward = {h: float(close.iloc[i + h] / open_.iloc[i + 1] - 1) for h in (1, 3, 5)}
            vol_ratio = volume.iloc[i] / prior_volume.iloc[i] if prior_volume.iloc[i] and pd.notna(prior_volume.iloc[i]) else np.nan
            conditions = {
                "S3-A": bool(atr10.iloc[i] <= 0.8 * prior20_atr.iloc[i] and close.iloc[i] > prior_high.iloc[i] and vol_ratio >= 1.5) if pd.notna(prior20_atr.iloc[i]) and pd.notna(prior_high.iloc[i]) and pd.notna(vol_ratio) else False,
                "S3-D": bool(vol_ratio >= 2.0 and ret.iloc[i] > 0.005) if pd.notna(vol_ratio) else False,
            }
            for hid, active in conditions.items():
                if active:
                    events.append({**common, "hypothesis_id": hid, "forward_return": forward})
                else:
                    controls.append({**common, "hypothesis_id": hid, "forward_return": forward})
            # A gap is observable at the next open. Return is direction-aligned from that day's close.
            # Gap classification uses unadjusted OHLC on both sides. Forward
            # return measurement uses consistently dividend-adjusted prices.
            gap = raw_open.iloc[i + 1] / raw_close.iloc[i] - 1 if raw_close.iloc[i] else np.nan
            if pd.notna(gap) and abs(gap) >= 0.01:
                aligned = {h: float(np.sign(gap) * (close.iloc[i + 1 + h] / close.iloc[i + 1] - 1)) for h in (1, 3, 5)}
                events.append({**common, "hypothesis_id": "S3-C", "signal_timestamp": frame.index[i + 1].date().isoformat() + "T09:45:00+07:00", "gap_pct": float(gap), "forward_return": aligned})
            else:
                controls.append({**common, "hypothesis_id": "S3-C", "forward_return": forward})

    event_df = pd.DataFrame(events)
    control_df = pd.DataFrame(controls)
    summaries = {}
    for hid in ("S3-A", "S3-B", "S3-C", "S3-D"):
        e = event_df[event_df.hypothesis_id == hid] if not event_df.empty else pd.DataFrame()
        c = control_df[control_df.hypothesis_id == hid] if not control_df.empty else pd.DataFrame()
        by_horizon = {}
        for h in (1, 3, 5):
            ev = [x[h] for x in e.forward_return] if len(e) else []
            # Same-date eligible non-event symbols; for gap events, orient the
            # control by the event's gap direction before calculating uplift.
            control_by_date = {}
            for date_key, rows in c.groupby("signal_date") if len(c) else []:
                control_by_date[date_key] = [x[h] for x in rows.forward_return]
            paired = []
            for row in e.itertuples() if len(e) else []:
                values = control_by_date.get(row.signal_date, [])
                if values:
                    orient = float(np.sign(row.gap_pct)) if hid == "S3-C" else 1.0
                    paired.append((row, float(np.mean(values)) * orient))
            ev = [x.forward_return[h] for x, _ in paired]
            cv = [v for _, v in paired]
            diffs = np.asarray(ev, dtype=float) - np.asarray(cv, dtype=float)
            ci = None
            p_boot = None
            if len(diffs) >= 30 and e.signal_date.nunique() >= 20 and e.symbol.nunique() >= 10:
                rng = np.random.default_rng(20261030)
                row_dates = np.asarray([x.signal_date for x, _ in paired])
                row_symbols = np.asarray([x.symbol for x, _ in paired])
                unique_dates, date_idx = np.unique(row_dates, return_inverse=True)
                unique_symbols, symbol_idx = np.unique(row_symbols, return_inverse=True)
                boot = np.empty(10000)
                for b in range(len(boot)):
                    date_counts = np.bincount(rng.integers(0, len(unique_dates), len(unique_dates)), minlength=len(unique_dates))
                    symbol_counts = np.bincount(rng.integers(0, len(unique_symbols), len(unique_symbols)), minlength=len(unique_symbols))
                    weights = date_counts[date_idx] * symbol_counts[symbol_idx]
                    boot[b] = np.average(diffs, weights=weights) if weights.sum() else np.nan
                boot = boot[np.isfinite(boot)]
                if len(boot):
                    ci = [float(x) for x in np.quantile(boot, [.025, .975])]
                    p_boot = float((np.sum(np.abs(boot - np.mean(boot)) >= abs(np.mean(diffs))) + 1) / (len(boot) + 1))
            by_horizon[str(h)] = {
                "event_n": len(ev), "event_mean": float(np.mean(ev)) if ev else None,
                "event_median": float(np.median(ev)) if ev else None,
                "event_hit_rate": float(np.mean(np.array(ev) > 0)) if ev else None,
                "control_n": len(cv), "control_mean": float(np.mean(cv)) if cv else None,
                "mean_uplift": float(np.mean(diffs)) if len(diffs) else None,
                "two_way_cluster_bootstrap_95pct_ci": ci, "bootstrap_p_two_sided_centered": p_boot,
                "event_q10_q90": [float(np.quantile(ev, .1)), float(np.quantile(ev, .9))] if ev else None,
            }
        symbols = e.symbol.nunique() if len(e) else 0
        dates = e.signal_date.nunique() if len(e) else 0
        symbol_effective = float(1 / np.square(e.symbol.value_counts(normalize=True)).sum()) if len(e) else 0.0
        date_effective = float(1 / np.square(e.signal_date.value_counts(normalize=True)).sum()) if len(e) else 0.0
        overlap_events = 0
        if len(e):
            for _, symbol_events in e.assign(_date=pd.to_datetime(e.signal_date)).groupby("symbol"):
                ordered_dates = symbol_events["_date"].sort_values().tolist()
                overlap_events += sum((current - previous).days <= 7 for previous, current in zip(ordered_dates, ordered_dates[1:]))
        adequacy = len(e) >= 30 and symbols >= 10 and dates >= 20
        status = "POSTPONED_INADEQUATE_SAMPLE" if not adequacy else "STAGE_B_REJECTED_REUSED_HISTORY"
        if hid == "S3-B":
            status = "POSTPONED_OFFICIAL_BENCHMARK_SERIES_UNAVAILABLE"
        summaries[hid] = {"status": status, "event_count": len(e), "unique_symbols": int(symbols), "unique_dates": int(dates),
                          "unique_symbol_date_pairs": int(e[["symbol", "signal_date"]].drop_duplicates().shape[0]) if len(e) else 0,
                          "effective_symbol_clusters_kish": symbol_effective, "effective_date_clusters_kish": date_effective,
                          "conservative_independent_cluster_proxy": min(symbol_effective, date_effective) if len(e) else 0.0,
                          "adjacent_events_within_7_calendar_days_same_symbol": int(overlap_events),
                          "control_count": len(c), "same_symbol_date_overlap": 0, "horizons": by_horizon}

    calculable = [(hid, values["horizons"]["5"]["bootstrap_p_two_sided_centered"])
                  for hid, values in summaries.items()
                  if values["horizons"]["5"]["bootstrap_p_two_sided_centered"] is not None]
    ordered = sorted(calculable, key=lambda item: item[1])
    running = 0.0
    adjusted = {}
    for rank, (hid, p_value) in enumerate(ordered):
        running = max(running, min(1.0, p_value * (len(ordered) - rank)))
        adjusted[hid] = running
    for hid, p_adjusted in adjusted.items():
        summaries[hid]["horizons"]["5"]["holm_adjusted_p"] = p_adjusted
    raw_paths = sorted(set(gate.approved_raw_file(s) for s in frames))
    payload = {
        "schema_version": 1, "engine": "RESEARCH_DIAGNOSTIC", "pre_registration": "docs/RESEARCH_PHASE3_PRE_REGISTRATION.md",
        "git_head": "0eb89f3272e1ab17cb4f9fa1a76316ebebb0b76a", "dirty_before_run": True,
        "sample_window": {"start": min(str(f.index.min().date()) for f in frames.values()), "end": max(str(f.index.max().date()) for f in frames.values())},
        "data_policy": "approved PIT daily data only; partial universe; not independent OOS; October collection inspection means later period not untouched",
        "source_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in [ROOT / "data/processed/approved_market_data_manifest.csv", ROOT / "data/processed/constituents/historical_set50.csv", *raw_paths]},
        "code_hashes": {str(p.relative_to(ROOT)): sha256(p) for p in [ROOT / "scripts/run_phase3_signal_screen.py", ROOT / "src/data/research.py", ROOT / "src/data/eligibility.py"]},
        "loaded_symbols": sorted(frames), "summaries": summaries,
        "uncertainty": {"method": "two-way date/symbol pigeonhole bootstrap", "replications": 10000,
                        "seed": 20261030, "multiplicity": "Holm across calculable 5-session primary hypotheses",
                        "holm_adjusted_p_values": adjusted},
        "limitations": ["Prior inspected history reused; no independent OOS claim", "Official benchmark price-index daily source unavailable in approved inputs", "Daily bars do not establish executable fills, spread, depth, queue, or exact signal-time auction semantics", "Matched controls use same-symbol non-event observations and can still carry time/regime confounding", "Holm adjustment is not used for promotion because the historical window is reused and there is no untouched confirmation period"],
        "promotion_summary": "NO_SIGNAL_PASSED_PROMOTION_GATE",
    }
    (ROOT / "reports/phase3_signal_screen_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    event_df.to_json(ROOT / "reports/phase3_signal_events.jsonl", orient="records", lines=True, force_ascii=False)
    control_df.to_json(ROOT / "reports/phase3_signal_controls.jsonl", orient="records", lines=True, force_ascii=False)
    print(json.dumps({k: {"status": v["status"], "n": v["event_count"], "symbols": v["unique_symbols"], "dates": v["unique_dates"]} for k, v in summaries.items()}, indent=2))


if __name__ == "__main__":
    main()

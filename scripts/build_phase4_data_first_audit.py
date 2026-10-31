"""Build versioned, data-first Phase 4 readiness diagnostics.

All outputs are diagnostic and non-promotional. Source archives are read only.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import random
import zipfile
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def dates(start: date, end: date):
    day = start
    while day <= end:
        yield day
        day += timedelta(days=1)


def calendar() -> dict:
    holidays = {"2026-12-31", "2027-01-01"}
    rows, ordinal = [], 0
    for day in dates(date(2026, 12, 16), date(2027, 1, 15)):
        iso = day.isoformat()
        if day.weekday() > 4:
            status, reason, n = "WEEKEND", "Saturday/Sunday", None
        elif iso in holidays:
            status, reason, n = "SET_HOLIDAY", "Listed in official SET annual holiday calendar", None
        else:
            ordinal += 1
            status, reason, n = "EXPECTED_TRADING_DAY", "Weekday not listed as a holiday in current SET annual calendars", ordinal
        rows.append({"date": iso, "status": status, "reason": reason, "trading_day_ordinal": n})
    return {"schema_version": 1, "calendar_id": "KGI_ALGO26_2026-12-16_2027-01-15_v1",
            "verified_as_of": "2026-10-31", "period_start": "2026-12-16", "period_end": "2027-01-15",
            "timezone": "Asia/Bangkok", "trading_day_count": ordinal, "ad_hoc_closures": [],
            "holiday_dates": sorted(holidays), "source_urls": [
                "https://www.set.or.th/en/about/event-calendar/holiday?year=2026",
                "https://www.set.or.th/th/about/event-calendar/holiday?year=2027"],
            "rows": rows,
            "note": "Expected session calendar from published SET annual holidays as of verification date; recheck subsequent ad-hoc closure notices before scoring."}


def pit_matrix() -> dict:
    remediation = read_csv(ROOT / "reports/market_data_remediation.csv")
    manifest = {r["set_symbol"]: r for r in read_csv(ROOT / "data/processed/approved_market_data_manifest.csv")}
    ticker_audit = {r["SET Symbol"]: r for r in read_csv(ROOT / "reports/yahoo_ticker_audit.csv")}
    membership = read_csv(ROOT / "data/processed/constituents/historical_set50.csv")
    periods: dict[str, list[dict]] = {}
    for row in membership:
        periods.setdefault(row["symbol"], []).append({"period": row["period"], "from": row["effective_from"], "to": row["effective_to"], "status": row["mapping_status"]})
    ts_dir = ROOT / "data/official/tradesim/history/daily_history"
    ts_files = {p.stem.upper(): p for p in ts_dir.glob("*.csv")}
    st_path = ROOT / "data/pilot/settrade/production/normalized/bars_1d/data.csv"
    st_rows = read_csv(st_path) if st_path.exists() else []
    st_by: dict[str, list[str]] = {}
    for row in st_rows:
        symbol = row.get("symbol") or row.get("Symbol")
        timestamp = row.get("timestamp") or row.get("datetime") or row.get("Date")
        if symbol and timestamp:
            st_by.setdefault(symbol.upper(), []).append(timestamp[:10])
    tick = ROOT / "Daily_Ticks.zip"
    final_summary = json.loads((ROOT / "reports/research_phase3_summary.json").read_text(encoding="utf-8-sig"))
    phase3_symbols = set(final_summary["data"]["approved_symbols"])
    tick_members = []
    tick_by_symbol: dict[str, dict] = {}
    if tick.exists():
        with zipfile.ZipFile(tick) as archive:
            nested_name = next((n for n in archive.namelist() if "tradeSim_ticks.zip" in n), None)
            if nested_name:
                with zipfile.ZipFile(archive.open(nested_name)) as nested:
                    tick_members = sorted(n for n in nested.namelist() if n.lower().endswith(".csv"))
                    for member in tick_members:
                        with nested.open(member) as stream:
                            reader = csv.DictReader(io.TextIOWrapper(stream, encoding="utf-8-sig", newline=""))
                            for tick_row in reader:
                                symbol = (tick_row.get("ShareCode") or "").strip().upper()
                                if symbol:
                                    entry = tick_by_symbol.setdefault(symbol, {"rows": 0, "session_dates": set()})
                                    entry["rows"] += 1
                                    entry["session_dates"].add(Path(member).stem)
    rows = []
    raw_dates_by_symbol: dict[str, set[str]] = {}
    for r in remediation:
        sym = r["set_symbol"].upper()
        raw = ROOT / r["raw_file"] if r.get("raw_file") else None
        raw_n = None
        raw_first = raw_last = None
        raw_dates: set[str] = set()
        if raw and raw.exists():
            raw_rows = read_csv(raw)
            raw_n = len(raw_rows)
            if raw_rows:
                keys = [k for k in raw_rows[0] if k.lower() in {"date", "datetime", "timestamp"}]
                if keys:
                    vals = sorted(x[keys[0]][:10] for x in raw_rows if x.get(keys[0]))
                    raw_dates = set(vals)
                    raw_first, raw_last = (vals[0], vals[-1]) if vals else (None, None)
        raw_dates_by_symbol[sym] = raw_dates
        ts_file = ts_files.get(sym)
        ts_n = None
        ts_first = ts_last = None
        if ts_file:
            rr = read_csv(ts_file)
            ts_n = len(rr)
            if rr:
                key = next((k for k in rr[0] if k.lower() in {"date", "datetime", "timestamp"}), None)
                vals = sorted(x[key][:10] for x in rr if key and x.get(key))
                ts_first, ts_last = (vals[0], vals[-1]) if vals else (None, None)
        st_dates = sorted(st_by.get(sym, []))
        m = manifest.get(sym)
        reason = r.get("reason", "")
        if r["approval_status"] == "NEEDS_REVIEW":
            blocker = "RAW_OHLC_OR_COVERAGE_FINDING_UNADJUDICATED; no primary-source reconciliation in existing evidence"
        elif r["approval_status"] == "REJECTED":
            blocker = "NO_VALIDATED_PRICE_SOURCE_AND_AMBIGUOUS_OR_RETIRED_SECURITY_IDENTITY"
        elif r["approval_status"] == "APPROVED_WITH_KNOWN_GAP":
            blocker = "ONLY_BOUNDED_POST_TRANSITION_HISTORY_ADMISSIBLE; predecessor period cannot be inferred"
        else:
            blocker = "ADMISSIBLE_ONLY_WITHIN_MANIFEST_DATES_AND_DATE_EFFECTIVE_PIT_MEMBERSHIP"
        per_symbol_interval_coverage = {}
        for p in periods.get(sym, []):
            observed = sorted(d for d in raw_dates if p["from"] <= d <= p["to"])
            approved_observed = sorted(d for d in observed if m and (not m.get("approved_from") or d >= m["approved_from"]) and (not m.get("approved_to") or d <= m["approved_to"]) and m.get("approval_status") in {"APPROVED", "APPROVED_WITH_KNOWN_GAP"})
            per_symbol_interval_coverage[p["period"]] = {"membership_from": p["from"], "membership_to": p["to"], "raw_observation_count": len(observed), "admissible_observation_count": len(approved_observed), "admissible_first": approved_observed[0] if approved_observed else None, "admissible_last": approved_observed[-1] if approved_observed else None}
        rows.append({"symbol": sym, "identity": r.get("yahoo_ticker"), "identity_audit_status": ticker_audit.get(sym, {}).get("Status"), "approval_status": r["approval_status"],
                     "phase3_event_panel_member": sym in phase3_symbols,
                     "phase3_panel_reason": ("Included in frozen final Phase 3 event panel" if sym in phase3_symbols else
                         "Approved and PIT-active from 2026-07-01, but only 48 gate-approved rows through 2026-09-04, below Phase 3's 55-row feature warmup" if sym in {"THAI", "MRDIYT"} else "Not admitted by source remediation/quality gate"),
                     "issue_classification": r.get("issue_classification"), "exclusion_or_scope_reason": reason,
                     "exact_gate_reason": blocker, "manifest": m,
                     "pit_membership_intervals": periods.get(sym, []),
                     "date_effective_data_coverage_by_PIT_interval": per_symbol_interval_coverage,
                     "sources": {
                         "approved_yahoo_panel": {"file": r.get("raw_file"), "rows": raw_n, "first_date": raw_first, "last_date": raw_last, "adjustment": "vendor adjusted fields present; source-specific", "eligible": bool(m)},
                         "official_tradesim_daily": {"file": str(ts_file.relative_to(ROOT)) if ts_file else None, "rows": ts_n, "first_date": ts_first, "last_date": ts_last, "eligible_as_distinct_research_panel": bool(ts_file), "pit_status": "membership intervals available separately; exact exchange-security identity and action mapping still require cross-check" if ts_file else "no local daily file"},
                         "settrade_production_daily": {"rows": len(st_dates), "first_date": st_dates[0] if st_dates else None, "last_date": st_dates[-1] if st_dates else None, "eligible_for_historical_PIT": False, "reason": "production observations are current-universe history and do not prove past membership or back-adjustment"},
                         "organizer_tick_archive": {"archive": "Daily_Ticks.zip", "archive_sha256": sha(tick) if tick.exists() else None, "daily_file_count": len(tick_members), "rows": tick_by_symbol.get(sym, {}).get("rows", 0), "observed_session_dates": sorted(tick_by_symbol.get(sym, {}).get("session_dates", set())), "eligible_for_historical_daily_panel": False, "reason": "short execution/tick window and separate provenance; not a substitute for historical daily PIT coverage"}},
                     "safe_resolution_with_existing_data": "NO" if r["approval_status"] in {"NEEDS_REVIEW", "REJECTED"} else "YES_WITHIN_EXPLICIT_MANIFEST_BOUNDARY"})
    counts = Counter(r["approval_status"] for r in remediation)
    by_period = {}
    for period in sorted({p["period"] for ps in periods.values() for p in ps}):
        period_symbols = {sym for sym, ps in periods.items() if any(p["period"] == period for p in ps)}
        period_members = {sym: next(p for p in periods[sym] if p["period"] == period) for sym in period_symbols}
        period_rows = {r["set_symbol"]: r for r in remediation if r["set_symbol"] in period_symbols}
        source_observed = {sym for sym, p in period_members.items() if any(p["from"] <= d <= p["to"] for d in raw_dates_by_symbol.get(sym, set()))}
        identity_verified = {sym for sym in source_observed if ticker_audit.get(sym, {}).get("Status") == "VERIFIED"}
        admissible = {sym for sym in identity_verified if period_rows[sym]["approval_status"] in {"APPROVED", "APPROVED_WITH_KNOWN_GAP"} and any(
            period_members[sym]["from"] <= d <= period_members[sym]["to"] and
            (not manifest.get(sym, {}).get("approved_from") or d >= manifest[sym]["approved_from"]) and
            (not manifest.get(sym, {}).get("approved_to") or d <= manifest[sym]["approved_to"])
            for d in raw_dates_by_symbol.get(sym, set()))}
        by_period[period] = {"pit_member_count": len(period_symbols),
            "raw_observation_in_PIT_interval_count": len(source_observed), "identity_audit_verified_with_observation_count": len(identity_verified),
            "admissible_quality_approved_observation_count": len(admissible),
            "admissible_full_status_approved_count": sum(period_rows[s]["approval_status"] == "APPROVED" for s in admissible),
            "admissible_bounded_gap_approved_count": sum(period_rows[s]["approval_status"] == "APPROVED_WITH_KNOWN_GAP" for s in admissible),
            "needs_review_with_observation_count": sum(period_rows[s]["approval_status"] == "NEEDS_REVIEW" for s in source_observed),
            "rejected_with_observation_count": sum(period_rows[s]["approval_status"] == "REJECTED" for s in source_observed)}
    return {"schema_version": 1, "as_of": "2026-10-31", "source_file": "reports/market_data_remediation.csv",
            "membership_intervals_file": "data/processed/constituents/historical_set50.csv",
            "corporate_action_identity_cases": [
                {"identities": ["TRUEE", "DTAC", "TRUE"], "issue": "pre-amalgamation names and new TRUE are separate security identities; no splicing", "evidence": "reports/pilot/historical_source_audit.md"},
                {"identities": ["GULF", "INTUCH", "GULFI"], "issue": "GULF/INTUCH pre-transaction histories remain separate; GULF post-transaction series starts at its approved boundary; no INTUCH-to-GULF backfill", "evidence": "reports/pilot/historical_source_audit.md; reports/market_data_remediation.csv"},
                {"identities": ["SCBB", "SCBX/SCB"], "issue": "legacy SCBB and successor SCBX/SCB periods require separate issuer mapping", "evidence": "reports/pilot/historical_source_audit.md"},
                {"identities": ["BANPUU", "BANPU"], "issue": "temporary BANPUU and new BANPU are separate; raw Yahoo BANPU has unresolved gap/anomaly and known suspension", "evidence": "reports/pilot/historical_source_audit.md; reports/market_data_remediation.csv"},
                {"identities": ["NTL", "TIDLOR"], "issue": "legacy NTL and TIDLOR Holdings are separate; TIDLOR only admitted from evidenced start", "evidence": "reports/pilot/historical_source_audit.md; reports/market_data_remediation.csv"}],
            "pipeline_counts": {"possible_candidates": len(rows), "available_raw_yahoo": sum(bool(r["sources"]["approved_yahoo_panel"]["file"]) for r in rows),
                "pit_mapped_candidates": sum(bool(r["pit_membership_intervals"]) for r in rows), "identity_verified_and_quality_approved_records": counts["APPROVED"] + counts["APPROVED_WITH_KNOWN_GAP"],
                "approved_rows": counts["APPROVED"], "approved_bounded_gap_rows": counts["APPROVED_WITH_KNOWN_GAP"], "needs_review": counts["NEEDS_REVIEW"], "rejected": counts["REJECTED"],
                "phase3_event_panel_symbols": len(phase3_symbols), "approved_status_rows": counts["APPROVED"],
                "approved_status_rows_overlapping_sample": sum(r["phase3_event_panel_member"] for r in rows if r["approval_status"] == "APPROVED"),
                "approved_status_rows_not_overlapping_sample": sum(r["approval_status"] == "APPROVED" and not r["phase3_event_panel_member"] for r in rows)},
            "counts_by_membership_interval": by_period,
            "admissible_panels": {"phase3_yahoo_pit_panel": 18, "approved_manifest_records": 20,
                "bounded_gap_additions": ["GULF from 2025-04-03", "TIDLOR from 2025-05-16"],
                "phase4_expanded_pit_candidate_panel": {"symbol_count": counts["APPROVED"] + counts["APPROVED_WITH_KNOWN_GAP"], "safe_for": "separate, non-promotional PIT random-basket feasibility baselines", "not_authorized_for": "relabeling prior Phase 3 tests as OOS or circumventing Phase 3's 55-row feature warmup", "additional_phase4_baseline_symbols": ["THAI", "MRDIYT"]},
                "official_tradesim_history": {"file_count": len(ts_files), "symbols": sorted(ts_files), "date_range": "2023-09-21 through 2026-10-21", "status": "distinct provenance candidate panel; exact instrument/action/adjustment compatibility has not been independently verified; not pooled or used to expand approved Yahoo PIT panel"},
                "settrade_production": "separate current-universe panel only; not PIT admissible for historic membership research",
                "organizer_ticks": "execution diagnostic only over archive date range; no PIT daily expansion"}, "symbols": rows}


def baseline_report(panel_id: str = "expanded_20") -> dict:
    # Random entry-date baskets from a source-approved panel, bounded by PIT and manifest dates.
    approved = read_csv(ROOT / "data/processed/approved_market_data_manifest.csv")
    approved_by_symbol = {r["set_symbol"]: r for r in approved}
    p3 = json.loads((ROOT / "reports/research_phase3_summary.json").read_text(encoding="utf-8-sig"))
    panel_symbols = (sorted(p3["data"]["approved_symbols"]) if panel_id == "phase3_18" else
                     sorted(r["set_symbol"] for r in approved if r["approval_status"] in {"APPROVED", "APPROVED_WITH_KNOWN_GAP"}))
    memberships = read_csv(ROOT / "data/processed/constituents/historical_set50.csv")
    intervals: dict[str, list[tuple[str, str]]] = {}
    for row in memberships:
        intervals.setdefault(row["symbol"], []).append((row["effective_from"], row["effective_to"]))
    series = {}
    for sym in panel_symbols:
        r = approved_by_symbol.get(sym)
        if not r or r["approval_status"] not in {"APPROVED", "APPROVED_WITH_KNOWN_GAP"}:
            continue
        path = ROOT / r["raw_file"]
        if not path.exists():
            continue
        data = read_csv(path)
        by_date = {}
        for item in data:
            d = next((item[k] for k in item if k.lower() in {"date", "datetime", "timestamp"}), None)
            c = next((item[k] for k in item if k.lower() in {"adj close", "adj_close", "adjusted close", "close"}), None)
            if d and c and r["approved_from"] <= d[:10] <= r["approved_to"]:
                try:
                    value = float(c)
                    if value > 0: by_date[d[:10]] = value
                except ValueError: pass
        series[sym] = by_date
    symbols = sorted(series)
    master_dates = sorted(set.union(*(set(series[s]) for s in symbols))) if symbols else []
    # Summarize fixed rolling 21 observation buy-and-hold windows, buy and liquidate with fees on both sides.
    fee = 0.0016799
    rng = random.Random(20261031)
    benchmark_path = ROOT / "data/official/tradesim/history/benchmark/SET50.csv"
    bench_rows = read_csv(benchmark_path)
    bench = {}
    for row in bench_rows:
        d = next((row[k] for k in row if k.lower() in {"date", "datetime", "timestamp"}), None)
        c = next((row[k] for k in row if k.lower() == "close"), None)
        if d and c:
            try: bench[d[:10]] = float(c)
            except ValueError: pass
    samples = {}
    for n in (3, 5, 8):
        selected_returns, mdds, net_returns, excess_returns, payoff_values, win_rates, profitable_counts = [], [], [], [], [], [], []
        drawdown_compares = []
        eligible_starts = censored = 0
        for start in range(max(0, len(master_dates) - 21)):
            window = master_dates[start:start + 22]
            if len(window) != 22: continue
            start_date = window[0]
            # Membership selection uses only effective PIT membership on the entry date.
            candidates = [s for s in symbols if any(a <= start_date <= b for a, b in intervals.get(s, [])) and start_date in series[s]]
            if len(candidates) < n: continue
            eligible_starts += 1
            basket = rng.sample(candidates, n)
            if any(any(day not in series[s] for day in window) for s in basket):
                censored += 1
                continue
            daily = [sum(series[s][d1] / series[s][d0] - 1 for s in basket) / len(basket) for d0, d1 in zip(window, window[1:])]
            nav = [1.0]
            for ret in daily: nav.append(nav[-1] * (1 + ret))
            gross = nav[-1] - 1
            net = (1 + gross) * (1 - fee) ** 2 - 1
            lot_net_returns = [(series[s][window[-1]] / series[s][window[0]]) * (1 - fee) ** 2 - 1 for s in basket]
            wins = [x for x in lot_net_returns if x > 0]
            losses = [x for x in lot_net_returns if x < 0]
            counted = len(wins) + len(losses)
            win_rate = len(wins) / counted if counted else 0.0
            payoff = win_rate * (sum(wins) / len(wins) if wins else 0.0) - (1 - win_rate) * (abs(sum(losses) / len(losses)) if losses else 0.0)
            payoff_values.append(payoff)
            win_rates.append(win_rate)
            profitable_counts.append(len(wins))
            benchmark_return = (bench[window[-1]] / bench[window[0]] - 1) if window[0] in bench and window[-1] in bench else None
            if benchmark_return is not None:
                excess_returns.append(net - benchmark_return)
            peak, mdd = nav[0], 0.0
            for x in nav:
                peak = max(peak, x)
                mdd = max(mdd, (peak - x) / peak)
            selected_returns.append(gross); net_returns.append(net); mdds.append(mdd)
            if all(day in bench for day in window):
                bnav = [bench[window[0]]]
                for day in window[1:]: bnav.append(bench[day])
                bpeak, bmdd = bnav[0], 0.0
                for value in bnav:
                    bpeak = max(bpeak, value)
                    if bpeak > 0: bmdd = max(bmdd, (bpeak - value) / bpeak)
                drawdown_compares.append({"pass": mdd < 1.5 * bmdd, "portfolio_mdd": mdd, "benchmark_mdd": bmdd})
        def quantile(values, p):
            if not values: return None
            ordered = sorted(values); idx = round((len(ordered) - 1) * p)
            return ordered[idx]
        samples[str(n)] = {"window_count": len(net_returns), "eligible_entry_windows": eligible_starts, "censored_for_missing_endpoint_prices": censored, "metric_scope": "overlapping 21-session retrospective entry-date random baskets; holdings selected only from PIT members on entry date; not OOS",
            "random_basket_seed": 20261031, "gross_return_median": quantile(selected_returns, .5), "net_return_median_after_two_side_fees": quantile(net_returns, .5),
            "net_return_q10_q90": [quantile(net_returns,.1), quantile(net_returns,.9)], "max_drawdown_median": quantile(mdds,.5),
            "excess_vs_official_tradesim_history_price_series_median": quantile(excess_returns,.5),
            "expected_payoff_median_return_per_completed_lot_after_two_side_fees": quantile(payoff_values,.5),
            "win_rate_median_excluding_zero_pnl_lots": quantile(win_rates,.5), "profitable_roundtrips_median_per_window": quantile(profitable_counts,.5),
            "benchmark_drawdown_comparison": {"matched_windows": len(drawdown_compares), "strict_1_5x_scenario_pass_fraction": (sum(x["pass"] for x in drawdown_compares) / len(drawdown_compares)) if drawdown_compares else None, "median_portfolio_mdd": quantile([x["portfolio_mdd"] for x in drawdown_compares], .5), "median_benchmark_mdd": quantile([x["benchmark_mdd"] for x in drawdown_compares], .5)},
            "eod_exposure_scenario": 1.0, "hypothetical_fifo_roundtrips_if_all_fills_occur": n,
            "execution_model": "daily adjusted-close mark-to-market; proportional stated commission+VAT charged at entry and exit; no slippage/fill claims; hypothetical roundtrips assume terminal liquidation and are not fill evidence"}
    return {"schema_version": 1, "classification": "NON-PROMOTIONAL_DIAGNOSTIC_ONLY", "panel_id": panel_id, "source": "approved_market_data_manifest.csv; raw Yahoo-adjusted close field where present",
        "source_hashes": {"manifest": sha(ROOT / "data/processed/approved_market_data_manifest.csv")},
        "dates": {"first_available": master_dates[0] if master_dates else None, "last_available": master_dates[-1] if master_dates else None, "date_count": len(master_dates), "official_approved_to_cap": "2026-09-04"},
        "symbols": symbols, "cash_only": {"net_return": 0.0, "eod_exposure": 0.0, "roundtrips": 0, "common_criteria": "fails exposure, roundtrips, and expected-payoff evidence by construction"},
        "equal_weight_buy_hold_scenarios": samples,
        "21_session_mechanics": {"average_eod_exposure_requirement": 0.5, "five_fifo_roundtrips": "order-count is mechanically schedulable in 21 sessions with 1-5 session lots if five actual buy/sell pairs fill; OHLC data cannot establish such fills or positive payoff", "known_completed_roundtrips_in_baseline": 0},
        "benchmark_reference": {"file": "data/official/tradesim/history/benchmark/SET50.csv", "sha256": sha(benchmark_path), "observations": len(bench), "first_date": min(bench) if bench else None, "last_date": max(bench) if bench else None, "quality": "unique date-only rows with positive closes; no intraday timestamp, source-revision metadata or scoring-feed identity embedded in this CSV", "type": "TradeSim-history SET50 daily index series; evidence supports use as a regime/benchmark research proxy only, exact organizer-scored feed/revision policy unconfirmed"},
        "limitations": ["Overlapping windows are not independent observations.", "This is a retrospective feasibility baseline, not a signal study or promotion candidate.", "Random baskets use only membership known for the entry date; outcome windows with missing future prices are censored and counted.", "No authentic tick/IOC execution, liquidity constraint, or slippage calibration is represented.", "The exact organizer scoring benchmark remains unconfirmed."]}


def phase3_reconciliation() -> dict:
    first_path = ROOT / "reports/phase3_signal_screen_summary.json"
    final_path = ROOT / "reports/research_phase3_summary.json"
    first = json.loads(first_path.read_text(encoding="utf-8-sig"))
    final = json.loads(final_path.read_text(encoding="utf-8-sig"))
    first_results = first["summaries"]
    final_results = final["hypothesis_summaries"]
    first_events = [json.loads(x) for x in (ROOT / "reports/phase3_signal_events.jsonl").read_text(encoding="utf-8").splitlines() if x]
    final_events = [json.loads(x) for x in (ROOT / "reports/research_phase3_event_outcomes.jsonl").read_text(encoding="utf-8").splitlines() if x]
    event_set_comparison = {}
    for hid in ("S3-A", "S3-C", "S3-D"):
        old_key = lambda row: (row["symbol"], row.get("entry_date", row["signal_date"]) if hid == "S3-C" else row["signal_date"])
        old = {old_key(x) for x in first_events if x.get("hypothesis_id") == hid}
        new = {(x["symbol"], x["date"]) for x in final_events if x.get("hypothesis") == hid and x.get("h") == 5 and x.get("event")}
        event_set_comparison[hid] = {"first_count": len(old), "final_count": len(new), "same_events": old == new,
                                     "only_first": sorted(old-new), "only_final": sorted(new-old)}
    changes = {
        "S3-A": {"events": [45, 45], "matched": [45, 45], "event_identity_check": event_set_comparison["S3-A"], "uplift": [first_results["S3-A"]["horizons"]["5"]["mean_uplift"], final_results["S3-A"]["horizons"]["5"]["mean_uplift"]], "ci": [first_results["S3-A"]["horizons"]["5"]["two_way_cluster_bootstrap_95pct_ci"], final_results["S3-A"]["horizons"]["5"]["ci95"]], "comparability": {"definition_endpoint_data_controls_event_set": "SAME", "effective_clusters_first": {"dates": first_results["S3-A"]["effective_date_clusters_kish"], "symbols": first_results["S3-A"]["effective_symbol_clusters_kish"]}, "effective_clusters_final": {"dates": final_results["S3-A"]["horizons"]["5"]["effective_date_clusters_kish"], "symbols": final_results["S3-A"]["horizons"]["5"]["effective_symbol_clusters_kish"]}, "uncertainty": "NON_COMPARABLE_MONTE_CARLO_GENERATION_DIFFERS (integer multinomial resampling vs multinomial batch draws), point estimate unchanged"}},
        "S3-B": {"events": [0, final_results["S3-B"]["raw_event_count_h5"]], "matched": [0, final_results["S3-B"]["matched_event_count_h5"]], "uplift": [None, final_results["S3-B"]["horizons"]["5"]["mean_uplift"]], "status": "NON_COMPARABLE_FIRST_RUN_POSTPONED_MISSING_INDEX_FINAL_RUN_USED_OFFICIAL_TRADESIM_SET50_SERIES"},
        "S3-C": {"events": [2269, final_results["S3-C"]["raw_event_count_h5"]], "matched": [2161, final_results["S3-C"]["matched_event_count_h5"]], "event_identity_check": event_set_comparison["S3-C"], "uplift": [first_results["S3-C"]["horizons"]["5"]["mean_uplift"], final_results["S3-C"]["horizons"]["5"]["mean_uplift"]], "comparability": {"definition_endpoint_source_event_set": "SAME (event identity matches after aligning first-run entry_date to final gap-session date)", "control": "NON_COMPARABLE: same-date cross-section vs same-symbol/same-year non-gap controls", "effective_clusters_first": {"dates": first_results["S3-C"]["effective_date_clusters_kish"], "symbols": first_results["S3-C"]["effective_symbol_clusters_kish"]}, "effective_clusters_final": {"dates": final_results["S3-C"]["horizons"]["5"]["effective_date_clusters_kish"], "symbols": final_results["S3-C"]["horizons"]["5"]["effective_symbol_clusters_kish"]}, "matching": "final same-symbol/year control matched all 2269; first same-date control matched 2161"}},
        "S3-D": {"events": [485, final_results["S3-D"]["raw_event_count_h5"]], "matched": [485, final_results["S3-D"]["matched_event_count_h5"]], "event_identity_check": event_set_comparison["S3-D"], "uplift": [first_results["S3-D"]["horizons"]["5"]["mean_uplift"], final_results["S3-D"]["horizons"]["5"]["mean_uplift"]], "comparability": {"definition_endpoint_control_source": "SAME for shared events", "extra_final_event": "IVL 2026-08-28", "cause": "EVENT-SET DIFFERENCE IDENTIFIED; root cause in first-screen versus final sample eligibility remains unreconciled", "effective_clusters_first": {"dates": first_results["S3-D"]["effective_date_clusters_kish"], "symbols": first_results["S3-D"]["effective_symbol_clusters_kish"]}, "effective_clusters_final": {"dates": final_results["S3-D"]["horizons"]["5"]["effective_date_clusters_kish"], "symbols": final_results["S3-D"]["horizons"]["5"]["effective_symbol_clusters_kish"]}}}
    }
    return {"schema_version": 1, "comparison_id": "PHASE3_RECONCILIATION_v1", "as_of": "2026-10-31",
        "classification": "RETROSPECTIVE_RECONCILIATION_NOT_NEW_EXPERIMENT", "git_head_at_runs": first["git_head"],
        "worktree_state": {"first_screen_dirty": first["dirty_before_run"], "final_run_dirty": final["worktree_dirty"], "final_run_porcelain_entries": final["worktree_porcelain_entries_at_run"], "current_dirty_work_preserved": True},
        "runs": [
            {"id": "P3_FIRST_SCREEN", "artifact": str(first_path.relative_to(ROOT)), "preregistration": first["pre_registration"], "sample": first["sample_window"], "seed": first["uncertainty"]["seed"], "bootstrap": first["uncertainty"], "controls": "same-date PIT non-event; for C direction oriented", "benchmark": "S3-B postponed: no official series in approved inputs", "source_hashes": first["source_hashes"], "code_hashes": first["code_hashes"], "raw_events": {k:v.get("event_count") for k,v in first_results.items()}},
            {"id": "P3_FINAL_ADDED_RUN", "artifact": str(final_path.relative_to(ROOT)), "preregistration": "docs/RESEARCH_PHASE3_PRE_REGISTRATION_FINAL.md", "sample": {"start":"2023-01-03","end":"2026-09-04"}, "seed": 20261030, "bootstrap": "two-way date/symbol pigeonhole bootstrap, 10,000 replications; final code uses numpy generator and weighted event rows; intervals percentile", "controls": {"A_B_D":"same-date PIT-eligible non-event names", "C":"same-symbol same-calendar-year non-gap controls; same-date controls separately diagnostic"}, "benchmark": "Daily_Ticks.zip official history SET50.csv; 747 closes 2023-09-21..2026-10-21; distinct from confirmed exact scoring feed", "source_hashes": final["data"].get("source_hashes"), "code_hashes": final["code_hashes"], "raw_events": {k:v.get("raw_event_count_h5") for k,v in final_results.items()}},
            {"id": "P3_DECISION_REPORT", "artifact": "docs/RESEARCH_PHASE3_DECISION_REPORT.md", "classification": "NARRATIVE_RESTATEMENT_OF_FIRST_SCREEN_PLUS_FINAL_ADDENDUM_NOT_AN_INDEPENDENT_RUN", "promotion": "NO_SIGNAL_PASSED_PROMOTION_GATE"}],
        "comparison": changes, "event_identity_checks": event_set_comparison,
        "statistical_interpretation": {"first_screen_calculable_hypotheses":"S3-A/C/D all CI cross zero; Holm p=1.0", "final_hypotheses":"S3-A/B/C/D all CI cross zero; Holm p=1.0; all REJECTED_G1_NOT_MET", "power_vs_negative_evidence":"Sparse effective symbol clusters (about 13-16) and overlapping endpoints limit power; S3-A/B/D intervals are inconclusive, while S3-C has near-zero/negative point estimate under final control but still not proof of no effect. Coverage is incomplete (18 names) and does not imply a negative signal over all SET50.", "independent_oos":"NONE; all analyzed history previously inspected."},
        "reproducers": [".\\.venv\\Scripts\\python.exe scripts\\run_phase3_signal_screen.py", ".\\.venv\\Scripts\\python.exe scripts\\run_phase3_final_research.py"],
        "promotion": "NO_SIGNAL_PASSED_PROMOTION_GATE", "do_not_select_strategy": True}


def main() -> None:
    write_json(ROOT / "reports/competition_calendar_verified.json", calendar())
    write_json(ROOT / "reports/phase4_pit_universe_eligibility.json", pit_matrix())
    write_json(ROOT / "reports/phase4_nonpromotional_baselines.json", baseline_report("expanded_20"))
    write_json(ROOT / "reports/phase4_nonpromotional_baselines_phase3_18.json", baseline_report("phase3_18"))
    write_json(ROOT / "reports/phase3_run_reconciliation.json", phase3_reconciliation())


if __name__ == "__main__":
    main()

"""Build descriptive, snapshot-only BBO execution diagnostics."""
from __future__ import annotations

import json
import sys
from decimal import Decimal, ROUND_FLOOR
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.run_design_a_backtest import set_tick_size
from src.research.execution.book import book_sweep_vwap, spread_metrics

NOTIONALS = (100_000, 500_000, 1_000_000)
TIMEZONE = "Asia/Bangkok"


def _snapshot_rows(frame: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    frame["retrieved_at"] = pd.to_datetime(frame["retrieved_at"], utc=True, errors="coerce")
    event_keys = [key for key in ["retrieved_at", "symbol", "collector_session_id", "generation", "rotation_group"] if key in frame]
    for _, snapshot in frame.dropna(subset=["retrieved_at"]).groupby(event_keys, sort=False):
        bids = snapshot[snapshot["side"] == "bid"].sort_values("level")
        asks = snapshot[snapshot["side"] == "ask"].sort_values("level")
        if bids.empty or asks.empty:
            continue
        bid_levels = [(Decimal(str(p)), Decimal(str(q))) for p, q in zip(bids["price"], bids["volume"])]
        ask_levels = [(Decimal(str(p)), Decimal(str(q))) for p, q in zip(asks["price"], asks["volume"])]
        best_bid, best_ask = bid_levels[0][0], ask_levels[0][0]
        if best_bid <= 0 or best_ask <= best_bid or bid_levels[0][1] <= 0 or ask_levels[0][1] <= 0:
            continue
        spread = spread_metrics(best_bid, best_ask)
        tick = set_tick_size(best_bid)
        timestamp = pd.Timestamp(snapshot["retrieved_at"].iloc[0])
        local = timestamp.tz_convert(TIMEZONE)
        minute = local.hour * 60 + local.minute
        session = "morning" if 570 <= minute < 750 else "afternoon" if 870 <= minute < 1000 else "pre_close" if 1000 <= minute < 1020 else "outside_continuous_session"
        item = {
            "symbol": str(snapshot["symbol"].iloc[0]), "timestamp": timestamp.isoformat(),
            "trading_day": str(local.date()), "session": session,
            "time_bucket": f"{local.hour:02d}:{'30' if local.minute >= 30 else '00'}",
            "spread": str(spread["spread"]), "spread_ticks": str(spread["spread"] / tick),
            "spread_bps": str(spread["spread_bps"]), "tick_size": str(tick),
            "best_bid_depth": str(bid_levels[0][1]), "best_ask_depth": str(ask_levels[0][1]),
        }
        for level in (3, 5, 10):
            item[f"bid_depth_{level}"] = str(sum(q for _, q in bid_levels[:level]))
            item[f"ask_depth_{level}"] = str(sum(q for _, q in ask_levels[:level]))
        for notional in NOTIONALS:
            for side, levels, quote in (("buy", ask_levels, best_ask), ("sell", bid_levels, best_bid)):
                quantity = (Decimal(notional) / quote).to_integral_value(rounding=ROUND_FLOOR)
                visible_quantity = min(quantity, sum((volume for _, volume in levels), Decimal("0")))
                vwap = book_sweep_vwap(levels, quantity) if quantity > 0 else None
                visible_vwap = book_sweep_vwap(levels, visible_quantity) if visible_quantity > 0 else None
                prefix = f"{side}_{notional}"
                item[f"{prefix}_quantity"] = int(quantity)
                item[f"{prefix}_visible_quantity"] = int(visible_quantity)
                item[f"{prefix}_fillable"] = vwap is not None
                item[f"{prefix}_vwap"] = str(vwap) if vwap is not None else None
                item[f"{prefix}_slippage_bps"] = str(abs(vwap - quote) / quote * Decimal(10000)) if vwap is not None else None
                item[f"{prefix}_slippage_ticks"] = str(abs(vwap - quote) / tick) if vwap is not None else None
                item[f"{prefix}_visible_vwap"] = str(visible_vwap) if visible_vwap is not None else None
                item[f"{prefix}_visible_slippage_bps"] = str(abs(visible_vwap - quote) / quote * Decimal(10000)) if visible_vwap is not None else None
                item[f"{prefix}_visible_slippage_ticks"] = str(abs(visible_vwap - quote) / tick) if visible_vwap is not None else None
        rows.append(item)
    return rows


def _summarize(frame: pd.DataFrame) -> tuple[dict, list[dict]]:
    metric_columns = ["spread", "spread_ticks", "spread_bps", "best_bid_depth", "best_ask_depth"]
    metric_columns += [f"{side}_depth_{level}" for side in ("bid", "ask") for level in (3, 5, 10)]
    stats: dict = {}
    for column in metric_columns:
        series = pd.to_numeric(frame[column], errors="coerce").dropna()
        stats[column] = {"count": int(series.count()), "median": float(series.median()), "mean": float(series.mean()), "p25": float(series.quantile(.25)), "p75": float(series.quantile(.75)), "p90": float(series.quantile(.90)), "p95": float(series.quantile(.95)), "max": float(series.max())}
    ticks = pd.to_numeric(frame["spread_ticks"], errors="coerce")
    stats["spread_tick_fractions"] = {"at_most_one_tick": float((ticks <= 1).mean()), "greater_than_one_tick": float((ticks > 1).mean())}
    for notional in NOTIONALS:
        for side in ("buy", "sell"):
            prefix = f"{side}_{notional}"
            fillable = frame[frame[f"{prefix}_fillable"]]
            visible = frame[pd.to_numeric(frame[f"{prefix}_visible_quantity"]) > 0]
            stats[prefix] = {
                "notional_thb": notional, "snapshot_count": int(len(frame)),
                "fillable_count": int(len(fillable)), "insufficient_visible_depth": int(len(frame) - len(fillable)),
                "median_requested_quantity": float(pd.to_numeric(frame[f"{prefix}_quantity"]).median()),
                "median_visible_fillable_quantity": float(pd.to_numeric(frame[f"{prefix}_visible_quantity"]).median()),
                "median_visible_quantity_fraction": float((pd.to_numeric(frame[f"{prefix}_visible_quantity"]) / pd.to_numeric(frame[f"{prefix}_quantity"])).median()),
                "median_slippage_bps": float(pd.to_numeric(fillable[f"{prefix}_slippage_bps"]).median()) if len(fillable) else None,
                "median_slippage_ticks": float(pd.to_numeric(fillable[f"{prefix}_slippage_ticks"]).median()) if len(fillable) else None,
                "median_visible_quantity_slippage_bps": float(pd.to_numeric(visible[f"{prefix}_visible_slippage_bps"]).median()) if len(visible) else None,
                "median_visible_quantity_slippage_ticks": float(pd.to_numeric(visible[f"{prefix}_visible_slippage_ticks"]).median()) if len(visible) else None,
            }
    grouping: list[dict] = []
    for keys in (["symbol"], ["trading_day"], ["session"], ["time_bucket"], ["symbol", "session"]):
        records = []
        for key, group in frame.groupby(keys, dropna=False, sort=True):
            if not isinstance(key, tuple):
                key = (key,)
            record = dict(zip(keys, key))
            record["snapshot_count"] = int(len(group))
            for column in metric_columns:
                record[f"{column}_median"] = float(pd.to_numeric(group[column], errors="coerce").median())
            for notional in NOTIONALS:
                for side in ("buy", "sell"):
                    prefix = f"{side}_{notional}"
                    good = group[group[f"{prefix}_fillable"]]
                    visible = group[pd.to_numeric(group[f"{prefix}_visible_quantity"]) > 0]
                    record[f"{prefix}_fillable_count"] = int(len(good))
                    record[f"{prefix}_insufficient_depth_count"] = int(len(group) - len(good))
                    record[f"{prefix}_median_visible_fillable_quantity"] = float(pd.to_numeric(group[f"{prefix}_visible_quantity"]).median())
                    record[f"{prefix}_median_slippage_ticks"] = float(pd.to_numeric(good[f"{prefix}_slippage_ticks"]).median()) if len(good) else None
                    record[f"{prefix}_median_slippage_bps"] = float(pd.to_numeric(good[f"{prefix}_slippage_bps"]).median()) if len(good) else None
                    record[f"{prefix}_median_visible_quantity_slippage_ticks"] = float(pd.to_numeric(visible[f"{prefix}_visible_slippage_ticks"]).median()) if len(visible) else None
            records.append(record)
        grouping.append({"group_by": keys, "rows": records})
    return stats, grouping


def main() -> int:
    path = ROOT / "data" / "pilot" / "settrade" / "normalized" / "bid_offer" / "data.csv"
    source = pd.read_csv(path) if path.exists() else pd.DataFrame()
    rows = _snapshot_rows(source) if not source.empty else []
    summary = pd.DataFrame(rows)
    stats, groups = _summarize(summary) if not summary.empty else ({}, [])
    date_range = [str(summary["trading_day"].min()), str(summary["trading_day"].max())] if not summary.empty else [None, None]
    audit_path = ROOT / "reports" / "settrade_collection_audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8")) if audit_path.exists() else {}
    event_keys = [key for key in ["retrieved_at", "symbol", "collector_session_id", "generation", "rotation_group"] if key in source]
    candidate_snapshots = int(source[event_keys].drop_duplicates().shape[0]) if not source.empty and event_keys else 0
    output = {
        "source": "normalized genuine Settrade BBO snapshots", "dataset_date_range": date_range,
        "complete_snapshot_count": len(rows), "symbol_count": int(summary["symbol"].nunique()) if not summary.empty else 0,
        "normalized_snapshot_candidates": candidate_snapshots,
        "excluded_from_spread_diagnostics": max(0, candidate_snapshots - len(rows)),
        "raw_bbo_events": audit.get("raw_bbo", {}).get("valid_events"),
        "bbo_readiness": audit.get("readiness", {}).get("bbo"),
        "statistics": stats, "by_group": groups,
        "semantics": "Descriptive BBO snapshot analysis. Hypothetical visible-book sweeps are not actual fills.",
        "limitations": ["Snapshot data cannot establish queue priority.", "Snapshot data cannot establish hidden liquidity or latency.", "Snapshot data cannot prove actual IOC fill probability.", "BBO updates are not executed transaction ticks."],
        "model_v1_review_status": "MODEL_V1_UNCHANGED_INSUFFICIENT_EVIDENCE",
    }
    (ROOT / "reports" / "settrade_execution_diagnostics.json").write_text(json.dumps(output, indent=2, allow_nan=False), encoding="utf-8")
    lines = ["# Settrade execution diagnostics", "", "Descriptive analysis of genuine persisted BBO snapshots. Hypothetical sweeps use only displayed depth and must not be read as actual fills.", "", f"- Dataset date range: {date_range[0]} to {date_range[1]}", f"- BBO readiness: {output['bbo_readiness']}", f"- Raw callback events: {output['raw_bbo_events']}; normalized event candidates: {candidate_snapshots:,}; valid two-sided, positive, uncrossed snapshots: {len(rows):,}; excluded from spread metrics: {output['excluded_from_spread_diagnostics']:,}", f"- Symbols: {output['symbol_count']}"]
    if stats:
        lines += [f"- Quoted spread median: {stats['spread']['median']:.4f} THB / {stats['spread_ticks']['median']:.3f} ticks / {stats['spread_bps']['median']:.2f} bps", f"- Spread <=1 tick: {stats['spread_tick_fractions']['at_most_one_tick']:.2%}; >1 tick: {stats['spread_tick_fractions']['greater_than_one_tick']:.2%}", f"- Best-level median depth: bid {stats['best_bid_depth']['median']:.0f}; ask {stats['best_ask_depth']['median']:.0f} shares", "", "Cumulative visible depth medians:"]
        for level in (3, 5, 10):
            lines.append(f"- Top {level}: bid {stats[f'bid_depth_{level}']['median']:.0f}; ask {stats[f'ask_depth_{level}']['median']:.0f} shares")
        lines += ["", "Hypothetical visible-book sweeps:"]
        for notional in NOTIONALS:
            for side in ("buy", "sell"):
                result = stats[f"{side}_{notional}"]
                lines.append(f"- {side.title()} {notional:,} THB: {result['fillable_count']:,}/{result['snapshot_count']:,} snapshots visibly fillable; insufficient depth {result['insufficient_visible_depth']:,}; median visible quantity {result['median_visible_fillable_quantity']:.0f} shares; median per-snapshot visible/requested fraction {result['median_visible_quantity_fraction']:.1%}; full-request slippage on fillable snapshots {result['median_slippage_ticks']} ticks / {result['median_slippage_bps']} bps; displayed-depth impact for available shares {result['median_visible_quantity_slippage_ticks']} ticks / {result['median_visible_quantity_slippage_bps']} bps.")
        lines += ["", "Time-of-day, per-day, per-symbol, and symbol-session medians and sweep coverage are in the JSON `by_group` sections. These are descriptive profiles, not rankings or recommendations.", "Spread tick conversion uses the explicit repository research tick-size helper. Sweep slippage is measured from the opposite best quote, excludes the cost to cross from a separate reference price, and represents visible-depth impact only."]
    lines += ["", "Limitations: snapshots cannot establish queue priority, hidden liquidity, latency, actual IOC fill probability, or executed trade ticks. The one-adverse-tick MODEL_V1 assumption is unchanged; this evidence is insufficient to establish realized fill cost.", "", "MODEL_V1_UNCHANGED_INSUFFICIENT_EVIDENCE"]
    (ROOT / "reports" / "settrade_execution_diagnostics.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"snapshots": len(rows), "symbols": output["symbol_count"], "date_range": date_range}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

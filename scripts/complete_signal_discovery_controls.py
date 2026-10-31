"""Add matched descriptive controls to the pre-registered H6 event study."""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.run_research_round2_signal import HORIZONS, _load_inputs, _regime  # noqa: E402
from src.data.eligibility import MarketDataEligibilityGate  # noqa: E402


def _observations(prices: dict[str, pd.DataFrame], regime: pd.DataFrame) -> list[dict]:
    rows: list[dict] = []
    gate = MarketDataEligibilityGate(ROOT)
    for symbol, frame in sorted(prices.items()):
        data = frame.sort_index()
        adj_close = pd.to_numeric(data["adjusted_close" if "adjusted_close" in data else "adj_close"], errors="coerce")
        close = pd.to_numeric(data["close"], errors="coerce")
        adj_open = pd.to_numeric(data["open"], errors="coerce") * adj_close / close
        eligibility = data.get("validity_status", pd.Series("VALID", index=data.index)).astype(str).str.upper()
        for pos, stamp in enumerate(data.index):
            if pos + max(HORIZONS.values()) >= len(data) or eligibility.iloc[pos] not in {"VALID", "USE", "USE_WITH_FLAG"}:
                continue
            if not gate.assess(symbol, stamp.date()).eligible:
                continue
            entry = adj_open.iloc[pos + 1]
            if pd.isna(entry) or entry <= 0:
                continue
            row = {"symbol": symbol, "signal_date": stamp, "year": stamp.year,
                   "regime": str(regime.at[stamp, "regime"]) if stamp in regime.index else "UNKNOWN"}
            for horizon, offset in HORIZONS.items():
                exit_price = adj_close.iloc[pos + offset]
                row[horizon] = float(exit_price / entry - 1) if pd.notna(exit_price) else None
            rows.append(row)
    return rows


def _summary(rows: list[dict], horizons: tuple[str, ...]) -> dict:
    result = {}
    for horizon in horizons:
        values = np.asarray([row[horizon] for row in rows if row.get(horizon) is not None], dtype=float)
        n = len(values)
        se = float(values.std(ddof=1) / np.sqrt(n)) if n > 1 else None
        result[horizon] = {
            "n": n, "mean": float(values.mean()) if n else None,
            "median": float(np.median(values)) if n else None,
            "hit_rate": float((values > 0).mean()) if n else None,
            "std_dev": float(values.std(ddof=1)) if n > 1 else None,
            "approx_95pct_mean_ci": [float(values.mean() - 1.96 * se), float(values.mean() + 1.96 * se)] if se is not None else None,
            "quantiles": {str(q): float(np.quantile(values, q)) for q in (0.05, 0.25, 0.5, 0.75, 0.95)} if n else {},
        }
    return result


def main() -> None:
    prior_path = ROOT / "reports/research_round2_summary.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    events = prior["events"]
    prices, benchmark = _load_inputs()
    regime = _regime(benchmark, prices)
    universe = _observations(prices, regime)
    rng = np.random.default_rng(2701)
    event_symbols = Counter(row["symbol"] for row in events)
    by_symbol: dict[str, list[dict]] = defaultdict(list)
    for row in universe:
        by_symbol[row["symbol"]].append(row)

    random_same_symbol = []
    for symbol, count in sorted(event_symbols.items()):
        options = by_symbol.get(symbol, [])
        if not options:
            continue
        indices = rng.choice(len(options), size=min(count, len(options)), replace=False)
        random_same_symbol.extend(options[int(index)] for index in indices)

    same_regime_pool = [row for row in universe if row["regime"] == "NEUTRAL_POSITIVE"]
    count = min(len(events), len(same_regime_pool))
    chosen = rng.choice(len(same_regime_pool), size=count, replace=False) if count else []
    same_regime = [same_regime_pool[int(index)] for index in chosen]

    event_days: dict[pd.Timestamp, list[dict]] = defaultdict(list)
    for row in universe:
        event_days[row["signal_date"]].append(row)
    cross_section = []
    for stamp, rows in sorted(event_days.items()):
        cross_section.append({"symbol": "CROSS_SECTION", "signal_date": stamp,
                              **{horizon: float(np.mean([r[horizon] for r in rows if r[horizon] is not None]))
                                 for horizon in HORIZONS}})

    horizon_names = tuple(HORIZONS)
    event_stats = _summary(events, horizon_names)
    controls = {
        "unconditional_eligible_symbol_dates": _summary(universe, horizon_names),
        "same_symbol_random_eligible_dates_seed_2701": _summary(random_same_symbol, horizon_names),
        "same_regime_random_eligible_dates_seed_2701": _summary(same_regime, horizon_names),
        "cross_section_equal_weight_daily_universe": _summary(cross_section, horizon_names),
    }
    hypothesis_specs = json.loads((ROOT / "reports/research_hypothesis_specs.json").read_text(encoding="utf-8"))
    hypothesis_registry = [
        {"id": item.get("id"), "rationale": item.get("rationale"),
         "testability": item.get("testability", "NOT_RUN"),
         "required_features": item.get("required_features", []),
         "rejection_criteria": item.get("rejection_criteria", "Not specified")}
        for item in hypothesis_specs.get("hypotheses", [])
    ]
    symbol_counts = Counter(row["symbol"] for row in events)
    year_counts = Counter(str(row["signal_date"])[:4] for row in events)
    output = {
        "schema_version": 1,
        "run_id": datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_signal_controls",
        "hypothesis_id": prior["hypothesis_id"],
        "evidence_classification": "SIGNAL_DIAGNOSTIC_ONLY",
        "source_run_id": prior["run_id"],
        "data_source": prior["data_source"],
        "seed": 2701,
        "preregistered_hypothesis_count": 6,
        "tested_hypothesis_count_in_this_control_run": 1,
        "hypothesis_registry": hypothesis_registry,
        "multiplicity": hypothesis_specs.get("multiplicity", {}),
        "horizons": list(horizon_names),
        "event_stats": event_stats,
        "controls": controls,
        "concentration": {
            "unique_symbols": len(symbol_counts), "symbol_counts": dict(sorted(symbol_counts.items())),
            "largest_symbol_share": max(symbol_counts.values()) / len(events) if events else None,
            "year_counts": dict(sorted(year_counts.items())),
            "largest_year_share": max(year_counts.values()) / len(events) if events else None,
        },
        "limitations": [
            "The controls use approved partial daily coverage and the available eligibility gate; they do not cure historical SET50 survivorship limitations.",
            "Control date selection is deterministic but does not remove serial dependence or overlap; normal confidence intervals are descriptive only.",
            "Same-symbol random control dates are sampled from observed eligible dates for event symbols; regime controls sample all observed eligible dates in the predeclared NEUTRAL_POSITIVE regime.",
            "This study is not a portfolio backtest and contains no execution or cost model.",
        ],
        "promotion_result": "NO_SIGNAL_PASSED_PROMOTION_GATE",
    }
    out = ROOT / "reports/signal_discovery_summary.json"
    out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"run_id": output["run_id"], "events": len(events), "controls": output["controls"], "concentration": output["concentration"]}, indent=2))


if __name__ == "__main__":
    main()

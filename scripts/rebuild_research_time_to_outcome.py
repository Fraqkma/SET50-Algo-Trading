"""Rebuild first-passage tables from the saved event close-return paths."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.research.holding_period import passage_counts
HORIZONS = (1, 2, 3, 4, 5, 7, 10, 15)
OBJECTIVES = (0.01, 0.02)
ADVERSE = (-0.01, -0.02)


def main() -> None:
    curve = json.loads((ROOT / "reports/research_holding_horizon_curve.json").read_text(encoding="utf-8"))
    prior_path = ROOT / "reports/research_time_to_outcome_distribution.json"
    prior = json.loads(prior_path.read_text(encoding="utf-8"))
    output: dict[str, object] = {
        "definition": "first eligible daily close crossing; opposite risk/objective boundary is a competing event",
        "thresholds_net_return": {"positive_objectives": list(OBJECTIVES), "adverse_boundaries": list(ADVERSE),
                                  "first_positive": 0.0,
                                  "selection_note": "predeclared descriptive levels, not fitted to maximize outcomes"},
        "by_hypothesis": {}, "event_paths": prior["event_paths"],
        "metadata": prior["metadata"],
    }
    for hypothesis, records in output["event_paths"].items():
        output["by_hypothesis"][hypothesis] = {}
        for cost, path_key in (("fee_only", "net_close_return_by_session_fee_only"),
                               ("one_tick_each_side", "net_close_return_by_session_one_tick")):
            rows = [{"net_path": row[path_key], "date": row["event_date"],
                     "symbol": row["symbol"]} for row in records]
            for threshold in (*OBJECTIVES, *ADVERSE, 0.0):
                key = f"{cost}:{threshold:+.1%}"
                competing = -0.01 if threshold >= 0 else 0.01
                output["by_hypothesis"][hypothesis][key] = passage_counts(
                    rows, threshold, HORIZONS, competing_threshold=competing,
                    replications=2_000, seed=20261101 + list(output["event_paths"]).index(hypothesis) * 1_000
                    + int(abs(threshold) * 10_000) + (100 if cost == "one_tick_each_side" else 0))
    output["metadata"].update({"first_passage_competing_risk": "opposite +/-1% boundary is treated as competing event for +/-1% and +/-2% targets; the other boundary is +1% for adverse thresholds; -1% for first-positive.",
                               "right_censoring": "15 observed sessions with neither target nor competing boundary hit",
                               "insufficient_followup": "censored at last available eligible daily close and retained in cohort denominator",
                               "uncertainty": "2,000 two-way date/symbol pigeonhole bootstrap replications; 95% percentile intervals on cumulative target-first incidence by session; dependence and small-cluster limits apply"})
    prior_path.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({h: {k: v["status_counts"] for k, v in d.items() if k in
                          ("fee_only:+1.0%", "fee_only:-1.0%", "fee_only:+0.0%")}
                      for h, d in output["by_hypothesis"].items()}, indent=2))


if __name__ == "__main__":
    main()

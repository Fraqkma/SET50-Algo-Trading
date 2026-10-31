"""Create fixed-fill arithmetic sensitivities from preserved run aggregates."""
from __future__ import annotations

import json
import hashlib
import platform
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
D = Decimal


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    meanrev_path = ROOT / "artifacts/research_runs/20261024T065012Z_candidate_discovery/candidate_discovery.json"
    meanrev = json.loads(meanrev_path.read_text(encoding="utf-8"))["candidates"]["CANDIDATE_MEANREV5"]["first_pass"]
    round2 = json.loads((ROOT / "reports/research_round2_summary.json").read_text(encoding="utf-8"))["portfolio_stage"]
    candidates = {"MeanRev5": meanrev, "Round2_H6": round2}
    results: dict[str, dict] = {}
    for name, source in candidates.items():
        gross_value = source["gross_pnl"] if "gross_pnl" in source else source["cost_decomposition"]["gross_pnl"]
        gross = D(str(gross_value))
        fees = D(str(source["total_fees"]))
        slippage = D(str(source.get("slippage", source.get("modeled_slippage"))))
        capital = D("10000000")
        zero_slip_net = gross + slippage - fees
        stress_net = gross - D("1.5") * fees - slippage
        results[name] = {
            "baseline": {
                "gross_pnl_after_modeled_slippage": str(gross), "fees": str(fees),
                "commission": str(source["commission"]), "vat": str(source["vat"]),
                "modeled_slippage": str(slippage), "net_pnl": str(source.get("fifo_realized_net_pnl", source.get("net_pnl", D(str(source["final_equity"])) - capital))),
                "final_equity": str(source["final_equity"]), "filled_orders": int(source["filled_orders"]),
                "non_fills": int(source["non_fills"]), "intended_orders": int(source["filled_orders"]) + int(source["non_fills"]),
                "turnover": str(source["turnover"]), "maximum_drawdown": str(abs(D(str(source["maximum_drawdown"])))),
                "average_eod_exposure": source.get("average_equity_exposure", source.get("average_equity_exposure")),
                "completed_fifo_roundtrips": int(source.get("completed_fifo_round_trips", source.get("completed_fifo_roundtrips"))),
            },
            "idealized_zero_slippage_fixed_fill_arithmetic": {
                "net_pnl": str(zero_slip_net), "net_return_on_initial_capital": str(zero_slip_net / capital),
                "formula": "baseline gross PnL + reported one-tick slippage add-back - unchanged fees",
                "fills_and_quantities": "held fixed from historical V1; not a re-simulated portfolio",
            },
            "stress_1_5x_fees_plus_second_adverse_tick_fixed_fill_arithmetic": {
                "stressed_fees": str(D("1.5") * fees), "additional_adverse_tick_cost": str(slippage),
                "net_pnl": str(stress_net), "net_return_on_initial_capital": str(stress_net / capital),
                "formula": "baseline gross PnL - 1.5x fees - one additional tick cost equal to baseline one-tick slippage",
                "fills_and_quantities": "held fixed; cash path, fill changes, DD and exposure are not recomputed",
            },
            "baseline_path_metrics_only": True,
        }
    payload = {
        "schema_version": 1, "classification": "NON_OFFICIAL_FIXED_FILL_ARITHMETIC",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "python_version": platform.python_version(),
        "v1_preserved": True, "v2": "NOT_NUMERICALLY_MODELED_DAILY_BARS_CANNOT_SUPPORT_AUTHENTIC_0_2_7_FILL_QUANTITIES",
        "execution_mechanics_evidence": "Existing 0.2.7 fixture matrix: 13 cases, 22 checks; not a fill-rate sample.",
        "scenarios": results,
        "source_artifacts": {
            str(meanrev_path.relative_to(ROOT)): sha(meanrev_path),
            "reports/research_round2_summary.json": sha(ROOT / "reports/research_round2_summary.json"),
            "reports/execution_sensitivity_summary.json": sha(ROOT / "reports/execution_sensitivity_summary.json"),
        },
        "limits": ["Counterfactual quantities are fixed at historical V1 values; changing slippage/fees would alter the cash path and later trades.",
                   "Baseline drawdown/exposure/turnover/FIFO are shown only for the original path; not recomputed for counterfactuals.",
                   "No daily volume cap, BBO, queue position, or fill probability was inferred."]
    }
    (ROOT / "reports/execution_sensitivity_027_fixed_fill_arithmetic.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps({name: {key: value[key] for key in ("idealized_zero_slippage_fixed_fill_arithmetic", "stress_1_5x_fees_plus_second_adverse_tick_fixed_fill_arithmetic")} for name, value in results.items()}, indent=2))


if __name__ == "__main__":
    main()

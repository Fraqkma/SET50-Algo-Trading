"""Fixed, descriptive root-cause diagnostics for existing approved A/C runs."""
from __future__ import annotations
import json
from pathlib import Path
import pandas as pd
import sys
sys.path.insert(0, str(ROOT) if 'ROOT' in globals() else str(Path(__file__).resolve().parents[1]))
from src.data.research import load_approved_market_data
from src.data.features import build_features

ROOT = Path(__file__).resolve().parents[1]

def _run(design: str) -> dict:
    orders = pd.read_csv(ROOT / "reports" / f"design_{design.lower()}_backtest_orders.csv")
    snaps = pd.read_csv(ROOT / "reports" / f"design_{design.lower()}_backtest_snapshots.csv")
    status = orders.get("status", pd.Series(dtype=str)).astype(str)
    filled = orders[status.eq("FILLED")].copy()
    filled["order_value"] = pd.to_numeric(filled.get("order_value", 0), errors="coerce").fillna(0)
    result = {"design": design, "fills": int(len(filled)), "orders": int(len(orders)),
              "non_fills": int(len(orders) - len(filled)),
              "turnover_value": float(filled["order_value"].sum()),
              "commission": float(pd.to_numeric(filled.get("commission", 0), errors="coerce").fillna(0).sum()),
              "vat": float(pd.to_numeric(filled.get("vat", 0), errors="coerce").fillna(0).sum()),
              "slippage": float(pd.to_numeric(filled.get("slippage", 0), errors="coerce").fillna(0).sum())}
    if "reason" in orders:
        result["non_fill_reasons"] = orders.loc[~status.eq("FILLED"), "reason"].fillna("UNKNOWN").value_counts().to_dict()
    if "positions" in snaps:
        result["snapshot_count"] = int(len(snaps)); result["valuation_complete"] = bool((snaps.get("valuation_status", "") == "COMPLETE").all())
    if "execution_date" in orders:
        dates = pd.to_datetime(orders["execution_date"], errors="coerce")
        result["turnover_decomposition"] = {"buy_value": float(filled.loc[filled.side.eq("BUY"), "order_value"].sum()) if "side" in filled else 0.0,
                                             "sell_value": float(filled.loc[filled.side.eq("SELL"), "order_value"].sum()) if "side" in filled else 0.0,
                                             "ioc_non_fill_count": int((~status.eq("FILLED")).sum())}
        result["holding_duration_note"] = "Existing order report does not contain position lot identifiers; duration is not inferable without replaying the engine."
    return result

def _signal_diagnostics() -> dict:
    horizons = [1, 3, 5, 10, 20]
    values = {str(h): [] for h in horizons}
    momentum = []
    for symbol in ["BDMS","BGRIM","CENTEL","COM7","GLOBAL","HMPRO","IVL","KKP","KTB","LH","MTC","OSP","PTTGC","RATCH","SCGP","THAI","TOP"]:
        frame = load_approved_market_data(symbol)
        feat = build_features(frame)
        close = pd.to_numeric(frame["close"], errors="coerce")
        for h in horizons:
            values[str(h)].extend((close.shift(-h) / close - 1.0).dropna().tolist())
        valid = feat[["momentum_20", "daily_return"]].dropna()
        momentum.extend(zip(valid["momentum_20"].tolist(), valid["daily_return"].tolist()))
    return {"forward_return_mean": {h: float(pd.Series(v).mean()) for h, v in values.items()},
            "forward_return_observations": {h: len(v) for h, v in values.items()},
            "momentum_20_daily_return_correlation": float(pd.DataFrame(momentum, columns=["momentum_20", "daily_return"]).corr().iloc[0,1])}

def run() -> dict:
    a, c = _run("A"), _run("C")
    payload = {"status": "DESCRIPTIVE_ONLY", "design_a": a, "design_c": c,
               "approved_report_metrics": {d: json.loads((ROOT / "reports" / f"design_{d.lower()}_backtest_report.json").read_text(encoding="utf-8")) for d in ("A", "C")},
               "signal_diagnostics": _signal_diagnostics(),
               "findings": ["Both runs use fixed approved strategy and execution rules.",
                             "Differences are descriptive and cannot establish causality.",
                             "No parameters, metrics, or subsets were searched."],
               "production_mutated": False}
    (ROOT / "reports" / "strategy_root_cause_analysis.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (ROOT / "reports" / "strategy_root_cause_analysis.md").write_text(
        "# Strategy root-cause diagnostics\n\nDescriptive-only analysis of existing approved Design A/C reports.\n\n" +
        "```json\n" + json.dumps(payload, indent=2) + "\n```\n", encoding="utf-8")
    return payload

if __name__ == "__main__": run()

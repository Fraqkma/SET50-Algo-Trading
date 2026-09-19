"""Build deterministic reports from completed bounded Settrade probes."""
from __future__ import annotations
import csv, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"

def main() -> None:
    universe = list(csv.DictReader((REPORTS / "current_set50_universe.csv").open(encoding="utf-8")))
    capability = {row["symbol"]: row for row in csv.DictReader((REPORTS / "settrade_set50_50_symbol_capability.csv").open(encoding="utf-8"))}
    mapping = []
    retention = []
    for item in universe:
        symbol = item["symbol"]
        row = capability[symbol]
        mapping.append({"symbol": symbol, "universe_status": item["status"], "quote": row.get("quote_accessible"), "daily": row.get("1d_accessible"), "intraday_1m": row.get("1m_accessible"), "intraday_5m": row.get("5m_accessible"), "intraday_15m": row.get("15m_accessible"), "mapping_status": "SUPPORTED" if all(row.get(k) == "True" for k in ("quote_accessible", "1d_accessible", "1m_accessible", "5m_accessible", "15m_accessible")) else "PARTIAL_OR_FAILED"})
        retention.append({"symbol": symbol, "daily_latest_observed": row.get("1d_last"), "daily_probe_status": "OBSERVED" if row.get("1d_rows", "0") not in ("", "0") else "NO_ROWS_IN_RECENT_WINDOW", "historical_boundary": "NOT_PROBED_PER_SYMBOL; PTT_BOUNDARY_OBSERVED_2023_12_01", "intraday_status": "RECENT_WINDOW_ONLY"})
    for name, rows in (("settrade_current_symbol_mapping_review.csv", mapping), ("settrade_set50_retention_by_symbol.csv", retention)):
        with (REPORTS / name).open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    realtime = json.loads((REPORTS / "settrade_realtime_schema.json").read_text(encoding="utf-8"))
    quality = json.loads((REPORTS / "settrade_orderbook_quality.json").read_text(encoding="utf-8"))
    ratio_path = REPORTS / "settrade_volume_ratio_analysis.csv"
    ratio_rows = list(csv.DictReader(ratio_path.open(encoding="utf-8"))) if ratio_path.exists() else []
    observed = [float(row["ratio_settrade_local"]) for row in ratio_rows if row.get("ratio_settrade_local") not in (None, "")]
    volume = {"status": "UNRESOLVED", "reason": "Settrade candlestick volume/value semantics were not independently proven against an authoritative overlapping source; raw fields are retained without conversion.", "production_conversion": None, "comparison_rows": len(ratio_rows), "overlap_rows": len(observed), "ratio_min": min(observed) if observed else None, "ratio_max": max(observed) if observed else None, "observed_realtime_fields": ["total_volume", "total_value"], "orders_placed": 0}
    (REPORTS / "settrade_volume_semantics.json").write_text(json.dumps(volume, indent=2), encoding="utf-8")
    if not ratio_path.exists():
        with ratio_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=["symbol", "status", "ratio", "note"]); writer.writeheader()
            for symbol in capability: writer.writerow({"symbol": symbol, "status": "UNRESOLVED", "ratio": "", "note": "No conversion applied"})
    rate = {"market_data_rps": 3, "realtime_topic_limit": 40, "realtime_topics_requested": realtime["topics_requested"], "realtime_limit_respected": realtime["topics_requested"] <= 40, "retry_policy": "bounded_retries_2", "orders_placed": 0}
    (REPORTS / "settrade_rate_limit_audit.json").write_text(json.dumps(rate, indent=2), encoding="utf-8")
    readiness = {"status": "READY_FOR_HUMAN_DECISION", "universe_size": len(universe), "capability_rows": len(capability), "supported_all_matrix": all(row.get("mapping_status") == "SUPPORTED" for row in mapping), "realtime_depth": realtime["bbo_or_depth"], "orderbook_quality_rows": len(quality), "orders_placed": 0, "blocked_production_actions": ["continuous licensed retention", "account trading", "order submission"]}
    (REPORTS / "settrade_collection_readiness.json").write_text(json.dumps(readiness, indent=2), encoding="utf-8")

if __name__ == "__main__": main()

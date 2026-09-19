"""Estimate pilot storage from measured schemas and explicit assumptions."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    sessions_per_month = 21
    sessions_per_year = 252
    minutes_per_session = 390
    bar_bytes = 100
    bbo_bytes = 1200  # conservative estimate for 10 bid + 10 ask levels and metadata
    durations = {"1_month": sessions_per_month, "3_months": sessions_per_month * 3, "6_months": sessions_per_month * 6, "12_months": sessions_per_year}
    rows = []
    for symbols in (20, 50):
        for frequency, observations_per_session, bytes_per_event, basis in (
            ("1m", minutes_per_session, bar_bytes, "ESTIMATED: 100 compressed-columnar bytes per normalized bar"),
            ("5m", minutes_per_session / 5, bar_bytes, "ESTIMATED: derived bar, same normalized row budget"),
            ("15m", minutes_per_session / 15, bar_bytes, "ESTIMATED: derived bar, same normalized row budget"),
            ("raw_BBO", minutes_per_session * 5, bbo_bytes, "ESTIMATED: 5 BBO events/minute; 10 levels observed, raw JSON-like payload"),
            ("normalized_BBO", minutes_per_session * 5, 500, "ESTIMATED: normalized 20-row depth snapshot"),
        ):
            for scenario, multiplier in (("LOW", 0.5), ("BASE", 1.0), ("HIGH", 2.0)):
                for duration, sessions in durations.items():
                    effective_observations = observations_per_session * (multiplier if frequency in {"raw_BBO", "normalized_BBO"} else 1.0)
                    total_events = symbols * effective_observations * sessions
                    rows.append({"symbols": symbols, "frequency": frequency, "scenario": scenario, "duration": duration, "events": int(total_events), "estimated_bytes": int(total_events * bytes_per_event), "basis": basis, "status": "ESTIMATED"})
    path = ROOT / "reports/settrade_storage_estimate.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (ROOT / "reports/settrade_storage_estimate.json").write_text(json.dumps({"status": "ESTIMATED", "scenarios": ["LOW", "BASE", "HIGH"], "assumptions": {"sessions_per_month": sessions_per_month, "sessions_per_year": sessions_per_year, "minutes_per_session": minutes_per_session, "normalized_bar_bytes": bar_bytes, "raw_bbo_bytes": bbo_bytes, "bbo_events_per_minute": 5, "event_rate_measurement": "NOT_MEASURED_THIS_RUN"}, "rows": rows}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

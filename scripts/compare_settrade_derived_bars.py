"""Bounded direct-vs-derived Settrade bar comparison."""
from __future__ import annotations
import csv, sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade import SettradeClient, SettradeConfig, normalize_candlestick
from src.data.settrade.retry import call_with_retries


def main() -> int:
    symbols = ["ADVANC", "BDMS", "PTT", "SCB", "TRUE"]
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3); client.authenticate()
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        one = call_with_retries(lambda: client.candlestick(symbol, "1m", limit=100), retries=2)
        source = normalize_candlestick(one, symbol, "1m", datetime.now(timezone.utc))
        by_time = {bar.timestamp: bar for bar in source}
        for minutes, interval in ((5, "5m"), (15, "15m")):
            direct = normalize_candlestick(call_with_retries(lambda interval=interval: client.candlestick(symbol, interval, limit=20), retries=2), symbol, interval, datetime.now(timezone.utc))
            derived_path = ROOT / "data/pilot/settrade/normalized" / f"bars_{minutes}m/data.csv"
            derived_rows = list(csv.DictReader(derived_path.open(encoding="utf-8"))) if derived_path.exists() else []
            derived = [row for row in derived_rows if row.get("symbol") == symbol]
            rows.append({"symbol": symbol, "interval": interval, "direct_rows": len(direct), "derived_rows_available": len(derived), "classification": "PENDING_ALIGNMENT" if direct and derived else "INSUFFICIENT_DATA", "note": "Bounded diagnostic; exact bucket alignment requires exchange-session calendar."})
    with (ROOT / "reports/settrade_direct_derived_comparison.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return 0


if __name__ == "__main__": raise SystemExit(main())

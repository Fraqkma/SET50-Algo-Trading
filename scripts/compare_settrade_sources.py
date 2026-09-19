"""Compare a tiny Settrade PTT sample with Yahoo staging and approved data."""
from __future__ import annotations

import csv
import sys
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade import SettradeClient, SettradeConfig


def main() -> int:
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3)
    client.authenticate()
    result = client.candlestick("PTT", "1d", limit=10, start="2026-01-01T00:00:00", end="2026-01-10T23:59:59")
    settrade = {}
    for index, epoch in enumerate(result.get("time", [])):
        date = datetime.fromtimestamp(epoch, tz=ZoneInfo("Asia/Bangkok")).date().isoformat()
        settrade[date] = {name: (result.get(name) or [None] * len(result.get("time", [])))[index] for name in ("open", "high", "low", "close", "volume")}
    yahoo_path = ROOT / "data/pilot/historical_daily/PTT_2010_2026.csv"
    approved_path = ROOT / "data/raw/market_data/PTT_BK.csv"
    yahoo = pd.read_csv(yahoo_path).set_index("Date")
    approved = pd.read_csv(approved_path).set_index("Date")
    rows = []
    for date, values in settrade.items():
        row = {"date": date, "settrade_status": "MATCHED", "yahoo_status": "MISSING", "approved_status": "MISSING"}
        for source, frame in (("yahoo", yahoo), ("approved", approved)):
            if date in frame.index:
                row[f"{source}_status"] = "PRESENT"
                for field, column in (("open", "Open"), ("high", "High"), ("low", "Low"), ("close", "Close"), ("volume", "Volume")):
                    left, right = float(values[field]), float(frame.loc[date, column])
                    row[f"{source}_{field}_difference"] = round(left - right, 8)
                differences = [row[f"{source}_{field}_difference"] for field in ("open", "high", "low", "close", "volume")]
                row[f"{source}_classification"] = "MATCH" if all(value == 0 for value in differences) else "MATERIAL_DIFFERENCE"
        rows.append(row)
    path = ROOT / "reports/settrade_source_comparison.csv"
    fields = sorted({key for row in rows for key in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

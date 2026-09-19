"""Bounded Settrade-vs-local volume comparison; never changes source data."""
from __future__ import annotations
import csv, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade import SettradeClient, SettradeConfig
from src.data.settrade.retry import call_with_retries


def main() -> int:
    symbols = [row["symbol"] for row in csv.DictReader((ROOT / "reports/current_set50_universe.csv").open(encoding="utf-8"))]
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3)
    client.authenticate()
    rows: list[dict[str, object]] = []
    for symbol in symbols:
        result = call_with_retries(lambda symbol=symbol: client.candlestick(symbol, "1d", limit=10, start="2026-01-05T00:00:00", end="2026-01-09T23:59:59"), retries=2)
        times = result.get("time") or []
        local_candidates = list((ROOT / "data/raw/market_data").glob(f"{symbol}_BK.csv")) + list((ROOT / "data/pilot/historical_daily").glob(f"{symbol}_2010_2026.csv"))
        frame = pd.read_csv(local_candidates[0]).set_index("Date") if local_candidates else None
        for index, epoch in enumerate(times):
            date = datetime.fromtimestamp(epoch, tz=ZoneInfo("Asia/Bangkok")).date().isoformat()
            source_volume = result.get("volume", [None] * len(times))[index]
            row: dict[str, object] = {"symbol": symbol, "date": date, "settrade_volume": source_volume, "settrade_value": (result.get("value", [None] * len(times))[index]), "local_status": "MISSING", "local_volume": None, "ratio_settrade_local": None, "classification": "NO_OVERLAP"}
            if frame is not None and date in frame.index and pd.notna(frame.loc[date, "Volume"]):
                local_volume = float(frame.loc[date, "Volume"])
                row.update(local_status="PRESENT", local_volume=local_volume)
                if local_volume:
                    ratio = float(source_volume) / local_volume if source_volume is not None else None
                    row.update(ratio_settrade_local=ratio, classification="RATIO_OBSERVED")
            rows.append(row)
    path = ROOT / "reports/settrade_volume_ratio_analysis.csv"
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0])); writer.writeheader(); writer.writerows(rows)
    return 0


if __name__ == "__main__": raise SystemExit(main())

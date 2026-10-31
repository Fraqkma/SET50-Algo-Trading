"""Generate the confirmed trading calendar for the canonical KGI period."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.competition.period import competition_calendar, load_competition_period


def main() -> None:
    calendar = competition_calendar(load_competition_period())
    calendar["generated_at"] = datetime.now(timezone.utc).isoformat()
    output = ROOT / "reports/competition_calendar.json"
    output.write_text(json.dumps(calendar, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(json.dumps({"output": str(output), "trading_day_count": calendar["trading_day_count"],
                      "trading_dates": [row["date"] for row in calendar["rows"] if row["status"] == "EXPECTED_TRADING_DAY"]}, indent=2))


if __name__ == "__main__":
    main()

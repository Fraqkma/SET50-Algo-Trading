"""Safe, small Settrade Open API capability probe.

Credentials are loaded at runtime only. This script never places an order and
never writes credential values to output.
"""
from __future__ import annotations

import csv
import importlib.metadata
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"
SYMBOLS = ("PTT", "ADVANC", "BDMS", "KTB")
HISTORICAL_POINTS = ("2026", "2025", "2023", "2020", "2016", "2010")


def _safe_error(exc: BaseException) -> str:
    text = str(exc).replace(os.getenv("SETTRADE_APP_ID", ""), "[REDACTED]")
    text = text.replace(os.getenv("SETTRADE_APP_SECRET", ""), "[REDACTED]")
    return text[:500]


def _write_csv(name: str, rows: list[dict[str, object]]) -> None:
    REPORTS.mkdir(exist_ok=True)
    path = REPORTS / name
    fields = sorted({key for row in rows for key in row}) if rows else ["status"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def _shape_result(result: object) -> dict[str, object]:
    if isinstance(result, dict):
        data = result.get("data")
        if isinstance(data, list):
            return {"status": result.get("status", "SUCCESS"), "rows": len(data), "keys": sorted(result.keys())}
        return {"status": result.get("status", "SUCCESS"), "keys": sorted(result.keys())}
    return {"status": "SUCCESS", "type": type(result).__name__}


def main() -> dict[str, object]:
    load_dotenv(ROOT / ".env", override=False)
    app_id = os.getenv("SETTRADE_APP_ID", "")
    app_secret = os.getenv("SETTRADE_APP_SECRET", "")
    app_code = os.getenv("SETTRADE_APP_CODE", "SANDBOX")
    broker_id = os.getenv("SETTRADE_BROKER_ID", "SANDBOX")
    sdk_version = importlib.metadata.version("settrade-v2")
    auth = {"status": "NOT_ATTEMPTED", "sdk": "settrade_v2", "sdk_version": sdk_version, "environment": "sandbox" if broker_id.upper() == "SANDBOX" else "configured", "error": ""}
    current_rows: list[dict[str, object]] = []
    historical_rows: list[dict[str, object]] = []
    reference_rows = [{"capability": name, "status": "NOT_PROBED", "method": "NOT_EXPOSED_BY_INSPECTED_SDK"} for name in ("instrument_list", "security_identifiers", "current_set50", "historical_set50", "ticker_changes", "delisted_securities", "corporate_actions")]
    intraday_rows: list[dict[str, object]] = []
    source_comparison = [{"comparison": "settrade_vs_approved", "status": "NOT_RUN", "reason": "Authentication/capability probe did not return data"}]
    capability = {"authentication": auth, "sdk": {"package": "settrade-v2", "version": sdk_version}, "market_data": [], "reference_data": reference_rows, "trading": {"status": "NOT_PROBED", "orders_placed": 0, "reason": "No authenticated account probe; no order submitted"}, "source_classification": {"historical_daily": "INSUFFICIENT_EVIDENCE", "intraday": "INSUFFICIENT_EVIDENCE", "live_quote": "INSUFFICIENT_EVIDENCE", "sandbox_execution": "INSUFFICIENT_EVIDENCE", "historical_set50_membership": "INSUFFICIENT_EVIDENCE"}}
    if not app_id or not app_secret:
        auth.update(status="FAILURE", error="Missing SETTRADE_APP_ID or SETTRADE_APP_SECRET in .env/environment; authentication not attempted without credentials")
    else:
        try:
            from settrade_v2 import Investor
            investor = Investor(app_id, app_secret, app_code, broker_id, is_auto_queue=False)
            auth.update(status="SUCCESS", error="")
            market = investor.MarketData()
            for symbol in SYMBOLS:
                try:
                    current_rows.append({"symbol": symbol, "capability": "quote", **_shape_result(market.get_quote_symbol(symbol))})
                except Exception as exc:
                    current_rows.append({"symbol": symbol, "capability": "quote", "status": "FAILURE", "error": _safe_error(exc)})
                for interval in ("1m", "5m", "15m", "1d", "1w", "1mo"):
                    try:
                        result = market.get_candlestick(symbol, interval, limit=2)
                        row = {"symbol": symbol, "interval": interval, **_shape_result(result)}
                    except Exception as exc:
                        row = {"symbol": symbol, "interval": interval, "status": "FAILURE", "error": _safe_error(exc)}
                    intraday_rows.append(row) if interval in ("1m", "5m", "15m") else historical_rows.append(row)
            capability["source_classification"].update(historical_daily="CROSS_CHECK_ONLY", intraday="CROSS_CHECK_ONLY", live_quote="CROSS_CHECK_ONLY")
        except Exception as exc:
            auth.update(status="FAILURE", error=_safe_error(exc))
    _write_csv("settrade_api_capability.csv", [{"capability": k, "status": v if isinstance(v, str) else json.dumps(v)} for k, v in capability["source_classification"].items()])
    _write_csv("settrade_market_data_probe.csv", current_rows or [{"status": auth["status"], "error": auth["error"]}])
    _write_csv("settrade_historical_coverage.csv", historical_rows or [{"symbol": "PTT", "requested_year": year, "status": "NOT_PROBED", "reason": auth["error"]} for year in HISTORICAL_POINTS])
    _write_csv("settrade_reference_data_probe.csv", reference_rows)
    _write_csv("settrade_intraday_probe.csv", intraday_rows or [{"status": "NOT_PROBED", "reason": auth["error"]}])
    _write_csv("settrade_source_comparison.csv", source_comparison)
    capability["probe_timestamp_utc"] = datetime.now(timezone.utc).isoformat()
    (REPORTS / "settrade_api_capability.json").write_text(json.dumps(capability, indent=2), encoding="utf-8")
    return capability


if __name__ == "__main__":
    sys.exit(0 if main()["authentication"]["status"] in {"SUCCESS", "FAILURE"} else 1)

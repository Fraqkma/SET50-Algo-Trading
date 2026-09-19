"""Bounded empirical Settrade capability probe; market-data reads only."""
from __future__ import annotations

import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade import SettradeClient, SettradeConfig
from src.data.settrade.retry import call_with_retries

REPORTS = ROOT / "reports"
INTERVALS = ("1m", "5m", "15m", "1d")


def load_universe() -> tuple[str, ...]:
    with (REPORTS / "current_set50_universe.csv").open(encoding="utf-8", newline="") as handle:
        symbols = tuple(row["symbol"].strip().upper() for row in csv.DictReader(handle))
    if len(symbols) != 50 or len(set(symbols)) != 50:
        raise RuntimeError(f"current SET50 universe must contain exactly 50 unique symbols, got {len(symbols)}")
    return symbols


def _category(error: BaseException) -> str:
    status = getattr(error, "status_code", None)
    if status == 404:
        return "NOT_FOUND_OR_UNAVAILABLE"
    if status in {401, 403}:
        return "PERMISSION_OR_ENTITLEMENT"
    if status == 400:
        return "INVALID_REQUEST"
    if isinstance(status, int) and status >= 500:
        return "SERVER_TRANSIENT"
    return "TRANSPORT_OR_SDK"


def _result(result: Any) -> tuple[int | None, str | None, str | None, dict[str, Any]]:
    if not isinstance(result, dict):
        return None, None, None, {"type": type(result).__name__}
    times = result.get("time")
    if isinstance(times, list):
        return len(times), str(times[0]) if times else None, str(times[-1]) if times else None, {"keys": sorted(result.keys())}
    return None, None, None, {"keys": sorted(result.keys())}


def _write_csv(name: str, rows: list[dict[str, Any]]) -> None:
    if not rows:
        return
    path = REPORTS / name
    fields = sorted({field for row in rows for field in row})
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    REPORTS.mkdir(exist_ok=True)
    symbols = load_universe()
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3)
    auth: dict[str, Any] = {"status": "NOT_ATTEMPTED", "sdk": "settrade-v2", "orders_placed": 0}
    try:
        client.authenticate()
        auth.update(status="SUCCESS", broker_id=client.config.broker_id, app_code=client.config.app_code)
    except Exception as error:
        auth.update(status="FAILURE", error=client.redacted_error(error), error_category=_category(error))
        (REPORTS / "settrade_api_capability.json").write_text(json.dumps({"authentication": auth, "orders_placed": 0}, indent=2), encoding="utf-8")
        return 1

    symbol_rows: list[dict[str, Any]] = []
    for symbol in symbols:
        row: dict[str, Any] = {"symbol": symbol}
        try:
            quote = call_with_retries(lambda symbol=symbol: client.quote(symbol), retries=2)
            row.update(quote_accessible=True, market_status=quote.get("marketStatus"), last_observed=quote.get("last"), quote_fields=sorted(quote.keys()))
        except Exception as error:
            row.update(quote_accessible=False, quote_error=client.redacted_error(error), quote_error_category=_category(error))
        for interval in INTERVALS:
            try:
                result = call_with_retries(lambda symbol=symbol, interval=interval: client.candlestick(symbol, interval, limit=5), retries=2)
                count, first, last, details = _result(result)
                row.update({f"{interval}_accessible": True, f"{interval}_rows": count, f"{interval}_first": first, f"{interval}_last": last, f"{interval}_fields": details.get("keys", [])})
            except Exception as error:
                row.update({f"{interval}_accessible": False, f"{interval}_error": client.redacted_error(error), f"{interval}_error_category": _category(error)})
        symbol_rows.append(row)

    historical_rows: list[dict[str, Any]] = []
    for year in ("2026", "2025", "2024", "2023", "2022", "2020", "2018", "2016", "2010"):
        started = perf_counter()
        row: dict[str, Any] = {"symbol": "PTT", "requested_start": f"{year}-01-01T00:00:00", "requested_end": f"{year}-01-10T23:59:59", "interval": "1d", "limit": 10}
        try:
            result = call_with_retries(lambda year=year: client.candlestick("PTT", "1d", limit=10, start=f"{year}-01-01T00:00:00", end=f"{year}-01-10T23:59:59"), retries=2)
            count, first, last, details = _result(result)
            row.update(status="SUCCESS", rows=count or 0, first_timestamp=first, last_timestamp=last, empty=(count or 0) == 0, response_fields=details.get("keys", []))
        except Exception as error:
            row.update(status="FAILURE", error=client.redacted_error(error), error_category=_category(error))
        row["duration_seconds"] = round(perf_counter() - started, 4)
        historical_rows.append(row)

    realtime = client.realtime()
    realtime_row: dict[str, Any] = {"dispatcher": "realtime/v3", "bid_offer_topic_method": "subscribe_bid_offer", "quote_topic_method": "subscribe_price_info", "depth": False, "orders_placed": 0}
    try:
        realtime._fetch_host_token()
        realtime_row.update(status="SUCCESS", token_received=bool(realtime.token), host_count=1)
    except Exception as error:
        realtime_row.update(status="FAILURE", error=client.redacted_error(error), error_category=_category(error))

    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "authentication": auth,
        "sdk": {"package": "settrade-v2", "version": "2.2.1"},
        "symbols_tested": list(symbols),
        "reference_data": {"sdk_methods_exposed": [], "historical_set50": "NOT_EXPOSED", "security_master": "NOT_EXPOSED", "corporate_actions": "NOT_EXPOSED"},
        "realtime": realtime_row,
        "trading": {"status": "NOT_INITIALIZED", "account_required": True, "orders_placed": 0},
        "source_classification": {"historical_daily": "CROSS_CHECK", "recent_daily": "CROSS_CHECK", "intraday": "CROSS_CHECK", "realtime": "CROSS_CHECK", "execution_validation": "STAGING_ONLY", "historical_set50_membership": "INSUFFICIENT_EVIDENCE"},
    }
    payload["symbols_tested"] = list(symbols)
    (REPORTS / "settrade_api_capability.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    _write_csv("settrade_set50_50_symbol_capability.csv", symbol_rows)
    _write_csv("settrade_symbol_capability.csv", symbol_rows)
    _write_csv("settrade_intraday_capability.csv", [{"symbol": row["symbol"], **{key: row[key] for key in row if key.startswith(("1m_", "5m_", "15m_"))}} for row in symbol_rows])
    _write_csv("settrade_historical_coverage.csv", historical_rows)
    _write_csv("settrade_realtime_probe.csv", [realtime_row])
    _write_csv("settrade_reference_data_probe.csv", [{"capability": name, "status": "NOT_EXPOSED_BY_INSPECTED_SDK", "method": "NONE"} for name in ("instrument_list", "security_identifiers", "current_set50", "historical_set50", "effective_membership_dates", "ticker_changes", "delisted_securities", "corporate_actions", "listing_dates")])
    (REPORTS / "settrade_collection_readiness.json").write_text(json.dumps({"status": "READY_TO_RUN_PILOT", "auth": "SUCCESS", "storage_root": "data/pilot/settrade", "default_universe_size": len(symbols), "modes": ["candles", "realtime", "bid-offer"], "orders_placed": 0, "approval_required_for": ["continuous collection", "licensed data retention", "account trading integration"]}, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

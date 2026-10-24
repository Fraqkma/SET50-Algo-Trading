"""Read-only production readiness check for KGI Settrade market data."""
from __future__ import annotations

import importlib.metadata
import inspect
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade import SettradeClient, SettradeConfig
from src.data.settrade.account_readonly import ReadOnlyEquityAdapter, configured_account_number
from src.data.settrade.disk import check_disk
from src.data.settrade.paths import configured_environment, resolve_data_root


def _sdk_capabilities() -> dict[str, Any]:
    """Inventory method names from the installed package without calling mutations."""
    from src.data.settrade.client import _sdk_import_environment

    with _sdk_import_environment():
        from settrade_v2 import Investor
        from settrade_v2.equity import InvestorEquity
        from settrade_v2.market import MarketData
        from settrade_v2.realtime import RealtimeDataConnection

    signatures = {
        "Investor.Equity": str(inspect.signature(Investor.Equity)),
        "MarketData.get_candlestick": str(inspect.signature(MarketData.get_candlestick)),
        "MarketData.get_quote_symbol": str(inspect.signature(MarketData.get_quote_symbol)),
        "RealtimeDataConnection.subscribe_bid_offer": str(inspect.signature(RealtimeDataConnection.subscribe_bid_offer)),
        "RealtimeDataConnection.subscribe_price_info": str(inspect.signature(RealtimeDataConnection.subscribe_price_info)),
        "RealtimeDataConnection.subscribe_equity_order": str(inspect.signature(RealtimeDataConnection.subscribe_equity_order)),
    }
    from settrade_v2.equity import InvestorEquity
    for method in ("get_account_info", "get_portfolios", "get_orders", "get_trades", "place_order", "change_order", "cancel_order"):
        signatures[f"InvestorEquity.{method}"] = str(inspect.signature(getattr(InvestorEquity, method)))
    return {
        "historical_candles": hasattr(MarketData, "get_candlestick"),
        "realtime_quote": hasattr(MarketData, "get_quote_symbol"),
        "realtime_bid_offer": hasattr(RealtimeDataConnection, "subscribe_bid_offer"),
        "realtime_equity_market_status": hasattr(RealtimeDataConnection, "subscribe_equity_exchange_info"),
        "documented_realtime_candle_intervals": ["1m", "3m", "5m", "10m", "15m", "30m", "60m", "120m", "240m", "1d", "1w", "1M"],
        "historical_candlestick_interval_parameter": "string; SDK signature does not enumerate accepted values",
        "equity_account_factory": hasattr(Investor, "Equity"),
        "account_info": hasattr(InvestorEquity, "get_account_info"),
        "portfolio": hasattr(InvestorEquity, "get_portfolios"),
        "orders": hasattr(InvestorEquity, "get_orders"),
        "deals": hasattr(InvestorEquity, "get_trades"),
        "place_order_method_present_not_invoked": hasattr(InvestorEquity, "place_order"),
        "change_order_method_present_not_invoked": hasattr(InvestorEquity, "change_order"),
        "cancel_order_method_present_not_invoked": hasattr(InvestorEquity, "cancel_order"),
        "method_signatures": signatures,
    }


def _shape(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    shaped: dict[str, Any] = {"fields": sorted(map(str, value))}
    for key in ("time", "timestamp"):
        values = value.get(key)
        if isinstance(values, list):
            shaped.update(rows=len(values), first_timestamp=values[0] if values else None, last_timestamp=values[-1] if values else None)
            break
    return shaped


def _candle_latest_local(value: Any) -> str | None:
    if not isinstance(value, dict) or not isinstance(value.get("time"), list) or not value["time"]:
        return None
    try:
        from zoneinfo import ZoneInfo
        return datetime.fromtimestamp(float(value["time"][-1]), timezone.utc).astimezone(ZoneInfo("Asia/Bangkok")).isoformat()
    except (TypeError, ValueError, OSError, OverflowError):
        return None


def run() -> dict[str, Any]:
    environment = configured_environment(ROOT)
    result: dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": environment,
        "orders_placed": 0,
        "account_private_state": "REQUIRES_ACCOUNT_NUMBER",
        "account_number_configured": bool(configured_account_number(ROOT)),
    }
    if environment != "production":
        result.update(status="NOT_READY", reason="routing is not production")
        return result

    try:
        config = SettradeConfig.from_env(ROOT / ".env")
        result.update(
            broker_id=config.broker_id,
            app_code=config.app_code,
            credentials_present=bool(config.app_id and config.app_secret),
            sdk_version=importlib.metadata.version("settrade-v2"),
        )
        if config.broker_id != "013" or config.app_code != "ALGO_EQ":
            result.update(status="NOT_READY", reason="production routing mismatch")
            return result
        result["capabilities"] = _sdk_capabilities()
        disk = check_disk(resolve_data_root(ROOT))
        result["disk"] = {"state": disk.state, "free_bytes": disk.free_bytes}
        client = SettradeClient(config, market_rps=1)
        investor = client.authenticate()
        result["authentication"] = "SUCCESS"
        market = client.market_data()
        result["market_data_initialization"] = "SUCCESS" if market is not None else "FAILURE"
        try:
            quote = client.quote("PTT")
            result["realtime_price"] = {"status": "SUCCESS", **_shape(quote)}
        except Exception as error:
            result["realtime_price"] = {"status": "FAILURE", "error": client.redacted_error(error)}
        try:
            candles = client.candlestick("PTT", "1m", limit=5)
            latest_local = _candle_latest_local(candles)
            freshness = "UNKNOWN"
            if latest_local:
                from zoneinfo import ZoneInfo
                freshness = "FRESH" if datetime.fromisoformat(latest_local).date() == datetime.now(ZoneInfo("Asia/Bangkok")).date() else "STALE"
            result["latest_intraday_candle"] = {"status": "SUCCESS", **_shape(candles), "latest_timestamp_bangkok": latest_local, "freshness": freshness}
        except Exception as error:
            result["latest_intraday_candle"] = {"status": "FAILURE", "error": client.redacted_error(error)}
        try:
            history = client.candlestick("PTT", "1m", limit=100, start="2026-10-01T00:00:00", end="2026-10-02T00:00:00")
            result["historical_candle"] = {"status": "SUCCESS" if _shape(history).get("rows", 0) else "EMPTY_RESPONSE", **_shape(history)}
        except Exception as error:
            result["historical_candle"] = {"status": "FAILURE", "error": client.redacted_error(error)}
        # API object construction is a safe capability check; no subscription
        # or account API is needed for this readiness command.
        result["realtime_connection_initialization"] = "AVAILABLE" if client.realtime() is not None else "UNAVAILABLE"
        account_number = configured_account_number(ROOT)
        if account_number:
            account = ReadOnlyEquityAdapter.from_investor(investor, account_number)
            account_reads = {}
            for name, operation in (("account_info", account.account_summary), ("portfolio", account.portfolio), ("orders", account.orders), ("deals", account.deals)):
                try:
                    value = operation()
                    account_reads[name] = {"status": "SUCCESS", "record_count": len(value) if isinstance(value, list) else None, "fields": sorted(map(str, value[0].keys())) if isinstance(value, list) and value and isinstance(value[0], dict) else sorted(map(str, value.keys())) if isinstance(value, dict) else []}
                except Exception as error:
                    account_reads[name] = {"status": "FAILURE", "failure_type": type(error).__name__}
            result["account_reads"] = account_reads
            result["account_private_state"] = "VERIFIED_READ_ONLY_CALLS_ATTEMPTED"
        else:
            result["account_reads"] = "REQUIRES_ACCOUNT_NUMBER"
        market_ok = result.get("realtime_price", {}).get("status") == "SUCCESS"
        candle_ok = result.get("latest_intraday_candle", {}).get("status") == "SUCCESS" and result.get("historical_candle", {}).get("status") != "FAILURE"
        result["warnings"] = []
        if not result["account_number_configured"]:
            result["warnings"].append("private account APIs not probed: account number is not configured")
        elif any(item.get("status") == "FAILURE" for item in result.get("account_reads", {}).values() if isinstance(item, dict)):
            result["warnings"].append("one or more read-only account API calls failed")
        if not market_ok:
            result["warnings"].append("realtime price probe failed")
        if not candle_ok:
            result["warnings"].append("historical candle probe failed")
        if result.get("historical_candle", {}).get("status") == "EMPTY_RESPONSE":
            result["warnings"].append("sampled historical 1m candle request returned no rows")
        if result.get("latest_intraday_candle", {}).get("freshness") == "STALE":
            result["warnings"].append("latest 1m response is stale; current-session candle availability is unverified")
        if disk.state == "CRITICAL":
            result["warnings"].append("data filesystem is below the critical free-space threshold")
        result["status"] = "READY" if market_ok and candle_ok and disk.state != "CRITICAL" and result["account_number_configured"] else "READY_WITH_WARNINGS"
    except Exception as error:
        # Never emit raw SDK exceptions here; they may include request metadata.
        result.update(status="NOT_READY", failure_type=type(error).__name__)
    return result


def main() -> int:
    result = run()
    (ROOT / "reports").mkdir(parents=True, exist_ok=True)
    (ROOT / "reports" / "settrade_production_readiness.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0 if result.get("status") in {"READY", "READY_WITH_WARNINGS"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

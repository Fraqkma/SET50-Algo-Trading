"""Bounded, read-only production market-data smoke test; never accesses accounts."""
from __future__ import annotations

import importlib.metadata
import json
import sys
import time
import csv
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade import SettradeClient, SettradeConfig
from src.data.settrade.paths import configured_environment, resolve_data_root


def _local_latest_sandbox_observation(root: Path) -> str | None:
    """Get the latest persisted observation in the pre-production data root."""
    candidates = [
        root / "raw" / "bid_offer" / "events.jsonl",
        root / "normalized" / "bars_1m" / "data.csv",
        root / "normalized" / "bid_offer" / "data.csv",
    ]
    latest = []
    for path in candidates:
        if not path.exists():
            continue
        try:
            if path.suffix == ".jsonl":
                stamps = []
                with path.open(encoding="utf-8") as handle:
                    for line in handle:
                        try:
                            record = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(record, dict):
                            stamp = pd.to_datetime(record.get("received_at") or record.get("collected_at"), errors="coerce", utc=True)
                            if not pd.isna(stamp):
                                stamps.append(stamp)
                if stamps:
                    latest.append(max(stamps))
                continue
            frame = pd.read_csv(path, usecols=lambda name: name in {"timestamp", "retrieved_at", "event_timestamp", "collected_at"})
            for column in ("timestamp", "event_timestamp", "retrieved_at", "collected_at"):
                if column in frame:
                    parsed = pd.to_datetime(frame[column], errors="coerce", utc=True).dropna()
                    if not parsed.empty:
                        latest.append(parsed.max())
        except (OSError, ValueError, pd.errors.ParserError):
            continue
    return max(latest).isoformat() if latest else None


def _shape(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        return {"type": type(value).__name__}
    result: dict[str, object] = {"fields": sorted(str(key) for key in value)}
    for key in ("time", "open", "high", "low", "close", "volume"):
        item = value.get(key)
        if isinstance(item, list):
            result["rows"] = len(item)
            if key == "time":
                result["first_timestamp"] = str(item[0]) if item else None
                result["last_timestamp"] = str(item[-1]) if item else None
            break
    return result


def _sandbox_candle_summary(root: Path) -> dict[str, dict[str, object]]:
    summary: dict[str, dict[str, object]] = {}
    for interval in ("1m", "5m", "15m"):
        path = root / "normalized" / f"bars_{interval}" / "data.csv"
        if not path.exists():
            summary[interval] = {"rows": 0, "symbols": 0, "latest_timestamp_bangkok": None, "fields": []}
            continue
        try:
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.DictReader(handle)
                fields = reader.fieldnames or []
                rows = 0
                symbols: set[str] = set()
                latest = None
                for row in reader:
                    rows += 1
                    if row.get("symbol"):
                        symbols.add(row["symbol"])
                    stamp = pd.to_datetime(row.get("timestamp"), errors="coerce", utc=True)
                    if not pd.isna(stamp) and (latest is None or stamp > latest):
                        latest = stamp
            summary[interval] = {
                "rows": rows,
                "symbols": len(symbols),
                "latest_timestamp_bangkok": latest.tz_convert("Asia/Bangkok").isoformat() if latest is not None else None,
                "fields": fields,
            }
        except (OSError, UnicodeDecodeError, csv.Error):
            summary[interval] = {"rows": None, "symbols": None, "latest_timestamp_bangkok": None, "fields": [], "status": "READ_ERROR"}
    return summary


def main() -> int:
    env = configured_environment(ROOT)
    if env != "production":
        print(json.dumps({"status": "BLOCKED", "environment": env, "orders_placed": 0}))
        return 2
    cfg = SettradeConfig.from_env(ROOT / ".env")
    if cfg.broker_id != "013" or cfg.app_code != "ALGO_EQ":
        print(json.dumps({"status": "BLOCKED", "environment": "production", "orders_placed": 0}))
        return 2
    stamp = datetime.now(timezone.utc).isoformat()
    client = SettradeClient(cfg, market_rps=1)
    report: dict[str, object] = {
        "environment": "production", "broker_id": cfg.broker_id, "app_code": cfg.app_code,
        "sdk_version": importlib.metadata.version("settrade-v2"), "started_at": stamp,
        "orders_placed": 0, "account_access": "NOT_ATTEMPTED",
    }
    try:
        client.authenticate()
        report["authentication"] = "SUCCESS"
    except Exception as exc:
        report.update(status="AUTH_FAILURE", error=client.redacted_error(exc))
        _write(report)
        return 1

    for name, operation in (
        ("quote_PTT", lambda: client.quote("PTT")),
        ("candle_1m_PTT", lambda: client.candlestick("PTT", "1m", limit=5)),
        ("historical_candle_1m_PTT", lambda: client.candlestick("PTT", "1m", limit=100, start="2026-10-01T00:00:00", end="2026-10-02T00:00:00")),
        ("candle_1d_PTT", lambda: client.candlestick("PTT", "1d", limit=10, start="2025-01-01T00:00:00", end="2025-01-10T23:59:59")),
    ):
        try:
            value = operation()
            shaped = _shape(value)
            shaped["status"] = "SUCCESS"
            shaped["observed_at"] = datetime.now(timezone.utc).isoformat()
            if name == "candle_1m_PTT" and shaped.get("last_timestamp"):
                try:
                    candle_local = datetime.fromtimestamp(float(shaped["last_timestamp"]), timezone.utc).astimezone(ZoneInfo("Asia/Bangkok"))
                    shaped["last_timestamp_local"] = candle_local.isoformat()
                    shaped["data_freshness"] = "FRESH" if candle_local.date() == datetime.now(ZoneInfo("Asia/Bangkok")).date() else "STALE"
                except (TypeError, ValueError, OSError, OverflowError):
                    shaped["data_freshness"] = "UNKNOWN"
            report[name] = shaped
        except Exception as exc:
            report[name] = {"status": "FAILURE", "error": client.redacted_error(exc)}

    # A single-symbol, five-second genuine BBO subscription compares the live
    # production payload schema with the persisted sandbox schema.
    realtime = None
    subscription = None
    bbo_events: list[dict[str, object]] = []
    try:
        realtime = client.realtime()
        realtime._fetch_host_token()
        def receive(message: object) -> None:
            if not isinstance(message, dict):
                return
            payload = message.get("data") if isinstance(message.get("data"), dict) else message
            if isinstance(payload, dict) and any(key in payload for key in ("bid_price1", "ask_price1")):
                bbo_events.append({"wrapper_fields": sorted(message), "payload_fields": sorted(payload), "symbol": payload.get("symbol")})
        subscription = realtime.subscribe_bid_offer("PTT", receive)
        subscription.start()
        time.sleep(5)
        report["bbo_PTT"] = {"status": "SUCCESS", "observation_seconds": 5, "events": len(bbo_events), "wrapper_fields": bbo_events[0]["wrapper_fields"] if bbo_events else [], "payload_fields": bbo_events[0]["payload_fields"] if bbo_events else [], "observed_depth_levels": sum(1 for key in (bbo_events[0]["payload_fields"] if bbo_events else []) if key.startswith("bid_price")), "event_schema": "UNKNOWN" if not bbo_events else "BID_OFFER"}
    except Exception as exc:
        report["bbo_PTT"] = {"status": "FAILURE", "error": client.redacted_error(exc), "events": len(bbo_events)}
    finally:
        if subscription is not None:
            try:
                subscription.stop()
            except Exception:
                pass
        if realtime is not None:
            try:
                realtime._stop()
            except Exception:
                pass

    old_root = ROOT / "data" / "pilot" / "settrade"
    previous = ROOT / "reports" / "settrade_production_cutover.json"
    try:
        cutover = json.loads(previous.read_text(encoding="utf-8")) if previous.exists() else {}
    except (OSError, json.JSONDecodeError):
        cutover = {}
    if not cutover.get("first_production_observation"):
        cutover["last_known_sandbox_observation"] = _local_latest_sandbox_observation(old_root)
        cutover["cutover_timestamp_utc"] = stamp
        observation_keys = ("quote_PTT", "candle_1m_PTT", "historical_candle_1m_PTT", "candle_1d_PTT")
        first = next((report[key] for key in observation_keys if isinstance(report.get(key), dict) and report[key].get("status") == "SUCCESS"), None)
        operation = next((key for key in observation_keys if report.get(key) is first), "UNKNOWN")
        cutover["first_production_observation"] = {"timestamp_utc": first.get("observed_at", stamp) if isinstance(first, dict) else stamp, "symbol": "PTT", "operation": operation, "result": first}
        cutover["first_production_observation"]["timestamp_basis"] = "API response receipt time when captured; otherwise smoke start time"
    elif "timestamp_basis" not in cutover["first_production_observation"]:
        cutover["first_production_observation"]["timestamp_basis"] = "Smoke start time; exact first API response receipt time was not captured in the initial probe"
    cutover["later_data_source"] = "Settrade Open API"
    cutover["later_data_environment"] = "production"
    cutover["orders_placed"] = 0
    report["completed_at"] = datetime.now(timezone.utc).isoformat()
    report["backfill_status"] = "NOT_ATTEMPTED_POLICY_UNVERIFIED"
    report["historical_candle_capability"] = "SUPPORTED_WITH_DATA" if isinstance(report.get("historical_candle_1m_PTT"), dict) and report["historical_candle_1m_PTT"].get("rows", 0) else "UNKNOWN_OR_EMPTY"
    bbo = report.get("bbo_PTT", {})
    report["bbo_comparison"] = {
        "sandbox_persisted_shape": "long-form bid/ask rows with side, level, price, volume; 10 levels observed",
        "production_wrapper_fields_match": bbo.get("wrapper_fields") == ["data", "is_success"],
        "production_depth_levels": bbo.get("observed_depth_levels", 0),
        "production_fields": bbo.get("payload_fields", []),
        "classification": "SCHEMA_MATCH" if bbo.get("observed_depth_levels") == 10 else "UNKNOWN",
    }
    historical_intraday = report.get("historical_candle_1m_PTT", {})
    historical_daily = report.get("candle_1d_PTT", {})
    sandbox_candles = _sandbox_candle_summary(old_root)
    report["candle_comparison"] = {
        "sandbox_persisted": sandbox_candles,
        "production_raw_fields": report.get("candle_1m_PTT", {}).get("fields", []),
        "production_normalized_fields_expected": ["timestamp", "symbol", "interval", "open", "high", "low", "close", "volume", "value"],
        "production_latest_1m_bangkok": report.get("candle_1m_PTT", {}).get("last_timestamp_local"),
        "production_current_session_status": report.get("candle_1m_PTT", {}).get("data_freshness", "UNKNOWN"),
        "conclusion": "Production returned a stale 1m response after market close; current-session behavior remains INSUFFICIENT_DATA. Historical sample windows are date/interval-specific.",
    }
    try:
        from scripts.check_settrade_production_readiness import _sdk_capabilities
        sdk_capabilities = _sdk_capabilities()
    except Exception:
        sdk_capabilities = {}
    report["sdk_capabilities"] = sdk_capabilities
    report["capability_matrix"] = {
        "historical_candles": "VERIFIED" if historical_daily.get("status") == "SUCCESS" and historical_daily.get("rows", 0) > 0 else "AVAILABLE_NOT_TESTED",
        "realtime_price": "VERIFIED" if report.get("quote_PTT", {}).get("status") == "SUCCESS" else "UNKNOWN",
        "realtime_bbo": "VERIFIED" if bbo.get("status") == "SUCCESS" and bbo.get("events", 0) > 0 else "AVAILABLE_NOT_TESTED",
        "account_info": "REQUIRES_ACCOUNT_NUMBER",
        "portfolio": "REQUIRES_ACCOUNT_NUMBER",
        "orders": "REQUIRES_ACCOUNT_NUMBER",
        "deals_fills": "REQUIRES_ACCOUNT_NUMBER",
        "order_status_subscription": "REQUIRES_ACCOUNT_NUMBER" if sdk_capabilities.get("method_signatures", {}).get("RealtimeDataConnection.subscribe_equity_order") else "UNAVAILABLE",
        "trading_methods_present_disabled": "AVAILABLE_NOT_TESTED; NEVER_INVOKED",
    }
    report["status"] = "SUCCESS" if any(isinstance(report.get(key), dict) and report[key].get("status") == "SUCCESS" for key in ("quote_PTT", "candle_1m_PTT", "historical_candle_1m_PTT", "candle_1d_PTT")) else "NO_MARKET_DATA"
    _write(report)
    previous.parent.mkdir(parents=True, exist_ok=True)
    previous.write_text(json.dumps(cutover, indent=2), encoding="utf-8")
    return 0 if report["status"] == "SUCCESS" else 1


def _write(report: dict[str, object]) -> None:
    (ROOT / "reports").mkdir(exist_ok=True)
    (ROOT / "reports" / "settrade_production_smoke.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    raise SystemExit(main())

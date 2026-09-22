"""Bounded, pilot-only Settrade collector.

Examples:
  .venv\\Scripts\\python.exe scripts/run_settrade_collector.py --mode candles --once
  .venv\\Scripts\\python.exe scripts/run_settrade_collector.py --mode bid-offer --duration-seconds 30

This script never constructs Investor.Equity(), never accepts account numbers,
and never calls an order method.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
import threading
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade import (
    PilotStorage,
    SettradeClient,
    SettradeConfig,
    aggregate_bars,
    normalize_candlestick,
    normalize_quote,
    validate_bar_records,
    validate_quote,
    require_disk,
    RotationScheduler,
)
from src.data.settrade.client import redact_error
from src.data.settrade.orderbook import normalize_bid_offer
from src.data.settrade.retry import call_with_retries

LOGGER = logging.getLogger("settrade_collector")
BAR_FIELDS = ["timestamp", "symbol", "interval", "open", "high", "low", "close", "volume", "turnover", "source", "retrieved_at", "timezone", "session", "adjustment_status"]
QUOTE_FIELDS = ["timestamp", "symbol", "last", "bid", "ask", "bid_size", "ask_size", "market_status", "source", "retrieved_at", "timezone"]
BBO_FIELDS = ["event_timestamp", "retrieved_at", "symbol", "side", "level", "price", "volume", "source", "collector_session_id", "rotation_group", "generation", "subscription_started_at"]


def candle_window(now: datetime | None = None) -> tuple[str, str]:
    """Return the current Bangkok calendar-day window in SDK format."""
    local = (now or datetime.now(timezone.utc)).astimezone(ZoneInfo("Asia/Bangkok"))
    start = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return start.strftime("%Y-%m-%dT%H:%M:%S"), (start + timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")


def load_config(path: Path, universe: str | None = None, custom_symbols: list[str] | None = None) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}
    selected = universe or config.get("universe", "approved_20")
    if selected == "custom":
        symbols = custom_symbols or config.get("custom")
    else:
        symbols = config.get(selected)
    if symbols is None and selected == "approved_20":
        symbols = config.get("symbols")
    if not isinstance(symbols, list) or not symbols or any(not isinstance(s, str) or not s.strip() for s in symbols):
        raise ValueError(f"config universe {selected!r} must be a non-empty list of strings")
    config["selected_universe"] = selected
    config["symbols"] = [str(symbol).strip().upper() for symbol in symbols]
    if selected == "current_set50" and (len(config["symbols"]) != 50 or len(set(config["symbols"])) != 50):
        raise ValueError("current_set50 must contain exactly 50 unique symbols")
    return config


def _record_dict(record: Any) -> dict[str, Any]:
    return {key: str(value) if isinstance(value, (datetime,)) else value for key, value in record.__dict__.items()}


def collect_candles(client: SettradeClient, storage: PilotStorage, symbols: list[str], limit: int, now: datetime | None = None) -> dict[str, Any]:
    summary: dict[str, Any] = {"status": "SUCCESS", "symbols": 0, "symbols_attempted": 0, "stale_symbols": [], "no_data_symbols": [], "latest_candle_timestamp": None, "rows_1m": 0, "rows_5m": 0, "rows_15m": 0, "validation_issues": 0}
    start, end = candle_window(now)
    expected_date = datetime.strptime(start, "%Y-%m-%dT%H:%M:%S").date()
    for symbol in symbols:
        require_disk(storage.root)
        retrieved = datetime.now(timezone.utc)
        raw = call_with_retries(lambda: client.candlestick(symbol, "1m", limit=limit, start=start, end=end))
        storage.append_jsonl("raw/candles/1m.jsonl", {"source": "settrade", "sdk": "settrade-v2", "retrieved_at": retrieved.isoformat(), "request_start": start, "request_end": end, "symbol": symbol, "interval": "1m", "response": raw})
        records = normalize_candlestick(raw, symbol, "1m", retrieved)
        issues = validate_bar_records(records)
        summary["validation_issues"] += len(issues)
        dedup = storage.append_csv_deduplicated("normalized/bars_1m/data.csv", (_record_dict(record) for record in records), BAR_FIELDS, ("symbol", "interval", "timestamp"))
        summary["duplicates"] = summary.get("duplicates", 0) + dedup["duplicates"]
        summary["conflicts"] = summary.get("conflicts", 0) + dedup["conflicts"]
        summary["rows_1m"] += len(records)
        for minutes, target in ((5, "bars_5m"), (15, "bars_15m")):
            aggregated = aggregate_bars(records, minutes)
            storage.append_csv_deduplicated(f"normalized/{target}/data.csv", ({**_record_dict(item.bar), "incomplete_bucket": item.incomplete_bucket, "observed_source_bars": item.observed_source_bars} for item in aggregated), BAR_FIELDS + ["incomplete_bucket", "observed_source_bars"], ("symbol", "interval", "timestamp"))
            summary[f"rows_{minutes}m"] += len(aggregated)
        latest = max((record.timestamp for record in records), default=None)
        if latest is not None and (summary["latest_candle_timestamp"] is None or latest.isoformat() > summary["latest_candle_timestamp"]):
            summary["latest_candle_timestamp"] = latest.isoformat()
        current_rows = [record for record in records if record.timestamp.astimezone(ZoneInfo("Asia/Bangkok")).date() == expected_date]
        status = "SUCCESS" if current_rows else ("STALE_RESPONSE" if records else "NO_DATA")
        if status != "SUCCESS":
            if status == "STALE_RESPONSE":
                summary["status"] = "STALE_RESPONSE"
            elif summary["status"] == "SUCCESS":
                summary["status"] = "NO_DATA"
            if status == "STALE_RESPONSE":
                summary["stale_symbols"].append(symbol)
            else:
                summary["no_data_symbols"].append(symbol)
        else:
            summary["symbols"] += 1
        summary["symbols_attempted"] += 1
        storage.write_checkpoint(f"candles_{symbol}", {"status": status, "expected_session_date": expected_date.isoformat(), "last_successful_authentication": retrieved.isoformat(), "last_candle_timestamp": latest.isoformat() if latest else None, "symbol": symbol, "rows": len(records), "current_session_rows": len(current_rows)})
        storage.write_checkpoint("candles", {"status": summary["status"], "expected_session_date": expected_date.isoformat(), "last_successful_authentication": retrieved.isoformat(), "last_candle_timestamp": summary["latest_candle_timestamp"], "symbols_attempted": summary["symbols_attempted"], "symbols_completed": summary["symbols"], "stale_symbols": list(summary["stale_symbols"]), "no_data_symbols": list(summary["no_data_symbols"])})
    return summary


def _bbo_payload(message: object) -> dict[str, Any] | None:
    if not isinstance(message, dict):
        return None
    payload = message.get("data") if isinstance(message.get("data"), dict) else message
    if not isinstance(payload, dict):
        return None
    # Only persist an actual SDK bid/offer payload.  Dispatcher acknowledgements
    # and subscription metadata are intentionally not treated as market events.
    if not any(key in payload for key in ("bid_price1", "ask_price1", "bid_volume1", "ask_volume1")):
        return None
    return dict(payload)


def collect_bid_offer(
    client: SettradeClient,
    storage: PilotStorage,
    symbols: list[str],
    max_topics: int,
    rotation_interval_seconds: int,
    duration_seconds: int,
    generation: int = 0,
) -> dict[str, Any]:
    """Collect genuine SDK callbacks for a bounded, rotating subscription run."""
    if duration_seconds < 1:
        raise ValueError("duration_seconds must be positive")
    rotation = RotationScheduler(symbols, max_topics=max_topics, interval_seconds=rotation_interval_seconds)
    realtime = client.realtime()
    realtime._fetch_host_token()
    metadata = rotation.metadata(generation, session_id=datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ"))
    events = 0
    events_by_symbol: dict[str, int] = {}
    write_lock = threading.Lock()
    subscriptions: list[Any] = []
    started = time.monotonic()

    group = rotation.group(generation)
    session_id = str(metadata["collector_session_id"])
    subscription_started_at = str(metadata["subscription_started_at"])

    def receive(message: object) -> None:
        nonlocal events
        payload = _bbo_payload(message)
        if payload is None:
            return
        symbol = str(payload.get("symbol") or payload.get("security_symbol") or "").upper()
        if not symbol:
            return
        received_at = datetime.now(timezone.utc).isoformat()
        record = {"source": "settrade", "sdk": "settrade-v2", "event_type": "bid_offer", "received_at": received_at, "symbol": symbol, "collector_session_id": session_id, "rotation_group": group.group_index, "generation": generation, "subscription_started_at": subscription_started_at, "payload": payload}
        with write_lock:
            storage.append_jsonl("raw/bid_offer/events.jsonl", record)
            storage.append_csv("normalized/bid_offer/data.csv", ({**row, "event_timestamp": payload.get("timestamp"), "retrieved_at": received_at, "source": "SETTRADE_BBO", "collector_session_id": session_id, "rotation_group": group.group_index, "generation": generation, "subscription_started_at": subscription_started_at} for row in normalize_bid_offer(payload)), BBO_FIELDS)
            events += 1
            events_by_symbol[symbol] = events_by_symbol.get(symbol, 0) + 1

    try:
        subscriptions = [realtime.subscribe_bid_offer(symbol, receive) for symbol in group.symbols]
        for subscription in subscriptions:
            subscription.start()
        while time.monotonic() - started < duration_seconds:
            time.sleep(min(0.25, max(0.01, duration_seconds - (time.monotonic() - started))))
    finally:
        for subscription in subscriptions:
            try:
                subscription.stop()
            except Exception:
                LOGGER.exception("failed to stop bid/offer subscription")
        realtime._stop()

    result = {"status": "SUCCESS", "dispatcher_token": bool(realtime.token), "events": events, "events_by_symbol": events_by_symbol, "symbols_requested": len(metadata["symbols"]), **metadata}
    storage.write_checkpoint("bid_offer", {"authenticated_at": datetime.now(timezone.utc).isoformat(), **result})
    return result


def collect_quotes(client: SettradeClient, storage: PilotStorage, symbols: list[str]) -> dict[str, int]:
    rows = 0
    for symbol in symbols:
        retrieved = datetime.now(timezone.utc)
        raw = call_with_retries(lambda: client.quote(symbol))
        storage.append_jsonl("raw/realtime/quotes.jsonl", {"source": "settrade", "sdk": "settrade-v2", "retrieved_at": retrieved.isoformat(), "symbol": symbol, "event_type": "quote", "payload": raw})
        quote = normalize_quote(raw, symbol, retrieved)
        storage.append_csv("normalized/quotes/data.csv", (_record_dict(quote),), QUOTE_FIELDS)
        rows += 1
        storage.write_checkpoint("quotes", {"last_successful_authentication": retrieved.isoformat(), "last_quote_symbol": symbol, "quote_rows": rows})
    return {"quote_rows": rows}


def run(args: argparse.Namespace) -> dict[str, Any]:
    custom_symbols = [item.strip().upper() for item in args.symbols.split(",") if item.strip()] if args.symbols else None
    config = load_config(ROOT / args.config, args.universe, custom_symbols)
    storage = PilotStorage(ROOT / config.get("storage_root", "data/pilot/settrade"))
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), float(config.get("market_rps", 3)))
    authenticated_at = datetime.now(timezone.utc)
    client.authenticate()
    symbols = config["symbols"]
    bbo_config = config.get("realtime", {})
    bbo_duration = args.duration_seconds if args.duration_seconds is not None else int(config.get("duration_seconds", 60))
    bbo_max_topics = int(bbo_config.get("bid_offer_topics_per_rotation", 35))
    bbo_interval = int(bbo_config.get("rotation_interval_seconds", 300))
    if args.mode == "candles":
        result = collect_candles(client, storage, symbols, int(config.get("candle_limit", 100)))
    elif args.mode == "realtime":
        result = collect_quotes(client, storage, symbols)
    elif args.mode == "bid-offer":
        result = collect_bid_offer(client, storage, symbols, bbo_max_topics, bbo_interval, bbo_duration, args.rotation_generation)
    elif args.mode == "combined":
        result = collect_candles(client, storage, symbols, int(config.get("candle_limit", 100)))
        result["realtime_rotation"] = collect_bid_offer(client, storage, symbols, bbo_max_topics, bbo_interval, bbo_duration, args.rotation_generation)
    else:
        raise ValueError(f"unsupported mode: {args.mode}")
    result["authenticated_at"] = authenticated_at.isoformat()
    result["orders_placed"] = 0
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/settrade_collection.yaml")
    parser.add_argument("--mode", choices=("candles", "realtime", "bid-offer", "combined"), default="candles")
    parser.add_argument("--universe", choices=("approved_20", "current_set50", "custom"), default=None)
    parser.add_argument("--symbols", default=None, help="comma-separated symbols for --universe custom")
    parser.add_argument("--once", action="store_true", help="bounded one-pass mode; retained for explicitness")
    parser.add_argument("--duration-seconds", type=int, default=None)
    parser.add_argument("--rotation-generation", type=int, default=0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        result = run(args)
    except Exception as error:
        result = {"status": "FAILURE", "error": redact_error(error), "orders_placed": 0}
    # stdout is the machine-readable protocol consumed by the daily runner.
    # Logging remains on stderr and must never be mixed into this payload.
    print(json.dumps(result, sort_keys=True))
    # NO_DATA is a valid, authenticated API response but is not a successful
    # collection.  Keep exit code 0 so the daily runner can continue BBO and
    # session lifecycle work while the machine-readable status exposes it.
    return 0 if result.get("status") in (None, "SUCCESS", "NO_DATA") else 1


if __name__ == "__main__":
    raise SystemExit(main())

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
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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
from src.data.settrade.retry import call_with_retries

LOGGER = logging.getLogger("settrade_collector")
BAR_FIELDS = ["timestamp", "symbol", "interval", "open", "high", "low", "close", "volume", "turnover", "source", "retrieved_at", "timezone", "session", "adjustment_status"]
QUOTE_FIELDS = ["timestamp", "symbol", "last", "bid", "ask", "bid_size", "ask_size", "market_status", "source", "retrieved_at", "timezone"]


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


def collect_candles(client: SettradeClient, storage: PilotStorage, symbols: list[str], limit: int) -> dict[str, int]:
    summary = {"symbols": 0, "rows_1m": 0, "rows_5m": 0, "rows_15m": 0, "validation_issues": 0}
    for symbol in symbols:
        require_disk(storage.root)
        retrieved = datetime.now(timezone.utc)
        raw = call_with_retries(lambda: client.candlestick(symbol, "1m", limit=limit))
        storage.append_jsonl("raw/candles/1m.jsonl", {"source": "settrade", "sdk": "settrade-v2", "retrieved_at": retrieved.isoformat(), "symbol": symbol, "interval": "1m", "response": raw})
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
        storage.write_checkpoint(f"candles_{symbol}", {"last_successful_authentication": retrieved.isoformat(), "last_candle_timestamp": records[-1].timestamp.isoformat() if records else None, "symbol": symbol, "rows": len(records)})
        storage.write_checkpoint("candles", {"last_successful_authentication": retrieved.isoformat(), "last_candle_timestamp": records[-1].timestamp.isoformat() if records else None, "symbols_completed": summary["symbols"] + 1})
        summary["symbols"] += 1
    return summary


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
    if args.mode == "candles":
        result = collect_candles(client, storage, symbols, int(config.get("candle_limit", 100)))
    elif args.mode == "realtime":
        result = collect_quotes(client, storage, symbols)
    elif args.mode == "bid-offer":
        realtime = client.realtime()
        rotation = RotationScheduler(symbols, max_topics=int(config.get("realtime", {}).get("bid_offer_topics_per_rotation", 35)), interval_seconds=int(config.get("realtime", {}).get("rotation_interval_seconds", 300)))
        metadata = rotation.metadata(0, session_id=authenticated_at.strftime("%Y%m%dT%H%M%S%fZ"))
        received = {"dispatcher_token": False, "events": 0, "symbols_requested": len(metadata["symbols"]), "note": "Subscriber is prepared only; no synthetic events are written.", **metadata}
        realtime._fetch_host_token()
        received["dispatcher_token"] = bool(realtime.token)
        storage.write_checkpoint("bid_offer", {"authenticated_at": authenticated_at.isoformat(), **received})
        result = received
    elif args.mode == "combined":
        result = collect_candles(client, storage, symbols, int(config.get("candle_limit", 100)))
        result["realtime_rotation"] = RotationScheduler(symbols, max_topics=int(config.get("realtime", {}).get("bid_offer_topics_per_rotation", 35)), interval_seconds=int(config.get("realtime", {}).get("rotation_interval_seconds", 300))).metadata(0, session_id=authenticated_at.strftime("%Y%m%dT%H%M%S%fZ"))
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
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    try:
        print(json.dumps(run(args), sort_keys=True))
    except Exception as error:
        print(json.dumps({"status": "FAILURE", "error": redact_error(error), "orders_placed": 0}))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

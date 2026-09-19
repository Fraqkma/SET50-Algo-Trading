"""Short empirical realtime topic probe; never starts an order/account stream."""
from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.settrade import SettradeClient, SettradeConfig
from src.data.settrade.orderbook import assess_orderbook, normalize_bid_offer


def main() -> int:
    client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3)
    client.authenticate()
    realtime = client.realtime()
    events: list[dict[str, object]] = []
    lock = Lock()

    def callback(kind: str):
        def receive(message: object) -> None:
            with lock:
                if len(events) >= 100:
                    return
                if isinstance(message, dict):
                    payload = message.get("data") if isinstance(message.get("data"), dict) else message
                    fields = sorted(payload.keys()) if isinstance(payload, dict) else sorted(message.keys())
                    sample = {key: payload[key] for key in fields if key in {"symbol", "timestamp", "last", "volume", "event_type", "sequence"} or key.startswith(("bid_price", "ask_price", "bid_volume", "ask_volume"))} if isinstance(payload, dict) else {}
                    events.append({"kind": kind, "wrapper_fields": sorted(message.keys()), "fields": fields, "sample": sample})
                else:
                    events.append({"kind": kind, "type": type(message).__name__})
        return receive

    subscriptions = []
    try:
        for symbol in ("PTT", "ADVANC"):
            subscriptions.append(realtime.subscribe_bid_offer(symbol, callback("bid_offer")))
            subscriptions.append(realtime.subscribe_price_info(symbol, callback("price_info")))
        for subscription in subscriptions:
            subscription.start()
        time.sleep(10)
    finally:
        for subscription in subscriptions:
            subscription.stop()
        realtime._stop()

    kinds = sorted({str(event["kind"]) for event in events})
    has_ten_levels = any("bid_price10" in event.get("fields", []) or "ask_price10" in event.get("fields", []) for event in events)
    result = {
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "symbols": ["PTT", "ADVANC"],
        "topics_requested": len(subscriptions),
        "events_received": len(events),
        "event_kinds": kinds,
        "events": events[:20],
        "bbo_or_depth": "DEPTH_10_LEVELS_OBSERVED" if has_ten_levels else "BBO_ONLY",
        "orders_placed": 0,
    }
    (ROOT / "reports/settrade_realtime_schema.json").write_text(json.dumps(result, indent=2, default=str), encoding="utf-8")
    normalized = []
    quality = []
    for event in events:
        payload = event.get("sample")
        if event.get("kind") == "bid_offer" and isinstance(payload, dict):
            normalized.extend(normalize_bid_offer(payload))
            quality.append(assess_orderbook(payload))
    for row in normalized:
        for key, value in list(row.items()):
            if hasattr(value, "to_eng_string"):
                row[key] = value.to_eng_string()
    (ROOT / "reports/settrade_orderbook_normalized.json").write_text(json.dumps(normalized, indent=2), encoding="utf-8")
    (ROOT / "reports/settrade_orderbook_quality.json").write_text(json.dumps(quality, indent=2, default=str), encoding="utf-8")
    print(json.dumps({key: result[key] for key in ("topics_requested", "events_received", "event_kinds", "bbo_or_depth", "orders_placed")}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

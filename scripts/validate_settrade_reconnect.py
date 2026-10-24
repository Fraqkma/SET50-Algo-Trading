"""Produce deterministic mock reconnect evidence; never toggles network state."""
from __future__ import annotations

import json
import hashlib
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade.resilience import (  # noqa: E402
    CollectorState, CollectorStateTracker, classify_failure, retry_delay_seconds,
)


def run_mock_validation() -> dict:
    """Exercise failure/recovery transitions with a local injected transport error."""
    checkpoint_path = ROOT / "data" / "pilot" / "settrade" / "production" / "checkpoints" / "candles.json"
    checkpoint_before = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() if checkpoint_path.exists() else None
    tracker = CollectorStateTracker()
    tracker.transition(CollectorState.LIVE, "MOCK_TRANSPORT_CONNECTED")
    failure = ConnectionError("mock injected socket disconnect")
    failure_kind = classify_failure(failure).value
    tracker.transition(CollectorState.DEGRADED, failure_kind)
    tracker.transition(CollectorState.OFFLINE, "MOCK_CONNECTION_CLOSED")
    tracker.transition(CollectorState.RECONNECTING, "MOCK_RETRY")
    # Simulated handshake is local evidence only; no broker/network call occurs.
    subscriptions = ["BBO:ADVANC", "BBO:PTT", "PRICE:ADVANC", "PRICE:PTT"]
    restored = list(dict.fromkeys(subscriptions))
    tracker.transition(CollectorState.RECOVERED, "MOCK_SUBSCRIPTIONS_RESTORED")
    tracker.transition(CollectorState.LIVE, "MOCK_CANDLES_AND_BBO_RESUMED")
    checkpoint_after = hashlib.sha256(checkpoint_path.read_bytes()).hexdigest() if checkpoint_path.exists() else None
    now = datetime.now(timezone.utc).isoformat()
    return {
        "generated_at": now, "validation_type": "MOCK",
        "live_network_interruption": "NOT_OBSERVED",
        "live_network_interruption_code": "LIVE_NETWORK_INTERRUPTION_NOT_OBSERVED",
        "transitions": tracker.transitions, "attempts": 1, "duration_seconds": 0.0,
        "failure_kind": failure_kind, "retry_backoff_seconds": retry_delay_seconds(1),
        "configured_subscriptions": subscriptions, "restored_subscriptions": restored,
        "subscription_restoration": restored == subscriptions,
        "checkpoint_continuity": {"path": str(checkpoint_path.relative_to(ROOT)),
                                  "present": checkpoint_before is not None,
                                  "sha256_before": checkpoint_before, "sha256_after": checkpoint_after,
                                  "unchanged": checkpoint_before == checkpoint_after},
        "post_reconnect_timestamps": {"mock_bbo": now, "mock_candle": now},
        "duplicate_result": {"subscription_keys_unique": len(restored) == len(set(restored)),
                              "persisted_rows_created": 0},
        "warnings": ["MOCK_ONLY_NO_LIVE_NETWORK_OR_BROKER_CALLS", "LIVE_NETWORK_INTERRUPTION_NOT_OBSERVED"],
        "orders_placed": 0,
    }


def main() -> int:
    report = run_mock_validation()
    path = ROOT / "reports" / "settrade_reconnect_validation.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

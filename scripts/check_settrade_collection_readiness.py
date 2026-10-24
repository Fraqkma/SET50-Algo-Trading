"""Readiness gate for safe Settrade pilot collection."""
from __future__ import annotations
import csv, json, shutil, sys
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade import RotationScheduler, SettradeClient, SettradeConfig, check_disk
from src.data.settrade.paths import resolve_data_root
from scripts.run_settrade_collector import load_config


def main() -> int:
    reasons: list[str] = []
    try:
        config = load_config(ROOT / "config/settrade_collection.yaml")
    except Exception as error:
        config = {}
        reasons.append(f"config: {error}")
    universe = list(csv.DictReader((ROOT / "reports/current_set50_universe.csv").open(encoding="utf-8"))) if (ROOT / "reports/current_set50_universe.csv").exists() else []
    if len(universe) != 50 or len({row["symbol"] for row in universe}) != 50:
        reasons.append("current universe is not exactly 50 unique rows")
    if config:
        rt = config.get("realtime", {})
        if int(rt.get("bid_offer_topics_per_rotation", 35)) > 35 or int(rt.get("max_topics", 40)) > 40:
            reasons.append("realtime topic configuration exceeds safety ceiling")
        try:
            rotation = RotationScheduler(config["symbols"], int(rt.get("bid_offer_topics_per_rotation", 35)), int(rt.get("rotation_interval_seconds", 300)))
            if max(map(len, rotation.groups)) > 35:
                reasons.append("rotation group exceeds 35 topics")
        except Exception as error:
            reasons.append(f"rotation: {error}")
    limits = config.get("disk", {})
    disk = check_disk(resolve_data_root(ROOT, config.get("storage_root", "data/pilot/settrade")), float(limits.get("warning_gb", 10)), float(limits.get("critical_gb", 5)))
    if disk.state == "CRITICAL": reasons.append("disk below critical threshold")
    auth = "NOT_CHECKED"
    try:
        client = SettradeClient(SettradeConfig.from_env(ROOT / ".env"), market_rps=3)
        client.authenticate()
        auth = "SUCCESS"
    except Exception as error:
        auth = "FAILURE"
        reasons.append(f"authentication: {client.redacted_error(error) if 'client' in locals() else type(error).__name__}")
    result = {"status": "READY" if not reasons and auth == "SUCCESS" else "NOT_READY", "authentication": auth, "universe_rows": len(universe), "disk_state": disk.state, "free_bytes": disk.free_bytes, "reasons": reasons, "orders_placed": 0}
    print(json.dumps(result, indent=2))
    return 0 if result["status"] == "READY" else 1


if __name__ == "__main__": raise SystemExit(main())

"""Report pilot collector checkpoints without loading credentials."""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.settrade.health import collect_health
from src.data.settrade.paths import resolve_data_root


def main() -> int:
    config = yaml.safe_load((ROOT / "config/settrade_collection.yaml").read_text(encoding="utf-8")) or {}
    data_root = resolve_data_root(ROOT, config.get("storage_root", "data/pilot/settrade"))
    checkpoint_dir = data_root / "checkpoints"
    result: dict[str, object] = {"source": "settrade", "checkpoint_dir": str(checkpoint_dir), "checkpoints": {}, **collect_health(ROOT, data_root)}
    for path in sorted(checkpoint_dir.glob("*.json")) if checkpoint_dir.exists() else []:
        data = json.loads(path.read_text(encoding="utf-8"))
        result["checkpoints"][path.stem] = {key: value for key, value in data.items() if "token" not in key.lower() and "secret" not in key.lower() and "app" not in key.lower()}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("filesystem_error") is None else 1


if __name__ == "__main__":
    raise SystemExit(main())

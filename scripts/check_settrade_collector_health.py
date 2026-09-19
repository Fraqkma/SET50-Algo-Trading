"""Report pilot collector checkpoints without loading credentials."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    checkpoint_dir = ROOT / "data/pilot/settrade/checkpoints"
    result: dict[str, object] = {"source": "settrade", "checkpoint_dir": str(checkpoint_dir.relative_to(ROOT)), "checkpoints": {}}
    for path in sorted(checkpoint_dir.glob("*.json")) if checkpoint_dir.exists() else []:
        data = json.loads(path.read_text(encoding="utf-8"))
        result["checkpoints"][path.stem] = {key: value for key, value in data.items() if "token" not in key.lower() and "secret" not in key.lower() and "app" not in key.lower()}
    result["checked_at"] = datetime.now(timezone.utc).isoformat()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

import json
from pathlib import Path


def test_settrade_probe_artifacts_contain_no_credentials():
    root = Path(__file__).resolve().parents[1]
    report = json.loads((root / "reports/settrade_api_capability.json").read_text(encoding="utf-8"))
    assert report["authentication"]["status"] in {"SUCCESS", "FAILURE"}
    serialized = json.dumps(report)
    assert "SETTRADE_APP_SECRET=" not in serialized
    assert "SETTRADE_APP_ID=" not in serialized
    assert report["trading"]["orders_placed"] == 0

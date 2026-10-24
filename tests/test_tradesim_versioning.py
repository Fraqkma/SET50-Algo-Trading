from __future__ import annotations

import zipfile

import pytest

from src.competition.tradesim_bridge.versioning import (
    _compare_archives, compatibility_status, discover_archives, extract_side_by_side,
    safe_extraction_target,
)


def _zip(path, files):
    with zipfile.ZipFile(path, "w") as bundle:
        for name, content in files.items():
            bundle.writestr(name, content)


def test_discovery_hashes_and_inspects_without_extracting(tmp_path):
    archive = tmp_path / "tradeSim0.3.0.zip"
    _zip(archive, {"tradeSim0.3.0/tradeSim/TradeSim.py": "class TradeSim: pass"})
    before = list(tmp_path.iterdir())
    found = discover_archives(tmp_path)
    assert found[0]["version"] == "0.3.0"
    assert len(found[0]["sha256"]) == 64
    assert list(tmp_path.iterdir()) == before
    assert compatibility_status("0.3.0") == "NEEDS_ADAPTER_UPDATE"
    assert compatibility_status("0.2.6") == "SUPPORTED_WITH_WARNINGS"
    assert compatibility_status(None) == "BLOCKED"


def test_side_by_side_extraction_refuses_overwrite_and_traversal(tmp_path):
    target = safe_extraction_target(tmp_path, "0.3.0")
    archive = tmp_path / "tradesim0.3.0.zip"
    _zip(archive, {"package/readme.txt": "ok"})
    assert extract_side_by_side(archive, target) == target
    with pytest.raises(FileExistsError):
        extract_side_by_side(archive, target)
    unsafe = tmp_path / "tradesim0.3.1.zip"
    _zip(unsafe, {"../outside.txt": "bad"})
    with pytest.raises(ValueError, match="Unsafe"):
        extract_side_by_side(unsafe, tmp_path / "new-runtime")


def test_archive_comparison_identifies_changed_requirements_and_execution_api(tmp_path):
    baseline = tmp_path / "tradeSim0.2.5.zip"
    future = tmp_path / "tradeSim0.3.0.zip"
    _zip(baseline, {"requirements.txt": "pandas==1\n", "TradingSimulation.ipynb": "old",
                    "tradeSim/Execution.py": "def place_order(): pass\n", "tradeSim/CommissionService.py": "fee=1"})
    _zip(future, {"package/requirements.txt": "pandas==2\n", "package/TradingSimulation.ipynb": "new",
                  "package/tradeSim/Execution.py": "def submit_order(): pass\n",
                  "package/tradeSim/CommissionService.py": "fee=1"})
    result = _compare_archives(baseline, future)
    assert result["requirements"]["status"] == "CHANGED"
    assert result["category_status"]["order_apis"] == "CHANGED"
    assert result["category_status"]["fees"] == "UNCHANGED"
    assert result["category_status"]["notebook_workflow"] == "CHANGED"


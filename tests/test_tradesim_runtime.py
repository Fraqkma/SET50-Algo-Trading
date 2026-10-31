import pytest

from src.competition.tradesim_bridge.runtime import (
    RuntimeErrorDetail,
    discover_python3130,
    inventory_ticks,
    inspect_archive,
    notebook_flow,
    runtime_diagnostic,
)


def test_local_archive_is_intact_official_027():
    info = inspect_archive()
    assert info["filename"] == "tradeSim0.2.7.zip"
    assert info["version"] == "0.2.7"
    assert info["integrity"] == "PASS"
    assert info["required_missing"] == []
    assert info["has_practice_ticks"]
    assert len(info["sha256"]) == 64
    assert info["practice_tick_file_count"] == 16


def test_notebook_flow_exposes_simulator_stages():
    sources = "\n".join(cell["source"] for cell in notebook_flow())
    for fragment in ("pd.read_csv", "TradeSim.tradeSim", "StrategyHandler.StrategyHandler",
                     "with_visual", "process_row", "isMatch", "save_summary_csv",
                     "save_portfolio", "trading_days"):
        assert fragment in sources


def test_runtime_root_prefers_extracted_organizer_version(tmp_path):
    from src.competition.tradesim_bridge.runtime import runtime_root

    expected = tmp_path / "tools" / "kgi_tradesim" / "0.2.6" / "tradeSim" / "TradeSim.py"
    expected.parent.mkdir(parents=True)
    expected.touch()
    assert runtime_root(tmp_path) == expected.parents[1]


def test_runtime_discovery_refuses_non_3130(monkeypatch):
    import shutil
    import subprocess
    from pathlib import Path

    monkeypatch.setattr(shutil, "which", lambda _: "py.exe")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: type("Result", (), {
        "returncode": 0, "stdout": "C:/Python313/python.exe\n3.13.16\n"})())
    monkeypatch.setattr(Path, "is_file", lambda _self: False)
    try:
        discover_python3130()
    except RuntimeErrorDetail as exc:
        assert "exact version" in str(exc)
    else:
        raise AssertionError("a different Python patch release must be rejected")


def test_check_reports_missing_exact_runtime_without_substitution(tmp_path, monkeypatch):
    import zipfile
    from pathlib import Path
    from src.competition.tradesim_bridge import runtime

    archive = tmp_path / "tradeSim0.2.5.zip"
    with zipfile.ZipFile(archive, "w") as output:
        output.writestr("requirements.txt", "pandas==2.3.1\n")
        output.writestr("TradingSimulation.ipynb", "{}")
        output.writestr("strategy/Strategies_template.py", "")
        output.writestr("strategy/Example_strategy.py", "")
        output.writestr("tradeSim/TradeSim.py", "")
        output.writestr("marketInfo/ticks/2026-09-09.csv", "")
    monkeypatch.setattr(runtime, "archive_path", lambda _root: archive)
    monkeypatch.setattr(runtime, "discover_python3130", lambda: (_ for _ in ()).throw(
        RuntimeErrorDetail("exact Python missing")))
    report = runtime_diagnostic(tmp_path)
    assert report["status"] == "BLOCKED"
    assert report["python"]["status"] == "MISSING_EXACT_VERSION"
    assert report["dependencies"]["status"] == "NOT_CHECKED"
    assert report["practice_data"]["present"] is False


def test_tick_inventory_reports_missing_data_directory(tmp_path):
    with pytest.raises(RuntimeErrorDetail, match="tick directory is missing"):
        inventory_ticks(tmp_path)

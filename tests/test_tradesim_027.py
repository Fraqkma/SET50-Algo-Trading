from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from src.competition.tradesim_bridge.runtime import preferred_version, runtime_root, runtime_source_hash, RuntimeErrorDetail
from src.data.settrade.automation import lock_state, runner_status

ROOT = Path(__file__).resolve().parents[1]


def test_preference_requires_validation_for_exact_bytes(tmp_path):
    for version in ("0.2.6", "0.2.7"):
        path = tmp_path / "tools/kgi_tradesim" / version / "tradeSim/TradeSim.py"
        path.parent.mkdir(parents=True)
        path.write_text("# official source")
    archive = tmp_path / "tradeSim0.2.7.zip"
    archive.write_bytes(b"package identity fixture")
    assert preferred_version(tmp_path) == "0.2.6"
    report = tmp_path / "reports/tradesim_027_readiness.json"
    report.parent.mkdir()
    report.write_text(json.dumps({"runtime_validated": True,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "runtime_source_sha256": runtime_source_hash(runtime_root(tmp_path, "0.2.7"))}))
    assert preferred_version(tmp_path) == "0.2.7"
    (runtime_root(tmp_path, "0.2.7") / "tradeSim/tick_size.json").write_text("changed")
    assert preferred_version(tmp_path) == "0.2.6"
    with pytest.raises(RuntimeErrorDetail):
        runtime_root(tmp_path, "0.2.8")


def test_pid_reuse_and_unverifiable_owner_are_not_active(monkeypatch):
    from src.data.settrade import automation
    monkeypatch.setattr(automation, "_pid_alive", lambda _: True)
    monkeypatch.setattr(automation, "process_identity", lambda _: {"created": 200, "executable": "python"})
    assert lock_state({"pid": 42, "process_identity": {"created": 100, "executable": "python"}}) == "STALE_LOCK"
    assert lock_state({"pid": 42, "process_identity": {"created": 200, "executable": "python"}}) == "ACTIVE"
    monkeypatch.setattr(automation, "process_identity", lambda _: {"unknown": True})
    assert lock_state({"pid": 42}) == "UNVERIFIABLE"


def test_runner_distinguishes_schedule_and_missing_or_corrupt_lock(tmp_path):
    path = tmp_path / "daily.lock"
    assert runner_status(path) == "NOT_RUNNING"
    assert runner_status(path, {"installed": True, "enabled": True}) == "SCHEDULED_WAITING"
    path.write_text("{")
    assert runner_status(path) == "ERROR"


def test_candle_coverage_uses_market_time_not_collection_time(tmp_path):
    from scripts.audit_settrade_production_coverage import _dataset_day_rows
    path = tmp_path / "data.csv"
    path.write_text("symbol,timestamp,retrieved_at\nPTT,2026-10-28T09:00:00+07:00,2026-10-29T01:00:00+07:00\n")
    days = _dataset_day_rows(tmp_path, "data.csv", "csv")
    assert list(days) == ["2026-10-28"]
    assert days["2026-10-28"][0]["timestamp"].startswith("2026-10-28T09:00")


def test_official_runtime_ioc_prices_volume_fifo_and_ladder(tmp_path):
    python = ROOT / ".venv-kgi313/Scripts/python.exe"
    if not python.exists() or not (ROOT / "tools/kgi_tradesim/0.2.7/tradeSim/TradeSim.py").exists():
        pytest.skip("Local organizer runtime not provisioned")
    output = tmp_path / "runtime-evidence"
    result = subprocess.run([str(python), str(ROOT / "scripts/validate_tradesim_027.py"), "--version", "0.2.7", "--output", str(output)], capture_output=True, text=True, timeout=60)
    assert result.returncode == 0, result.stderr
    report = json.loads((output / "matrix.json").read_text())
    assert report["all_checks_pass"]
    assert len(report["checks"]) >= 22
    partial = next(o for o in report["observed_orders"] if o["requested_quantity"] == 1000 and o["filled_quantity"] == 300)
    assert partial["canceled_quantity"] == 700
    assert partial["status"] == "PARTIALLY_FILLED_IOC_CANCELED"
    assert any("42.01" in r["rejection_reason"] for r in report["rejections"])


def test_bridge_normalizes_ioc_cancellation_without_phantom_lots(tmp_path):
    from src.competition.tradesim_bridge.core import OfficialRepo, normalize_result
    root = ROOT / "tools/kgi_tradesim/0.2.7"
    official = OfficialRepo(root, ROOT / ".venv-kgi313/Scripts/python.exe", "3.13.0", "fixture", False, "0.2.7")
    fill = {"Order Number": "one", "Symbol": "PTT", "Side": "Buy", "Volume": 300, "Price": 42.25,
            "Market Price": 42.0, "Type": "Limit", "Timestamp": "2026-10-28 10:00:00"}
    raw = {"transactions": [fill], "orders": [{"order_id": "one", "requested_quantity": 1000,
            "remaining_quantity": 700, "status": "PARTIALLY_FILLED_IOC_CANCELED", "validity": "IOC"}]}
    result = normalize_result(raw, "fixture", "fixture", ["2026-10-28"], "hash", ROOT, root, official, 0, tmp_path)
    assert result["orders"][0]["canceled_quantity"] == 700
    assert result["orders"][0]["remaining_quantity"] == 0
    assert result["partial_fill_count"] == 1
    assert result["fifo_roundtrips"][0]["quantity"] == 300
    assert result["slippage_cost"] == 75
    assert result["total_fees"] == pytest.approx(300 * 42.25 * 0.0016799)


def test_current_calendar_excludes_weekend():
    from scripts.build_weekend_maintenance_report import trading_dates_for_week
    assert trading_dates_for_week(["2026-10-23", "2026-10-24", "2026-10-25", "2026-10-26", "2026-10-27", "2026-10-28"], {"2026-10-23"}) == ["2026-10-26", "2026-10-27", "2026-10-28"]

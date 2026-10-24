import zipfile

from scripts.inspect_official_tradesim_data import extract_source_data, inspect_zip


def test_official_history_inventory_preserves_archive_provenance(tmp_path):
    archive_path = tmp_path / "tradeSim_history.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("marketInfo/daily_history/PTT.csv",
                         "Date,Open,High,Low,Close,Volume\n2026-10-20,30,31,29,30.5,1000\n")
    result = inspect_zip(archive_path)
    assert result["status"] == "PASS"
    assert result["source"] == "TRADESIM_OFFICIAL_HISTORY"
    assert result["sha256"]
    assert result["files"][0]["rows"] == 1
    assert result["files"][0]["schema"] == ["Date", "Open", "High", "Low", "Close", "Volume"]
    assert result["files"][0]["sha256"]


def test_source_extract_is_hash_keyed_and_never_overwrites(tmp_path, monkeypatch):
    from scripts import inspect_official_tradesim_data as adapter

    archive_path = tmp_path / "tradeSim_ticks.zip"
    with zipfile.ZipFile(archive_path, "w") as archive:
        archive.writestr("marketInfo/ticks/2026-10-01.csv", "TradeDateTime,ShareCode\n")
        archive.writestr("strategy/unsafe-to-merge.py", "")
    monkeypatch.setattr(adapter, "ROOT", tmp_path)
    destination = extract_source_data(archive_path)
    assert "tradesim_official_ticks" in str(destination)
    assert (destination / "marketInfo" / "ticks" / "2026-10-01.csv").is_file()
    assert not (destination / "strategy").exists()
    try:
        extract_source_data(archive_path)
    except FileExistsError:
        pass
    else:
        raise AssertionError("extraction must refuse to overwrite identical archive data")


def test_daily_ticks_outer_archive_preserves_nested_archives_and_standalone_csvs(tmp_path):
    from scripts.ingest_official_daily_ticks import extract_package, sha256_file

    nested_history = tmp_path / "history.zip"
    nested_ticks = tmp_path / "ticks.zip"
    with zipfile.ZipFile(nested_history, "w") as archive:
        archive.writestr("marketInfo/daily_history/PTT.csv", "Date,Open,High,Low,Close,Volume\n2026-10-01,1,1,1,1,1\n")
    with zipfile.ZipFile(nested_ticks, "w") as archive:
        archive.writestr("marketInfo/ticks/2026-10-01.csv", "ShareCode,TradeDateTime,LastPrice,Volume\nPTT,2026-10-01 10:00:00,1,1\n")
    outer = tmp_path / "Daily_Ticks.zip"
    with zipfile.ZipFile(outer, "w") as archive:
        archive.write(nested_history, "Daily_Ticks/history/tradeSim_history.zip")
        archive.write(nested_ticks, "Daily_Ticks/history/tradeSim_ticks.zip")
        archive.writestr("Daily_Ticks/2026-10-01.csv", "ShareCode,TradeDateTime,LastPrice,Volume\nPTT,2026-10-01 10:00:00,1,1\n")
    destination = tmp_path / "official"
    result = extract_package(outer, destination)
    assert result["outer_archive"]["sha256"] == sha256_file(outer)
    assert set(result["nested_archives"]) == {"tradeSim_history.zip", "tradeSim_ticks.zip"}
    assert (destination / "archives" / "Daily_Ticks.zip").read_bytes() == outer.read_bytes()
    assert (destination / "daily_ticks" / "2026-10-01.csv").is_file()
    assert (destination / "history" / "daily_history" / "PTT.csv").is_file()
    assert (destination / "ticks" / "ticks" / "2026-10-01.csv").is_file()
    second = extract_package(outer, destination)
    assert second["outer_archive"]["sha256"] == result["outer_archive"]["sha256"]


def test_package_extraction_rejects_traversal(tmp_path):
    from scripts.ingest_official_daily_ticks import extract_package

    outer = tmp_path / "Daily_Ticks.zip"
    with zipfile.ZipFile(outer, "w") as archive:
        archive.writestr("Daily_Ticks/../escape.csv", "unsafe")
    try:
        extract_package(outer, tmp_path / "official")
    except ValueError as exc:
        assert "Unsafe ZIP member path" in str(exc)
    else:
        raise AssertionError("ZIP traversal must be rejected")


def test_official_loaders_filter_without_resorting_and_retain_provenance(tmp_path):
    from src.competition.official_data import load_official_history, load_official_ticks

    history = tmp_path / "history" / "daily_history"
    history.mkdir(parents=True)
    (history / "PTT.csv").write_text(
        "Date,Open,High,Low,Close,Volume\n2026-10-01,1,2,0.5,1.5,10\n", encoding="utf-8"
    )
    ticks = tmp_path / "ticks" / "ticks"
    ticks.mkdir(parents=True)
    (ticks / "2026-10-01.csv").write_text(
        "ShareCode,TradeDateTime,LastPrice,Volume,Flag\n"
        "PTT,2026-10-01 10:00:01.000,1.1,5,A\n"
        "AOT,2026-10-01 10:00:02.000,2.0,10,B\n"
        "PTT,2026-10-01 10:00:00.000,1.0,2,C\n", encoding="utf-8"
    )
    bars = load_official_history("ptt", root=tmp_path)
    assert bars.iloc[0]["source"] == "TRADESIM_OFFICIAL_HISTORY"
    assert str(bars.iloc[0]["timestamp"].tz) == "Asia/Bangkok"
    assert bool(bars.iloc[0]["ohlc_valid"])
    frame = load_official_ticks(trading_date="2026-10-01", symbols=["PTT"], root=tmp_path)
    assert frame["tick_sequence"].tolist() == [0, 2]
    assert frame["price"].tolist() == [1.1, 1.0]
    assert frame["source"].eq("TRADESIM_OFFICIAL_TICKS").all()
    assert frame["timestamp"].is_monotonic_decreasing


def test_official_runtime_copy_uses_only_selected_official_ticks(tmp_path, monkeypatch):
    from src.competition.tradesim_bridge import core

    runtime = tmp_path / "runtime_source" / "0.2.6"
    (runtime / "marketInfo" / "ticks").mkdir(parents=True)
    (runtime / "marketInfo" / "ticks" / "2026-09-30.csv").write_text("practice", encoding="utf-8")
    (runtime / "tradeSim").mkdir()
    (runtime / "tradeSim" / "TradeSim.py").write_text("# official", encoding="utf-8")
    (runtime / "TradingSimulation.ipynb").write_text("{}", encoding="utf-8")
    data_root = tmp_path / "official"
    tick_dir = data_root / "ticks" / "ticks"
    tick_dir.mkdir(parents=True)
    (tick_dir / "2026-10-01.csv").write_text("official tick", encoding="utf-8")
    history_dir = data_root / "history" / "daily_history"
    history_dir.mkdir(parents=True)
    (history_dir / "PTT.csv").write_text("official history", encoding="utf-8")
    monkeypatch.setattr("src.competition.official_data.DEFAULT_ROOT", data_root)
    copy_path = tmp_path / "run" / "runtime"
    core.prepare_official_data_runtime(runtime, tmp_path, copy_path, ["2026-10-01"])
    assert (copy_path / "marketInfo" / "ticks" / "2026-10-01.csv").read_text() == "official tick"
    assert not (copy_path / "marketInfo" / "ticks" / "2026-09-30.csv").exists()
    assert (copy_path / "marketInfo" / "daily_history" / "PTT.csv").read_text() == "official history"


def test_official_history_and_source_comparison_reports_are_readable():
    import json
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    package = json.loads((root / "reports" / "tradesim_official_daily_ticks_package.json").read_text(encoding="utf-8"))
    comparison = json.loads((root / "reports" / "tradesim_vs_settrade_data_comparison.json").read_text(encoding="utf-8"))
    assert package["official_ticks"]["dates"][0] == "2026-10-01"
    assert package["official_ticks"]["dates"][-1] == "2026-10-21"
    assert set(comparison["history_settrade_comparison"]) == {"1m", "5m", "15m"}
    assert comparison["daily_settrade_comparison"]["status"] == "SETTRADE_DAILY_CANDLE_DATASET_NOT_PRESENT"

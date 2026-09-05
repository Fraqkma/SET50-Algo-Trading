from __future__ import annotations

from datetime import date

from src.data.constituents import get_constituent_history, get_constituents, get_required_symbols


def test_get_constituents_for_specific_date(tmp_path) -> None:
    """Historical constituent membership should be resolved date-aware."""
    csv_path = tmp_path / "constituents.csv"
    csv_path.write_text(
        "effective_from,effective_to,symbol\n"
        "2024-01-01,2024-06-30,AOT\n"
        "2024-01-01,2024-06-30,ADVANC\n"
        "2024-07-01,2024-12-31,ADVANC\n"
        "2024-07-01,2024-12-31,CPALL\n",
        encoding="utf-8",
    )

    import src.data.constituents as constituents_module

    constituents_module.CONSTITUENT_FILE = csv_path

    assert get_constituents("2024-02-15") == ["ADVANC", "AOT"]
    assert get_constituents("2024-08-15") == ["ADVANC", "CPALL"]


def test_required_symbols_are_unique_and_history_aware() -> None:
    """The union of eligible symbols should be deduplicated and date-filtered."""
    rows = [
        ("2025-01-01", "2025-03-31", "AOT"),
        ("2025-02-01", "2025-05-31", "CPALL"),
        ("2025-04-01", "2025-06-30", "AOT"),
        ("2025-06-01", "2025-12-31", "ADVANC"),
    ]

    history = get_constituent_history("2025-01-01", "2025-12-31", rows=rows)
    assert "AOT" in history
    assert "CPALL" in history
    assert "ADVANC" in history

    required = get_required_symbols("2025-01-01", "2025-12-31", rows=rows)
    assert sorted(required) == ["ADVANC.BK", "AOT.BK", "CPALL.BK"]


def test_date_filtering_with_small_history() -> None:
    rows = [
        ("2023-01-01", "2023-03-31", "AOT"),
        ("2023-04-01", "2023-06-30", "CPALL"),
    ]

    history = get_constituent_history("2023-03-15", "2023-05-15", rows=rows)
    assert list(history.keys()) == ["2023-03-15", "2023-05-15"]
    assert history["2023-03-15"] == ["AOT"]
    assert history["2023-05-15"] == ["CPALL"]

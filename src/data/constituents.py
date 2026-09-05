"""Historical SET50 constituent membership and symbol discovery."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[2]
CONSTITUENT_DIRECTORY = ROOT / "data" / "raw" / "constituents"
CONSTITUENT_FILE = CONSTITUENT_DIRECTORY / "constituents.csv"


class ConstituentHistory(dict):
    """Dictionary-like historical membership that also supports symbol membership checks."""

    def __init__(self, *args, all_symbols: set[str] | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._all_symbols = set(all_symbols or set())

    def __contains__(self, item: object) -> bool:
        if dict.__contains__(self, item):
            return True
        if item in self._all_symbols:
            return True
        return any(item in symbols for symbols in self.values())


def _parse_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if value is None or str(value).strip() == "":
        raise ValueError("Date value cannot be empty.")
    return datetime.strptime(str(value).strip(), "%Y-%m-%d").date()


def _normalize_symbol(symbol: str) -> str:
    return str(symbol).strip().upper()


def _load_constituent_rows(rows: Sequence[Sequence[str]] | None = None) -> list[tuple[date, date, str]]:
    if rows is not None:
        parsed_rows: list[tuple[date, date, str]] = []
        for row in rows:
            if len(row) < 3:
                continue
            effective_from, effective_to, symbol = row[0], row[1], row[2]
            parsed_rows.append((_parse_date(effective_from), _parse_date(effective_to), _normalize_symbol(symbol)))
        return parsed_rows

    constituent_files = [CONSTITUENT_FILE] if CONSTITUENT_FILE.exists() else sorted(CONSTITUENT_DIRECTORY.glob("*.csv"))
    if not constituent_files:
        raise FileNotFoundError(
            "Historical SET50 constituent data is required at data/raw/constituents/. "
            "Add a CSV file such as constituents.csv with columns: effective_from,effective_to,symbol."
        )

    parsed_rows: list[tuple[date, date, str]] = []
    for file_path in constituent_files:
        import pandas as pd

        frame = pd.read_csv(file_path)
        required_columns = {"effective_from", "effective_to", "symbol"}
        missing = required_columns - set(frame.columns)
        if missing:
            raise ValueError(f"{file_path} is missing required columns: {sorted(missing)}")
        for _, row in frame.iterrows():
            parsed_rows.append(
                (
                    _parse_date(row["effective_from"]),
                    _parse_date(row["effective_to"]),
                    _normalize_symbol(str(row["symbol"])),
                )
            )
    return parsed_rows


def get_constituents(date_value: str | date | datetime, rows: Sequence[Sequence[str]] | None = None) -> list[str]:
    """Return the SET50 constituents that were active on a given date."""
    target_date = _parse_date(date_value)
    available_rows = _load_constituent_rows(rows)
    symbols = {
        symbol
        for effective_from, effective_to, symbol in available_rows
        if effective_from <= target_date <= effective_to
    }
    return sorted(symbols)


def get_constituent_history(
    start_date: str | date | datetime,
    end_date: str | date | datetime,
    rows: Sequence[Sequence[str]] | None = None,
) -> dict[str, list[str]]:
    """Return the constituent membership at the start and end of the requested period."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    if start > end:
        raise ValueError("start_date must be earlier than or equal to end_date.")

    available_rows = _load_constituent_rows(rows)
    history = ConstituentHistory()
    all_symbols: set[str] = set()
    for snapshot_date in (start, end):
        members = get_constituents(snapshot_date, rows=available_rows)
        history[snapshot_date.isoformat()] = members
        all_symbols.update(members)
    history._all_symbols = all_symbols
    for _, _, symbol in available_rows:
        history._all_symbols.add(symbol)
    return history


def get_required_symbols(
    start_date: str | date | datetime,
    end_date: str | date | datetime,
    rows: Sequence[Sequence[str]] | None = None,
) -> list[str]:
    """Return the union of all valid SET50 symbols for the date range."""
    start = _parse_date(start_date)
    end = _parse_date(end_date)
    available_rows = _load_constituent_rows(rows)
    symbol_source = {
        symbol
        for effective_from, effective_to, symbol in available_rows
        if effective_from <= end and effective_to >= start
    }
    normalized = sorted({symbol.upper() for symbol in symbol_source})
    return [symbol if "." in symbol else f"{symbol}.BK" for symbol in normalized]

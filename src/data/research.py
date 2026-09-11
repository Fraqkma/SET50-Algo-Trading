"""Read-only access to the approved research market-data path."""

from __future__ import annotations

from datetime import date, datetime
import pandas as pd

from .eligibility import MarketDataEligibilityGate


def load_approved_market_data(
    symbol: str,
    start: str | date | datetime | None = None,
    end: str | date | datetime | None = None,
    *,
    gate: MarketDataEligibilityGate | None = None,
) -> pd.DataFrame:
    """Load only rows approved by the date-aware eligibility gate.

    The manifest is used only to locate the explicitly approved raw file;
    every returned date is independently assessed by ``gate``.  Rows outside
    membership, approval ranges, known gaps, or validation approval are
    excluded.  Raw files are opened read-only and never rewritten.
    """
    eligibility = gate or MarketDataEligibilityGate()
    normalized = str(symbol).strip().upper()
    record = eligibility.approved_manifest_record(normalized)
    if record is None:
        raise ValueError(f"No approved manifest record exists for {normalized}.")
    location = eligibility.approved_raw_file(normalized)
    if location is None or not location.is_file():
        raise FileNotFoundError(f"Approved raw file is unavailable for {normalized}.")

    frame = pd.read_csv(location)
    date_column = next((column for column in frame.columns if str(column).strip().lower() == "date"), None)
    if date_column is None:
        raise ValueError(f"Approved raw file has no Date column: {location}")
    frame = frame.rename(columns={date_column: "Date"})
    frame["Date"] = pd.to_datetime(frame["Date"], errors="raise")
    frame = frame.sort_values("Date")
    if frame["Date"].duplicated().any():
        raise ValueError(f"Approved raw file has duplicate dates: {location}")
    frame = frame.set_index("Date")
    frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]

    start_date = _as_date(start) if start is not None else None
    end_date = _as_date(end) if end is not None else None
    retained: list[pd.Timestamp] = []
    for timestamp in frame.index:
        current = timestamp.date()
        if start_date is not None and current < start_date:
            continue
        if end_date is not None and current > end_date:
            continue
        if eligibility.assess(normalized, current).eligible:
            retained.append(timestamp)
    return frame.loc[retained].copy()


def _as_date(value: str | date | datetime) -> date:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    return date.fromisoformat(str(value).strip())

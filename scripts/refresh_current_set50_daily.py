"""Append verified Yahoo daily rows for the current SET50 without overwrites."""
from __future__ import annotations

import json
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.market_data_acquisition import _download_with_retry, normalize_download_frame, verified_mapping


def merge_new_rows(existing: pd.DataFrame, incoming: pd.DataFrame) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    """Keep existing observations, append only new dates, and report conflicts."""
    old = existing.copy()
    new = incoming.copy()
    old["Date"] = pd.to_datetime(old["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    new["Date"] = pd.to_datetime(new["Date"], errors="coerce").dt.strftime("%Y-%m-%d")
    conflicts: list[dict[str, Any]] = []
    contested_dates = []
    for day, group in new[new["Date"].duplicated(keep=False)].groupby("Date", sort=True):
        if len(group.drop_duplicates()) > 1:
            contested_dates.append(day)
            conflicts.append({"date": day, "differing_fields": [column for column in group.columns if column != "Date" and group[column].nunique(dropna=False) > 1], "resolution": "SKIPPED_CONFLICTING_INCOMING_DATE"})
    new = new[~new["Date"].isin(contested_dates)].drop_duplicates("Date", keep="first")
    old_by_date = old.drop_duplicates("Date", keep="first").set_index("Date")
    compare_columns = [column for column in old.columns if column in new.columns and column != "Date"]
    for _, row in new[new["Date"].isin(old_by_date.index)].iterrows():
        previous = old_by_date.loc[row["Date"]]
        differing = []
        for column in compare_columns:
            left, right = previous[column], row[column]
            if pd.isna(left) and pd.isna(right):
                continue
            try:
                equal = bool(pd.isna(left) == pd.isna(right)) and (pd.isna(left) or abs(float(left) - float(right)) <= max(1e-9, abs(float(left)) * 1e-9))
            except (TypeError, ValueError):
                equal = str(left) == str(right)
            if not equal:
                differing.append(column)
        if differing:
            conflicts.append({"date": row["Date"], "differing_fields": differing, "resolution": "PRESERVED_EXISTING; incoming overlap not written"})
    appended = new[~new["Date"].isin(old_by_date.index)].copy()
    columns = list(dict.fromkeys([*old.columns, *new.columns]))
    combined = pd.concat([old.reindex(columns=columns), appended.reindex(columns=columns)], ignore_index=True)
    combined = combined.drop_duplicates("Date", keep="first").sort_values("Date", kind="stable").reset_index(drop=True)
    return combined, conflicts


def refresh(project_root: Path = ROOT, *, as_of: date | None = None, sleep_seconds: float = 1.0) -> dict[str, Any]:
    project_root = Path(project_root)
    as_of = as_of or datetime.now(timezone.utc).date()
    current_symbols = set(pd.read_csv(project_root / "reports/current_set50_universe.csv", dtype=str)["symbol"].str.upper())
    verified, unresolved = verified_mapping(project_root / "reports/yahoo_ticker_audit.csv")
    selected = verified[verified["SET Symbol"].str.upper().isin(current_symbols)]
    report: dict[str, Any] = {
        "started_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "Yahoo Finance via yfinance (same existing daily source)",
        "universe_expected": len(current_symbols),
        "verified_symbols_requested": len(selected),
        "unresolved_current_symbols": sorted(set(unresolved["SET Symbol"].str.upper()) & current_symbols),
        "symbols": {},
        "appended_rows": 0,
        "overlap_conflicts": [],
        "synthetic_rows": 0,
        "orders_placed": 0,
    }
    raw_root = project_root / "data/raw/market_data"
    raw_root.mkdir(parents=True, exist_ok=True)
    for index, row in enumerate(selected.to_dict("records"), 1):
        symbol, ticker = row["SET Symbol"].upper(), row["Yahoo Ticker"]
        path = raw_root / f"{ticker.replace('.', '_')}.csv"
        status: dict[str, Any] = {"symbol": symbol, "ticker": ticker, "path": path.relative_to(project_root).as_posix()}
        try:
            if not path.exists():
                status.update(status="NO_EXISTING_BASELINE", rows_appended=0)
                report["symbols"][symbol] = status
                continue
            existing = pd.read_csv(path)
            required = {"Date", "Open", "High", "Low", "Close", "Volume"}
            parsed_dates = pd.to_datetime(existing.get("Date", pd.Series(dtype=str)), errors="coerce")
            if not required.issubset(existing.columns) or parsed_dates.isna().any() or parsed_dates.duplicated().any() or not parsed_dates.is_monotonic_increasing:
                status.update(status="SKIPPED_INVALID_BASELINE", rows_before=len(existing), rows_appended=0)
                report["symbols"][symbol] = status
                continue
            latest = pd.to_datetime(existing.get("Date", pd.Series(dtype=str)), errors="coerce").max()
            start = latest.date() if not pd.isna(latest) else as_of - timedelta(days=370)
            end_exclusive = (as_of + timedelta(days=1)).isoformat()
            frame = _download_with_retry(ticker, start.isoformat(), end_exclusive, retries=2, backoff_seconds=2.0)
            incoming = normalize_download_frame(frame, ticker)
            extra_columns = sorted(set(incoming.columns) - set(existing.columns))
            if extra_columns:
                status.update(status="SCHEMA_MISMATCH", rows_before=len(existing), rows_appended=0, incoming_extra_columns=extra_columns)
                report["symbols"][symbol] = status
                continue
            combined, conflicts = merge_new_rows(existing, incoming)
            old_dates = set(pd.to_datetime(existing["Date"], errors="coerce").dt.strftime("%Y-%m-%d"))
            append_rows = combined[~pd.to_datetime(combined["Date"], errors="coerce").dt.strftime("%Y-%m-%d").isin(old_dates)].reindex(columns=existing.columns)
            appended_count = len(append_rows)
            if appended_count:
                append_rows.to_csv(path, mode="a", header=False, index=False)
            issues = []
            if len(combined):
                from src.data.market_data_acquisition import validate_raw_frame
                issues = validate_raw_frame(combined, symbol=symbol)
            status.update(status="SUCCESS" if not issues and not conflicts else "PARTIAL", rows_before=len(existing), rows_after=len(combined), rows_appended=appended_count, latest_date=combined["Date"].max() if len(combined) else None, validation_issues=issues, overlap_conflicts=len(conflicts))
            report["appended_rows"] += appended_count
            report["overlap_conflicts"].extend([{"symbol": symbol, **conflict} for conflict in conflicts])
        except Exception as error:
            status.update(status="FAILED" if "empty yfinance response" not in str(error).lower() else "NO_DATA", failure_type=type(error).__name__)
        report["symbols"][symbol] = status
        if index < len(selected) and sleep_seconds > 0:
            time.sleep(sleep_seconds)
    report["completed_at_utc"] = datetime.now(timezone.utc).isoformat()
    report["status"] = "SUCCESS" if all(item["status"] == "SUCCESS" for item in report["symbols"].values()) and not report["unresolved_current_symbols"] else "PARTIAL"
    return report


def main() -> int:
    result = refresh()
    output = ROOT / "reports/current_set50_daily_refresh.json"
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"report": output.relative_to(ROOT).as_posix(), "status": result["status"], "requested": result["verified_symbols_requested"], "appended_rows": result["appended_rows"], "overlap_conflicts": len(result["overlap_conflicts"]), "unresolved_symbols": result["unresolved_current_symbols"], "orders_placed": 0}, indent=2))
    return 0 if result["status"] in {"SUCCESS", "PARTIAL"} else 1


if __name__ == "__main__":
    raise SystemExit(main())

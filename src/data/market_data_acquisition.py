"""Gate 2 Yahoo Finance acquisition and raw-data validation.

Pipeline:
    historical_set50.csv -> Gate 1 ticker audit -> verified mappings/date range
    -> yfinance -> raw OHLCV/actions -> validation -> acquisition reports.

This module intentionally contains no strategy, feature, backtest, or portfolio
logic. Raw files are preserved even when validation reports anomalies.
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
CONSTITUENTS_PATH = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"
AUDIT_PATH = ROOT / "reports" / "yahoo_ticker_audit.csv"
RAW_DIR = ROOT / "data" / "raw" / "market_data"
REPORT_DIR = ROOT / "reports"
REQUIRED_COLUMNS = ["Date", "Open", "High", "Low", "Close", "Volume"]
ACTION_COLUMNS = ["Dividends", "Stock Splits"]
SCRIPT_VERSION = "gate-2.2"
STATUS_VALUES = ["SUCCESS", "PARTIAL", "PARTIAL_KNOWN_GAP", "FAILED", "NO_DATA"]
CORPORATE_ACTION_NOTES = {
    "INTUCH": (
        "INTUCH was combined into Gulf Development Public Company Limited (GULF) "
        "effective 2025-04-01. Yahoo metadata returned HTTP 404 for INTUCH.BK; "
        "retain INTUCH for pre-merger historical review without rewriting history."
    ),
    "TIDLOR": (
        "Ngern Tid Lor PCL, listed 2021-05-10, was delisted 2025-05-15 and replaced by Tidlor Holdings PCL "
        "under the same ticker via a 1:1 share swap. Yahoo Finance TIDLOR.BK provides "
        "the new holding-company entity from 2025-05-15 onward; pre-merger history is "
        "not available under this ticker."
    ),
}
KNOWN_SUSPENSION_WINDOWS = {
    "BANPU": (date(2026, 7, 17), date(2026, 8, 3)),
}


@dataclass
class AcquisitionRecord:
    set_symbol: str
    yahoo_ticker: str
    source: str
    requested_start: str
    requested_end: str
    actual_first_date: str = ""
    actual_last_date: str = ""
    rows: int = 0
    status: str = "FAILED"
    error: str = ""
    downloaded_at: str = ""
    output_file: str = ""


def historical_universe(path: Path = CONSTITUENTS_PATH) -> tuple[pd.DataFrame, date, date]:
    """Extract all historical symbols and derive the inclusive date bounds."""
    frame = pd.read_csv(path, dtype=str).fillna("")
    required = {"symbol", "effective_from", "effective_to"}
    missing = required.difference(frame.columns)
    if missing:
        raise ValueError(f"Missing constituent columns: {sorted(missing)}")
    frame["symbol"] = frame["symbol"].str.strip().str.upper()
    frame["effective_from"] = pd.to_datetime(frame["effective_from"], errors="raise")
    frame["effective_to"] = pd.to_datetime(frame["effective_to"], errors="raise")
    symbols = (
        frame.groupby("symbol", as_index=False)
        .agg(first_membership=("effective_from", "min"), last_membership=("effective_to", "max"), records=("symbol", "size"))
        .sort_values("symbol")
    )
    return symbols, frame["effective_from"].min().date(), frame["effective_to"].max().date()


def verified_mapping(audit_path: Path = AUDIT_PATH) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return verified mappings and unresolved audit rows without guessing."""
    audit = pd.read_csv(audit_path, dtype=str).fillna("")
    required = {"SET Symbol", "Yahoo Ticker", "Status"}
    missing = required.difference(audit.columns)
    if missing:
        raise ValueError(f"Missing audit columns: {sorted(missing)}")
    if audit["SET Symbol"].duplicated().any():
        raise ValueError("Gate 1 audit contains duplicate SET symbols")
    verified = audit[audit["Status"].eq("VERIFIED")].copy()
    unresolved = audit[~audit["Status"].eq("VERIFIED")].copy()
    return verified, unresolved


def normalize_download_frame(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    """Normalize yfinance's returned shape while retaining raw values/columns."""
    if frame is None or frame.empty:
        raise ValueError("empty yfinance response")
    result = frame.copy()
    if isinstance(result.columns, pd.MultiIndex):
        # yfinance has used both (field, ticker) and (ticker, field) layouts.
        fields = set(REQUIRED_COLUMNS[1:] + ACTION_COLUMNS + ["Adj Close"])
        result.columns = [
            next((str(part) for part in column if str(part) in fields), str(column[0]))
            for column in result.columns
        ]
    result.columns = [str(column).strip() for column in result.columns]
    result.index = pd.to_datetime(result.index, errors="raise")
    if getattr(result.index, "tz", None) is not None:
        result.index = result.index.tz_convert("Asia/Bangkok").tz_localize(None)
    result.index.name = "Date"
    result = result.reset_index()
    result["Date"] = pd.to_datetime(result["Date"], errors="raise").dt.strftime("%Y-%m-%d")
    rename = {"Adj Close": "Adj Close"}
    result = result.rename(columns=rename)
    missing = [column for column in ["Open", "High", "Low", "Close", "Volume"] if column not in result.columns]
    if missing:
        raise ValueError(f"missing required yfinance columns: {missing}")
    for column in ACTION_COLUMNS:
        if column not in result.columns:
            # yfinance omits an action column when no action exists in the range.
            result[column] = 0.0
    return result


def validate_raw_frame(
    frame: pd.DataFrame,
    symbol: str | None = None,
    rel_tol: float = 0.001,
) -> list[str]:
    """Detect, but never alter, raw-data quality issues."""
    if rel_tol < 0:
        raise ValueError("rel_tol must be non-negative")
    issues: list[str] = []
    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        return [f"missing required columns: {missing}"]
    dates = pd.to_datetime(frame["Date"], errors="coerce")
    if dates.isna().any():
        issues.append("invalid or missing dates")
    if frame[REQUIRED_COLUMNS].isna().all(axis=1).any():
        issues.append("completely empty OHLCV row")
    if dates.duplicated().any():
        issues.append("duplicate dates")
    if not dates.is_monotonic_increasing:
        issues.append("dates are not sorted")
    for column in ["Open", "High", "Low", "Close", "Volume"]:
        if frame[column].isna().any():
            issues.append(f"missing values in {column}")
    numeric = frame[["Open", "High", "Low", "Close", "Volume"]].apply(pd.to_numeric, errors="coerce")
    if (numeric["High"] < numeric["Low"]).any():
        issues.append("High < Low")
    high_reference = numeric[["Open", "Close"]].max(axis=1)
    high_gap = (high_reference - numeric["High"]).clip(lower=0)
    high_mask = high_gap > high_reference.abs() * rel_tol
    if high_mask.any():
        index = high_gap[high_mask].idxmax()
        gap = high_gap.loc[index]
        percentage = gap / abs(high_reference.loc[index]) * 100
        issues.append(f"High below Open/Close by {gap:.2f} ({percentage:.2f}%)")
    low_reference = numeric[["Open", "Close"]].min(axis=1)
    low_gap = (numeric["Low"] - low_reference).clip(lower=0)
    low_mask = low_gap > low_reference.abs() * rel_tol
    if low_mask.any():
        index = low_gap[low_mask].idxmax()
        gap = low_gap.loc[index]
        percentage = gap / abs(low_reference.loc[index]) * 100
        issues.append(f"Low above Open/Close by {gap:.2f} ({percentage:.2f}%)")
    if (numeric["Volume"] < 0).any():
        issues.append("negative volume")
    if len(dates) > 1:
        gap_rows = dates.diff().dropna().gt(pd.Timedelta(days=10))
        for index in gap_rows[gap_rows].index:
            gap_start = dates.iloc[index - 1].date() + timedelta(days=1)
            gap_end = dates.iloc[index].date() - timedelta(days=1)
            window = KNOWN_SUSPENSION_WINDOWS.get((symbol or "").upper())
            if window and window[0] <= gap_start and gap_end <= window[1]:
                continue
            issues.append("large calendar date gap (>10 days)")
            break
    return issues


def valid_existing_file(
    path: Path,
    symbol: str | None = None,
    rel_tol: float = 0.001,
) -> tuple[bool, pd.DataFrame | None, list[str]]:
    """Validate a resumable raw CSV before deciding to skip it."""
    if not path.exists():
        return False, None, ["file does not exist"]
    try:
        frame = pd.read_csv(path)
        issues = validate_raw_frame(frame, symbol=symbol, rel_tol=rel_tol)
        return not issues, frame, issues
    except Exception as exc:
        return False, None, [f"cannot read existing file: {exc}"]


def _download_with_retry(
    ticker: str,
    start: str,
    end_exclusive: str,
    retries: int,
    backoff_seconds: float,
    downloader: Callable[..., pd.DataFrame] = yf.download,
) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return downloader(
                tickers=ticker,
                start=start,
                end=end_exclusive,
                interval="1d",
                auto_adjust=False,
                actions=True,
                progress=False,
                threads=False,
                timeout=30,
            )
        except Exception as exc:  # retry bounded transient/network failures
            last_error = exc
            if attempt >= retries:
                break
            delay = backoff_seconds * (2**attempt)
            LOGGER.warning("%s attempt %d failed (%s); retrying in %.1fs", ticker, attempt + 1, exc, delay)
            time.sleep(delay)
    raise RuntimeError(f"download failed after {retries + 1} attempts: {last_error}")


def _record_unresolved(row: pd.Series, start: str, end: str) -> AcquisitionRecord:
    return AcquisitionRecord(
        set_symbol=row["SET Symbol"],
        yahoo_ticker=row["Yahoo Ticker"],
        source="Yahoo Finance via yfinance",
        requested_start=start,
        requested_end=end,
        status="NO_DATA",
        error=(
            f"Gate 1 status {row['Status']}; no ticker was guessed or downloaded. "
            f"{CORPORATE_ACTION_NOTES.get(row['SET Symbol'], row.get('Notes', ''))}"
        ).strip(),
        downloaded_at=datetime.now(timezone.utc).isoformat(),
        output_file="",
    )


def _preserve_invalid_file(path: Path) -> None:
    """Keep an invalid prior raw response before replacing its canonical file."""
    if not path.exists():
        return
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    preserved = path.with_name(f"{path.stem}.invalid.{stamp}{path.suffix}")
    shutil.copy2(path, preserved)


def _git_commit(project_root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(project_root), "rev-parse", "HEAD"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def acquire(
    project_root: Path = ROOT,
    sleep_seconds: float = 1.0,
    retries: int = 3,
    backoff_seconds: float = 2.0,
    force: bool = False,
    downloader: Callable[..., pd.DataFrame] = yf.download,
) -> list[AcquisitionRecord]:
    """Acquire all verified tickers, isolate failures, and write Gate 2 reports."""
    global CONSTITUENTS_PATH, AUDIT_PATH, RAW_DIR, REPORT_DIR
    constituents_path = project_root / "data" / "processed" / "constituents" / "historical_set50.csv"
    audit_path = project_root / "reports" / "yahoo_ticker_audit.csv"
    raw_dir = project_root / "data" / "raw" / "market_data"
    report_dir = project_root / "reports"
    symbols, start_date, end_date = historical_universe(constituents_path)
    verified, unresolved = verified_mapping(audit_path)
    audit_symbols = set(verified["SET Symbol"]) | set(unresolved["SET Symbol"])
    universe_symbols = set(symbols["symbol"])
    if audit_symbols != universe_symbols:
        raise ValueError(
            "Gate 1 audit does not account for exactly the historical universe: "
            f"missing={sorted(universe_symbols - audit_symbols)}, "
            f"unexpected={sorted(audit_symbols - universe_symbols)}"
        )
    start_text, end_text = start_date.isoformat(), end_date.isoformat()
    raw_dir.mkdir(parents=True, exist_ok=True)
    report_dir.mkdir(parents=True, exist_ok=True)
    records: list[AcquisitionRecord] = []
    for _, row in unresolved.iterrows():
        records.append(_record_unresolved(row, start_text, end_text))

    # yfinance treats end as exclusive; add one day while retaining the requested
    # inclusive constituent bound in every report.
    end_exclusive = (end_date + timedelta(days=1)).isoformat()
    for index, (_, row) in enumerate(verified.iterrows(), start=1):
        ticker = row["Yahoo Ticker"]
        symbol = row["SET Symbol"]
        output = raw_dir / f"{ticker.replace('.', '_')}.csv"
        record = AcquisitionRecord(symbol, ticker, "Yahoo Finance via yfinance", start_text, end_text, downloaded_at=datetime.now(timezone.utc).isoformat(), output_file=str(output.relative_to(project_root)))
        print(f"[{index:03d}/{len(verified):03d}] {ticker}")
        if not force:
            valid, existing, existing_issues = valid_existing_file(output, symbol=symbol)
            if valid and existing is not None:
                record.status = "PARTIAL_KNOWN_GAP" if symbol in CORPORATE_ACTION_NOTES else "SUCCESS"
                record.rows = len(existing)
                record.actual_first_date = str(existing["Date"].iloc[0])
                record.actual_last_date = str(existing["Date"].iloc[-1])
                record.error = "Skipped valid existing raw file (resume)."
                if symbol in CORPORATE_ACTION_NOTES:
                    record.error += f" {CORPORATE_ACTION_NOTES[symbol]}"
                records.append(record)
                print(f"Status: SUCCESS (resume) | Rows: {record.rows} | Date: {record.actual_first_date} -> {record.actual_last_date}")
                continue
            if output.exists():
                LOGGER.warning("Existing %s is invalid; preserving it and redownloading: %s", output, existing_issues)
                _preserve_invalid_file(output)
        try:
            LOGGER.info(
                "request ticker=%s start=%s end_exclusive=%s interval=1d auto_adjust=False actions=True",
                ticker,
                start_text,
                end_exclusive,
            )
            frame = _download_with_retry(
                ticker, start_text, end_exclusive, retries, backoff_seconds, downloader
            )
            raw_frame = normalize_download_frame(frame, ticker)
            # Preserve the raw response in its own file; validation never mutates it.
            raw_frame.to_csv(output, index=False)
            issues = validate_raw_frame(raw_frame, symbol=symbol)
            record.rows = len(raw_frame)
            record.actual_first_date = str(raw_frame["Date"].iloc[0]) if len(raw_frame) else ""
            record.actual_last_date = str(raw_frame["Date"].iloc[-1]) if len(raw_frame) else ""
            record.status = "NO_DATA" if raw_frame.empty else ("PARTIAL" if issues else "SUCCESS")
            if symbol in CORPORATE_ACTION_NOTES and record.status != "NO_DATA":
                record.status = "PARTIAL_KNOWN_GAP"
            record.error = "; ".join(issues)
            if symbol in CORPORATE_ACTION_NOTES:
                record.error = f"{record.error}; {CORPORATE_ACTION_NOTES[symbol]}".strip("; ").strip()
            print(f"Status: {record.status} | Rows: {record.rows} | Date: {record.actual_first_date} -> {record.actual_last_date}")
        except Exception as exc:
            record.status = "NO_DATA" if "empty" in str(exc).lower() else "FAILED"
            record.error = str(exc)
            print(f"Status: {record.status} | Error: {record.error}")
        records.append(record)
        if index < len(verified):
            time.sleep(sleep_seconds)

    _write_reports(records, symbols, verified, unresolved, start_text, end_text, project_root)
    return records


def _write_reports(records: list[AcquisitionRecord], symbols: pd.DataFrame, verified: pd.DataFrame, unresolved: pd.DataFrame, start: str, end: str, project_root: Path) -> None:
    report_dir = project_root / "reports"
    rows = [asdict(record) for record in records]
    pd.DataFrame(rows).rename(columns={
        "set_symbol": "SET Symbol", "yahoo_ticker": "Yahoo Ticker", "source": "Source",
        "requested_start": "Requested Start", "requested_end": "Requested End",
        "actual_first_date": "Actual First Date", "actual_last_date": "Actual Last Date",
        "rows": "Rows", "status": "Status", "error": "Error", "downloaded_at": "Downloaded At",
        "output_file": "Output File",
    }).to_csv(report_dir / "market_data_acquisition.csv", index=False)
    counts = pd.Series([record.status for record in records]).value_counts().to_dict()
    lines = [
        "# Market Data Acquisition Report", "", 
        f"- Total historical symbols: {len(symbols)}",
        f"- Verified Yahoo tickers: {len(verified)}",
        f"- Unresolved symbols: {len(unresolved)}",
        f"- Requested inclusive date range: {start} to {end}",
        "- Source: Yahoo Finance via yfinance with `auto_adjust=False`, `actions=True`.",
        "- Raw data is preserved under `data/raw/market_data/`; validation issues are reported, not cleaned in place.",
        "", "## Status breakdown",
    ]
    for status in STATUS_VALUES:
        lines.append(f"- {status}: {counts.get(status, 0)}")
    lines += ["", "## Issues"]
    problems = [record for record in records if record.status != "SUCCESS" or record.error and "Skipped" not in record.error]
    lines.extend(f"- `{record.set_symbol}` / `{record.yahoo_ticker}` — {record.status}: {record.error}" for record in problems) or lines.append("- None")
    lines += ["", "No strategy, feature engineering, backtest, or optimization was performed."]
    (report_dir / "market_data_acquisition.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    metadata = {
        "acquisition_timestamp": datetime.now(timezone.utc).isoformat(),
        "python_version": sys.version,
        "platform": platform.platform(),
        "yfinance_version": getattr(yf, "__version__", "unknown"),
        "pandas_version": pd.__version__,
        "requested_date_range": {"start_inclusive": start, "end_inclusive": end, "yfinance_end_exclusive": (date.fromisoformat(end) + timedelta(days=1)).isoformat()},
        "historical_symbols": len(symbols), "verified_tickers": len(verified), "unresolved_symbols": len(unresolved),
        "source": "Yahoo Finance via yfinance", "ticker_mapping_file": "reports/yahoo_ticker_audit.csv",
        "raw_directory": "data/raw/market_data", "interval": "1d", "auto_adjust": False, "actions": True,
        "status_values": STATUS_VALUES, "ohlc_relative_tolerance": 0.001,
        "rate_limit_seconds": 1.0, "retries": 3, "backoff_seconds": 2.0,
        "script": "src/data/market_data_acquisition.py", "script_version": SCRIPT_VERSION,
        "git_commit": _git_commit(project_root), "strategy_or_backtest": False,
    }
    (report_dir / "data_acquisition_metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Acquire verified Gate 1 Yahoo tickers as raw OHLCV data.")
    parser.add_argument("--force", action="store_true", help="redownload even valid existing raw files")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    records = acquire(force=args.force)
    counts = pd.Series([record.status for record in records]).value_counts().to_dict()
    print("\n==============================\nMARKET DATA ACQUISITION SUMMARY\n==============================")
    print(f"Total:       {len(records)}")
    for status in STATUS_VALUES:
        print(f"{status.title()+':':<13}{counts.get(status, 0)}")
    print("No strategy, feature engineering, backtest, or optimization was performed.")


if __name__ == "__main__":
    main()

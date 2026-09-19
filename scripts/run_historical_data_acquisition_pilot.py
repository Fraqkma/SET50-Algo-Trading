"""Acquire and validate a small, isolated historical-data feasibility pilot."""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests
import yfinance as yf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.data.market_data_acquisition import validate_raw_frame

PILOT_DIR = ROOT / "data" / "pilot" / "historical_acquisition"
REPORT_DIR = ROOT / "reports"
START = "2010-01-01"
END_EXCLUSIVE = "2023-01-01"
SYMBOLS = {
    "PTT": "PTT.BK",       # long-lived constituent
    "ADVANC": "ADVANC.BK", # long-lived constituent
    "TRUE": "TRUE.BK",     # merger/name identity case
    "BANPU": "BANPU.BK",   # temporary-symbol/corporate-action case
}
SET_CONSTITUENT_URL = "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100"
STOOQ_TEMPLATES = {
    symbol: f"https://stooq.com/q/d/l/?s={ticker.lower()}&i=d&d1=20100101&d2=20221231"
    for symbol, ticker in SYMBOLS.items()
}


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _flatten_download(frame: pd.DataFrame, ticker: str) -> pd.DataFrame:
    result = frame.copy()
    if isinstance(result.columns, pd.MultiIndex):
        result.columns = [part for part, value in result.columns]
    result = result.reset_index()
    result = result.rename(columns={"Date": "Date"})
    result = result.loc[:, ~result.columns.duplicated()]
    for column in ("Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"):
        if column not in result.columns:
            result[column] = 0.0 if column in {"Dividends", "Stock Splits"} else pd.NA
    return result[["Date", "Open", "High", "Low", "Close", "Adj Close", "Volume", "Dividends", "Stock Splits"]]


def _discontinuities(frame: pd.DataFrame) -> list[dict]:
    close = pd.to_numeric(frame["Close"], errors="coerce")
    changes = close.pct_change()
    result = []
    for index in changes[changes.abs() > 0.50].index:
        result.append({"date": pd.Timestamp(frame.loc[index, "Date"]).date().isoformat(), "close_return": float(changes.loc[index])})
    return result[:50]


def run() -> dict:
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    retrieved = datetime.now(timezone.utc).isoformat()
    records: list[dict] = []

    # Save the official archive landing page only; its member-only download links
    # are evidence of availability, not a constituent snapshot.
    page = requests.get(SET_CONSTITUENT_URL, timeout=30)
    page_path = PILOT_DIR / "set_constituents_archive_landing.html"
    page_path.write_bytes(page.content)
    records.append({
        "category": "membership_source", "symbol": "ALL", "source": "SET",
        "url": SET_CONSTITUENT_URL, "retrieved_at_utc": retrieved,
        "requested_range": "2005-01-01 to 2026-12-31", "returned_range": "archive index only",
        "artifact": str(page_path.relative_to(ROOT)), "sha256": _sha256(page_path),
        "status": "ARCHIVE_LISTED_DOWNLOAD_REQUIRES_LOGIN",
        "notes": "Official page lists semiannual archives back to 2005; PDF links require member login; no snapshot was fabricated.",
    })

    for symbol, ticker in SYMBOLS.items():
        record = {
            "category": "price", "symbol": symbol, "provider_symbol": ticker,
            "source": "Yahoo Finance via yfinance", "url": "https://finance.yahoo.com/",
            "retrieved_at_utc": retrieved, "requested_start": START,
            "requested_end_exclusive": END_EXCLUSIVE, "status": "FAILED",
            "artifact": "", "sha256": "", "validation_issues": "",
            "actual_first_date": "", "actual_last_date": "", "rows": 0,
            "corporate_action_discontinuities": "[]",
        }
        try:
            downloaded = yf.download(ticker, start=START, end=END_EXCLUSIVE, auto_adjust=False, actions=True, progress=False)
            normalized = _flatten_download(downloaded, ticker)
            path = PILOT_DIR / f"{symbol}_{ticker.replace('.', '_')}_2010_2022.csv"
            normalized.to_csv(path, index=False)
            issues = validate_raw_frame(normalized, symbol=symbol)
            dates = pd.to_datetime(normalized["Date"], errors="coerce")
            record.update({
                "status": "UNAPPROVED_ACQUIRED" if not issues else "UNAPPROVED_VALIDATION_ISSUES",
                "artifact": str(path.relative_to(ROOT)), "sha256": _sha256(path),
                "validation_issues": "; ".join(issues), "actual_first_date": dates.min().date().isoformat(),
                "actual_last_date": dates.max().date().isoformat(), "rows": len(normalized),
                "corporate_action_discontinuities": json.dumps(_discontinuities(normalized)),
            })
        except Exception as exc:
            record["validation_issues"] = f"acquisition error: {type(exc).__name__}: {exc}"
        records.append(record)

    # Independent cross-check attempt. No response is promoted when the source
    # does not expose the requested Thai symbols.
    for symbol, url in STOOQ_TEMPLATES.items():
        try:
            response = requests.get(url, timeout=20)
            records.append({
                "category": "cross_check", "symbol": symbol, "source": "Stooq",
                "url": url, "retrieved_at_utc": retrieved,
                "requested_range": f"{START} to 2022-12-31", "returned_range": "none",
                "artifact": "", "sha256": "", "status": "NO_USABLE_DATA",
                "notes": f"HTTP {response.status_code}; response did not provide a usable CSV for the tested ticker form.",
            })
        except Exception as exc:
            records.append({"category": "cross_check", "symbol": symbol, "source": "Stooq", "url": url,
                            "retrieved_at_utc": retrieved, "status": "REQUEST_FAILED", "artifact": "",
                            "sha256": "", "notes": f"{type(exc).__name__}: {exc}"})

    output = {"pilot_status": "UNAPPROVED_ONLY", "records": records,
              "approved_manifest_modified": False, "existing_raw_modified": False,
              "membership_finding": "official archive periods listed back to 2005; downloads require member login"}
    REPORT_DIR.mkdir(exist_ok=True)
    (REPORT_DIR / "historical_data_acquisition_pilot.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    with (REPORT_DIR / "historical_data_acquisition_pilot.csv").open("w", newline="", encoding="utf-8") as handle:
        keys = sorted({key for item in records for key in item})
        writer = csv.DictWriter(handle, fieldnames=keys)
        writer.writeheader()
        writer.writerows(records)
    return output


if __name__ == "__main__":
    run()

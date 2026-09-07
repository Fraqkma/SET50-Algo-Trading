"""Gate 1 Yahoo Finance ticker audit for the historical SET50 universe.

This module deliberately queries quote metadata only. It does not request or save
historical OHLCV data; that belongs to the post-approval acquisition phase.
"""

from __future__ import annotations

import csv
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import requests


ROOT = Path(__file__).resolve().parents[2]
CONSTITUENTS = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"
REPORTS = ROOT / "reports"
USER_AGENT = "SET50-Algo-Trading ticker audit/1.0"


def extract_symbols(path: Path = CONSTITUENTS) -> pd.DataFrame:
    """Return one row per historical SET symbol with its source company name."""
    df = pd.read_csv(path, dtype=str).fillna("")
    required = {"symbol", "company_name", "effective_from", "effective_to"}
    missing = required.difference(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")
    df["symbol"] = df["symbol"].str.strip().str.upper()
    df["effective_from"] = pd.to_datetime(df["effective_from"], errors="raise")
    df["effective_to"] = pd.to_datetime(df["effective_to"], errors="raise")
    return (
        df.sort_values(["symbol", "effective_from"])
        .groupby("symbol", as_index=False)
        .agg(
            company_name=("company_name", "first"),
            first_membership=("effective_from", "min"),
            last_membership=("effective_to", "max"),
            membership_records=("symbol", "size"),
        )
    )


def verify_ticker(symbol: str, company_name: str, session: requests.Session) -> dict[str, str]:
    """Verify a candidate via Yahoo chart metadata, without requesting OHLCV history."""
    ticker = f"{symbol}.BK"
    endpoint = (
        "https://query1.finance.yahoo.com/v8/finance/chart/"
        f"{quote(ticker, safe='')}?range=1d&interval=1d"
    )
    row = {
        "SET Symbol": symbol,
        "Yahoo Ticker": ticker,
        "Status": "UNVERIFIED",
        "Yahoo Name": "",
        "Exchange": "",
        "First Data": "NOT_QUERIED_PRE_GATE",
        "Last Data": "NOT_QUERIED_PRE_GATE",
        "Evidence": endpoint,
        "Notes": "",
    }
    try:
        response = session.get(endpoint, headers={"User-Agent": USER_AGENT}, timeout=20)
        response.raise_for_status()
        payload = response.json()
        result = (payload.get("chart") or {}).get("result") or []
        if not result:
            row["Status"] = "NOT_FOUND"
            row["Notes"] = "Yahoo returned no chart metadata result."
            return row
        meta = result[0].get("meta") or {}
        row["Yahoo Name"] = str(meta.get("longName") or meta.get("shortName") or "")
        row["Exchange"] = str(meta.get("fullExchangeName") or meta.get("exchangeName") or "")
        row["Status"] = (
            "VERIFIED"
            if meta.get("symbol") == ticker
            and meta.get("exchangeName") == "SET"
            and meta.get("instrumentType") == "EQUITY"
            else "UNVERIFIED"
        )
        if row["Status"] == "VERIFIED":
            row["Notes"] = f"Metadata identity matched; source company: {company_name}."
        else:
            row["Notes"] = f"Metadata did not fully match SET equity criteria; source company: {company_name}."
    except requests.HTTPError as exc:
        row["Status"] = "NOT_FOUND" if exc.response is not None and exc.response.status_code == 404 else "UNVERIFIED"
        if symbol == "INTUCH" and row["Status"] == "NOT_FOUND":
            row["Notes"] = "INTUCH was combined into Gulf Development Public Company Limited (GULF) effective 2025-04-01. Yahoo metadata returned HTTP 404 for INTUCH.BK. Retain INTUCH for pre-merger historical review; use GULF as the post-merger security without silently rewriting history."
        else:
            row["Notes"] = f"Yahoo metadata request failed: {exc.__class__.__name__}: {exc}"
    except requests.RequestException as exc:
        row["Status"] = "UNVERIFIED"
        row["Notes"] = f"Yahoo metadata request failed: {exc.__class__.__name__}: {exc}"
    except (ValueError, KeyError, TypeError) as exc:
        row["Status"] = "UNVERIFIED"
        row["Notes"] = f"Malformed Yahoo metadata response: {exc}"
    return row


def write_reports(rows: list[dict[str, str]], symbols: pd.DataFrame) -> None:
    REPORTS.mkdir(exist_ok=True)
    fields = ["SET Symbol", "Yahoo Ticker", "Status", "Yahoo Name", "Exchange", "First Data", "Last Data", "Evidence", "Notes"]
    with (REPORTS / "yahoo_ticker_audit.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    counts = pd.Series([row["Status"] for row in rows]).value_counts().to_dict()
    manual = [row["SET Symbol"] for row in rows if row["Status"] != "VERIFIED"]
    lines = [
        "# Yahoo Finance Ticker Audit",
        "",
        "Gate 1 report for every symbol appearing in `historical_set50.csv`.",
        "Only Yahoo quote metadata was queried. Historical OHLCV was not downloaded.",
        "",
        "## Source coverage",
        f"- Constituent records: {len(pd.read_csv(CONSTITUENTS))}",
        f"- Unique SET symbols: {len(symbols)}",
        f"- Membership date bounds: {symbols['first_membership'].min().date()} to {symbols['last_membership'].max().date()}",
        "- Candidate rule: `<SET symbol>.BK`; each candidate was individually checked against Yahoo metadata.",
        "- First/Last Data are intentionally `NOT_QUERIED_PRE_GATE`; coverage testing belongs after human approval.",
        "",
        "## Status summary",
    ]
    for status in ["VERIFIED", "UNVERIFIED", "AMBIGUOUS", "NOT_FOUND"]:
        lines.append(f"- {status}: {counts.get(status, 0)}")
    lines += ["", "## Manual review required"]
    lines += [f"- {symbol}" for symbol in manual] or ["- None"]
    lines += ["", "## Audit limitations", "- Yahoo metadata confirms ticker identity and exchange, not historical date coverage.", "- No raw data files, processed datasets, or downloader were created.", "", f"Audit generated: {datetime.now(timezone.utc).isoformat()}"]
    (REPORTS / "yahoo_ticker_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    symbols = extract_symbols()
    session = requests.Session()
    rows = []
    for index, item in symbols.iterrows():
        row = verify_ticker(item["symbol"], item["company_name"], session)
        rows.append(row)
        print(f"[{index + 1}/{len(symbols)}] {row['Yahoo Ticker']} - {row['Status']}")
        if index + 1 < len(symbols):
            time.sleep(1.0)
    write_reports(rows, symbols)
    counts = pd.Series([row["Status"] for row in rows]).value_counts().to_dict()
    print("\nYahoo Ticker Audit Complete")
    print(f"Total SET symbols: {len(rows)}")
    for status in ["VERIFIED", "UNVERIFIED", "AMBIGUOUS", "NOT_FOUND"]:
        print(f"{status.title()}: {counts.get(status, 0)}")
    print("\nManual review required:")
    manual = [row["SET Symbol"] for row in rows if row["Status"] != "VERIFIED"]
    print("\n".join(f"- {symbol}" for symbol in manual) or "- None")
    print("\nNo data / insufficient coverage:")
    print("- All symbols: historical coverage not queried before Gate 1 approval")
    print("\nReports written to reports/yahoo_ticker_audit.csv and reports/yahoo_ticker_audit.md")


if __name__ == "__main__":
    main()

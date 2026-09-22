"""Isolated Yahoo/yfinance availability audit for the 2022_H2-2026_H2 universe.

This script deliberately writes only to data/pilot/historical_set50_availability/
and reports/pilot/. It does not call the production acquisition workflow.
"""

from __future__ import annotations

import argparse
import json
import logging
import platform
import subprocess
import sys
import time
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

import pandas as pd
import yfinance as yf
from yfinance import cache as yf_cache

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.market_data_acquisition import (
    coverage_issues,
    normalize_download_frame,
    validate_raw_frame,
)

CANONICAL_UNIVERSE = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"
PILOT_DIR = ROOT / "data" / "pilot" / "historical_set50_availability"
REPORT_DIR = ROOT / "reports" / "pilot"
AUDIT_PATH = ROOT / "reports" / "yahoo_ticker_audit.csv"
PRODUCTION_RAW_DIR = ROOT / "data" / "raw" / "market_data"
SCOPE_PERIODS = [
    "2022_H2", "2023_H1", "2023_H2", "2024_H1", "2024_H2",
    "2025_H1", "2025_H2", "2026_H1", "2026_H2",
]
H2_SOURCE_URL = "https://media.set.or.th/set/Documents/2022/Jun/SET50_SET100_H2_2022.pdf"
H2_ARCHIVE_URL = "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100"
H2_SYMBOLS = {
    "ADVANC", "AOT", "AWC", "BANPU", "BBL", "BDMS", "BEM", "BGRIM", "BH", "BLA",
    "BTS", "CBG", "CPALL", "CPF", "CPN", "DTAC", "EA", "EGCO", "GLOBAL", "GPSC",
    "GULF", "HMPRO", "INTUCH", "IRPC", "IVL", "JMART", "JMT", "KBANK", "KCE", "KTB",
    "KTC", "LH", "MINT", "MTC", "OR", "OSP", "PTT", "PTTEP", "PTTGC", "SAWAD", "SCB",
    "SCC", "SCGP", "TIDLOR", "TISCO", "TOP", "TRUE", "TTB", "TU", "CRC",
}
KNOWN_CORPORATE_ACTIONS = {
    "SCB": "SCB X / SCBB restructuring boundary requires identity review.",
    "TTB": "TMB to TTB historical identity transition requires date-effective review.",
    "TIDLOR": "2021 listing and 2025 holding-company transition require identity review.",
    "TRUE": "TRUE/TRUEE/DTAC corporate-action history requires identity review.",
    "INTUCH": "INTUCH/GULF combination effective 2025-04-01 requires identity review.",
    "GULF": "INTUCH/GULF combination effective 2025-04-01 requires identity review.",
    "BANPU": "BANPU/BANPUU corporate-action context requires identity review.",
}
LOGGER = logging.getLogger(__name__)


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def build_universe() -> pd.DataFrame:
    canonical = pd.read_csv(CANONICAL_UNIVERSE, dtype=str).fillna("")
    required = {"period", "effective_from", "effective_to", "symbol", "company_name"}
    missing = required - set(canonical.columns)
    if missing:
        raise ValueError(f"Canonical universe missing columns: {sorted(missing)}")
    canonical = canonical[canonical["period"].isin(SCOPE_PERIODS[1:])].copy()
    h2 = pd.DataFrame(
        {
            "period": "2022_H2",
            "effective_from": "2022-07-01",
            "effective_to": "2022-12-31",
            "symbol": sorted(H2_SYMBOLS),
            "company_name": "",
            "source_url": H2_SOURCE_URL,
            "provenance_source_url": H2_ARCHIVE_URL,
            "revision_status": "OFFICIAL_PDF_EXPERIMENT_INPUT",
            "mapping_status": "AS_PUBLISHED_BY_SET",
        }
    )
    return pd.concat([h2, canonical], ignore_index=True, sort=False)


def membership_summary(universe: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, str]] = []
    for symbol, group in universe.groupby("symbol", sort=True):
        periods = sorted(group["period"].unique(), key=SCOPE_PERIODS.index)
        rows.append(
            {
                "symbol": symbol,
                "first_membership_period": periods[0],
                "last_membership_period": periods[-1],
                "membership_periods": ",".join(periods),
            }
        )
    return pd.DataFrame(rows)


def mapping_lookup() -> dict[str, dict[str, str]]:
    frame = pd.read_csv(AUDIT_PATH, dtype=str).fillna("")
    required = {"SET Symbol", "Yahoo Ticker", "Status"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Yahoo audit missing columns: {sorted(missing)}")
    return {
        row["SET Symbol"].strip().upper(): {
            "ticker": row["Yahoo Ticker"].strip(),
            "status": row["Status"].strip(),
        }
        for _, row in frame.iterrows()
    }


def download_with_retry(
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
        except Exception as exc:  # provider/network failures are isolated per ticker
            last_error = exc
            if attempt >= retries:
                break
            delay = backoff_seconds * (2**attempt)
            LOGGER.warning("%s attempt %d failed: %s; retrying in %.1fs", ticker, attempt + 1, exc, delay)
            time.sleep(delay)
    raise RuntimeError(f"download failed after {retries + 1} attempts: {last_error}")


def gap_details(frame: pd.DataFrame) -> tuple[int, int]:
    if frame.empty or "Date" not in frame.columns:
        return 0, 0
    dates = pd.to_datetime(frame["Date"], errors="coerce").dropna().sort_values()
    if len(dates) < 2:
        return 0, 0
    gaps = dates.diff().dropna().dt.days - 1
    material = gaps[gaps > 10]
    return int(len(material)), int(material.max()) if not material.empty else 0


def existing_overlap_note(symbol: str, frame: pd.DataFrame) -> str:
    production = PRODUCTION_RAW_DIR / f"{symbol}.csv"
    mapping = mapping_lookup().get(symbol, {})
    ticker = mapping.get("ticker", "")
    if ticker:
        production = PRODUCTION_RAW_DIR / f"{ticker.replace('.', '_')}.csv"
    if not production.exists() or frame.empty or "Date" not in frame.columns:
        return "no comparable production file"
    existing = pd.read_csv(production, usecols=lambda column: column == "Date")
    pilot_dates = set(pd.to_datetime(frame["Date"], errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
    existing_dates = set(pd.to_datetime(existing["Date"], errors="coerce").dropna().dt.strftime("%Y-%m-%d"))
    overlap = len(pilot_dates & existing_dates)
    return f"production overlap dates={overlap}; production file read-only"


def classify(
    frame: pd.DataFrame,
    expected_start: str,
    expected_end: str,
    validation_issues: list[str],
) -> tuple[str, str, int, int]:
    if frame.empty:
        return "NO_DATA", "FAIL", 0, 0
    gaps, largest = gap_details(frame)
    issues = coverage_issues(frame, expected_start, expected_end)
    all_issues = validation_issues + issues
    validation_status = "PASS" if not validation_issues else "ISSUES"
    actual_start = pd.to_datetime(frame["Date"], errors="coerce").min().date().isoformat()
    actual_end = pd.to_datetime(frame["Date"], errors="coerce").max().date().isoformat()
    complete_boundaries = actual_start <= expected_start and actual_end >= expected_end
    status = "FULL" if complete_boundaries and not all_issues else "PARTIAL"
    return status, validation_status, gaps, largest


def run(*, end_date: str, force: bool, retries: int, backoff_seconds: float, sleep_seconds: float) -> dict[str, Any]:
    universe = build_universe()
    memberships = membership_summary(universe)
    mappings = mapping_lookup()
    expected_end = pd.Timestamp(end_date).date()
    scope_start = "2022-07-01"
    end_exclusive = (expected_end + timedelta(days=1)).isoformat()
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    # Keep yfinance's SQLite cookie/timezone cache inside the isolated pilot area.
    # This avoids depending on a user-level cache that may be unavailable in a
    # managed research environment.
    yf_cache.set_cache_location(str(PILOT_DIR / ".yfinance-cache"))
    records: list[dict[str, Any]] = []

    for index, row in memberships.iterrows():
        symbol = row["symbol"]
        periods = row["membership_periods"].split(",")
        expected_start = universe.loc[universe["symbol"].eq(symbol), "effective_from"].min()
        expected_end_symbol = universe.loc[universe["symbol"].eq(symbol), "effective_to"].max()
        expected_end_symbol = min(pd.Timestamp(expected_end_symbol).date(), expected_end).isoformat()
        mapping = mappings.get(symbol, {})
        ticker = mapping.get("ticker", "")
        mapping_status = mapping.get("status", "UNMAPPED")
        record: dict[str, Any] = {
            "symbol": symbol,
            "yahoo_ticker": ticker,
            "mapping_status": mapping_status,
            "first_membership_period": periods[0],
            "last_membership_period": periods[-1],
            "membership_periods": row["membership_periods"],
            "expected_start": expected_start,
            "expected_end": expected_end_symbol,
            "actual_start": "",
            "actual_end": "",
            "row_count": 0,
            "status": (
                "UNMAPPED" if mapping_status == "UNMAPPED"
                else "NO_DATA" if mapping_status == "NOT_FOUND"
                else "ERROR"
            ),
            "gap_count": 0,
            "largest_gap_days": 0,
            "validation_status": "NOT_RUN",
            "corporate_action_flag": symbol in KNOWN_CORPORATE_ACTIONS,
            "error": "",
            "notes": KNOWN_CORPORATE_ACTIONS.get(symbol, ""),
        }
        if mapping_status != "VERIFIED":
            record["error"] = f"Yahoo mapping status={mapping_status}; no ticker guessed."
            records.append(record)
            continue

        output = PILOT_DIR / f"{ticker.replace('.', '_')}.csv"
        try:
            if output.exists() and not force:
                frame = pd.read_csv(output)
                record["notes"] = (record["notes"] + "; existing pilot file reused" if record["notes"] else "existing pilot file reused")
            else:
                LOGGER.info("[%d/%d] downloading %s", index + 1, len(memberships), ticker)
                frame = normalize_download_frame(
                    download_with_retry(ticker, scope_start, end_exclusive, retries, backoff_seconds),
                    ticker,
                )
                frame.to_csv(output, index=False)
            record["row_count"] = int(len(frame))
            if not frame.empty and "Date" in frame.columns:
                dates = pd.to_datetime(frame["Date"], errors="coerce")
                record["actual_start"] = dates.min().date().isoformat()
                record["actual_end"] = dates.max().date().isoformat()
            issues = validate_raw_frame(frame, symbol=symbol)
            status, validation_status, gaps, largest = classify(frame, expected_start, expected_end_symbol, issues)
            record.update({"status": status, "validation_status": validation_status, "gap_count": gaps, "largest_gap_days": largest})
            record["error"] = "; ".join(issues + coverage_issues(frame, expected_start, expected_end_symbol))
            overlap = existing_overlap_note(symbol, frame)
            record["notes"] = "; ".join(filter(None, [record["notes"], overlap]))
        except Exception as exc:
            record["status"] = "ERROR"
            record["error"] = f"{type(exc).__name__}: {exc}"
        records.append(record)
        if ticker and index + 1 < len(memberships):
            time.sleep(sleep_seconds)

    result = {
        "scope_periods": SCOPE_PERIODS,
        "scope_start": scope_start,
        "scope_end": expected_end.isoformat(),
        "period_count": len(SCOPE_PERIODS),
        "rows": int(len(universe)),
        "unique_symbol_count": int(len(memberships)),
        "mapped_count": int(sum(record["mapping_status"] == "VERIFIED" for record in records)),
        "unmapped_count": int(sum(record["status"] == "UNMAPPED" for record in records)),
        "status_counts": pd.Series([record["status"] for record in records]).value_counts().to_dict(),
        "FULL_count": int(sum(record["status"] == "FULL" for record in records)),
        "PARTIAL_count": int(sum(record["status"] == "PARTIAL" for record in records)),
        "PARTIAL_KNOWN_GAP_count": int(sum(record["status"] == "PARTIAL_KNOWN_GAP" for record in records)),
        "NO_DATA_count": int(sum(record["status"] == "NO_DATA" for record in records)),
        "ERROR_count": int(sum(record["status"] == "ERROR" for record in records)),
        "validation_pass_count": int(sum(record["validation_status"] == "PASS" for record in records)),
        "validation_issue_count": int(sum(record["validation_status"] == "ISSUES" for record in records)),
        "corporate_action_flag_count": int(sum(record["corporate_action_flag"] for record in records)),
        "experiment": {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "branch": git_value("branch", "--show-current"),
            "commit": git_value("rev-parse", "HEAD"),
            "python_version": sys.version,
            "platform": platform.platform(),
            "yfinance_version": getattr(yf, "__version__", "unknown"),
            "source": "Yahoo Finance via yfinance",
            "interval": "1d",
            "auto_adjust": False,
            "actions": True,
            "requested_start_inclusive": scope_start,
            "requested_end_inclusive": expected_end.isoformat(),
            "requested_end_exclusive": end_exclusive,
            "retries": retries,
            "backoff_seconds": backoff_seconds,
            "inter_symbol_sleep_seconds": sleep_seconds,
            "force_download": force,
            "production_files_modified": False,
        },
        "membership": memberships.to_dict(orient="records"),
        "records": records,
    }
    pd.DataFrame(records).to_csv(REPORT_DIR / "historical_set50_data_availability.csv", index=False)
    memberships.to_csv(REPORT_DIR / "historical_set50_data_availability_membership.csv", index=False)
    (REPORT_DIR / "historical_set50_data_availability.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(result)
    return result


def write_markdown(result: dict[str, Any]) -> None:
    records = result["records"]
    counts = result["status_counts"]
    lines = [
        "# Historical SET50 Data Availability Experiment",
        "",
        "## 1. Objective",
        "Measure Yahoo/yfinance daily OHLCV availability without modifying production data.",
        "",
        "## 2. Scope",
        f"- Periods: `{', '.join(result['scope_periods'])}`",
        f"- Requested range: `{result['scope_start']}` through `{result['scope_end']}` inclusive",
        f"- Period rows: `{result['rows']}`; periods: `{result['period_count']}`; unique symbols: `{result['unique_symbol_count']}`",
        "- 2022_H1 was intentionally excluded.",
        "",
        "## 3. Universe",
        "2022_H2 was supplied from the official SET H2 2022 PDF as an experiment-only input; 2023_H1 onward was read from the canonical processed universe.",
        "",
        "## 4. Yahoo Mapping Coverage",
        f"- Verified mappings: `{result['mapped_count']}`",
        f"- Unmapped/non-verified: `{result['unmapped_count']}`",
        "- No ticker was guessed or written back to the production audit.",
        "",
        "## 5. Download Method",
        "- Yahoo Finance via yfinance; interval `1d`; `auto_adjust=False`; `actions=True`.",
        "- Pilot CSVs are stored under `data/pilot/historical_set50_availability/`.",
        "- Production acquisition was not called.",
        "",
        "## 6. Validation Method",
        "Reused `normalize_download_frame`, `validate_raw_frame`, and `coverage_issues` from `src/data/market_data_acquisition.py`. No filling, repairing, row deletion, or tolerance changes were performed.",
        "",
        "## 7. Availability Results",
    ]
    for status in ["FULL", "PARTIAL", "PARTIAL_KNOWN_GAP", "NO_DATA", "ERROR", "UNMAPPED"]:
        lines.append(f"- `{status}`: `{counts.get(status, 0)}`")
    lines += [
        "",
        "## 8. Missing / Partial Symbols",
    ]
    for record in records:
        if record["status"] in {"PARTIAL", "PARTIAL_KNOWN_GAP", "NO_DATA", "ERROR", "UNMAPPED"}:
            lines.append(f"- `{record['symbol']}` `{record['status']}`: {record['error'] or 'no additional error'}")
    lines += ["", "## 9. Corporate Action Flags"]
    for record in records:
        if record["corporate_action_flag"]:
            lines.append(f"- `{record['symbol']}`: {record['notes']}")
    lines += [
        "",
        "## 10. Source/Data Issues",
        "Availability and validity are reported separately. A returned series with OHLC or coverage issues remains an observed source result and is not repaired.",
        "",
        "## 11. Key Findings",
        "See the CSV/JSON records for per-symbol actual dates, row counts, gap measurements, validation status, and production overlap notes.",
        "",
        "## 12. Limitations",
        "- The experiment uses observed dates, not an official Thailand trading-calendar utility.",
        "- A date gap is not classified as a market closure without independent evidence.",
        "- Corporate-action flags are not resolved in this step.",
        "",
        "## 13. Recommended Next Step",
        "Review partial histories and corporate-action flags before any research approval or backtest use.",
        "",
        "## Reproducibility",
        f"- Branch: `{result['experiment']['branch']}`",
        f"- Commit: `{result['experiment']['commit']}`",
        f"- yfinance: `{result['experiment']['yfinance_version']}`",
        f"- Experiment timestamp UTC: `{result['experiment']['timestamp_utc']}`",
        "- Production files modified: `False`",
    ]
    (REPORT_DIR / "historical_set50_data_availability.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--end", default=date.today().isoformat(), help="inclusive experiment end date")
    parser.add_argument("--force", action="store_true", help="redownload pilot files")
    parser.add_argument("--retries", type=int, default=3)
    parser.add_argument("--backoff-seconds", type=float, default=2.0)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run(
        end_date=args.end,
        force=args.force,
        retries=args.retries,
        backoff_seconds=args.backoff_seconds,
        sleep_seconds=args.sleep_seconds,
    )
    print(json.dumps({"unique_symbol_count": result["unique_symbol_count"], "status_counts": result["status_counts"]}, indent=2))


if __name__ == "__main__":
    main()

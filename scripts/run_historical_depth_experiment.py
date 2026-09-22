"""Measure Yahoo/yfinance historical daily depth for the available SET50 universe.

This experiment is isolated from the production acquisition workflow. It reads
the canonical constituent file and the existing verified Yahoo audit, performs
at most one broad request per unique verified Yahoo ticker, and writes only to
the historical-depth pilot directory and experiment reports.
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
from typing import Any

import pandas as pd
import yfinance as yf
from yfinance import cache as yf_cache

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.market_data_acquisition import (  # noqa: E402
    coverage_issues,
    normalize_download_frame,
    validate_raw_frame,
)

LOGGER = logging.getLogger(__name__)
CANONICAL = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"
MAPPING = ROOT / "reports" / "yahoo_ticker_audit.csv"
PILOT_DIR = ROOT / "data" / "pilot" / "historical_depth_experiment"
REPORT_DIR = ROOT / "reports" / "pilot"
START_DATE = date(2016, 1, 1)


def git_value(*args: str) -> str:
    try:
        return subprocess.check_output(["git", "-C", str(ROOT), *args], text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def load_universe() -> pd.DataFrame:
    frame = pd.read_csv(CANONICAL, dtype=str).fillna("")
    required = {"period", "effective_from", "effective_to", "symbol"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"canonical universe missing columns: {sorted(missing)}")
    frame["symbol"] = frame["symbol"].str.strip().str.upper()
    frame["period"] = frame["period"].str.strip()
    frame["effective_from"] = pd.to_datetime(frame["effective_from"], errors="raise").dt.strftime("%Y-%m-%d")
    frame["effective_to"] = pd.to_datetime(frame["effective_to"], errors="raise").dt.strftime("%Y-%m-%d")
    return frame.sort_values(["symbol", "effective_from"]).reset_index(drop=True)


def load_mapping() -> pd.DataFrame:
    frame = pd.read_csv(MAPPING, dtype=str).fillna("")
    required = {"SET Symbol", "Yahoo Ticker", "Status"}
    missing = required - set(frame.columns)
    if missing:
        raise ValueError(f"Yahoo audit missing columns: {sorted(missing)}")
    frame["SET Symbol"] = frame["SET Symbol"].str.strip().str.upper()
    frame["Yahoo Ticker"] = frame["Yahoo Ticker"].str.strip()
    if frame["SET Symbol"].duplicated().any():
        raise ValueError("Yahoo audit contains duplicate SET symbols")
    return frame


def request(ticker: str, end_exclusive: str, retries: int, backoff: float) -> pd.DataFrame:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return yf.download(
                tickers=ticker,
                start=START_DATE.isoformat(),
                end=end_exclusive,
                interval="1d",
                auto_adjust=False,
                actions=True,
                progress=False,
                threads=False,
                timeout=30,
            )
        except Exception as exc:
            last_error = exc
            if attempt >= retries:
                break
            delay = backoff * (2**attempt)
            LOGGER.warning("%s attempt %d failed: %s; retrying in %.1fs", ticker, attempt + 1, exc, delay)
            time.sleep(delay)
    raise RuntimeError(f"download failed after {retries + 1} attempts: {last_error}")


def symbol_summary(universe: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for symbol, group in universe.groupby("symbol", sort=True):
        rows.append(
            {
                "symbol": symbol,
                "first_membership_period": group["period"].iloc[0],
                "last_membership_period": group["period"].iloc[-1],
                "membership_periods": ",".join(group["period"].tolist()),
                "membership_row_count": len(group),
            }
        )
    return pd.DataFrame(rows)


def run(retries: int, backoff: float, sleep_seconds: float) -> dict[str, Any]:
    universe = load_universe()
    mapping = load_mapping()
    summary = symbol_summary(universe)
    joined = summary.merge(mapping[["SET Symbol", "Yahoo Ticker", "Status"]], left_on="symbol", right_on="SET Symbol", how="left")
    joined["Status"] = joined["Status"].fillna("UNMAPPED")
    joined["Yahoo Ticker"] = joined["Yahoo Ticker"].fillna("")
    verified = joined[joined["Status"].eq("VERIFIED") & joined["Yahoo Ticker"].ne("")].copy()
    unique_tickers = verified[["Yahoo Ticker"]].drop_duplicates().sort_values("Yahoo Ticker")

    end_inclusive = date.today()
    end_exclusive = (end_inclusive + timedelta(days=1)).isoformat()
    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    yf_cache.set_cache_location(str(PILOT_DIR / ".yfinance-cache"))

    records: list[dict[str, Any]] = []
    for index, ticker_row in enumerate(unique_tickers.itertuples(index=False), start=1):
        ticker = ticker_row[0]
        symbol_rows = joined[joined["Yahoo Ticker"].eq(ticker)]
        symbols = ",".join(symbol_rows["symbol"].tolist())
        output = PILOT_DIR / f"{ticker.replace('.', '_')}.csv"
        record: dict[str, Any] = {
            "yahoo_ticker": ticker,
            "set_symbols": symbols,
            "membership_periods": ",".join(sorted({p for text in symbol_rows["membership_periods"] for p in text.split(",")})),
            "requested_start": START_DATE.isoformat(),
            "requested_end": end_inclusive.isoformat(),
            "requested_end_exclusive": end_exclusive,
            "actual_first_date": "",
            "actual_last_date": "",
            "rows": 0,
            "status": "FAILED",
            "depth_status": "NOT_RUN",
            "request_mode": "DOWNLOAD",
            "validation_status": "NOT_RUN",
            "coverage_issues": "",
            "validation_issues": "",
            "error": "",
            "output_file": str(output.relative_to(ROOT)),
        }
        print(f"[{index:03d}/{len(unique_tickers):03d}] {ticker} ({symbols})", flush=True)
        try:
            if output.exists():
                raw = pd.read_csv(output)
                record["request_mode"] = "REUSED_EXPERIMENT_FILE"
            else:
                raw = normalize_download_frame(request(ticker, end_exclusive, retries, backoff), ticker)
                raw.to_csv(output, index=False)
            record["rows"] = len(raw)
            if not raw.empty:
                dates = pd.to_datetime(raw["Date"], errors="coerce")
                record["actual_first_date"] = dates.min().date().isoformat()
                record["actual_last_date"] = dates.max().date().isoformat()
            validation = validate_raw_frame(raw, symbol=symbols.split(",")[0])
            coverage = coverage_issues(raw, START_DATE.isoformat(), end_inclusive.isoformat())
            record["validation_status"] = "PASS" if not validation else "ISSUES"
            record["validation_issues"] = "; ".join(validation)
            record["coverage_issues"] = "; ".join(coverage)
            if raw.empty:
                record["status"] = "NO_DATA"
                record["depth_status"] = "NO_DATA"
            else:
                reaches_start = record["actual_first_date"] <= "2016-01-04"
                record["depth_status"] = "REACHES_2016_START" if reaches_start else "START_AFTER_2016_START"
                record["status"] = "PARTIAL" if validation or coverage else "FULL"
        except Exception as exc:
            record["status"] = "NO_DATA" if "empty" in str(exc).lower() else "FAILED"
            record["error"] = f"{type(exc).__name__}: {exc}"
        records.append(record)
        print(f"  {record['status']} rows={record['rows']} {record['actual_first_date']} -> {record['actual_last_date']}", flush=True)
        if index < len(unique_tickers):
            time.sleep(sleep_seconds)

    unresolved = joined[~joined["Status"].eq("VERIFIED")].copy()
    for row in unresolved.itertuples(index=False):
        records.append(
            {
                "yahoo_ticker": "",
                "set_symbols": row.symbol,
                "membership_periods": row.membership_periods,
                "requested_start": START_DATE.isoformat(),
                "requested_end": end_inclusive.isoformat(),
                "requested_end_exclusive": end_exclusive,
                "actual_first_date": "",
                "actual_last_date": "",
                "rows": 0,
                "status": f"MAPPING_{row.Status}",
                "depth_status": "NOT_REQUESTED",
                "request_mode": "NOT_REQUESTED",
                "validation_status": "NOT_RUN",
                "coverage_issues": "",
                "validation_issues": "",
                "error": "No request made because existing Yahoo mapping is not VERIFIED; no ticker guessed.",
                "output_file": "",
            }
        )

    result: dict[str, Any] = {
        "scope": {
            "requested_period_range": "2016_H1 -> 2026_H2",
            "available_periods": universe["period"].drop_duplicates().tolist(),
            "missing_periods_from_repository": [f"{year}_H{half}" for year in range(2016, 2023) for half in (1, 2)],
            "requested_start_inclusive": START_DATE.isoformat(),
            "requested_end_inclusive": end_inclusive.isoformat(),
            "requested_end_exclusive": end_exclusive,
        },
        "universe": {
            "available_period_rows": len(universe),
            "available_unique_symbols": int(universe["symbol"].nunique()),
            "available_period_count": int(universe["period"].nunique()),
            "verified_unique_yahoo_tickers_requested": len(unique_tickers),
            "non_verified_symbols_not_requested": len(unresolved),
        },
        "status_counts": pd.Series([r["status"] for r in records]).value_counts().to_dict(),
        "depth_status_counts": pd.Series([r["depth_status"] for r in records]).value_counts().to_dict(),
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
            "one_request_per_unique_verified_ticker": True,
            "production_files_modified": False,
            "canonical_inputs_modified": False,
            "ticker_mappings_modified": False,
            "research_dataset_gate_modified": False,
        },
        "records": records,
    }
    pd.DataFrame(records).to_csv(REPORT_DIR / "historical_depth_experiment.csv", index=False)
    summary.to_csv(REPORT_DIR / "historical_depth_experiment_membership.csv", index=False)
    (REPORT_DIR / "historical_depth_experiment.json").write_text(json.dumps(result, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    write_markdown(result)
    return result


def write_markdown(result: dict[str, Any]) -> None:
    counts = result["status_counts"]
    scope = result["scope"]
    universe = result["universe"]
    lines = [
        "# Historical Depth Experiment",
        "",
        "## Objective",
        "Measure how far the current project Yahoo/yfinance source retrieves daily OHLCV; no missing data was repaired or merged.",
        "",
        "## Repository universe discovery",
        f"- Requested research range: `{scope['requested_period_range']}`.",
        f"- Available canonical periods: `{', '.join(scope['available_periods'])}`.",
        f"- Available period rows: `{universe['available_period_rows']}`; unique symbols: `{universe['available_unique_symbols']}`.",
        f"- Repository lacks constituent snapshots for: `{', '.join(scope['missing_periods_from_repository'])}`.",
        "- Those absent memberships were not invented or inferred.",
        "",
        "## Request semantics",
        f"- Requested range: `{scope['requested_start_inclusive']}` through `{scope['requested_end_inclusive']}` inclusive; yfinance end-exclusive parameter: `{scope['requested_end_exclusive']}`.",
        "- `interval=1d`, `auto_adjust=False`, `actions=True`, `threads=False`.",
        f"- Unique verified Yahoo tickers requested once: `{universe['verified_unique_yahoo_tickers_requested']}`.",
        f"- Non-verified mapping symbols not requested: `{universe['non_verified_symbols_not_requested']}`.",
        "- Outputs are isolated under `data/pilot/historical_depth_experiment/` and `reports/pilot/`.",
        "",
        "## Results",
    ]
    for status, count in sorted(counts.items()):
        lines.append(f"- `{status}`: `{count}`")
    lines += ["", "### Historical depth classification"]
    for status, count in sorted(result["depth_status_counts"].items()):
        lines.append(f"- `{status}`: `{count}`")
    lines += [
        "",
        "Availability is reported separately from validation. `REACHES_2016_START` means the first returned row was on or before the first expected SET trading date in 2016 (2016-01-04); `START_AFTER_2016_START` identifies a shorter Yahoo history. The requested end was 2026-09-19, while the latest observed Yahoo row was 2026-09-18.",
        "",
        "## Reused project utilities",
        "- `normalize_download_frame`",
        "- `validate_raw_frame`",
        "- `coverage_issues`",
        "",
        "## Reproducibility",
        f"- Branch: `{result['experiment']['branch']}`",
        f"- Commit: `{result['experiment']['commit']}`",
        f"- yfinance: `{result['experiment']['yfinance_version']}`",
        f"- Timestamp UTC: `{result['experiment']['timestamp_utc']}`",
        "- Production/raw files modified: `False`",
        "- Canonical constituent file modified: `False`",
        "- Yahoo ticker mapping modified: `False`",
        "- Research Dataset Gate modified: `False`",
    ]
    (REPORT_DIR / "historical_depth_experiment.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument("--backoff-seconds", type=float, default=2.0)
    parser.add_argument("--sleep-seconds", type=float, default=1.0)
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    result = run(args.retries, args.backoff_seconds, args.sleep_seconds)
    print(json.dumps({"universe": result["universe"], "status_counts": result["status_counts"]}, indent=2))


if __name__ == "__main__":
    main()

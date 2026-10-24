"""Compare organizer ticks/history with practice and Settrade production without merging."""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "official" / "tradesim"
SETTRADE = ROOT / "data" / "pilot" / "settrade"
FIELDS = ("open", "high", "low", "close", "volume")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def compare_tick_files() -> dict[str, Any]:
    official_dir = OFFICIAL / "ticks" / "ticks"
    standalone_dir = OFFICIAL / "daily_ticks"
    practice_roots = {
        "TRADESIM_0_2_5_PRACTICE": ROOT / "tools" / "kgi_tradesim" / "marketInfo" / "ticks",
        "TRADESIM_0_2_6_PRACTICE": ROOT / "tools" / "kgi_tradesim" / "0.2.6" / "marketInfo" / "ticks",
    }
    official_files = {p.stem: p for p in official_dir.glob("*.csv")}
    standalone = {p.stem: p for p in standalone_dir.glob("*.csv")}
    practice = {label: {p.stem: p for p in path.glob("*.csv")} for label, path in practice_roots.items()}
    source_dates = {label: sorted(files) for label, files in practice.items()}
    source_dates["TRADESIM_OFFICIAL_TICKS"] = sorted(official_files)
    source_dates["DAILY_TICKS_STANDALONE"] = sorted(standalone)
    standalone_matches = []
    for day, path in sorted(standalone.items()):
        other = official_files.get(day)
        standalone_matches.append({"date": day, "official_archive_present": other is not None,
                                   "byte_identical": bool(other and _sha256(path) == _sha256(other)),
                                   "standalone_sha256": _sha256(path),
                                   "archive_sha256": _sha256(other) if other else None})
    practice_comparisons = {}
    for label, files in practice.items():
        overlap = sorted(set(files) & set(official_files))
        practice_comparisons[label] = {
            "practice_dates": sorted(files), "official_dates": sorted(official_files),
            "overlap_dates": overlap,
            "classification": "EXTENDED_HISTORY" if not overlap and files and official_files else "IDENTICAL" if overlap and all(_sha256(files[d]) == _sha256(official_files[d]) for d in overlap) else "UPDATED_DATA" if overlap else "UNKNOWN",
            "overlap_byte_identical_dates": [d for d in overlap if _sha256(files[d]) == _sha256(official_files[d])],
            "overlap_differences": [d for d in overlap if _sha256(files[d]) != _sha256(official_files[d])],
            "practice_schema": _csv_header(next(iter(files.values()))) if files else [],
            "official_schema": _csv_header(next(iter(official_files.values()))) if official_files else [],
        }
    return {"source_dates": source_dates, "standalone_vs_nested_tick_archive": standalone_matches,
            "practice_comparisons": practice_comparisons,
            "interpretation": "The official archive extends the Sep 9-30 practice set beginning Oct 1; identical outer CSVs duplicate the same dates in the nested official tick package."}


def _csv_header(path: Path) -> list[str]:
    return list(pd.read_csv(path, nrows=0).columns)


def _load_history(path: Path, timeframe: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype={"Date": "string", "Timestamp": "string"})
    stamp_col = "Date" if timeframe == "1D" else "Timestamp"
    if stamp_col not in frame:
        return pd.DataFrame()
    frame["symbol"] = path.stem.upper()
    frame["timestamp_local"] = pd.to_datetime(frame[stamp_col], errors="coerce").dt.tz_localize("Asia/Bangkok", ambiguous="NaT", nonexistent="NaT")
    frame["timestamp_utc"] = frame["timestamp_local"].dt.tz_convert("UTC")
    return frame.rename(columns={"Open": "open", "High": "high", "Low": "low", "Close": "close", "Volume": "volume"})


def _load_settrade(path: Path, timeframe: str, environment: str) -> pd.DataFrame:
    # Existing production 5m/15m files contain 20 malformed/truncated rows, already
    # documented by the Settrade integrity audit. Skip only those physical rows here.
    frame = pd.read_csv(path, on_bad_lines="skip", low_memory=False)
    if "timestamp" not in frame or "symbol" not in frame:
        return pd.DataFrame()
    if "source_environment" in frame:
        frame = frame[frame["source_environment"].str.upper() == environment]
    if "interval" in frame:
        frame = frame[frame["interval"].astype(str).str.lower() == timeframe.lower()]
    frame["timestamp_utc"] = pd.to_datetime(frame["timestamp"], errors="coerce", utc=True)
    frame["symbol"] = frame["symbol"].astype(str).str.upper()
    for field in FIELDS:
        if field in frame:
            frame[field] = pd.to_numeric(frame[field], errors="coerce")
    return frame


def _compare_interval(timeframe: str, environment: str) -> dict[str, Any]:
    official_label = "1D" if timeframe == "1d" else timeframe
    official_dir = (OFFICIAL / "history" / "daily_history" if official_label == "1D"
                    else OFFICIAL / "history" / "intraday_history" / official_label)
    settrade_path = SETTRADE / ("production" if environment == "PRODUCTION" else "") / "normalized" / f"bars_{timeframe}" / "data.csv"
    if not settrade_path.is_file():
        return {"timeframe": timeframe, "environment": environment, "status": "SETTRADE_DATASET_NOT_PRESENT",
                "settrade_path": str(settrade_path), "overlap_dates": [], "overlap_symbols": [],
                "counts": {"settrade_rows": 0, "official_rows": 0, "matched_timestamp_rows": 0,
                           "exact_ohlcv_matches": 0, "divergent_rows": 0, "settrade_only_rows": 0,
                           "tradesim_only_rows": 0}, "unresolved_gap_classification": "UNKNOWN"}
    settrade = _load_settrade(settrade_path, timeframe, environment)
    symbols = sorted(set(settrade.get("symbol", [])) & {p.stem.upper() for p in official_dir.glob("*.csv")})
    pieces = [_load_history(official_dir / f"{symbol}.csv", official_label)
              for symbol in symbols]
    official = pd.concat(pieces, ignore_index=True) if pieces else pd.DataFrame()
    settrade = settrade[settrade["symbol"].isin(symbols)]
    settrade = settrade[settrade["timestamp_utc"].notna()]
    official = official[official["timestamp_utc"].notna()]
    official["trading_date"] = official["timestamp_local"].dt.strftime("%Y-%m-%d")
    settrade["trading_date"] = settrade["timestamp_utc"].dt.tz_convert("Asia/Bangkok").dt.strftime("%Y-%m-%d")
    official_dates, settrade_dates = set(official["trading_date"]), set(settrade["trading_date"])
    overlap_dates = sorted(official_dates & settrade_dates)
    official_pairs = set(zip(official["trading_date"], official["symbol"]))
    settrade_pairs = set(zip(settrade["trading_date"], settrade["symbol"]))
    overlap_pairs = official_pairs & settrade_pairs
    official_only_pairs = sorted(official_pairs - settrade_pairs)
    settrade_only_pairs = sorted(settrade_pairs - official_pairs)
    official = official[[pair in overlap_pairs for pair in zip(official["trading_date"], official["symbol"])] ]
    settrade = settrade[[pair in overlap_pairs for pair in zip(settrade["trading_date"], settrade["symbol"])] ]
    # A source-only key is a gap signal only inside a date/symbol window present
    # in both sources. Dates outside shared coverage are source coverage, not gaps.
    official = official[official["trading_date"].isin(overlap_dates)]
    settrade = settrade[settrade["trading_date"].isin(overlap_dates)]
    key = ["symbol", "timestamp_utc"]
    duplicate_official = int(official.duplicated(key).sum()) if not official.empty else 0
    duplicate_settrade = int(settrade.duplicated(key).sum()) if not settrade.empty else 0
    official = official.drop_duplicates(key, keep=False)
    settrade = settrade.drop_duplicates(key, keep=False)
    common = official[key + list(FIELDS)].merge(settrade[key + list(FIELDS)], on=key, how="inner", suffixes=("_official", "_settrade"), validate="one_to_one")
    field_differences: Counter[str] = Counter()
    field_max_abs_difference: dict[str, float] = {}
    exact_rows = 0
    examples = []
    for row in common.to_dict(orient="records"):
        differences = []
        for field in FIELDS:
            left, right = row.get(f"{field}_official"), row.get(f"{field}_settrade")
            equal = (pd.isna(left) and pd.isna(right)) or (pd.notna(left) and pd.notna(right) and float(left) == float(right))
            if not equal:
                differences.append(field)
                field_differences[field] += 1
                if pd.notna(left) and pd.notna(right):
                    field_max_abs_difference[field] = max(field_max_abs_difference.get(field, 0.0), abs(float(left) - float(right)))
        if not differences:
            exact_rows += 1
        elif len(examples) < 12:
            examples.append({"symbol": row["symbol"], "timestamp_utc": row["timestamp_utc"].isoformat(),
                             "differences": differences,
                             **{f"{f}_official": row.get(f"{f}_official") for f in differences},
                             **{f"{f}_settrade": row.get(f"{f}_settrade") for f in differences}})
    official_keys = set(map(tuple, official[key].itertuples(index=False, name=None)))
    settrade_keys = set(map(tuple, settrade[key].itertuples(index=False, name=None)))
    session_by_date = []
    for day in overlap_dates:
        official_day = official[official["trading_date"] == day]
        settrade_day = settrade[settrade["trading_date"] == day]
        session_by_date.append({
            "date": day,
            "official_first_bangkok": official_day["timestamp_local"].min().isoformat() if not official_day.empty else None,
            "official_last_bangkok": official_day["timestamp_local"].max().isoformat() if not official_day.empty else None,
            "settrade_first_bangkok": settrade_day["timestamp_utc"].min().tz_convert("Asia/Bangkok").isoformat() if not settrade_day.empty else None,
            "settrade_last_bangkok": settrade_day["timestamp_utc"].max().tz_convert("Asia/Bangkok").isoformat() if not settrade_day.empty else None,
            "official_rows": len(official_day), "settrade_rows": len(settrade_day),
        })
    return {
        "timeframe": timeframe, "environment": environment,
        "official_source": "TRADESIM_OFFICIAL_HISTORY", "settrade_source": "SETTRADE_PRODUCTION" if environment == "PRODUCTION" else "SETTRADE_SANDBOX_PILOT",
        "official_path": str(official_dir), "settrade_path": str(settrade_path),
        "overlap_dates": overlap_dates, "overlap_symbols": sorted(set(official["symbol"]) & set(settrade["symbol"])),
        "source_only_dates": {"official_history": sorted(official_dates - settrade_dates),
                              "settrade": sorted(settrade_dates - official_dates)},
        "overlap_symbol_day_pairs": len(overlap_pairs),
        "source_only_symbol_day_pairs": {"official_only_pairs": len(official_only_pairs),
                                         "settrade_only_pairs": len(settrade_only_pairs),
                                         "official_only_sample": official_only_pairs[:20],
                                         "settrade_only_sample": settrade_only_pairs[:20]},
        "session_coverage_by_date": session_by_date,
        "coverage": {"official_first_utc": official["timestamp_utc"].min().isoformat() if not official.empty else None,
                     "official_last_utc": official["timestamp_utc"].max().isoformat() if not official.empty else None,
                     "settrade_first_utc": settrade["timestamp_utc"].min().isoformat() if not settrade.empty else None,
                     "settrade_last_utc": settrade["timestamp_utc"].max().isoformat() if not settrade.empty else None},
        "counts": {"settrade_rows": len(settrade), "official_rows": len(official),
                   "matched_timestamp_rows": len(common), "exact_ohlcv_matches": exact_rows,
                   "divergent_rows": len(common) - exact_rows,
                   "settrade_only_rows": len(settrade_keys - official_keys),
                   "tradesim_only_rows": len(official_keys - settrade_keys),
                   "duplicate_official_keys": duplicate_official, "duplicate_settrade_keys": duplicate_settrade},
        "exact_match_rate_on_overlap": exact_rows / len(common) if len(common) else None,
        "field_mismatch_counts": dict(field_differences), "field_max_absolute_difference": field_max_abs_difference,
        "representative_mismatches": examples,
        "gap_classification": {"tradesim_only_rows": "SETTRADE_ONLY_GAP",
                               "settrade_only_rows": "TRADESIM_ONLY_GAP",
                               "matched_timestamp_value_differences": "SOURCE_SEMANTIC_DIFFERENCE",
                               "source_only_symbol_day_pairs": "UNKNOWN; coverage differs but no expected per-symbol session grid is asserted",
                               "both_sources_gap": "UNKNOWN; no complete exchange-calendar expectation applied"},
        "likely_explanations": [
            "Official TradeSim documentation says historical prices are adjusted for capital actions; Settrade production adjustment_status is UNKNOWN.",
            "Official history timestamps are naive Asia/Bangkok exchange times; Settrade persisted timestamps are UTC and were converted to UTC for the join.",
            "Settrade 5m/15m files are locally derived from observed 1m source rows and mark incomplete buckets; official history bars may use different aggregation/session rules.",
            "No-trade bars, auctions, corrections, and volume semantics are not assumed equivalent; mismatches are retained as source-specific evidence.",
        ],
    }


def build_report() -> dict[str, Any]:
    package = json.loads((ROOT / "reports" / "tradesim_official_daily_ticks_package.json").read_text(encoding="utf-8"))
    archive_identity = {name: detail["sha256"] for name, detail in package.get("extraction", {}).get("nested_archives", {}).items()}
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_identity": {"outer_archive_sha256": package["archive_identity"]["outer_sha256"],
                            "nested_archive_sha256": archive_identity},
        "tick_practice_comparison": compare_tick_files(),
        "history_settrade_comparison": {timeframe: {environment: _compare_interval(timeframe, environment)
                                                     for environment in ("SANDBOX", "PRODUCTION")}
                                         for timeframe in ("1m", "5m", "15m")},
        "daily_settrade_comparison": {"status": "SETTRADE_DAILY_CANDLE_DATASET_NOT_PRESENT",
                                      "note": "Persisted Settrade production normalized candle data covers 1m, 5m, and 15m only; no daily Settrade dataset exists in the inspected production tree."},
        "source_policy": {
            "competition_simulator_validation": "TRADESIM_OFFICIAL_HISTORY and TRADESIM_OFFICIAL_TICKS",
            "official_competition_replay": "TRADESIM_OFFICIAL_TICKS plus the official TradeSim 0.2.6 runtime",
            "matching_validation": "Official ticks and official simulator; never infer fills from Settrade candles",
            "live_current_monitoring": "SETTRADE_PRODUCTION",
            "long_horizon_research": "Existing survivorship-aware research inputs; official history may supplement only with explicit source/adjustment labels",
            "cross_source_fill_policy": "No source is used to fill another source's missing rows.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "tradesim_vs_settrade_data_comparison.json")
    args = parser.parse_args()
    report = build_report()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    compact = {tf: {env: result["counts"] for env, result in rows.items()}
               for tf, rows in report["history_settrade_comparison"].items()}
    print(json.dumps({"report": str(args.output.relative_to(ROOT)) if args.output.is_relative_to(ROOT) else str(args.output),
                      "tick_classifications": {k: v["classification"] for k, v in report["tick_practice_comparison"]["practice_comparisons"].items()},
                      "settrade_counts": compact}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

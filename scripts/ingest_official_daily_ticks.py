"""Preserve and inventory the organizer Daily_Ticks package without merging sources."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUTER_NAME = "Daily_Ticks.zip"
SOURCE = "TRADESIM_OFFICIAL_TICKS"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _safe_parts(name: str) -> tuple[str, ...]:
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or not path.parts:
        raise ValueError(f"Unsafe ZIP member path: {name}")
    return path.parts


def _field(fields: list[str], *candidates: str) -> str | None:
    by_lower = {name.lower(): name for name in fields}
    return next((by_lower[name.lower()] for name in candidates if name.lower() in by_lower), None)


def inventory_csv(path: Path, *, archive_member: str | None = None,
                  data: bytes | None = None) -> dict[str, Any]:
    """Stream one CSV and collect structural checks without rewriting its bytes."""
    if data is None:
        with path.open("rb") as stream:
            raw = stream.read()
    else:
        raw = data
    digest = sha256_bytes(raw)
    rows = 0
    malformed_rows = 0
    invalid_timestamps = 0
    invalid_numeric_values = 0
    invalid_price_rows = 0
    negative_volume_rows = 0
    invalid_ohlc_rows = 0
    duplicate_rows = 0
    out_of_order_timestamps = 0
    out_of_order_within_symbol = 0
    duplicate_symbol_timestamps = 0
    symbols: set[str] = set()
    dates: set[str] = set()
    first_timestamp: str | None = None
    last_timestamp: str | None = None
    minimum_timestamp: str | None = None
    maximum_timestamp: str | None = None
    previous_timestamp: str | None = None
    previous_by_symbol: dict[str, str] = {}
    seen_symbol_timestamps: set[tuple[str, str]] = set()
    validation_examples: list[dict[str, Any]] = []
    duplicate_hashes: set[str] = set()
    schema: list[str] = []
    numeric_value_counts: dict[str, int] = {}
    sample: list[dict[str, str | None]] = []
    try:
        text = raw.decode("utf-8-sig")
        reader = csv.DictReader(text.splitlines())
        schema = reader.fieldnames or []
        numeric_value_counts = {column: 0 for column in schema}
        time_col = _field(schema, "TradeDateTime", "Timestamp", "Date", "Time")
        symbol_col = _field(schema, "ShareCode", "Symbol", "symbol")
        open_col, high_col = _field(schema, "Open"), _field(schema, "High")
        low_col, close_col = _field(schema, "Low"), _field(schema, "Close")
        volume_col = _field(schema, "Volume", "TradeVolume", "Qty", "Quantity")
        price_col = _field(schema, "Price", "LastPrice", "TradePrice")
        for row in reader:
            rows += 1
            if None in row:
                malformed_rows += 1
            symbol = (row.get(symbol_col) or "").strip() if symbol_col else ""
            stamp = (row.get(time_col) or "").strip() if time_col else ""
            if symbol:
                symbols.add(symbol)
            if stamp:
                dates.add(stamp[:10])
                if first_timestamp is None:
                    first_timestamp = stamp
                minimum_timestamp = stamp if minimum_timestamp is None else min(minimum_timestamp, stamp)
                maximum_timestamp = stamp if maximum_timestamp is None else max(maximum_timestamp, stamp)
                if previous_timestamp is not None and stamp < previous_timestamp:
                    out_of_order_timestamps += 1
                previous_timestamp = stamp
                if symbol and (symbol, stamp) in seen_symbol_timestamps:
                    duplicate_symbol_timestamps += 1
                if symbol:
                    seen_symbol_timestamps.add((symbol, stamp))
                    if symbol in previous_by_symbol and stamp < previous_by_symbol[symbol]:
                        out_of_order_within_symbol += 1
                    previous_by_symbol[symbol] = stamp
                last_timestamp = stamp
                try:
                    datetime.fromisoformat(stamp.replace("Z", "+00:00"))
                except ValueError:
                    invalid_timestamps += 1
            elif time_col:
                invalid_timestamps += 1
            numeric_names = [c for c in (open_col, high_col, low_col, close_col, volume_col, price_col) if c]
            numbers: dict[str, float] = {}
            for column in numeric_names:
                value = (row.get(column) or "").strip().replace(",", "")
                try:
                    number = float(value)
                    if number != number or number in (float("inf"), float("-inf")):
                        raise ValueError
                    numbers[column] = number
                    numeric_value_counts[column] = numeric_value_counts.get(column, 0) + 1
                except ValueError:
                    invalid_numeric_values += 1
            price_fields = [column for column in (open_col, high_col, low_col, close_col, price_col) if column]
            if any(column not in numbers or numbers[column] <= 0 for column in price_fields):
                invalid_price_rows += 1
            if volume_col and (volume_col not in numbers or numbers[volume_col] < 0):
                negative_volume_rows += 1
            if all(column and column in numbers for column in (open_col, high_col, low_col, close_col)):
                op, hi, lo, cl = (numbers[column] for column in (open_col, high_col, low_col, close_col))
                if min(op, hi, lo, cl) <= 0 or hi < max(op, cl) or lo > min(op, cl) or hi < lo:
                    invalid_ohlc_rows += 1
                    if len(validation_examples) < 10:
                        validation_examples.append({"issue": "INVALID_OHLC", "row": rows,
                                                    "symbol": symbol or None, "timestamp": stamp or None,
                                                    "open": op, "high": hi, "low": lo, "close": cl})
            row_hash = hashlib.sha256("\x1f".join(str(row.get(c) or "") for c in schema).encode()).hexdigest()
            if row_hash in duplicate_hashes:
                duplicate_rows += 1
            duplicate_hashes.add(row_hash)
            if len(sample) < 3:
                sample.append({key: row.get(key) for key in schema})
    except (UnicodeError, csv.Error) as exc:
        return {"path": str(path), "archive_member": archive_member, "sha256": digest,
                "size_bytes": len(raw), "error": str(exc), "empty": not raw}
    return {
        "path": str(path), "archive_member": archive_member, "sha256": digest,
        "size_bytes": len(raw), "rows": rows, "schema": schema, "sample_rows": sample,
        "inferred_dtypes": {column: ("numeric" if rows > 0 and numeric_value_counts.get(column, 0) == rows else "string")
                            for column in schema},
        "symbols": sorted(symbols), "symbol_count": len(symbols), "dates": sorted(dates),
        "earliest_timestamp": minimum_timestamp, "latest_timestamp": maximum_timestamp,
        "first_row_timestamp": first_timestamp, "last_row_timestamp": last_timestamp,
        "timestamp_column": _field(schema, "TradeDateTime", "Timestamp", "Date", "Time"),
        "timestamp_timezone": "naive local exchange time (Asia/Bangkok assumption from TradeSim workflow; no offset in CSV)",
        "duplicate_full_rows": duplicate_rows, "duplicate_symbol_timestamp_rows": duplicate_symbol_timestamps,
        "out_of_order_timestamps_global": out_of_order_timestamps,
        "out_of_order_timestamps_within_symbol": out_of_order_within_symbol,
        "invalid_timestamps": invalid_timestamps, "invalid_numeric_values": invalid_numeric_values,
        "invalid_price_rows": invalid_price_rows, "negative_volume_rows": negative_volume_rows,
        "invalid_ohlc_rows": invalid_ohlc_rows, "malformed_rows": malformed_rows,
        "validation_examples": validation_examples,
        "empty": rows == 0,
    }


def extract_package(outer: Path, destination: Path) -> dict[str, Any]:
    """Copy originals and safely extract organizer datasets, idempotently by hash."""
    outer_hash = sha256_file(outer)
    base = destination
    archives_dir = base / "archives"
    manifests_dir = base / "manifests"
    archives_dir.mkdir(parents=True, exist_ok=True)
    manifests_dir.mkdir(parents=True, exist_ok=True)
    outer_copy = archives_dir / OUTER_NAME
    if outer.resolve() != outer_copy.resolve():
        if outer_copy.exists() and sha256_file(outer_copy) != outer_hash:
            raise FileExistsError(f"Preserved archive differs; refusing overwrite: {outer_copy}")
        if not outer_copy.exists():
            outer_copy.write_bytes(outer.read_bytes())
    records: dict[str, dict[str, Any]] = {}
    with zipfile.ZipFile(outer) as zf:
        bad = zf.testzip()
        if bad:
            raise zipfile.BadZipFile(f"Corrupt outer member: {bad}")
        members = zf.infolist()
        for info in members:
            parts = _safe_parts(info.filename)
            name_lower = parts[-1].lower()
            if name_lower in {"tradesim_history.zip", "tradesim_ticks.zip"}:
                nested = zf.read(info.filename)
                nested_hash = sha256_bytes(nested)
                archive_copy = archives_dir / parts[-1]
                if archive_copy.exists() and sha256_file(archive_copy) != nested_hash:
                    raise FileExistsError(f"Preserved nested archive differs: {archive_copy}")
                if not archive_copy.exists():
                    archive_copy.write_bytes(nested)
                with zipfile.ZipFile(archive_copy) as nested_zip:
                    nested_bad = nested_zip.testzip()
                    if nested_bad:
                        raise zipfile.BadZipFile(f"Corrupt nested member {nested_bad} in {parts[-1]}")
                    members_summary = []
                    for nested_info in nested_zip.infolist():
                        nested_parts = _safe_parts(nested_info.filename)
                        if nested_info.is_dir() or not nested_parts or nested_parts[0] != "marketInfo":
                            continue
                        kind = "history" if "history" in parts[-1].lower() else "ticks"
                        out = base / kind / Path(*nested_parts[1:])
                        content = nested_zip.read(nested_info.filename)
                        out.parent.mkdir(parents=True, exist_ok=True)
                        if out.exists() and sha256_file(out) != sha256_bytes(content):
                            raise FileExistsError(f"Extracted data differs; refusing overwrite: {out}")
                        if not out.exists():
                            out.write_bytes(content)
                        members_summary.append({"member": nested_info.filename, "path": str(out),
                                                "size_bytes": nested_info.file_size,
                                                "sha256": sha256_bytes(content)})
                records[parts[-1]] = {"outer_member": info.filename, "archive_path": str(archive_copy),
                                      "size_bytes": len(nested), "sha256": nested_hash,
                                      "zip_integrity": "PASS", "member_count": len(nested_zip.infolist()),
                                      "members": members_summary}
            elif name_lower.endswith(".csv") and "/history/" not in info.filename.lower():
                # Preserve the standalone dated CSVs as organizer-provided daily tick files.
                if len(parts) == 2 and parts[0].lower() == "daily_ticks":
                    content = zf.read(info.filename)
                    out = base / "daily_ticks" / parts[-1]
                    out.parent.mkdir(parents=True, exist_ok=True)
                    if out.exists() and sha256_file(out) != sha256_bytes(content):
                        raise FileExistsError(f"Daily tick differs; refusing overwrite: {out}")
                    if not out.exists():
                        out.write_bytes(content)
    return {"outer_archive": {"path": str(outer.resolve()), "copy": str(outer_copy),
                              "size_bytes": outer.stat().st_size, "sha256": outer_hash,
                              "zip_integrity": "PASS", "member_count": len(members),
                              "member_names": [i.filename for i in members]},
            "nested_archives": records}


def inventory_tree(root: Path) -> dict[str, Any]:
    csv_files = sorted(root.rglob("*.csv"))
    files = [inventory_csv(path) for path in csv_files]
    return {"root": str(root), "file_count": len(files), "total_rows": sum(int(row.get("rows", 0)) for row in files),
            "symbols": sorted({symbol for row in files for symbol in row.get("symbols", [])}),
            "dates": sorted({date for row in files for date in row.get("dates", [])}), "files": files}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, default=ROOT / OUTER_NAME)
    parser.add_argument("--destination", type=Path, default=ROOT / "data" / "official" / "tradesim")
    parser.add_argument("--inventory-only", action="store_true")
    args = parser.parse_args()
    outer = args.archive.resolve()
    if not outer.is_file():
        parser.error(f"Daily_Ticks package not found: {outer}")
    if args.inventory_only:
        previous_path = ROOT / "reports" / "tradesim_official_daily_ticks_package.json"
        previous = json.loads(previous_path.read_text(encoding="utf-8")) if previous_path.is_file() else {}
        extracted = previous.get("extraction", {})
        for detail in extracted.get("nested_archives", {}).values():
            archive_copy = Path(detail.get("archive_path", ""))
            if archive_copy.is_file():
                with zipfile.ZipFile(archive_copy) as nested_zip:
                    corrupt = nested_zip.testzip()
                    detail["zip_integrity"] = "PASS" if corrupt is None else "FAIL"
                    detail["member_count"] = len(nested_zip.infolist())
        for detail in extracted.get("nested_archives", {}).values():
            archive_copy = Path(detail.get("archive_path", ""))
            if archive_copy.is_file():
                with zipfile.ZipFile(archive_copy) as nested_zip:
                    corrupt = nested_zip.testzip()
                    detail["zip_integrity"] = "PASS" if corrupt is None else "FAIL"
                    detail["member_count"] = len(nested_zip.infolist())
    else:
        extracted = extract_package(outer, args.destination.resolve())
    base = args.destination.resolve()
    nested_archive_identity = {name: {"sha256": detail["sha256"], "size_bytes": detail["size_bytes"],
                                     "path": detail["archive_path"], "zip_integrity": detail["zip_integrity"],
                                     "member_count": detail["member_count"]}
                              for name, detail in extracted.get("nested_archives", {}).items()}
    report = {"generated_at_utc": datetime.now(timezone.utc).isoformat(),
              "source": SOURCE, "ingestion_version": 1, "extraction": extracted,
              "official_history": inventory_tree(base / "history"),
              "official_ticks": inventory_tree(base / "ticks"),
              "standalone_daily_ticks": inventory_tree(base / "daily_ticks"),
              "archive_identity": {"outer_sha256": sha256_file(outer),
                                   "nested_archives": nested_archive_identity}}
    report_dir = ROOT / "reports"
    report_dir.mkdir(exist_ok=True)
    for field, filename in (("official_history", "tradesim_official_history_inventory.json"),
                            ("official_ticks", "tradesim_official_tick_inventory.json")):
        payload = {"generated_at_utc": report["generated_at_utc"], "source": SOURCE,
                   "archive_identity": report["archive_identity"], **report[field]}
        (report_dir / filename).write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    (report_dir / "tradesim_official_daily_ticks_package.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps({"history_files": report["official_history"]["file_count"],
                      "history_rows": report["official_history"]["total_rows"],
                      "tick_files": report["official_ticks"]["file_count"],
                      "tick_rows": report["official_ticks"]["total_rows"],
                      "standalone_tick_files": report["standalone_daily_ticks"]["file_count"],
                      "report": "reports/tradesim_official_daily_ticks_package.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

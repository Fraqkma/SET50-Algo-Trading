"""Inventory local organizer TradeSim history/tick ZIPs without extraction."""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import zipfile
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def inspect_zip(path: Path) -> dict:
    result = {"path": str(path.resolve()), "filename": path.name,
              "size_bytes": path.stat().st_size, "sha256": _sha256(path),
              "source": "TRADESIM_OFFICIAL_HISTORY" if "history" in path.name.lower() else "TRADESIM_OFFICIAL_TICKS"}
    files = []
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        result.update({"zip_integrity": "PASS" if corrupt is None else "FAIL",
                       "corrupt_member": corrupt, "member_count": len(archive.namelist())})
        for info in archive.infolist():
            name = info.filename
            if info.is_dir() or not name.lower().endswith(".csv"):
                continue
            parts = PurePosixPath(name).parts
            if not any(part in {"daily_history", "intraday_history", "ticks"} for part in parts):
                continue
            try:
                with archive.open(info) as stream:
                    text = (line.decode("utf-8-sig") for line in stream)
                    reader = csv.DictReader(text)
                    fields = reader.fieldnames or []
                    count = duplicates = 0
                    symbols, timestamps, seen = set(), [], set()
                    symbol_column = next((c for c in ("ShareCode", "Symbol") if c in fields), None)
                    time_column = next((c for c in ("TradeDateTime", "Timestamp", "Date") if c in fields), None)
                    for row in reader:
                        count += 1
                        symbol = (row.get(symbol_column) or Path(name).stem).strip() if symbol_column else Path(name).stem
                        stamp = (row.get(time_column) or "").strip() if time_column else ""
                        symbols.add(symbol)
                        if stamp:
                            timestamps.append(stamp)
                        key = (symbol, stamp) if stamp else tuple(row.items())
                        if key in seen:
                            duplicates += 1
                        seen.add(key)
                files.append({"path": name, "size_bytes": info.file_size, "rows": count,
                              "schema": fields, "symbols": sorted(symbols),
                              "earliest_timestamp": min(timestamps) if timestamps else None,
                              "latest_timestamp": max(timestamps) if timestamps else None,
                              "duplicate_symbol_timestamp_rows": duplicates,
                              "timestamp_timezone": "naive local exchange time unless source metadata states otherwise",
                              "empty": count == 0, "sha256": hashlib.sha256(archive.read(name)).hexdigest()})
            except (UnicodeError, csv.Error, OSError) as exc:
                files.append({"path": name, "error": str(exc), "empty": None})
    result["files"] = files
    result["csv_file_count"] = len(files)
    result["status"] = "PASS" if result["zip_integrity"] == "PASS" and not any("error" in item for item in files) else "CHECK"
    return result


def extract_source_data(path: Path) -> Path:
    """Copy marketInfo files to an archive-hash-specific, source-only folder."""
    digest = _sha256(path)
    source_dir = "tradesim_official_history" if "history" in path.name.lower() else "tradesim_official_ticks"
    destination = ROOT / "data" / "raw" / source_dir / digest
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite source archive extraction: {destination}")
    with zipfile.ZipFile(path) as archive:
        bad = archive.testzip()
        if bad:
            raise zipfile.BadZipFile(f"Corrupt member: {bad}")
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe archive path: {info.filename}")
            if info.is_dir() or not member.parts or member.parts[0] != "marketInfo":
                continue
            target = destination.joinpath(*member.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(info.filename))
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, help="Inspect one locally available ZIP")
    parser.add_argument("--extract-source-data", action="store_true",
                        help="Extract only marketInfo under data/raw/<source>/<archive-sha256>; refuses overwrite")
    args = parser.parse_args()
    candidates = [args.archive.resolve()] if args.archive else sorted(
        path for path in ROOT.glob("*.zip")
        if path.name.lower() in {"tradesim_history.zip", "tradesim_ticks.zip"}
        or ("tradesim" in path.name.lower() and ("history" in path.name.lower() or "ticks" in path.name.lower())))
    if not candidates:
        print(json.dumps({"status": "OFFICIAL_HISTORY_ARCHIVE_NOT_PRESENT",
                          "checked_root": str(ROOT), "archives": []}, indent=2))
        return 0
    reports = [inspect_zip(path) for path in candidates]
    if args.extract_source_data:
        for report, path in zip(reports, candidates):
            if report["status"] == "PASS":
                report["extracted_to"] = str(extract_source_data(path))
    print(json.dumps({"status": "PASS" if all(r["status"] == "PASS" for r in reports) else "CHECK",
                      "archives": reports}, indent=2))
    return 0 if all(r["status"] == "PASS" for r in reports) else 2


if __name__ == "__main__":
    raise SystemExit(main())

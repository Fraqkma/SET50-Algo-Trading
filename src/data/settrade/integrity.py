"""Non-mutating structural checks for active Settrade market-data files."""
from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Any

def scan_integrity(root: Path) -> list[dict[str, Any]]:
    """Inspect only Settrade BBO and candle artifacts; never edit source files."""
    root = Path(root)
    candidates = [
        root / "raw/bid_offer/events.jsonl",
        root / "normalized/bid_offer/data.csv",
        root / "raw/candles/1m.jsonl",
        root / "raw/candles/probes.jsonl",
        *(root / "normalized" / f"bars_{tf}" / "data.csv" for tf in ("1m", "5m", "15m")),
    ]
    findings: list[dict[str, Any]] = []
    for path in candidates:
        if not path.exists():
            continue
        result: dict[str, Any] = {"path": str(path), "bytes": path.stat().st_size, "rows": 0, "malformed_rows": 0, "duplicate_keys": 0, "timestamp_regressions": 0, "truncated_final_record": False, "issues": []}
        if result["bytes"] == 0:
            result["issues"].append("ZERO_BYTE")
            findings.append(result)
            continue
        if path.suffix == ".jsonl":
            previous_time: datetime | None = None
            seen: set[str] = set()
            with path.open("rb") as handle:
                raw_lines = handle.readlines()
            for index, raw_line in enumerate(raw_lines):
                if not raw_line.strip():
                    continue
                try:
                    record = json.loads(raw_line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    result["malformed_rows"] += 1
                    if index == len(raw_lines) - 1:
                        result["truncated_final_record"] = True
                    continue
                result["rows"] += 1
                signature = json.dumps(record, sort_keys=True, separators=(",", ":"))
                result["duplicate_keys"] += signature in seen
                seen.add(signature)
                raw_timestamp = record.get("received_at") if isinstance(record, dict) else None
                try:
                    timestamp = datetime.fromisoformat(str(raw_timestamp).replace("Z", "+00:00")) if raw_timestamp else None
                except ValueError:
                    timestamp = None
                if timestamp is not None:
                    if previous_time is not None and timestamp < previous_time:
                        result["timestamp_regressions"] += 1
                    previous_time = timestamp
        else:
            seen: set[tuple[str, ...]] = set()
            previous_by_symbol: dict[str, datetime] = {}
            with path.open(encoding="utf-8", newline="") as handle:
                reader = csv.reader(handle)
                try:
                    header = next(reader)
                except StopIteration:
                    header = []
                timestamp_index = next((header.index(col) for col in ("retrieved_at", "timestamp") if col in header), None)
                symbol_index = header.index("symbol") if "symbol" in header else None
                key_columns = ("symbol", "interval", "timestamp") if "interval" in header else ("retrieved_at", "symbol", "side", "level", "collector_session_id", "generation")
                key_indices = [header.index(col) for col in key_columns if col in header]
                last_row_malformed = False
                for row in reader:
                    result["rows"] += 1
                    if len(row) != len(header):
                        result["malformed_rows"] += 1
                        last_row_malformed = True
                        continue
                    last_row_malformed = False
                    key = tuple(row[index] for index in key_indices) if key_indices else tuple(row)
                    result["duplicate_keys"] += key in seen
                    seen.add(key)
                    if timestamp_index is not None:
                        try:
                            timestamp = datetime.fromisoformat(row[timestamp_index].replace("Z", "+00:00"))
                        except ValueError:
                            timestamp = None
                        if timestamp is not None:
                            symbol = row[symbol_index] if symbol_index is not None else ""
                            if symbol in previous_by_symbol and timestamp < previous_by_symbol[symbol]:
                                result["timestamp_regressions"] += 1
                            previous_by_symbol[symbol] = timestamp
                result["truncated_final_record"] = last_row_malformed
        if result["malformed_rows"]:
            result["issues"].append("MALFORMED_ROWS")
        if result["duplicate_keys"]:
            result["issues"].append("DUPLICATE_ROWS")
        if result["timestamp_regressions"]:
            result["issues"].append("TIMESTAMP_REGRESSION")
        if result["truncated_final_record"]:
            result["issues"].append("TRUNCATED_FINAL_RECORD")
        if result["issues"]:
            findings.append(result)
    return findings

"""Append-safe pilot storage with atomic checkpoints."""

from __future__ import annotations

import csv
import json
import os
import tempfile
import time
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable


class PilotStorage:
    """Storage rooted only under ``data/pilot/settrade``."""

    def __init__(self, root: Path) -> None:
        self.root = root
        for relative in ("raw/candles", "raw/realtime", "raw/bid_offer", "normalized/bars_1m", "normalized/bars_5m", "normalized/bars_15m", "normalized/quotes", "metadata", "checkpoints"):
            (root / relative).mkdir(parents=True, exist_ok=True)

    def append_jsonl(self, relative: str, record: dict[str, Any]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, default=str, sort_keys=True) + "\n")
        return path

    def append_csv(self, relative: str, rows: Iterable[dict[str, Any]], fieldnames: list[str]) -> Path:
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        exists = path.exists() and path.stat().st_size > 0
        with path.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
            if not exists:
                writer.writeheader()
            writer.writerows(rows)
        return path

    def append_csv_deduplicated(self, relative: str, rows: Iterable[dict[str, Any]], fieldnames: list[str], key_fields: tuple[str, ...]) -> dict[str, int]:
        """Append new keys while flagging conflicting payloads without deleting rows."""
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        existing: dict[tuple[str, ...], dict[str, str]] = {}
        if path.exists() and path.stat().st_size:
            with path.open(newline="", encoding="utf-8") as handle:
                for row in csv.DictReader(handle):
                    existing[tuple(row.get(field, "") for field in key_fields)] = row
        unique: list[dict[str, Any]] = []
        duplicates = conflicts = 0
        for row in rows:
            key = tuple(str(row.get(field, "")) for field in key_fields)
            if key in existing:
                duplicates += 1
                previous = existing[key]
                # Retrieval/session metadata and unresolved turnover encodings may
                # legitimately vary between reads. Core OHLCV is the conflict key.
                core_fields = {"open", "high", "low", "close", "volume"}
                if any(str(row.get(field, "")) != str(previous.get(field, "")) for field in core_fields if field in fieldnames):
                    conflicts += 1
                continue
            existing[key] = {field: str(row.get(field, "")) for field in fieldnames}
            unique.append(row)
        if unique:
            self.append_csv(relative, unique, fieldnames)
        return {"written": len(unique), "duplicates": duplicates, "conflicts": conflicts}

    def write_checkpoint(self, name: str, state: dict[str, Any]) -> Path:
        path = self.root / "checkpoints" / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary_name: str | None = None
        try:
            # A fixed ``.json.tmp`` name allowed a stale pilot process or an
            # antivirus scan to block the next Windows replace.  A unique
            # sibling keeps each writer isolated while retaining atomic replace.
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=path.parent,
                prefix=f".{path.stem}.",
                suffix=".tmp",
                delete=False,
            ) as handle:
                temporary_name = handle.name
                handle.write(json.dumps(state, indent=2, sort_keys=True, default=str))
                handle.flush()
                os.fsync(handle.fileno())
            temporary = Path(temporary_name)
            for attempt in range(5):
                try:
                    os.replace(temporary, path)
                    break
                except PermissionError:
                    if attempt == 4:
                        raise
                    time.sleep(0.05 * (2**attempt))
        finally:
            if temporary_name:
                Path(temporary_name).unlink(missing_ok=True)
        return path

    def read_checkpoint(self, name: str) -> dict[str, Any] | None:
        path = self.root / "checkpoints" / f"{name}.json"
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))


def dataclass_record(record: Any) -> dict[str, Any]:
    """Serialize a normalized dataclass without lossy field invention."""
    return asdict(record)

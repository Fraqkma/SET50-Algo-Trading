"""Safe, filesystem-based lifecycle primitives for the Windows pilot runner."""

from __future__ import annotations

import json
import os
import socket
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from .session import session_state

THAILAND = ZoneInfo("Asia/Bangkok")


class AlreadyRunningError(RuntimeError):
    """Raised when another live daily runner owns the lock."""


@dataclass(frozen=True)
class MarketWindow:
    state: str
    market_day: bool
    collecting: bool
    reason: str


def classify_market_window(now: datetime, api_status: str | None = None) -> MarketWindow:
    """Classify a timestamp conservatively without maintaining a holiday list."""
    local = now.astimezone(THAILAND)
    scheduled = session_state(local)
    if local.weekday() >= 5:
        return MarketWindow("CLOSED", False, False, "WEEKEND")

    status = (api_status or "").strip().casefold().replace("_", "-")
    # The API status is a point-in-time hint.  Never let a stale PRE_OPEN
    # response override the authoritative Bangkok session clock after open.
    if status and any(token in status for token in ("pre-open", "preopen")) and scheduled == "PRE_OPEN":
        return MarketWindow("PRE_OPEN", True, False, "API_PRE_OPEN")
    if status and any(token in status for token in ("auction", "pre-close")) and scheduled == "PRE_CLOSE_AUCTION":
        return MarketWindow("PRE_CLOSE_AUCTION", True, False, "API_AUCTION")
    if status and any(token in status for token in ("break", "lunch")) and scheduled == "MIDDAY_BREAK":
        return MarketWindow("MIDDAY_BREAK", True, False, "API_MIDDAY_BREAK")
    if status and any(token in status for token in ("open", "continuous")):
        if scheduled in {"CONTINUOUS_MORNING", "CONTINUOUS_AFTERNOON"}:
            return MarketWindow(scheduled, True, True, "API_OPEN")
    if status and any(token in status for token in ("close", "closed", "halt")):
        if scheduled in {"CONTINUOUS_MORNING", "CONTINUOUS_AFTERNOON", "PRE_CLOSE_AUCTION"}:
            return MarketWindow("CLOSED", False, False, "API_CLOSED_OR_HOLIDAY")

    if scheduled == "CLOSED":
        return MarketWindow("CLOSED", False, False, "OUTSIDE_SET_SESSION")
    return MarketWindow(scheduled, True, scheduled in {"CONTINUOUS_MORNING", "CONTINUOUS_AFTERNOON"}, "SCHEDULE")


def _pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


class SingleInstanceLock:
    """Atomic lock file with PID validation and stale-lock recovery."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.token = f"{socket.gethostname()}:{os.getpid()}:{id(self)}"
        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            payload = {"pid": os.getpid(), "host": socket.gethostname(), "token": self.token, "created_at": datetime.now(timezone.utc).isoformat()}
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                    active = _pid_alive(int(existing.get("pid", 0)))
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    active = False
                if active:
                    raise AlreadyRunningError("ALREADY_RUNNING")
                try:
                    self.path.unlink()
                except FileNotFoundError:
                    continue
                continue
            with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, indent=2)
            self.acquired = True
            return
        raise AlreadyRunningError("ALREADY_RUNNING")

    def release(self) -> None:
        if not self.acquired:
            return
        try:
            current = json.loads(self.path.read_text(encoding="utf-8"))
            if current.get("token") == self.token:
                self.path.unlink(missing_ok=True)
        except (OSError, json.JSONDecodeError):
            pass
        finally:
            self.acquired = False

    def __enter__(self) -> "SingleInstanceLock":
        self.acquire()
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


def request_stop(lock_path: Path, stop_path: Path) -> bool:
    """Request graceful stop for the PID currently holding ``lock_path``."""
    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
        pid = int(lock["pid"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    if not _pid_alive(pid):
        lock_path.unlink(missing_ok=True)
        return False
    stop_path.parent.mkdir(parents=True, exist_ok=True)
    stop_path.write_text(json.dumps({"pid": pid, "requested_at": datetime.now(timezone.utc).isoformat()}), encoding="utf-8")
    return True


def stop_requested(stop_path: Path, pid: int | None = None) -> bool:
    try:
        request = json.loads(stop_path.read_text(encoding="utf-8"))
        return pid is None or int(request.get("pid")) == pid
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False


def atomic_json_write(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    os.replace(temporary, path)

"""Safe, filesystem-based lifecycle primitives for the Windows pilot runner."""

from __future__ import annotations

import json
import os
import socket
import ctypes
from ctypes import wintypes
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
    if os.name == "nt":
        # os.kill(pid, 0) is not a process-existence probe on Windows (it
        # returns WinError 87). Query a handle instead and fail closed on
        # access-denied or other uncertain errors.
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel32.OpenProcess.restype = wintypes.HANDLE
        kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel32.OpenProcess(0x1000, False, pid)  # PROCESS_QUERY_LIMITED_INFORMATION
        if handle:
            kernel32.CloseHandle(handle)
            return True
        return ctypes.get_last_error() != 87  # ERROR_INVALID_PARAMETER means no such PID.
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def process_identity(pid: int) -> dict[str, Any] | None:
    """Use process birth time and executable to distinguish a reused PID."""
    import psutil

    try:
        process = psutil.Process(pid)
        return {"created": process.create_time(), "executable": process.exe(),
                "runner_script": any(Path(arg).name == "run_settrade_daily.py" for arg in process.cmdline())}
    except psutil.NoSuchProcess:
        return None
    except (psutil.AccessDenied, OSError):
        return {"unknown": True}


def lock_state(value: dict[str, Any]) -> str:
    """Fail closed on inaccessible/foreign owners, never call them active."""
    host = str(value.get("host") or "").casefold()
    if host and host != socket.gethostname().casefold():
        return "ERROR"
    try:
        pid = int(value.get("pid", 0))
        if pid <= 0 or not _pid_alive(pid):
            return "STALE_LOCK"
        identity = process_identity(pid)
        if identity is None:
            return "STALE_LOCK"
        if identity.get("unknown"):
            return "UNVERIFIABLE"
        expected = value.get("process_identity")
        if expected:
            if expected.get("unknown"):
                return "UNVERIFIABLE"
            return "ACTIVE" if (expected.get("created") == identity.get("created")
                                and expected.get("executable") == identity.get("executable")) else "STALE_LOCK"
        # Legacy locks have no birth token. A live unrelated process is not a runner.
        if not identity.get("runner_script"):
            return "STALE_LOCK"
        created = value.get("created_at")
        if created and identity["created"] > datetime.fromisoformat(created).timestamp() + 1:
            return "STALE_LOCK"
        return "ACTIVE"
    except (ValueError, TypeError, OverflowError):
        return "ERROR"


def runner_status(lock_path: Path, scheduler: dict[str, Any] | None = None) -> str:
    try:
        value = json.loads(lock_path.read_text(encoding="utf-8"))
        return lock_state(value) if isinstance(value, dict) else "ERROR"
    except FileNotFoundError:
        return "SCHEDULED_WAITING" if scheduler and scheduler.get("installed") and scheduler.get("enabled") else "NOT_RUNNING"
    except OSError:
        return "UNVERIFIABLE"
    except ValueError:
        return "ERROR"


class SingleInstanceLock:
    """Atomic lock file with PID validation and stale-lock recovery."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.token = f"{socket.gethostname()}:{os.getpid()}:{id(self)}"
        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            payload = {"pid": os.getpid(), "host": socket.gethostname(), "token": self.token,
                       "process_identity": process_identity(os.getpid()),
                       "created_at": datetime.now(timezone.utc).isoformat()}
            try:
                descriptor = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                try:
                    existing = json.loads(self.path.read_text(encoding="utf-8"))
                    state = lock_state(existing)
                except (OSError, ValueError, TypeError, json.JSONDecodeError):
                    state = "ERROR"
                if state == "ACTIVE":
                    raise AlreadyRunningError("ALREADY_RUNNING")
                if state in {"ERROR", "UNVERIFIABLE"}:
                    raise AlreadyRunningError("LOCK_OWNER_UNVERIFIABLE")
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
        owner_host = str(lock.get("host") or "").casefold()
        if owner_host and owner_host != socket.gethostname().casefold():
            return False
        pid = int(lock["pid"])
    except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return False
    if lock_state(lock) != "ACTIVE":
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

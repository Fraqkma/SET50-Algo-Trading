"""Non-destructive disk guard for pilot collection."""
from __future__ import annotations

import shutil
import logging
from dataclasses import dataclass
from pathlib import Path

LOGGER = logging.getLogger("settrade_disk")


@dataclass(frozen=True)
class DiskStatus:
    free_bytes: int
    warning_bytes: int
    critical_bytes: int

    @property
    def state(self) -> str:
        if self.free_bytes < self.critical_bytes:
            return "CRITICAL"
        if self.free_bytes < self.warning_bytes:
            return "WARNING"
        return "OK"


def filesystem_probe_path(path: Path) -> Path:
    """Return the nearest existing path on the intended output filesystem."""
    candidate = Path(path).expanduser().resolve()
    while not candidate.exists() and candidate.parent != candidate:
        candidate = candidate.parent
    return candidate


def check_disk(path: Path, warning_gb: float = 10.0, critical_gb: float = 5.0) -> DiskStatus:
    usage = shutil.disk_usage(filesystem_probe_path(path))
    return DiskStatus(usage.free, int(warning_gb * 1024**3), int(critical_gb * 1024**3))


def require_disk(path: Path, warning_gb: float = 10.0, critical_gb: float = 5.0) -> DiskStatus:
    status = check_disk(path, warning_gb, critical_gb)
    if status.state == "CRITICAL":
        LOGGER.error("market-data filesystem below critical free-space threshold path=%s free_bytes=%s", path, status.free_bytes)
        raise RuntimeError(f"pilot collection stopped: disk free below critical threshold ({status.free_bytes} bytes)")
    if status.state == "WARNING":
        LOGGER.warning("market-data filesystem below warning free-space threshold path=%s free_bytes=%s", path, status.free_bytes)
    return status

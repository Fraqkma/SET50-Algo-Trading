"""Non-destructive disk guard for pilot collection."""
from __future__ import annotations

import shutil
from dataclasses import dataclass
from pathlib import Path


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


def check_disk(path: Path, warning_gb: float = 10.0, critical_gb: float = 5.0) -> DiskStatus:
    usage = shutil.disk_usage(path)
    return DiskStatus(usage.free, int(warning_gb * 1024**3), int(critical_gb * 1024**3))


def require_disk(path: Path, warning_gb: float = 10.0, critical_gb: float = 5.0) -> DiskStatus:
    status = check_disk(path, warning_gb, critical_gb)
    if status.state == "CRITICAL":
        raise RuntimeError(f"pilot collection stopped: disk free below critical threshold ({status.free_bytes} bytes)")
    return status

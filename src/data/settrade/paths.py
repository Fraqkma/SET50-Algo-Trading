"""Resolve repo-relative and optional external Settrade data paths."""
from __future__ import annotations

import os
from dotenv import dotenv_values
from pathlib import Path


def configured_environment(project_root: Path) -> str:
    """Classify routing without returning or logging credential material."""
    broker = os.environ.get("SETTRADE_BROKER_ID")
    app_code = os.environ.get("SETTRADE_APP_CODE")
    if not broker or not app_code:
        values = dotenv_values(Path(project_root) / ".env")
        broker = broker or values.get("SETTRADE_BROKER_ID")
        app_code = app_code or values.get("SETTRADE_APP_CODE")
    if broker == "013" and app_code == "ALGO_EQ":
        return "production"
    if str(broker).upper() == "SANDBOX" or str(app_code).upper() == "SANDBOX":
        return "sandbox"
    return "unknown"


def resolve_data_root(project_root: Path, configured_storage_root: str | Path = "data/pilot/settrade") -> Path:
    """Resolve Settrade storage, honoring ``SET50_DATA_ROOT`` when configured.

    The environment variable names the root for large research data. Settrade
    pilot artifacts live below ``pilot/settrade`` there. Without it, the
    configured storage path is interpreted relative to the active repository.
    A relative environment value is also resolved from the repository root.
    """
    project_root = Path(project_root).resolve()
    external_root = os.environ.get("SET50_DATA_ROOT")
    if not external_root:
        env_file = project_root / ".env"
        if env_file.exists():
            try:
                from dotenv import dotenv_values

                external_root = dotenv_values(env_file).get("SET50_DATA_ROOT")
            except (ImportError, OSError):
                external_root = None
    if external_root:
        base = Path(external_root).expanduser()
        if not base.is_absolute():
            base = project_root / base
        root = base / "pilot" / "settrade"
        if configured_environment(project_root) == "production":
            root = root / "production"
        return root.resolve()

    configured = Path(configured_storage_root).expanduser()
    if not configured.is_absolute():
        configured = project_root / configured
    if configured_environment(project_root) == "production":
        configured = configured / "production"
    return configured.resolve()

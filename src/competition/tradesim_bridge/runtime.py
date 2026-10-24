"""Discovery and inventory helpers for the repository-local official runtime."""
from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import Any


class RuntimeErrorDetail(RuntimeError):
    pass


def repository_root() -> Path:
    return Path(__file__).resolve().parents[3]


def archive_path(root: Path | None = None, version: str | None = None) -> Path:
    root = (root or repository_root()).resolve()
    matches = sorted(p for p in root.glob("*.zip") if p.is_file()
                     and "tradesim" in p.name.lower()
                     and (version is None or version in p.name))
    if version is None and len(matches) > 1:
        designated = [p for p in matches if "0.2.6" in p.name]
        if len(designated) == 1:
            matches = designated
    if len(matches) != 1:
        raise RuntimeErrorDetail(f"Expected one local TradeSim ZIP{f' for {version}' if version else ''}, found {len(matches)}")
    return matches[0]


def runtime_root(root: Path | None = None, version: str | None = None) -> Path:
    base = (root or repository_root()) / "tools" / "kgi_tradesim"
    if version:
        return base / version
    return base / "0.2.6" if (base / "0.2.6" / "tradeSim" / "TradeSim.py").is_file() else base


def inspect_archive(path: Path | None = None) -> dict[str, Any]:
    path = path or archive_path()
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    with zipfile.ZipFile(path) as archive:
        corrupt = archive.testzip()
        names = archive.namelist()
        required = ["requirements.txt", "TradingSimulation.ipynb",
                    "strategy/Strategies_template.py", "strategy/Example_strategy.py",
                    "tradeSim/TradeSim.py"]
        missing = [name for name in required if name not in names]
        tick_files = [n for n in names if n.startswith("marketInfo/ticks/") and n.lower().endswith(".csv")]
        templates = [n for n in names if n.startswith("strategy/") and n.lower().endswith(".py")]
        return {"filename": path.name, "sha256": digest.hexdigest(), "size_bytes": path.stat().st_size,
                "version": next(iter(re.findall(r"\d+\.\d+\.\d+", path.name)), None),
                "version_evidence": "archive filename" if re.search(r"\d+\.\d+\.\d+", path.name) else "package layout",
                "integrity": "PASS" if corrupt is None else "FAIL",
                "corrupt_member": corrupt, "member_count": len(names), "required_missing": missing,
                "has_practice_ticks": bool(tick_files), "practice_tick_file_count": len(tick_files),
                "strategy_templates_and_examples": templates,
                "notebook": "TradingSimulation.ipynb" if "TradingSimulation.ipynb" in names else None,
                "requirements": "requirements.txt" if "requirements.txt" in names else None,
                "source_files": [n for n in names if n.startswith("tradeSim/") and n.endswith(".py")]}


def discover_python3130(launcher: str = "py") -> Path:
    """Find only an exact Python 3.13.0 executable; never fall back by patch."""
    candidates: list[Path] = []
    for command in (shutil.which(launcher),):
        if command:
            result = subprocess.run([command, "-3.13", "-c", "import sys;print(sys.executable);print('.'.join(map(str,sys.version_info[:3])))"],
                                    capture_output=True, text=True, check=False)
            if result.returncode == 0:
                lines = result.stdout.splitlines()
                if len(lines) >= 2 and lines[-1].strip() == "3.13.0":
                    candidates.append(Path(lines[-2].strip()))
    # The Windows launcher may expose only its registered 3.13 patch release while
    # an exact 3.13.0 installation remains available at a side-by-side path.
    local = Path.home() / "AppData" / "Local"
    candidates.extend([
        local / "Python" / "pythoncore-3.13-64" / "python.exe",
        local / "Programs" / "Python" / "Python313" / "python.exe",
        Path("C:/Program Files/Python313/python.exe"),
        Path("C:/Python313/python.exe"),
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            candidate = candidate.resolve()
        except OSError:
            continue
        if candidate in seen or not candidate.is_file():
            continue
        seen.add(candidate)
        result = subprocess.run([str(candidate), "-c", "import sys;print('.'.join(map(str,sys.version_info[:3])))"],
                                capture_output=True, text=True, check=False, timeout=15)
        if result.returncode == 0 and result.stdout.strip().splitlines()[-1:] == ["3.13.0"]:
            return candidate
    if not seen:
        raise RuntimeErrorDetail("Python 3.13.0 is unavailable; the exact version is required and other versions must not be substituted.")
    raise RuntimeErrorDetail("Python 3.13.0 is unavailable; side-by-side candidates were checked and other versions must not be substituted.")


def runtime_diagnostic(root: Path | None = None) -> dict[str, Any]:
    """Report archive, extraction, exact interpreter and dependency readiness."""
    root = (root or repository_root()).resolve()
    archives = sorted(p for p in root.glob("*.zip") if "tradesim" in p.name.lower())
    preferred_archive = next((p for p in archives if "0.2.6" in p.name.lower()), None)
    preferred_archive = preferred_archive or next((p for p in archives if "0.2.5" in p.name.lower()), None)
    if preferred_archive is None:
        raise RuntimeErrorDetail("No identifiable local TradeSim archive is available.")
    archive = inspect_archive(preferred_archive)
    version = archive["version"]
    extracted = runtime_root(root, version)
    required_runtime_files = ["TradingSimulation.ipynb", "requirements.txt",
                              "tradeSim/TradeSim.py", "strategy/Strategies_template.py",
                              "strategy/Example_strategy.py"]
    missing_runtime_files = [name for name in required_runtime_files
                             if not (extracted / name).is_file()]
    venv_python = root / ".venv-kgi313" / "Scripts" / "python.exe"
    python_path = venv_python
    python_error = None
    try:
        detected_python = discover_python3130()
        python_status = "EXACT_BASE_AVAILABLE"
        python_version = "3.13.0"
    except RuntimeErrorDetail as exc:
        python_status = "MISSING_EXACT_VERSION"
        python_version = None
        python_error = str(exc)

    if python_status == "EXACT_BASE_AVAILABLE":
        if not venv_python.is_file():
            python_status = "VENV_MISSING"
            python_error = "Python 3.13.0 is installed, but .venv-kgi313 has not been created."
        else:
            venv_probe = subprocess.run(
                [str(venv_python), "-c", "import sys; print('.'.join(map(str, sys.version_info[:3])))"],
                capture_output=True, text=True, check=False, timeout=15)
            venv_version = venv_probe.stdout.strip().splitlines()[-1] if venv_probe.returncode == 0 and venv_probe.stdout.strip() else None
            if venv_version != "3.13.0":
                python_status = "VENV_WRONG_VERSION"
                python_version = venv_version
                python_error = f".venv-kgi313 must be exactly Python 3.13.0; found {venv_version or 'UNKNOWN'}."
            else:
                python_status = "AVAILABLE"

    dependencies_status = "NOT_CHECKED"
    import_status = "NOT_CHECKED"
    notebook_imports_status = "NOT_CHECKED"
    dependency_error = None
    if python_status == "AVAILABLE":
        probe = subprocess.run(
            [str(python_path), "-c", (
                "import importlib.metadata as m, json; "
                "print(json.dumps({d.metadata['Name'].lower().replace('_','-'):d.version "
                "for d in m.distributions()}))"
            )], capture_output=True, text=True, check=False, timeout=30)
        if probe.returncode == 0:
            installed = json.loads(probe.stdout.splitlines()[-1])
            req_path = extracted / "requirements.txt"
            missing = []
            if req_path.is_file():
                for line in req_path.read_text(encoding="utf-8").splitlines():
                    requirement = line.strip()
                    if not requirement or requirement.startswith("#"):
                        continue
                    package = requirement.split("==", 1)[0].split(";", 1)[0].strip().lower().replace("_", "-")
                    if package not in installed:
                        missing.append(package)
            dependencies_status = "PASS" if not missing else "MISSING"
            dependency_error = {"missing": missing}
        else:
            dependencies_status = "ERROR"
            dependency_error = probe.stderr[-2000:]
        imports = subprocess.run(
            [str(python_path), "-c", "import tradeSim, pandas, numpy; print(tradeSim.__file__)"],
            cwd=extracted, capture_output=True, text=True, check=False, timeout=30)
        import_status = "PASS" if imports.returncode == 0 else "FAIL"
        notebook_probe = subprocess.run(
            [str(python_path), "-c", "import pandas, numpy, talib, IPython, nbformat, notebook"],
            cwd=extracted, capture_output=True, text=True, check=False, timeout=30)
        notebook_imports_status = "PASS" if notebook_probe.returncode == 0 else "FAIL"

    tick_dir = extracted / "marketInfo" / "ticks"
    template_files = sorted(str(path.relative_to(extracted)) for path in (extracted / "strategy").glob("*.py")) if (extracted / "strategy").is_dir() else []
    adapter_status = "SUPPORTED" if version == "0.2.5" else "SUPPORTED_WITH_WARNINGS" if version == "0.2.6" else "NEEDS_ADAPTER_UPDATE"
    ready = (python_status == "AVAILABLE" and adapter_status in {"SUPPORTED", "SUPPORTED_WITH_WARNINGS"} and not missing_runtime_files
             and dependencies_status == "PASS" and import_status == "PASS"
             and notebook_imports_status == "PASS")
    result = {
        "status": "READY" if ready else "BLOCKED",
        "repository_root": str(root),
        "archive": archive,
        "preferred_competition_version": "0.2.6",
        "validated_runtime_version": version if ready else None,
        "adapter_status": adapter_status,
        "extracted_runtime": str(extracted),
        "runtime_files_missing": missing_runtime_files,
        "python": {"status": python_status, "path": str(python_path), "version": python_version},
        "dependencies": {"status": dependencies_status, "details": dependency_error},
        "tradesim_import": import_status,
        "notebook_imports": notebook_imports_status,
        "practice_data": {"present": tick_dir.is_dir(), "tick_csv_count": len(list(tick_dir.glob("*.csv"))) if tick_dir.is_dir() else 0},
        "strategy_templates": template_files,
    }
    if python_status != "AVAILABLE":
        result["python"]["reason"] = python_error or python_status
    return result


def inventory_ticks(root: Path | None = None) -> dict[str, Any]:
    base = runtime_root(root)
    folder = base / "marketInfo" / "ticks"
    if not folder.is_dir():
        raise RuntimeErrorDetail(f"TradeSim tick directory is missing: {folder}")
    universe_path = base / "marketInfo" / "symbolSET50" / "Symbol_SET50.csv"
    try:
        with universe_path.open(encoding="utf-8-sig", newline="") as stream:
            universe_reader = csv.DictReader(stream)
            universe = {row.get("Symbol", "").strip().upper() for row in universe_reader}
    except (OSError, csv.Error):
        universe = set()
    files = []
    for path in sorted(folder.glob("*.csv")):
        try:
            with path.open(encoding="utf-8-sig", newline="") as stream:
                reader = csv.DictReader(stream)
                fields = reader.fieldnames or []
                count = 0
                first = last = None
                dates = set()
                symbols = set()
                invalid_timestamp = 0
                invalid_market_rows = 0
                for row in reader:
                    count += 1
                    try:
                        from datetime import datetime
                        stamp = datetime.fromisoformat(row["TradeDateTime"].replace("Z", "+00:00"))
                        first = stamp if first is None or stamp < first else first
                        last = stamp if last is None or stamp > last else last
                        dates.add(stamp.date().isoformat())
                    except (KeyError, ValueError, TypeError):
                        invalid_timestamp += 1
                    try:
                        price = float(row["LastPrice"])
                        volume = float(row["Volume"])
                        if price <= 0 or volume < 0:
                            invalid_market_rows += 1
                    except (KeyError, ValueError, TypeError):
                        invalid_market_rows += 1
                    if row.get("ShareCode", "").strip():
                        symbols.add(row["ShareCode"].strip())
            days = sorted(dates)
            expected_day = path.stem
            correct_day = days == [expected_day]
            outside_universe = sorted(symbol for symbol in symbols if universe and symbol.upper() not in universe)
            file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            files.append({"file": path.name, "path": str(path.resolve()), "size_bytes": path.stat().st_size,
                          "sha256": file_hash, "source": f"TRADESIM_{'0_2_6' if base.name == '0.2.6' else '0_2_5'}_PRACTICE",
                          "timestamp_timezone": "naive local exchange time (Asia/Bangkok assumed from organizer tick workflow)",
                          "dates": days, "rows": count,
                          "first_timestamp": first.isoformat() if first else None,
                          "last_timestamp": last.isoformat() if last else None,
                          "symbols": sorted(symbols), "symbol_count": len(symbols),
                          "invalid_timestamp_rows": invalid_timestamp,
                          "invalid_market_rows": invalid_market_rows,
                          "outside_set50_universe": outside_universe,
                          "filename_date_matches": correct_day,
                          "integrity": "PASS" if count and universe and {"TradeDateTime", "ShareCode", "LastPrice", "Volume"} <= set(fields) and not invalid_timestamp and not invalid_market_rows and not outside_universe and correct_day else "CHECK"})
        except (OSError, csv.Error, UnicodeError) as exc:
            files.append({"file": path.name, "integrity": "FAIL", "error": str(exc)})
    dates = sorted({d for item in files for d in item.get("dates", [])})
    return {"file_count": len(files), "dates": dates, "earliest_date": dates[0] if dates else None,
            "latest_date": dates[-1] if dates else None, "files": files}


def notebook_flow(root: Path | None = None) -> list[dict[str, Any]]:
    path = runtime_root(root) / "TradingSimulation.ipynb"
    notebook = json.loads(path.read_text(encoding="utf-8"))
    output = []
    for index, cell in enumerate(notebook.get("cells", [])):
        source = "".join(cell.get("source", []))
        if cell.get("cell_type") == "code":
            output.append({"cell": index, "source": source})
    return output

"""Safe discovery and side-by-side planning for locally supplied TradeSim archives.

This module never downloads archives and never extracts over an existing runtime.
"""
from __future__ import annotations

import hashlib
import json
import re
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

from .runtime import inspect_archive, runtime_root

VERSION_RE = re.compile(r"(?<!\d)(\d+\.\d+\.\d+)(?!\d)")
ADAPTER_VERSION = "1"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _tree_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    for item in sorted(p for p in path.rglob("*") if p.is_file()
                       and p.relative_to(path).parts[0] not in {"0.2.5", "0.2.6"}):
        digest.update(item.relative_to(path).as_posix().encode("utf-8"))
        digest.update(item.read_bytes())
    return digest.hexdigest()


def _candidate_version(path: Path, names: list[str]) -> tuple[str | None, str]:
    match = VERSION_RE.search(path.name)
    if match:
        return match.group(1), "filename"
    roots = {PurePosixPath(name).parts[0] for name in names if name}
    root_versions = [v for root in roots if (v := VERSION_RE.search(root))]
    if len(root_versions) == 1:
        return root_versions[0].group(1), "archive_root"
    return None, "undetermined"


def discover_archives(root: Path) -> list[dict[str, Any]]:
    """Hash and inspect local ZIP candidates without extracting them."""
    results = []
    for path in sorted(root.glob("*.zip")):
        if "tradesim" not in path.name.lower():
            continue
        try:
            with zipfile.ZipFile(path) as archive:
                names = archive.namelist()
                bad_member = archive.testzip()
                version, evidence = _candidate_version(path, names)
                top_level = sorted({PurePosixPath(name).parts[0] for name in names if PurePosixPath(name).parts})
                results.append({
                    "path": str(path), "filename": path.name, "sha256": _sha256(path),
                    "size_bytes": path.stat().st_size, "version": version,
                    "version_evidence": evidence,
                    "integrity": "PASS" if bad_member is None else "FAIL",
                    "corrupt_member": bad_member, "member_count": len(names),
                    "top_level_structure": top_level,
                    "members": sorted(names),
                })
        except (OSError, zipfile.BadZipFile) as exc:
            results.append({"path": str(path), "filename": path.name,
                            "integrity": "FAIL", "error": str(exc)})
    return results


def runtime_descriptor(root: Path) -> dict[str, Any]:
    """Describe the selected local official runtime without assuming a ZIP remains."""
    archives = discover_archives(root)
    selected = next((item for item in archives if item.get("version") == "0.2.6"), None)
    selected = selected or next((item for item in archives if item.get("version") == "0.2.5"), None)
    extracted = runtime_root(root, selected.get("version") if selected else None)
    archive = inspect_archive(Path(selected["path"])) if selected else None
    if archive is None:
        raise FileNotFoundError("No identifiable local TradeSim archive is available")
    return {
        "archive_path": str(root / archive["filename"]), "archive_sha256": archive["sha256"],
        "detected_version": archive["version"], "version_evidence": archive["version_evidence"],
        "extracted_root": str(extracted), "python_requirement": "==3.13.0",
        "requirements_file": "requirements.txt", "notebook": archive["notebook"],
        "strategy_template": "strategy/Strategies_template.py",
        "strategy_example": "strategy/Example_strategy.py",
        "practice_data_root": "marketInfo/ticks", "adapter_version": ADAPTER_VERSION,
        "archive_integrity": archive["integrity"],
    }


def compatibility_status(version: str | None, *, known_versions: set[str] = frozenset({"0.2.5", "0.2.6"})) -> str:
    if version is None:
        return "BLOCKED"
    if version == "0.2.6" and version in known_versions:
        return "SUPPORTED_WITH_WARNINGS"
    if version in known_versions:
        return "SUPPORTED"
    return "NEEDS_ADAPTER_UPDATE"


def _archive_contents(path: Path) -> tuple[dict[str, str], dict[str, bytes]]:
    if path.is_dir():
        contents = {p.relative_to(path).as_posix(): p.read_bytes()
                    for p in path.rglob("*") if p.is_file()
                    and p.relative_to(path).parts[0] not in {"0.2.5", "0.2.6"}}
    else:
        with zipfile.ZipFile(path) as archive:
            raw_names = [name for name in archive.namelist() if not name.endswith("/")]
            roots = {PurePosixPath(name).parts[0] for name in raw_names if PurePosixPath(name).parts}
            wrapper = next(iter(roots)) if len(roots) == 1 and all("/" in name for name in raw_names) else None
            contents = {}
            for name in raw_names:
                rel = name[len(wrapper) + 1:] if wrapper and name.startswith(wrapper + "/") else name
                contents[rel] = archive.read(name)
    hashes = {name: hashlib.sha256(content).hexdigest() for name, content in contents.items()}
    return hashes, contents


def _compare_archives(baseline_path: Path, future_path: Path) -> dict[str, Any]:
    base_hashes, base_content = _archive_contents(baseline_path)
    future_hashes, future_content = _archive_contents(future_path)
    base_names, future_names = set(base_hashes), set(future_hashes)
    changed = sorted(name for name in base_names & future_names if base_hashes[name] != future_hashes[name])
    added, removed = sorted(future_names - base_names), sorted(base_names - future_names)

    def status_for(prefixes: tuple[str, ...], names: tuple[str, ...] = ()) -> str:
        selected = [name for name in base_names | future_names if name.startswith(prefixes) or name in names]
        return "UNCHANGED" if selected and not any(name in added or name in removed or name in changed for name in selected) else "CHANGED" if selected else "UNKNOWN"

    base_req = base_content.get("requirements.txt")
    future_req = future_content.get("requirements.txt")
    def requirement_map(body: bytes | None) -> dict[str, str]:
        result = {}
        for line in (body or b"").decode("utf-8", errors="replace").splitlines():
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            name = re.split(r"[<>=!~; ]", value, maxsplit=1)[0].lower().replace("_", "-")
            result[name] = value
        return result
    base_requirements = requirement_map(base_req)
    future_requirements = requirement_map(future_req)
    base_strategy = sorted(name for name in base_names if name.startswith("strategy/") and name.endswith(".py"))
    future_strategy = sorted(name for name in future_names if name.startswith("strategy/") and name.endswith(".py"))
    base_sources = {name: body for name, body in base_content.items() if name.startswith("tradeSim/") and name.endswith(".py")}
    future_sources = {name: body for name, body in future_content.items() if name.startswith("tradeSim/") and name.endswith(".py")}
    api_tokens = (b"create_order", b"place_order", b"change_order", b"cancel_order", b"submit_order")
    def api_surface(sources: dict[str, bytes]) -> dict[str, list[str]]:
        return {name: [token.decode() for token in api_tokens if token in body]
                for name, body in sources.items() if any(token in body for token in api_tokens)}

    return {
        "changed_files": changed, "added_files": added, "removed_files": removed,
        "wrapper_roots_normalized": True,
        "requirements": {"status": "UNCHANGED" if base_req == future_req else "CHANGED",
                         "baseline_sha256": hashlib.sha256(base_req).hexdigest() if base_req else None,
                         "future_sha256": hashlib.sha256(future_req).hexdigest() if future_req else None,
                         "added": sorted(future_requirements.keys() - base_requirements.keys()),
                         "removed": sorted(base_requirements.keys() - future_requirements.keys()),
                         "version_changes": {name: {"baseline": base_requirements[name], "future": future_requirements[name]}
                                             for name in sorted(base_requirements.keys() & future_requirements.keys())
                                             if base_requirements[name] != future_requirements[name]},
                         "baseline_present": base_req is not None, "future_present": future_req is not None},
        "strategy_templates_examples": {"status": "UNCHANGED" if base_strategy == future_strategy and not any(name.startswith("strategy/") for name in changed) else "CHANGED",
                                         "baseline": base_strategy, "future": future_strategy},
        "notebook_workflow": {"status": status_for((), ("TradingSimulation.ipynb",)) if "TradingSimulation.ipynb" in base_names | future_names else "UNKNOWN",
                              "baseline_present": "TradingSimulation.ipynb" in base_names,
                              "future_present": "TradingSimulation.ipynb" in future_names},
        "order_api_surface_tokens": {"baseline": api_surface(base_sources), "future": api_surface(future_sources)},
        "category_status": {
            "package_files": "CHANGED" if changed or added or removed else "UNCHANGED",
            "requirements": "UNCHANGED" if base_req == future_req else "CHANGED",
            "strategy_template_examples": "CHANGED" if base_strategy != future_strategy or any(name.startswith("strategy/") for name in changed) else "UNCHANGED",
            "notebook_workflow": "CHANGED" if "TradingSimulation.ipynb" in changed else "UNCHANGED",
            "order_apis": "CHANGED" if api_surface(base_sources) != api_surface(future_sources) else "UNCHANGED",
            "matching": status_for(("tradeSim/Execution.py", "tradeSim/Order.py", "tradeSim/StrategyHandler.py")),
            "fees": status_for(("tradeSim/CommissionService.py",)),
            "slippage": status_for(("tradeSim/Execution.py",)),
            "persistence": status_for(("tradeSim/TradeSim.py", "tradeSim/Portfolio.py", "tradeSim/TransactionLog.py")),
            "metrics": status_for(("tradeSim/PortSummarize.py", "tradeSim/Benchmark.py")),
            "practice_data_layout": status_for(("marketInfo/",)),
        },
    }


def safe_extraction_target(root: Path, version: str) -> Path:
    """Return a versioned destination only if it cannot overwrite a runtime."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        raise ValueError("version must be a semantic x.y.z value")
    destination = root / "tools" / "kgi_tradesim" / version
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing TradeSim runtime: {destination}")
    return destination


def extract_side_by_side(archive: Path, destination: Path) -> Path:
    """Extract an archive into a new destination after traversal checks."""
    if destination.exists():
        raise FileExistsError(f"Refusing to overwrite existing TradeSim runtime: {destination}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as bundle:
        bad = bundle.testzip()
        if bad:
            raise zipfile.BadZipFile(f"Corrupt archive member: {bad}")
        for name in bundle.namelist():
            member = PurePosixPath(name)
            if member.is_absolute() or ".." in member.parts:
                raise ValueError(f"Unsafe archive member path: {name}")
        bundle.extractall(destination)
    return destination


def build_comparison_report(root: Path) -> dict[str, Any]:
    archives = discover_archives(root)
    known = next((row for row in archives if row.get("version") == "0.2.5"), None)
    future = next((row for row in archives if row.get("version") == "0.2.6"
                   and row.get("integrity") == "PASS"), None)
    unknown = [row for row in archives if row.get("version") not in {"0.2.5", "0.2.6"}]
    baseline_dir = root / "tools" / "kgi_tradesim"
    if not known and (baseline_dir / "tradeSim" / "TradeSim.py").is_file():
        known = {"path": str(baseline_dir), "filename": "tools/kgi_tradesim (legacy 0.2.5 extraction)",
                 "version": "0.2.5", "version_evidence": "existing unversioned compatibility extraction; original ZIP absent",
                 "sha256": None, "source_tree_sha256": _tree_sha256(baseline_dir),
                 "size_bytes": None, "integrity": "SOURCE_TREE_AVAILABLE",
                 "member_count": sum(p.is_file() for p in baseline_dir.rglob("*")
                                      if p.relative_to(baseline_dir).parts[0] not in {"0.2.5", "0.2.6"})}
    # Keep reports useful: archive member inventories can be hundreds of entries.
    known = {k: v for k, v in known.items() if k != "members"} if known else None
    future = {k: v for k, v in future.items() if k != "members"} if future else None
    comparison = {
        "generated_at": __import__("datetime").datetime.now().astimezone().isoformat(),
        "baseline": known, "future": future,
        "future_status": "AVAILABLE_FOR_REVIEW" if future else "NEEDS_ADAPTER_UPDATE" if unknown else "NOT_AVAILABLE_YET",
        "version_statuses": {
            **({"0.2.5": compatibility_status("0.2.5")} if known and not any(a.get("version") == "0.2.5" for a in archives) else {}),
            **{item.get("version", "UNKNOWN"): compatibility_status(item.get("version"))
               for item in archives},
        },
        "baseline_extraction": known if known and known.get("integrity") == "SOURCE_TREE_AVAILABLE" else None,
        "unknown_versions": unknown,
        "adapter_policy": {
            "SUPPORTED": "Known adapter validated for this exact archive layout/version.",
            "SUPPORTED_WITH_WARNINGS": "Known version with explicitly listed non-blocking differences.",
            "NEEDS_ADAPTER_UPDATE": "Unknown version; do not run under 0.2.5 assumptions.",
            "BLOCKED": "Archive/version/runtime cannot be safely identified or validated.",
        },
        "capabilities": {name: {"status": "UNKNOWN" if future else "NOT_AVAILABLE_YET"}
                         for name in ("package_files", "requirements", "strategy_template_examples",
                                      "notebook_workflow", "order_apis", "matching", "fees",
                                      "slippage", "persistence", "metrics", "practice_data_layout")},
        "archives_discovered": [{k: v for k, v in item.items() if k != "members"} for item in archives],
        "archive_diff": _compare_archives(Path(known["path"]), Path(future["path"])) if known and future else None,
        "extraction_policy": "Side-by-side only at tools/kgi_tradesim/<version>; never overwrite.",
        "organizer_designated_competition_version": "0.2.6",
        "active_preferred_version": None,
        "active_preferred_version_gate": "Set only after exact Python 3.13.0 runtime validation succeeds.",
        "runtime_validation": "BLOCKED_EXACT_PYTHON_3_13_0_NOT_FOUND",
        "changelog_behavior_summary": [
            {"behavior": "Resting limit orders fill only after a trade through the limit; a touch does not fill.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "Each resting fill is capped by triggering tick volume, rounded down to board lots of 100; zero lot quantity does not fill.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "Earlier orders share a tick volume cap in placement order; residual remains open intraday.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "Immediate limit fills retain prior timing/price behavior and are subject to tick quantity cap.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "Remaining limit quantity is canceled at EOD and does not carry overnight.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "Market-order behavior is unchanged.", "evidence": "CHANGELOG DOCUMENTED; market fill source unchanged", "runtime": "NOT OBSERVED"},
            {"behavior": "Trade volume caps are tracked per symbol and reduced by team fills already made that day.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "One transaction-log row is written per fill; multiple fills for one order share an order number.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
            {"behavior": "All fills for one buy order join one portfolio lot; sell fills can close that lot in pieces.", "evidence": "CHANGELOG DOCUMENTED + SOURCE IMPLEMENTED", "runtime": "NOT OBSERVED"},
        ],
        "official_submission_repository_accessed": False,
    }
    return comparison


def write_comparison_report(root: Path, path: Path | None = None) -> dict[str, Any]:
    report = build_comparison_report(root)
    output = path or root / "reports" / "tradesim_version_comparison.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return report

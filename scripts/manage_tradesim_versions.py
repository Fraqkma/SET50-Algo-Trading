"""Inspect locally supplied TradeSim archives without downloading them."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.competition.tradesim_bridge.versioning import (  # noqa: E402
    build_comparison_report, extract_side_by_side, runtime_descriptor,
    safe_extraction_target, write_comparison_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="print descriptor and archive comparison")
    parser.add_argument("--extract-version", help="extract one locally discovered, identified version side-by-side")
    args = parser.parse_args()
    report = build_comparison_report(ROOT)
    if args.extract_version:
        future = next((item for item in report["archives_discovered"]
                       if item.get("version") == args.extract_version and item.get("integrity") == "PASS"), None)
        if future is None:
            parser.error("requested version is not present as an intact local TradeSim archive")
        target = safe_extraction_target(ROOT, args.extract_version)
        extract_side_by_side(Path(future["path"]), target)
        report["extracted_to"] = str(target)
    output = write_comparison_report(ROOT)
    output["runtime_descriptor"] = runtime_descriptor(ROOT)
    print(json.dumps(output, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Audit isolated historical daily artifacts without approving or repairing them."""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
STAGING_DIRS = [ROOT / "data" / "pilot" / "historical_daily", ROOT / "data" / "pilot" / "historical_acquisition"]


def audit_file(path: Path) -> dict:
    out = {"artifact": str(path.relative_to(ROOT)), "status": "UNAPPROVED", "rows": 0, "issues": []}
    try:
        frame = pd.read_csv(path)
        out["rows"] = int(len(frame))
        date_col = next((c for c in frame.columns if str(c).lower() == "date"), None)
        if date_col is None:
            out["issues"].append("missing Date column")
            return out
        dates = pd.to_datetime(frame[date_col], errors="coerce")
        out.update({"first_date": dates.min().date().isoformat(), "last_date": dates.max().date().isoformat()})
        if dates.isna().any(): out["issues"].append("invalid dates")
        if dates.duplicated().any(): out["issues"].append("duplicate dates")
        if not dates.is_monotonic_increasing: out["issues"].append("dates not monotonic")
        for col in ("Open", "High", "Low", "Close", "Volume"):
            if col in frame:
                values = pd.to_numeric(frame[col], errors="coerce")
                if values.isna().any(): out["issues"].append(f"invalid {col}")
                if col != "Volume" and (values <= 0).any(): out["issues"].append(f"non-positive {col}")
                if col == "Volume" and (values < 0).any(): out["issues"].append("negative Volume")
    except Exception as exc:
        out["issues"].append(f"read error: {type(exc).__name__}: {exc}")
    return out


def run() -> dict:
    paths = sorted({p for directory in STAGING_DIRS if directory.exists() for p in directory.glob("*.csv")})
    records = [audit_file(p) for p in paths]
    payload = {"status": "UNAPPROVED_AUDIT", "records": records, "production_mutated": False,
               "approved_manifest_mutated": False}
    (ROOT / "reports" / "historical_daily_coverage.csv").write_text("", encoding="utf-8")
    if records:
        with (ROOT / "reports" / "historical_daily_coverage.csv").open("w", newline="", encoding="utf-8") as f:
            keys = sorted({k for r in records for k in r if k != "issues"}) + ["issues"]
            writer = csv.DictWriter(f, fieldnames=keys); writer.writeheader()
            for r in records:
                row = {k: r.get(k, "") for k in keys}; row["issues"] = "; ".join(r.get("issues", [])); writer.writerow(row)
    (ROOT / "reports" / "historical_daily_quality.csv").write_text("artifact,issue_count,issues\n" + "\n".join(
        f"{r['artifact']},{len(r.get('issues', []))},\"{'; '.join(r.get('issues', []))}\"" for r in records), encoding="utf-8")
    (ROOT / "reports" / "historical_daily_audit.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload


if __name__ == "__main__":
    argparse.ArgumentParser().parse_args(); run()

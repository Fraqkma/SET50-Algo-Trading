"""Audit immutable raw OHLC anomalies without repairing vendor data."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
RELATIVE_TOLERANCE = 0.001
OFFICIAL_SET_EOD_SOURCE = "https://www.set.or.th/en/services/connectivity-and-data/data/historical"


@dataclass(frozen=True)
class OhlcAdjudication:
    """One raw date that breaches the OHLC envelope beyond tolerance."""

    set_symbol: str
    yahoo_ticker: str
    raw_file: str
    date: str
    open: str
    high: str
    low: str
    close: str
    volume: str
    violated_rule: str
    gap: str
    classification: str
    evidence_source: str
    approval_decision: str
    reason: str


def find_ohlc_anomalies(project_root: str | Path = ROOT) -> list[OhlcAdjudication]:
    """Inspect every reported OHLC anomaly using the raw CSV unchanged."""
    root = Path(project_root).resolve()
    with (root / "reports" / "market_data_remediation.csv").open("r", encoding="utf-8-sig", newline="") as handle:
        remediation = list(csv.DictReader(handle))
    findings: list[OhlcAdjudication] = []
    for record in remediation:
        if "OHLC_ANOMALY" not in (record.get("issue_classification") or ""):
            continue
        reported_file = record.get("raw_file") or ""
        raw_file = (root / reported_file).resolve()
        if not raw_file.is_file():
            raise FileNotFoundError(f"Reported anomaly file is missing: {reported_file}")
        with raw_file.open("r", encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                findings.extend(_row_anomalies(record, reported_file, row))
    return findings


def write_ohlc_adjudication_report(project_root: str | Path = ROOT) -> list[OhlcAdjudication]:
    """Write an auditable anomaly report without changing raw inputs."""
    root = Path(project_root).resolve()
    findings = find_ohlc_anomalies(root)
    path = root / "reports" / "ohlc_anomaly_adjudication.csv"
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(asdict(findings[0])))
        writer.writeheader()
        writer.writerows(asdict(finding) for finding in findings)
    lines = ["# OHLC Anomaly Adjudication", "", f"- Investigated symbols: {len({item.set_symbol for item in findings})}", f"- Violating raw rows: {len(findings)}", "", "## Decision", "", "Every row remains `NEEDS_REVIEW`. The raw values breach the OHLC envelope and the repository has no licensed official SET daily EOD extract with which to corroborate individual dates. The official reference source is listed per row; no replacement data was used."]
    (root / "reports" / "ohlc_anomaly_adjudication.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return findings


def _row_anomalies(record: dict[str, str], reported_file: str, row: dict[str, str]) -> list[OhlcAdjudication]:
    open_price, high, low, close = (float(row[column]) for column in ("Open", "High", "Low", "Close"))
    high_gap = max(0.0, max(open_price, close) - high)
    low_gap = max(0.0, low - min(open_price, close))
    results: list[OhlcAdjudication] = []
    if high_gap > max(open_price, close) * RELATIVE_TOLERANCE:
        results.append(_finding(record, reported_file, row, "HIGH_BELOW_OPEN_OR_CLOSE", high_gap))
    if low_gap > min(open_price, close) * RELATIVE_TOLERANCE:
        results.append(_finding(record, reported_file, row, "LOW_ABOVE_OPEN_OR_CLOSE", low_gap))
    return results


def _finding(record: dict[str, str], reported_file: str, row: dict[str, str], rule: str, gap: float) -> OhlcAdjudication:
    return OhlcAdjudication(
        set_symbol=record["set_symbol"], yahoo_ticker=record["yahoo_ticker"], raw_file=reported_file,
        date=row["Date"], open=row["Open"], high=row["High"], low=row["Low"], close=row["Close"], volume=row["Volume"],
        violated_rule=rule, gap=f"{gap:.10g}", classification="YAHOO_VENDOR_DATA_ISSUE_SUSPECTED",
        evidence_source=f"Immutable Yahoo raw file; official SET EOD reference requires licensed access: {OFFICIAL_SET_EOD_SOURCE}",
        approval_decision="NEEDS_REVIEW",
        reason="The OHLC envelope is mathematically violated. No public authoritative per-date comparison was available; raw data was neither changed nor replaced.",
    )


if __name__ == "__main__":
    findings = write_ohlc_adjudication_report()
    print(f"symbols={len({item.set_symbol for item in findings})} rows={len(findings)}")

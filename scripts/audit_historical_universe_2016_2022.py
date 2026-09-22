"""Generate the research-only historical SET50 universe audit.

This script deliberately writes only under data/pilot and reports/pilot.  It does
not alter the canonical constituent file, mappings, raw data, or production code.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "pilot" / "historical_universe_2016_2022"
REPORT_DIR = ROOT / "reports" / "pilot" / "historical_universe_2016_2022"
CANONICAL = ROOT / "data" / "processed" / "constituents" / "historical_set50.csv"

ARCHIVE_URL = "https://www.set.or.th/en/market/information/securities-list/constituents-list-set50-set100"

PERIODS = [
    f"{year}_H{half}" for year in range(2016, 2023) for half in (1, 2)
]

FULL_LISTS = {
    "2017_H1": "ADVANC,AOT,BA,BANPU,BBL,BCP,BDMS,BEM,BH,BLA,BTS,CBG,CENTEL,CK,CPALL,CPF,CPN,DELTA,DTAC,EGCO,GLOBAL,GLOW,GPSC,HMPRO,INTUCH,IRPC,IVL,KBANK,KCE,KKP,KTB,LH,MINT,PS,PTG,PTT,PTTEP,PTTGC,ROBINS,SCB,SCC,SPRC,TCAP,THAI,TMB,TOP,TPIPL,TRUE,TU,WHA",
    "2020_H2": "ADVANC,AOT,AWC,BBL,BDMS,BEM,BGRIM,BH,BJC,BPP,BTS,CBG,CPALL,CPF,CPN,CRC,DTAC,EA,EGCO,GLOBAL,GPSC,GULF,HMPRO,INTUCH,IRPC,IVL,KBANK,KTB,KTC,LH,MINT,MTC,OSP,PTT,PTTEP,PTTGC,RATCH,SAWAD,SCB,SCC,TCAP,TISCO,TMB,TOA,TOP,TRUE,TTW,TU,VGI,WHA",
    "2021_H2": "ADVANC,AOT,BBL,BDMS,BEM,BGRIM,BH,BJC,BTS,CBG,COM7,CPALL,CPF,CPN,CRC,DELTA,DTAC,EA,EGCO,GLOBAL,GPSC,GULF,HMPRO,INTUCH,IRPC,IVL,KBANK,KCE,KTB,KTC,LH,MINT,MTC,OR,OSP,PTT,PTTEP,PTTGC,RATCH,SAWAD,SCB,SCC,SCGP,STA,STGT,TISCO,TOP,TRUE,TTB,TU",
    "2022_H1": "ADVANC,AOT,AWC,BANPU,BBL,BDMS,BEM,BGRIM,BH,BTS,CBG,COM7,CPALL,CPF,CPN,CRC,DTAC,EA,EGCO,GLOBAL,GPSC,GULF,HMPRO,INTUCH,IRPC,IVL,KBANK,KCE,KTB,KTC,LH,MINT,MTC,OR,OSP,PTT,PTTEP,PTTGC,RATCH,SAWAD,SCB,SCC,SCGP,STGT,TIDLOR,TISCO,TOP,TRUE,TTB,TU",
    "2022_H2": "ADVANC,AOT,AWC,BANPU,BBL,BDMS,BEM,BGRIM,BH,BLA,BTS,CBG,CPALL,CPF,CPN,CRC,DTAC,EA,EGCO,GLOBAL,GPSC,GULF,HMPRO,INTUCH,IRPC,IVL,JMART,JMT,KBANK,KCE,KTB,KTC,LH,MINT,MTC,OR,OSP,PTT,PTTEP,PTTGC,SAWAD,SCB,SCC,SCGP,TIDLOR,TISCO,TOP,TRUE,TTB,TU",
}

SOURCE_BY_PERIOD = {
    "2017_H1": ("https://mondovisione.com/_assets/files/Attachment-for-SETRelease-111-2016-Eng.pdf", "SECONDARY_MIRROR_OF_SET_DOCUMENT", "2016-12-16"),
    "2020_H2": ("https://www.lhsec.co.th/uploads/userfiles/files/2020/SET50_H2_2020.pdf", "SECONDARY_MIRROR_OF_SET_DOCUMENT", "2020-06-15"),
    "2021_H2": ("https://investor.aapico.com/storage/updates/press-releases/2021/06/20210625-ah-news-en.pdf", "SECONDARY_MIRROR_OF_SET_DOCUMENT", "2021-06-16"),
    "2022_H1": ("https://www.lhsec.co.th/uploads/userfiles/files/2022/SET50_H1_2022.pdf", "SECONDARY_MIRROR_OF_SET_DOCUMENT", "2021-12-17"),
    "2022_H2": ("https://media.set.or.th/set/Documents/2022/Jun/SET50_SET100_H2_2022.pdf", "OFFICIAL_SET_PDF", "2022-06-20"),
}

PARTIAL_NOTES = {
    "2016_H1": "Secondary change-only evidence located; no complete constituent table asserted.",
    "2016_H2": "Official archive entry exists, but the downloadable constituent file is login-gated; no complete list asserted.",
    "2017_H2": "Secondary change announcement located; no complete constituent table asserted.",
    "2018_H1": "Official archive entry exists; no accessible complete constituent table located in this audit.",
    "2018_H2": "Secondary change announcement located; no complete constituent table asserted.",
    "2021_H1": "Secondary review announcement located; no complete constituent table asserted.",
}


def dates(period: str) -> tuple[str, str]:
    year, half = period.split("_H")
    return (f"{year}-01-01", f"{year}-06-30") if half == "1" else (f"{year}-07-01", f"{year}-12-31")


def canonical_symbols(period: str) -> set[str]:
    with CANONICAL.open(newline="", encoding="utf-8-sig") as handle:
        return {row["symbol"] for row in csv.DictReader(handle) if row["period"] == period}


def delta(left: set[str], right: set[str]) -> dict[str, list[str] | int]:
    return {
        "added": sorted(right - left),
        "removed": sorted(left - right),
        "unchanged": sorted(left & right),
        "unchanged_count": len(left & right),
    }


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    research_rows: list[dict[str, str]] = []
    period_results: list[dict[str, object]] = []
    source_registry: dict[str, dict[str, str]] = {
        "official_archive": {
            "source_url": ARCHIVE_URL,
            "source_type": "OFFICIAL_SET_ARCHIVE",
            "coverage": "Lists all requested half-year archive entries and review dates; downloads are login-gated.",
            "confidence": "HIGH_FOR_PERIOD_EXISTENCE",
        }
    }

    for period in PERIODS:
        start, end = dates(period)
        if period in FULL_LISTS:
            url, source_type, publication = SOURCE_BY_PERIOD[period]
            symbols = FULL_LISTS[period].split(",")
            status = "OFFICIAL" if source_type == "OFFICIAL_SET_PDF" else "SECONDARY"
            for symbol in symbols:
                research_rows.append({
                    "period": period, "effective_from": start, "effective_to": end,
                    "symbol": symbol, "company_name": "", "source_url": url,
                    "source_type": source_type, "provenance_source_url": url,
                    "confidence": "HIGH", "revision_status": "SOURCE_SNAPSHOT_REPORTED",
                    "mapping_status": "UNREVIEWED_HISTORICAL_SECURITY_IDENTITY",
                    "notes": "Company name intentionally blank; identity continuity is out of scope.",
                })
            source_registry[period] = {"source_url": url, "source_type": source_type, "publication_date": publication, "coverage": "Complete 50-symbol table", "confidence": "HIGH"}
            period_results.append({"period": period, "effective_from": start, "effective_to": end, "number_of_constituents": len(symbols), "source_status": status, "confidence": "HIGH", "source_url": url, "source_type": source_type, "publication_date": publication, "coverage": "Complete constituent table", "notes": "Full list transcribed from cited source."})
        else:
            status = "PARTIAL" if period in PARTIAL_NOTES else "UNRESOLVED"
            note = PARTIAL_NOTES.get(period, "Official archive entry exists, but no complete constituent table was verified; no membership inferred.")
            period_results.append({"period": period, "effective_from": start, "effective_to": end, "number_of_constituents": 0, "source_status": status, "confidence": "LOW", "source_url": ARCHIVE_URL, "source_type": "OFFICIAL_SET_ARCHIVE", "publication_date": "", "coverage": "Archive entry only; no full membership rows asserted", "notes": note})

    research_csv = DATA_DIR / "historical_set50_2016_2022_research.csv"
    fields = list(research_rows[0])
    with research_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(research_rows)

    by_period = {period: {row["symbol"] for row in research_rows if row["period"] == period} for period in FULL_LISTS}
    membership_changes = []
    for left, right in zip(PERIODS, PERIODS[1:]):
        if left in by_period and right in by_period:
            changes = delta(by_period[left], by_period[right])
            membership_changes.append({"from_period": left, "to_period": right, "status": "COMPUTABLE", **changes})
        else:
            membership_changes.append({"from_period": left, "to_period": right, "status": "NOT_COMPUTABLE", "reason": "At least one adjacent period lacks a verified complete constituent table."})

    canonical_2023 = canonical_symbols("2023_H1")
    comparison = {"from_period": "2022_H2", "to_period": "2023_H1", "canonical_file": str(CANONICAL.relative_to(ROOT)), "status": "COMPUTABLE", **delta(by_period["2022_H2"], canonical_2023)}
    audit_csv = REPORT_DIR / "historical_universe_2016_2022_audit.csv"
    audit_fields = ["period", "effective_from", "effective_to", "number_of_constituents", "source_status", "confidence", "source_url", "source_type", "publication_date", "coverage", "notes"]
    with audit_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=audit_fields)
        writer.writeheader()
        writer.writerows(period_results)

    audit = {
        "scope": {"periods": PERIODS, "effective_date_rule": "Jan 1-Jun 30 / Jul 1-Dec 31 unless source states otherwise", "source_archive": ARCHIVE_URL},
        "period_results": period_results,
        "source_registry": list(source_registry.values()),
        "complete_periods": [p for p in PERIODS if p in FULL_LISTS],
        "partial_periods": [p for p in PERIODS if p in PARTIAL_NOTES],
        "unresolved_periods": [p for p in PERIODS if p not in FULL_LISTS and p not in PARTIAL_NOTES],
        "research_row_count": len(research_rows),
        "unique_historical_securities": sorted({row["symbol"] for row in research_rows}),
        "membership_changes": membership_changes,
        "canonical_comparison": comparison,
        "integrity": {"all_required_periods_audited": len(period_results) == len(PERIODS), "all_research_rows_have_provenance": all(row["provenance_source_url"] for row in research_rows), "canonical_modified": False, "raw_data_modified": False, "mapping_modified": False},
    }
    (REPORT_DIR / "historical_universe_2016_2022_audit.json").write_text(json.dumps(audit, indent=2, ensure_ascii=False), encoding="utf-8")

    lines = ["# Historical SET50 Universe Audit 2016–2022", "", "## Executive result", "", f"This is a research-only audit. It does not replace the canonical universe. Five periods have complete cited tables ({len(research_rows)} rows); nine periods remain partial or unresolved. The result is not yet strong enough for canonical adoption.", "", "## Coverage", "", "| Period | Constituents | Status | Confidence |", "|---|---:|---|---|"]
    lines += [f"| {r['period']} | {r['number_of_constituents']} | {r['source_status']} | {r['confidence']} |" for r in period_results]
    lines += ["", "## Source quality and evidence gaps", "", "The SET archive lists every requested half-year and provides the effective review windows, but its downloads are login-gated in the public page. Complete lists for 2017 H1, 2020 H2, 2021 H2, and 2022 H1 come from secondary mirrors of SET-origin documents; 2022 H2 comes from an official SET PDF. Partial periods have change-only or archive evidence and no full membership is inferred.", "", "Unresolved/partial periods: " + ", ".join(p for p in PERIODS if p not in FULL_LISTS), ".", "", "## Membership changes", ""]
    for change in membership_changes:
        if change["status"] == "COMPUTABLE":
            lines.append(f"- {change['from_period']} → {change['to_period']}: added {', '.join(change['added']) or 'none'}; removed {', '.join(change['removed']) or 'none'}; unchanged {change['unchanged_count']}.")
        else:
            lines.append(f"- {change['from_period']} → {change['to_period']}: not computable — {change['reason']}")
    lines += ["", "## Comparison with canonical 2023 H1", "", f"2022 H2 → canonical 2023 H1: added {', '.join(comparison['added']) or 'none'}; removed {', '.join(comparison['removed']) or 'none'}; unchanged {comparison['unchanged_count']}.", "The canonical file was read only and was not modified.", "", "## Identity and provenance controls", "", "Historical symbols are preserved exactly as published by each cited source. No predecessor/successor securities were merged. Company names are blank in the research rows to avoid unsupported historical-name inference; identity continuity remains a separate audit. Every included row has a provenance URL.", "", "## Integrity", "", f"- Research rows: {len(research_rows)}", f"- Unique historical securities represented: {len(audit['unique_historical_securities'])}", "- Required periods audited: yes", "- Raw/canonical/mapping/gate/strategy/backtest files modified: no", "- OHLCV downloaded: no", "", "## Source URLs", "", f"- Official SET archive: {ARCHIVE_URL}"]
    for period in FULL_LISTS:
        lines.append(f"- {period}: {SOURCE_BY_PERIOD[period][0]}")
    (REPORT_DIR / "historical_universe_2016_2022_audit.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"research_rows": len(research_rows), "unique_historical_securities": len(audit["unique_historical_securities"]), "report_dir": str(REPORT_DIR)}, indent=2))


if __name__ == "__main__":
    main()

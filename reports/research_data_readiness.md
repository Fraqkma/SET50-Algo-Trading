# Final Research-Data Readiness

This report is derived from the acquisition, remediation, and OHLC adjudication records. Raw Yahoo files were not modified and no OHLC values were repaired or fabricated.

## Status counts
- APPROVED: 18
- APPROVED_WITH_KNOWN_GAP: 2
- NEEDS_REVIEW: 42
- REJECTED: 1

## Symbol decisions
- `INTUCH` — REJECTED; range=none to none; classification=MISSING_YAHOO_DATA;CORPORATE_ACTION_ISSUE;TICKER_IDENTITY_ISSUE; reason=Yahoo mapping/data is unavailable; retain INTUCH only as the pre-merger identity.
- `ADVANC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `AOT` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `AWC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BANPU` — NEEDS_REVIEW; range=none to none; classification=KNOWN_SUSPENSION;OHLC_ANOMALY;INSUFFICIENT_HISTORICAL_COVERAGE; reason=Suspension is documented, but the OHLC anomaly and trailing coverage gap require review.
- `BBL` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BCP` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BDMS` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `BEM` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BGRIM` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `BH` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BJC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `BTS` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CBG` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CCET` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CENTEL` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `COM7` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `CPALL` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CPF` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CPN` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `CRC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `DELTA` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `EA` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `EGCO` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `GLOBAL` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `GPSC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `GULF` — APPROVED_WITH_KNOWN_GAP; range=2025-04-03 to 2026-09-04; classification=INSUFFICIENT_HISTORICAL_COVERAGE;CORPORATE_ACTION_ISSUE; reason=Approved only for the observed post-merger GULF series; no pre-merger history is inferred.
- `HMPRO` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `ITC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `IVL` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `JMART` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `JMT` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `KBANK` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `KCE` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `KKP` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `KTB` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `KTC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `LH` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `MINT` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `MRDIYT` — APPROVED; range=2025-11-05 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `MTC` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `OR` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `OSP` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `PTT` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `PTTEP` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `PTTGC` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `RATCH` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `SAWAD` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `SCB` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `SCC` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `SCGP` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `TCAP` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `TFG` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `THAI` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `TIDLOR` — APPROVED_WITH_KNOWN_GAP; range=2025-05-16 to 2026-09-04; classification=INSUFFICIENT_HISTORICAL_COVERAGE;CORPORATE_ACTION_ISSUE; reason=Approved only from the observed Tidlor Holdings series start; the pre-2025-05-16 entity gap remains excluded.
- `TISCO` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `TLI` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `TOP` — APPROVED; range=2023-01-03 to 2026-09-04; classification=NONE; reason=No acquisition validation findings were recorded.
- `TRUE` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `TTB` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `TU` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `VGI` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.
- `WHA` — NEEDS_REVIEW; range=none to none; classification=OHLC_ANOMALY;YAHOO_VENDOR_DATA_ISSUE_SUSPECTED; reason=Raw OHLC relationship warning is visible; adjudication found no public authoritative daily comparison, so it cannot be accepted, repaired, or replaced.

## Downstream manifest

Only `APPROVED` and `APPROVED_WITH_KNOWN_GAP` rows appear in `data/processed/approved_market_data_manifest.csv`. Consumers must still pass each date through `MarketDataEligibilityGate`.

Feature engineering and backtesting are not started.

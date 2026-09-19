from pathlib import Path

from scripts.audit_historical_set50_acquisition_plan import (
    IDENTITY_CASES,
    build_payload,
    build_matrix,
    read_symbols,
    required_snapshots,
)


def test_required_snapshots_are_deterministic_and_complete():
    snapshots = required_snapshots()
    assert len(snapshots) == 22
    assert snapshots[0] == {"period": "2016 H1", "effective_from": "2016-01-01", "effective_to": "2016-06-30"}
    assert snapshots[-1]["period"] == "2026 H2"
    assert snapshots[-1]["effective_from"] == "2026-07-01"


def test_symbols_are_provisional_and_include_identity_aliases():
    symbols = read_symbols()
    assert len(symbols) == len(set(symbols))
    for symbol in ("TRUEE", "DTAC", "GULFI", "INTUCH", "BANPUU", "MRDIYT"):
        assert symbol in symbols


def test_matrix_is_planning_only():
    rows = build_matrix(read_symbols())
    assert rows
    assert all(row["acquisition_status"] == "NOT_STARTED" for row in rows)
    assert all(row["validation_status"] == "NOT_STARTED" for row in rows)
    assert all(row["human_approval_required"] == "YES" for row in rows)


def test_payload_does_not_claim_acquisition_or_modify_approved_data():
    payload = build_payload()
    assert payload["required_snapshot_count"] == 22
    assert payload["acquisition_performed"] is False
    assert payload["approved_manifest_modified"] is False
    assert payload["raw_data_modified"] is False
    assert payload["eligibility_gate_modified"] is False
    assert payload["backtest_run"] is False
    assert {case["historical_symbol"] for case in IDENTITY_CASES} <= set(payload["observed_repository_and_known_identity_symbols"])

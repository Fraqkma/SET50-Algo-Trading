from scripts.audit_historical_security_identity import CASES, payload


def test_all_required_identity_cases_are_present():
    names = {row["case"] for row in CASES}
    assert {"TRUE / TRUEE / DTAC", "GULF / INTUCH / GULFI", "TIDLOR", "BANPU / BANPUU", "MRDIYT", "SCB", "TTB"} <= names


def test_audit_is_conservative_and_read_only():
    data = payload()
    assert data["bulk_price_acquisition"] is False
    assert data["approved_manifest_modified"] is False
    assert data["raw_data_modified"] is False
    assert data["eligibility_gate_modified"] is False
    assert data["strategy_or_backtest_modified"] is False
    assert all(row["human_approval"] in {"YES", "NO_FOR_BOUNDARY; YES_FOR_APPROVAL", "YES_FOR_DATA_MAPPING"} for row in CASES)


def test_confidence_values_and_source_provenance():
    assert {row["confidence"] for row in CASES} <= {"VERIFIED", "PARTIALLY_VERIFIED", "UNRESOLVED"}
    assert all(source["official"] is True for source in payload()["sources"])
    assert all(source["url"].startswith("https://") for source in payload()["sources"])

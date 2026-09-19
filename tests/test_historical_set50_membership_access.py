from scripts.audit_historical_set50_membership_access import PERIODS, payload


def test_exact_missing_snapshot_set_and_boundaries():
    data = payload()
    assert len(PERIODS) == 14
    assert [row["period"] for row in data["snapshots"]] == PERIODS
    assert data["snapshots"][0]["effective_from"] == "2016-01-01"
    assert data["snapshots"][-1]["effective_to"] == "2022-12-31"


def test_access_audit_is_conservative():
    data = payload()
    assert data["official_source_identified_count"] == 14
    assert data["accessible_without_authentication_count"] == 0
    assert data["requiring_legitimate_set_access_count"] == 14
    assert data["constituent_list_verified_count"] == 0
    assert data["period_metadata_unverified_count"] == 0
    assert data["ready_for_full_historical_price_acquisition"] is False
    assert data["synthetic_membership_constructed"] is False


def test_no_production_mutation_and_required_identity_cross_reference():
    data = payload()
    assert not data["bulk_price_data_downloaded"]
    assert not data["raw_data_modified"]
    assert not data["approved_manifest_modified"]
    assert not data["eligibility_rules_modified"]
    cases = {row["case"] for row in data["identity_cross_reference"]}
    assert {"TRUE / TRUEE / DTAC", "GULF / INTUCH / GULFI", "TIDLOR", "BANPU / BANPUU", "SCB / SCBB", "TMB / TTB", "MRDIYT"} == cases

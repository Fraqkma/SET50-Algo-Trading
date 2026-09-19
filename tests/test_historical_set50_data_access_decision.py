from scripts.audit_historical_set50_data_access_decision import payload


def test_routes_are_official_and_include_recommended_path():
    data = payload()
    assert len(data["routes"]) == 5
    assert all(route["official"] for route in data["routes"])
    assert any(route["assessment"] == "MOST_SUITABLE_INITIAL_ROUTE" for route in data["routes"])


def test_minimum_schema_and_acceptance_are_conservative():
    data = payload()
    fields = {row["field"]: row["priority"] for row in data["minimum_dataset_fields"]}
    for required in ("index_name", "effective_start_date", "effective_end_date", "historical_symbol", "security_identifier", "issuer_security_name", "membership_status", "revision_or_boundary_date", "source_provenance_and_revision"):
        assert fields[required] == "REQUIRED"
    assert len(data["acceptance_criteria"]) >= 5
    assert len(data["rejection_criteria"]) >= 5


def test_no_acquisition_or_production_mutation():
    data = payload()
    assert data["ready_for_price_acquisition"] is False
    assert data["bulk_price_data_downloaded"] is False
    assert data["production_data_modified"] is False
    assert "separate official security master" in data["membership_only_consequence"]

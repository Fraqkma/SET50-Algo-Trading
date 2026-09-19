from scripts.build_historical_set50_data_request_spec import payload


def test_spec_covers_exact_22_periods():
    data = payload()
    assert data["period_count"] == 22
    assert data["canonical_periods"][0] == "2016 H1"
    assert data["canonical_periods"][-1] == "2026 H2"


def test_required_identity_and_price_semantics_are_requested():
    data = payload()
    fields = {row["field"]: row["priority"] for row in data["requested_fields"]}
    for field in ("index_name", "effective_start_date", "effective_end_date", "historical_symbol", "security_identifier", "issuer_security_name", "membership_status", "revision_boundary_date", "source_provenance"):
        assert fields[field] == "REQUIRED"
    categories = {row["category"] for row in data["request_checklist"]}
    assert {"price_semantics", "execution_suitability", "price_corporate_actions", "licensing"} <= categories


def test_pre_acquisition_and_import_gates_are_false():
    data = payload()
    assert data["price_acquisition_requested_now"] is False
    assert data["data_downloaded"] is False
    assert data["production_data_modified"] is False
    assert data["ready_for_import"] is False
    assert data["licensing_cost_status"] == "UNRESOLVED_UNTIL_SET_QUOTE"

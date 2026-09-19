from scripts.audit_intraday_data_sources import SYMBOLS, payload, storage_rows


def test_probe_universe_is_exact_current_approved_symbol_set():
    assert len(SYMBOLS) == 20
    assert {"BDMS", "GULF", "MRDIYT", "TIDLOR", "TOP"} <= set(SYMBOLS)


def test_official_source_is_primary_and_no_collection_occurs():
    data = payload()
    official = next(row for row in data["sources"] if row["provider_type"] == "OFFICIAL")
    assert official["classification"] == "A_PRIMARY_INTRADAY_COLLECTION"
    assert data["network_probes_performed"] is False
    assert data["market_data_downloaded"] is False
    assert data["daily_dataset_modified"] is False
    assert data["collector_ready"] is False


def test_storage_estimates_cover_requested_dimensions_without_gap_filling():
    records = storage_rows()
    assert len(records) == 18
    assert {(row["symbols"], row["frequency"], row["retention"]) for row in records} >= {(20, "1m", "1_month"), (50, "15m", "1_year")}
    assert all(row["estimated_compressed_storage_mb"] > 0 for row in records)
    assert all("no synthetic gap bars" in row["assumption"] for row in records)

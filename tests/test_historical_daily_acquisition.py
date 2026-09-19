from scripts.acquire_historical_daily import acquire, planned_symbols


def test_plan_is_staging_only_and_deterministic():
    first = acquire(download=False)
    second = acquire(download=False)
    assert first["status"] == "PLAN_ONLY"
    assert first["symbols"] == second["symbols"]
    assert first["production_mutated"] is False
    assert first["approved_manifest_mutated"] is False


def test_planned_symbols_are_unique():
    symbols = planned_symbols()
    assert symbols == sorted(set(symbols))

from scripts.validate_settrade_reconnect import run_mock_validation


def test_mock_reconnect_has_full_transitions_and_restores_unique_subscriptions():
    report = run_mock_validation()
    states = [item["state"] for item in report["transitions"]]
    assert states == ["STARTING", "LIVE", "DEGRADED", "OFFLINE", "RECONNECTING", "RECOVERED", "LIVE"]
    assert report["validation_type"] == "MOCK"
    assert report["subscription_restoration"] is True
    assert report["duplicate_result"]["persisted_rows_created"] == 0
    assert "LIVE_NETWORK_INTERRUPTION_NOT_OBSERVED" in report["warnings"]
    assert report["orders_placed"] == 0

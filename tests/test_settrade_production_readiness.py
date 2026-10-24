from __future__ import annotations

from types import SimpleNamespace

import scripts.check_settrade_production_readiness as readiness


def test_readiness_never_calls_sdk_mutation_methods(monkeypatch) -> None:
    called: list[str] = []

    class FakeClient:
        def __init__(self, *_args, **_kwargs):
            pass

        def authenticate(self):
            return object()

        def market_data(self):
            return object()

        def quote(self, symbol):
            assert symbol == "PTT"
            return {"last": 10}

        def candlestick(self, symbol, interval, **kwargs):
            return {"time": ["timestamp"]}

        def realtime(self):
            return object()

    monkeypatch.setattr(readiness, "configured_environment", lambda _root: "production")
    monkeypatch.setattr(readiness, "configured_account_number", lambda _root: None)
    monkeypatch.setattr(readiness, "SettradeConfig", SimpleNamespace(from_env=lambda *_: SimpleNamespace(broker_id="013", app_code="ALGO_EQ", app_id="id", app_secret="secret")))
    monkeypatch.setattr(readiness.importlib.metadata, "version", lambda _name: "2.2.1")
    monkeypatch.setattr(readiness, "_sdk_capabilities", lambda: {"place_order_method_present_not_invoked": True})
    monkeypatch.setattr(readiness, "check_disk", lambda *_: SimpleNamespace(state="OK", free_bytes=100))
    monkeypatch.setattr(readiness, "resolve_data_root", lambda *_: readiness.ROOT)
    monkeypatch.setattr(readiness, "SettradeClient", FakeClient)

    result = readiness.run()

    assert result["status"] == "READY_WITH_WARNINGS"
    assert result["orders_placed"] == 0
    assert result["account_private_state"] == "REQUIRES_ACCOUNT_NUMBER"
    assert called == []


def test_readiness_refuses_nonproduction_routing(monkeypatch) -> None:
    monkeypatch.setattr(readiness, "configured_environment", lambda _root: "sandbox")
    result = readiness.run()
    assert result["status"] == "NOT_READY"
    assert "broker_id" not in result


def test_coverage_audit_keeps_unobserved_days_unknown(tmp_path) -> None:
    from scripts.audit_settrade_production_coverage import _day_by_day

    sandbox = tmp_path / "sandbox"
    production = tmp_path / "production"
    candle = sandbox / "normalized/bars_1m/data.csv"
    candle.parent.mkdir(parents=True)
    candle.write_text(
        "timestamp,symbol\n2026-10-01T03:00:00+00:00,AAA\n",
        encoding="utf-8",
    )
    report = _day_by_day(
        {"universe": {"symbols": ["AAA", "BBB"]}, "daily_collection": {"2026-10-01": {"quality": "PARTIAL_SESSION"}}, "weekday_dates_without_artifacts": ["2026-10-02"]},
        {"sandbox": (sandbox, "sandbox"), "production": (production, "production")},
    )

    day = report["candles_1m"]["2026-10-01"]["sandbox"]
    assert day["provenance"] == "SANDBOX"
    assert day["missing_symbols"] == ["BBB"]
    assert day["reason_code"] == "PARTIAL_SESSION"
    missing = report["candles_1m"]["2026-10-02"]["sandbox"]
    assert missing["reason_code"] == "NO_RUNTIME_EVIDENCE"
    assert missing["provenance"] == "UNKNOWN"


def test_daily_refresh_preserves_overlapping_values_and_appends_only_new_dates() -> None:
    import pandas as pd
    from scripts.refresh_current_set50_daily import merge_new_rows

    existing = pd.DataFrame([{"Date": "2026-10-01", "Close": 10.0}])
    incoming = pd.DataFrame([{"Date": "2026-10-01", "Close": 11.0}, {"Date": "2026-10-02", "Close": 12.0}])
    merged, conflicts = merge_new_rows(existing, incoming)

    assert merged["Close"].tolist() == [10.0, 12.0]
    assert conflicts == [{"date": "2026-10-01", "differing_fields": ["Close"], "resolution": "PRESERVED_EXISTING; incoming overlap not written"}]

    duplicate_data = pd.DataFrame([{"Date": "2026-10-03", "Close": 13.0}, {"Date": "2026-10-03", "Close": 14.0}])
    merged, conflicts = merge_new_rows(existing, duplicate_data)
    assert "2026-10-03" not in merged["Date"].tolist()
    assert conflicts[0]["resolution"] == "SKIPPED_CONFLICTING_INCOMING_DATE"


def test_read_only_equity_adapter_exposes_reads_without_mutations() -> None:
    from src.data.settrade.account_readonly import ReadOnlyEquityAdapter

    calls: list[str] = []

    class Equity:
        def get_account_info(self):
            calls.append("account")
            return {"cash": 100}

        def get_portfolios(self):
            calls.append("portfolio")
            return []

        def get_orders(self):
            calls.append("orders")
            return []

        def get_trades(self):
            calls.append("deals")
            return []

    adapter = ReadOnlyEquityAdapter(Equity())
    assert adapter.account_summary() == {"cash": 100}
    assert adapter.portfolio() == []
    assert adapter.orders() == []
    assert adapter.deals() == []
    assert calls == ["account", "portfolio", "orders", "deals"]
    assert not any(hasattr(adapter, name) for name in ("place_order", "change_order", "cancel_order"))


def test_collector_provenance_has_nonsecret_routing_and_code_identity() -> None:
    from scripts.run_settrade_collector import _collector_provenance

    client = SimpleNamespace(config=SimpleNamespace(broker_id="013", app_code="ALGO_EQ"))
    provenance = _collector_provenance(client)
    assert provenance["source_environment"] == "production"
    assert provenance["broker_id"] == "013"
    assert provenance["app_code"] == "ALGO_EQ"
    assert provenance["git_head"]
    assert provenance["collector_version"].startswith("workspace-sha256:")

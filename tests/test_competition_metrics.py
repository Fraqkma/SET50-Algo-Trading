from src.competition.metrics import (FifoLotLedger, award_readiness,
                                     competition_metrics, fifo_metrics_from_fills,
                                     qualification_report, rank_award_candidates)
import pytest


def test_fifo_partial_sell_then_completion_and_multiple_lots():
    ledger = FifoLotLedger()
    first = ledger.buy("AAA", 100, 10, "d1")
    second = ledger.buy("AAA", 100, 11, "d2")
    assert ledger.sell("AAA", 150, 12, "d3", "sell-1")
    assert first.completed and not second.completed
    assert second.remaining_quantity == 50
    ledger.sell("AAA", 50, 9, "d4", "sell-2")
    assert second.completed and len(ledger.completed_roundtrips) == 2
    assert [x.net_pnl for x in ledger.completed_roundtrips] == [200, -50]


def test_fifo_symbol_independence_cross_day_and_partial_fill_quantities():
    ledger = FifoLotLedger()
    ledger.buy("AAA", 100, 20, "2026-01-01")
    ledger.buy("BBB", 200, 5, "2026-01-01")
    matched = ledger.sell("BBB", 50, 6, "2026-02-01", "fill-1")
    assert matched[0]["quantity"] == 50
    assert ledger.open_lots["AAA"][0].remaining_quantity == 100
    assert ledger.open_lots["BBB"][0].remaining_quantity == 150


def test_fifo_rejects_short_fill():
    ledger = FifoLotLedger()
    try:
        ledger.sell("AAA", 100, 1, "d", "s")
    except ValueError as exc:
        assert "exceeds held" in str(exc)
    else:
        raise AssertionError("short sale fill must be rejected")


def test_fifo_duplicate_fill_events_are_idempotent_and_conflicts_fail():
    ledger = FifoLotLedger()
    first = ledger.buy("AAA", 100, 10, "d1", event_id="buy-1")
    repeated = ledger.buy("AAA", 100, 10, "d1", event_id="buy-1")
    assert repeated == first
    assert len(ledger.lots) == 1

    original_matches = ledger.sell("AAA", 40, 11, "d2", event_id="sell-1")
    repeated_matches = ledger.sell("AAA", 40, 11, "d2", event_id="sell-1")
    assert repeated_matches == original_matches
    assert first.remaining_quantity == 60
    assert first.matched_sell_quantity == 40
    assert first.closing_events == ["sell-1"]

    with pytest.raises(ValueError, match="different fill"):
        ledger.sell("AAA", 41, 11, "d2", event_id="sell-1")


def test_fee_allocation_and_fill_reconstruction():
    ledger, metrics = fifo_metrics_from_fills([
        {"Order Number": "b1", "Side": "Buy", "Symbol": "AAA", "Volume": 100,
         "Price": 10, "Timestamp": "day1"},
        {"Order Number": "s1", "Side": "Sell", "Symbol": "AAA", "Volume": 100,
         "Price": 11, "Timestamp": "day2"}], 0.00157, 0.07)
    expected_fees = (1000 + 1100) * 0.00157 * 1.07
    assert ledger.completed_roundtrips[0].net_pnl == pytest.approx(100 - expected_fees)
    assert metrics["round_trips"] == 1


def test_close_metrics_returns_drawdowns_exposure_calmar_and_payoff():
    ledger = FifoLotLedger()
    ledger.buy("AAA", 100, 10, "d1")
    ledger.sell("AAA", 100, 12, "d2", "s1")
    ledger.buy("BBB", 100, 10, "d3")
    ledger.sell("BBB", 100, 9, "d4", "s2")
    m = competition_metrics([100, 120, 110], [100, 110, 105], [50, 90, 55],
                            ledger.completed_roundtrips, starting_nav=100)
    assert abs(m["portfolio_total_return"] - 10) < 1e-10
    assert abs(m["benchmark_return"] - 5) < 1e-10
    assert m["portfolio_max_drawdown"] == pytest.approx(10 / 120 * 100)
    assert m["benchmark_max_drawdown"] == pytest.approx(5 / 110 * 100)
    assert m["excess_return"] == pytest.approx(5)
    assert m["calmar_ratio"] == pytest.approx(1.2)
    assert m["average_portfolio_exposure"] == pytest.approx((0.5 + 0.75 + 0.5) / 3)
    assert m["round_trips"] == 2 and m["win_rate"] == 50
    assert m["average_win"] == 200 and m["average_loss"] == 100
    assert m["expected_payoff"] == 50


def test_qualification_reports_pass_fail_and_unknown():
    passed = qualification_report({"portfolio_max_drawdown": 10, "benchmark_max_drawdown": 10,
                                  "round_trips": 5, "average_portfolio_exposure": .5,
                                  "expected_payoff": .01})
    assert all(x["status"] == "PASS" for x in passed.values())
    assert all(x["explanation"] for x in passed.values())
    assert passed["drawdown_vs_benchmark"]["margin"] == pytest.approx(5.0)
    assert passed["minimum_roundtrips"]["margin"] == 0
    assert passed["average_exposure"]["margin"] == pytest.approx(0)
    failed = qualification_report({"portfolio_max_drawdown": 16, "benchmark_max_drawdown": 10,
                                   "round_trips": 4, "average_portfolio_exposure": .49,
                                   "expected_payoff": 0})
    assert all(x["status"] == "FAIL" for x in failed.values())
    unknown = qualification_report({})
    assert all(x["status"] == "UNKNOWN" for x in unknown.values())
    assert all("unavailable" in x["explanation"] for x in unknown.values())
    assert all(x["source_evidence"] == "TASK_SPECIFICATION_PDF_NOT_VERIFIED" for x in unknown.values())


def test_award_readiness_is_descriptive_and_keeps_unknowns():
    view = award_readiness({"portfolio_total_return": None, "excess_return": 1,
                            "round_trips": 3, "win_rate": .5})
    assert view["best_alpha"]["criteria"]["portfolio_total_return_nonnegative"] == "UNKNOWN"
    assert view["best_alpha"]["criteria"]["excess_return_nonnegative"] == "PASS"
    assert view["best_alpha"]["award_eligible"] == "UNKNOWN"
    assert view["most_active_trader_roundtrips"] == 3


def test_award_rankings_apply_eligibility_and_documented_tiebreaks():
    ranked = rank_award_candidates({
        "alpha_a": {"portfolio_total_return": 2, "excess_return": 1, "calmar_ratio": 2,
                    "portfolio_max_drawdown": 4, "round_trips": 8, "win_rate": 60},
        "alpha_b": {"portfolio_total_return": 3, "excess_return": 1, "calmar_ratio": 3,
                    "portfolio_max_drawdown": 3, "round_trips": 9, "win_rate": 70},
        "ineligible": {"portfolio_total_return": -1, "excess_return": 3, "calmar_ratio": 9,
                       "portfolio_max_drawdown": 2, "round_trips": 2, "win_rate": 20},
    })
    assert [row["candidate"] for row in ranked["best_alpha"]] == ["alpha_b", "alpha_a"]
    assert [row["candidate"] for row in ranked["best_risk_control"]] == ["ineligible", "alpha_b", "alpha_a"]
    assert ranked["most_active_trader"][0]["candidate"] == "alpha_b"
    assert ranked["precision_trader"][0]["candidate"] == "alpha_b"


def test_zero_trade_metrics_are_zero_but_missing_trade_data_stays_unknown():
    observed_empty = competition_metrics([], [], roundtrips=[])
    assert observed_empty["round_trips"] == 0
    assert observed_empty["win_rate"] == 0
    assert observed_empty["expected_payoff"] == 0
    unavailable = competition_metrics([], [], roundtrips=None)
    assert unavailable["round_trips"] is None
    assert unavailable["expected_payoff"] is None


def test_calmar_zero_drawdown_is_safe():
    result = competition_metrics([100, 101], [100, 100], roundtrips=[], starting_nav=100)
    assert result["calmar_ratio"] is None

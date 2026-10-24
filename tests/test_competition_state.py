from src.competition.state import (
    CompetitionSnapshot,
    CompetitionState,
    assess_order_eligibility,
    derive_competition_state,
)


def test_state_precedence_keeps_closed_and_stale_inputs_safe():
    assert derive_competition_state(CompetitionSnapshot(False, False, 10)) == CompetitionState.MARKET_CLOSED
    assert derive_competition_state(CompetitionSnapshot(True, None, 0)) == CompetitionState.DATA_DEGRADED


def test_state_reports_simulation_until_rules_are_confirmed():
    snapshot = CompetitionSnapshot(True, True, 100, rules_confirmed=False, simulation_only=False)
    assert derive_competition_state(snapshot) == CompetitionState.SIMULATION_ONLY


def test_state_tracks_position_reduction_and_open_position():
    reducing = CompetitionSnapshot(True, True, 100, pending_sell_quantity=100, rules_confirmed=True, simulation_only=False)
    opened = CompetitionSnapshot(True, True, 100, pending_sell_quantity=20, rules_confirmed=True, simulation_only=False)
    assert derive_competition_state(reducing) == CompetitionState.POSITION_REDUCING
    assert derive_competition_state(opened) == CompetitionState.POSITION_OPEN


def test_order_eligibility_does_not_promote_unconfirmed_rules():
    result = assess_order_eligibility(
        symbol_is_set50=True, quantity=100, side="BUY", cash_available=100_000,
        order_value_with_fees=10_000, holdings=0, order_type="LIMIT",
        session_open=True, data_fresh=True, board_lot=100,
        organizer_order_rule_confirmed=False,
    )
    assert result.status == "UNKNOWN"
    assert not result.eligible
    assert {rule.rule_id: rule.status for rule in result.rules}["ORGANIZER_ORDER_RULE"] == "UNKNOWN"


def test_order_eligibility_rejects_oversell_even_if_other_rules_are_unknown():
    result = assess_order_eligibility(
        symbol_is_set50=True, quantity=200, side="SELL", cash_available=None,
        order_value_with_fees=None, holdings=100, order_type="LIMIT",
        session_open=True, data_fresh=True, board_lot=100,
        organizer_order_rule_confirmed=True,
    )
    assert result.status == "FAIL"
    assert not result.eligible
    assert any(rule.rule_id == "HELD_QUANTITY" and rule.status == "FAIL" for rule in result.rules)

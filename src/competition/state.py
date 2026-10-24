"""Rule-aware, deterministic competition state and order eligibility helpers.

This module is descriptive only. It never creates or submits orders.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class CompetitionState(StrEnum):
    PRE_MARKET = "PRE_MARKET"
    READY = "READY"
    WATCHING = "WATCHING"
    POSITION_OPEN = "POSITION_OPEN"
    POSITION_REDUCING = "POSITION_REDUCING"
    FLAT = "FLAT"
    QUALIFICATION_AT_RISK = "QUALIFICATION_AT_RISK"
    DATA_DEGRADED = "DATA_DEGRADED"
    SIMULATION_ONLY = "SIMULATION_ONLY"
    MARKET_CLOSED = "MARKET_CLOSED"


@dataclass(frozen=True)
class CompetitionSnapshot:
    """Inputs known at one decision timestamp; unknowns must remain explicit."""

    market_open: bool
    data_fresh: bool | None
    holdings: int
    pending_sell_quantity: int = 0
    qualification_at_risk: bool = False
    rules_confirmed: bool = False
    simulation_only: bool = True


def derive_competition_state(snapshot: CompetitionSnapshot) -> CompetitionState:
    """Return a stable descriptive state using safety-first precedence."""
    if not snapshot.market_open:
        return CompetitionState.MARKET_CLOSED
    if snapshot.data_fresh is not True:
        return CompetitionState.DATA_DEGRADED
    if snapshot.qualification_at_risk:
        return CompetitionState.QUALIFICATION_AT_RISK
    if snapshot.simulation_only or not snapshot.rules_confirmed:
        return CompetitionState.SIMULATION_ONLY
    if snapshot.holdings > 0 and snapshot.pending_sell_quantity >= snapshot.holdings:
        return CompetitionState.POSITION_REDUCING
    if snapshot.holdings > 0:
        return CompetitionState.POSITION_OPEN
    return CompetitionState.FLAT


@dataclass(frozen=True)
class RuleEvidence:
    rule_id: str
    status: str
    reason: str


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    status: str
    rules: tuple[RuleEvidence, ...]


def assess_order_eligibility(
    *, symbol_is_set50: bool | None, quantity: int, side: str,
    cash_available: float | None, order_value_with_fees: float | None,
    holdings: int | None, order_type: str, session_open: bool | None,
    data_fresh: bool | None, board_lot: int | None = None,
    organizer_order_rule_confirmed: bool = False,
) -> EligibilityResult:
    """Check known constraints; unresolved rules yield UNKNOWN, never approval."""
    checks: list[RuleEvidence] = []

    def add(rule_id: str, passed: bool | None, reason: str) -> None:
        checks.append(RuleEvidence(rule_id, "UNKNOWN" if passed is None else "PASS" if passed else "FAIL", reason))

    add("SET50_SYMBOL", symbol_is_set50, "Membership must be established for the relevant date.")
    add("POSITIVE_QUANTITY", quantity > 0, "Quantity must be a positive integer.")
    lot_ok = None if board_lot is None else quantity % board_lot == 0
    add("BOARD_LOT", lot_ok, "Board-lot size is unconfirmed unless supplied by verified rules.")
    normalized_side = side.upper()
    add("SIDE", normalized_side in {"BUY", "SELL"}, "Only BUY and SELL are supported.")
    if normalized_side == "BUY":
        cash_ok = None if cash_available is None or order_value_with_fees is None else cash_available >= order_value_with_fees
        add("AVAILABLE_CASH", cash_ok, "Available cash must cover notional and fees.")
    elif normalized_side == "SELL":
        holdings_ok = None if holdings is None else quantity <= holdings
        add("HELD_QUANTITY", holdings_ok, "Sell quantity cannot exceed current holdings.")
    else:
        add("HELD_QUANTITY", False, "Unknown side cannot pass holdings validation.")
    add("ORDER_TYPE", order_type.upper() in {"LIMIT", "MARKET_TO_LIMIT"}, "Only locally documented competition order types are considered.")
    add("ORGANIZER_ORDER_RULE", True if organizer_order_rule_confirmed else None, "Simulator/API acceptance does not confirm organizer legality.")
    add("MARKET_SESSION", session_open, "Order session status must be known and open.")
    add("FRESH_DATA", data_fresh, "Decision inputs must be fresh.")
    statuses = {rule.status for rule in checks}
    return EligibilityResult(
        eligible=statuses == {"PASS"},
        status="FAIL" if "FAIL" in statuses else "UNKNOWN" if "UNKNOWN" in statuses else "PASS",
        rules=tuple(checks),
    )

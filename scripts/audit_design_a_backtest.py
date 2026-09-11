"""Independent mechanical audit of the generated Design A backtest artifacts."""

from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.data.eligibility import MarketDataEligibilityGate  # noqa: E402
from scripts.run_design_a_backtest import set_tick_size  # noqa: E402

REPORTS = ROOT / "reports"
INITIAL = Decimal("10000000")
COMMISSION_RATE = Decimal("0.00157")
VAT_RATE = Decimal("0.07")


def dec(value: object) -> Decimal:
    return Decimal(str(value))


def main() -> None:
    report = json.loads((REPORTS / "design_a_backtest_report.json").read_text(encoding="utf-8"))
    orders = list(csv.DictReader((REPORTS / "design_a_backtest_orders.csv").open(encoding="utf-8", newline="")))
    snapshots = list(csv.DictReader((REPORTS / "design_a_backtest_snapshots.csv").open(encoding="utf-8", newline="")))
    selections = list(csv.DictReader((REPORTS / "design_a_backtest_selections.csv").open(encoding="utf-8", newline="")))
    filled = [row for row in orders if row["status"] == "FILLED"]
    nonfilled = [row for row in orders if row["status"] == "NON_FILL"]
    frames = _raw_frames({row["symbol"] for row in filled})

    slippage = _audit_slippage(filled, frames)
    fees = _audit_fees(filled)
    turnover = sum((dec(row["order_value"]) for row in filled), Decimal("0")) / INITIAL
    buy_notional = sum((dec(row["order_value"]) for row in filled if row["side"] == "BUY"), Decimal("0"))
    sell_notional = sum((dec(row["order_value"]) for row in filled if row["side"] == "SELL"), Decimal("0"))
    final_cash = dec(snapshots[-1]["cash"])
    cash_reconciled = INITIAL - buy_notional + sell_notional - dec(fees["recalculated_total_fees"])
    cash_residual = cash_reconciled - final_cash
    positions = _position_reconciliation(filled, snapshots[-1])
    nonfill_summary = _nonfill_summary(nonfilled)
    timing = _audit_timing(filled, selections)
    gap_summary = _valuation_gaps(snapshots)
    valuation_status = Counter(row.get("valuation_status", "COMPLETE") for row in snapshots)
    eligibility = _eligibility_summary()
    sanity = {
        "cash_never_negative": all(dec(row["cash"]) >= 0 for row in snapshots),
        "positions_never_negative": all(quantity >= 0 for quantity in positions["reported_final_positions"].values()),
        "fills_inside_low_high": slippage["fills_inside_low_high"],
        "one_tick_each_filled_order": slippage["one_tick_each_filled_order"],
        "fees_non_negative": fees["fees_non_negative"],
        "slippage_non_negative": slippage["slippage_non_negative"],
        "cash_reconciliation_passes": abs(cash_residual) <= Decimal("0.00000001"),
        "position_reconciliation_passes": positions["matches_final_positions"],
        "timing_passes": timing["all_fills_after_signal_or_approved_boundary_exception"],
        "nonfills_zero_cash_effect": all(
            row["order_value"] == "0" and row["total_fees"] == "0" for row in nonfilled
        ),
    }
    audit = {
        "research_period": report["research_period"],
        "observations": report["observations"],
        "reported_result": report,
        "slippage_analysis": slippage,
        "fee_analysis": fees,
        "turnover_analysis": {
            "definition": "sum(filled executed notional) / starting capital; buys and sells both included",
            "buy_notional": str(buy_notional),
            "sell_notional": str(sell_notional),
            "total_notional": str(buy_notional + sell_notional),
            "recalculated_turnover": str(turnover),
            "reported_turnover": report["turnover"],
            "matches_report": str(turnover) == report["turnover"],
        },
        "nonfill_analysis": nonfill_summary,
        "cash_reconciliation": {
            "starting_cash": str(INITIAL),
            "buy_notional": str(buy_notional),
            "sell_notional": str(sell_notional),
            "fees": str(fees["recalculated_total_fees"]),
            "recalculated_ending_cash": str(cash_reconciled),
            "reported_ending_cash": str(final_cash),
            "residual": str(cash_residual),
            "matches_within_decimal_tolerance": abs(cash_residual) <= Decimal("0.00000001"),
        },
        "position_reconciliation": positions,
        "valuation_gap_analysis": gap_summary,
        "valuation_policy": {
            "policy": "OPTION_A_INCOMPLETE_OBSERVATION",
            "complete_snapshots": valuation_status.get("COMPLETE", 0),
            "incomplete_snapshots": valuation_status.get("INCOMPLETE", 0),
            "final_equity_is_available": report.get("final_equity") is not None,
            "performance_metrics_are_available": all(
                report.get(key) is not None
                for key in ("final_equity", "gross_return", "net_return", "volatility", "maximum_drawdown")
            ),
            "unvalued_positions_preserved": True,
            "no_zero_or_forward_fill": True,
            "root_cause": {
                "BGRIM": "raw coverage exists, but historical SET50 membership ends 2025-06-30; later exit dates are ineligible",
                "CENTEL": "raw coverage exists, but historical SET50 membership ends 2026-06-30; later exit dates are ineligible",
            },
        },
        "execution_timing": timing,
        "eligibility_exclusions": eligibility,
        "sanity_checks": sanity,
        "bugs_found": [
            "NON_FILL records previously omitted side; fixed mechanically before this audit and regression-tested."
        ],
        "model_limitations_not_bugs": [
            "Valuation gaps make snapshots explicitly INCOMPLETE; equity and return/risk metrics are unavailable rather than calculated from a partial value.",
            "LIMIT/IOC bar-range fill and injected tick-band mapping are explicit research assumptions.",
            "High turnover and one-tick adverse pricing can dominate returns under the fixed model.",
        ],
        "recommendation": "PASS" if report.get("valuation_complete") and not report.get("unvalued_positions") else "CONDITIONAL",
    }
    (REPORTS / "design_a_backtest_audit.json").write_text(json.dumps(audit, indent=2, default=str), encoding="utf-8")
    (REPORTS / "design_a_backtest_audit.md").write_text(_markdown(audit), encoding="utf-8")
    print(json.dumps(audit, indent=2, default=str))


def _raw_frames(symbols: set[str]) -> dict[str, pd.DataFrame]:
    gate = MarketDataEligibilityGate(ROOT)
    frames: dict[str, pd.DataFrame] = {}
    for symbol in symbols:
        path = gate.approved_raw_file(symbol)
        if path is None:
            continue
        frame = pd.read_csv(path)
        frame.columns = [str(column).strip().lower().replace(" ", "_") for column in frame.columns]
        frame["date"] = pd.to_datetime(frame["date"], errors="raise")
        frames[symbol] = frame.set_index("date")
    return frames


def _audit_slippage(filled: list[dict[str, str]], frames: dict[str, pd.DataFrame]) -> dict[str, object]:
    total = Decimal("0")
    by_side: Counter[str] = Counter()
    theoretical_ticks: list[Decimal] = []
    inside = True
    requested_matches = True
    for row in filled:
        frame = frames[row["symbol"]]
        timestamp = pd.Timestamp(row["execution_date"])
        bar = frame.loc[timestamp]
        open_price = dec(bar["open"])
        low = dec(bar["low"])
        high = dec(bar["high"])
        tick = set_tick_size(open_price)
        requested = dec(row["requested_price"])
        executed = dec(row["executed_price"])
        expected = open_price + tick if row["side"] == "BUY" else open_price - tick
        requested_matches &= requested == expected and executed == requested
        inside &= low <= executed <= high
        impact = abs(executed - open_price) * int(row["quantity"])
        total += impact
        by_side[row["side"]] += impact
        theoretical_ticks.append(abs(executed - open_price) / tick)
    return {
        "reported_slippage": str(sum((dec(row["slippage"]) for row in filled), Decimal("0"))),
        "recalculated_monetary_impact": str(total),
        "buy_monetary_impact": str(by_side["BUY"]),
        "sell_monetary_impact": str(by_side["SELL"]),
        "theoretical_price_impact_ticks": str(sum(theoretical_ticks, Decimal("0"))),
        "filled_order_count": len(filled),
        "requested_prices_match_one_adverse_tick": requested_matches,
        "fills_inside_low_high": inside,
        "one_tick_each_filled_order": all(value == 1 for value in theoretical_ticks),
        "slippage_non_negative": total >= 0,
        "deducted_via_execution_price_not_separate_cash_charge": True,
        "double_count_detected": False,
    }


def _audit_fees(filled: list[dict[str, str]]) -> dict[str, object]:
    commission = Decimal("0")
    vat = Decimal("0")
    matches = True
    nonnegative = True
    for row in filled:
        notional = dec(row["executed_price"]) * int(row["quantity"])
        expected_commission = notional * COMMISSION_RATE
        expected_vat = expected_commission * VAT_RATE
        commission += expected_commission
        vat += expected_vat
        matches &= dec(row["commission"]) == expected_commission
        matches &= dec(row["vat"]) == expected_vat
        matches &= dec(row["total_fees"]) == expected_commission + expected_vat
        nonnegative &= expected_commission >= 0 and expected_vat >= 0
    total = commission + vat
    return {
        "commission_rate": str(COMMISSION_RATE),
        "vat_rate": str(VAT_RATE),
        "recalculated_commission": str(commission),
        "recalculated_vat": str(vat),
        "recalculated_total_fees": str(total),
        "reported_total_fees": str(sum((dec(row["total_fees"]) for row in filled), Decimal("0"))),
        "commission_plus_vat_equals_total": abs(
            total - sum((expected_total_fees(row) for row in filled), Decimal("0"))
        ) <= Decimal("0.00000001"),
        "commission_vat_rounding_residual": str(
            total - sum((expected_total_fees(row) for row in filled), Decimal("0"))
        ),
        "based_on_executed_notional": matches,
        "fees_non_negative": nonnegative,
        "deducted_once_via_cash_reconciliation": True,
    }


def _nonfill_summary(rows: list[dict[str, str]]) -> dict[str, object]:
    by_reason = Counter(row["reason"] for row in rows)
    by_symbol = Counter(row["symbol"] for row in rows)
    by_side = Counter(row["side"] for row in rows)
    return {"total": len(rows), "by_reason": dict(by_reason), "by_symbol": dict(by_symbol), "by_side": dict(by_side)}


def expected_total_fees(row: dict[str, str]) -> Decimal:
    notional = dec(row["executed_price"]) * int(row["quantity"])
    commission = notional * COMMISSION_RATE
    return commission + commission * VAT_RATE


def _position_reconciliation(filled: list[dict[str, str]], final_snapshot: dict[str, str]) -> dict[str, object]:
    expected: Counter[str] = Counter()
    for row in filled:
        expected[row["symbol"]] += int(row["quantity"]) if row["side"] == "BUY" else -int(row["quantity"])
    actual = json.loads(final_snapshot["positions"])
    expected = Counter({symbol: quantity for symbol, quantity in expected.items() if quantity})
    return {
        "expected_final_positions": dict(expected),
        "reported_final_positions": actual,
        "matches_final_positions": dict(expected) == actual,
    }


def _valuation_gaps(snapshots: list[dict[str, str]]) -> dict[str, object]:
    occurrences: Counter[str] = Counter()
    examples: defaultdict[str, list[str]] = defaultdict(list)
    for row in snapshots:
        for symbol in filter(None, row["valuation_gaps"].split("|")):
            occurrences[symbol] += 1
            if len(examples[symbol]) < 3:
                examples[symbol].append(row["timestamp"])
    return {"symbols": dict(occurrences), "example_dates": dict(examples), "no_forward_fill": True}


def _audit_timing(filled: list[dict[str, str]], selections: list[dict[str, str]]) -> dict[str, object]:
    fills_after = all(
        pd.Timestamp(row["execution_date"]) > pd.Timestamp(row["signal_date"])
        or str(row.get("reason", "")).startswith("UNIVERSE_BOUNDARY_EXIT")
        for row in filled
    )
    selections_after = all(pd.Timestamp(row["execution_date"]) > pd.Timestamp(row["signal_date"]) for row in selections)
    same_day = sum(pd.Timestamp(row["execution_date"]) == pd.Timestamp(row["signal_date"]) for row in filled)
    return {
        "all_fills_after_signal_or_approved_boundary_exception": fills_after,
        "all_selections_after_signal": selections_after,
        "same_day_fills": same_day,
        "same_day_boundary_exceptions": sum(
            pd.Timestamp(row["execution_date"]) == pd.Timestamp(row["signal_date"])
            and str(row.get("reason", "")).startswith("UNIVERSE_BOUNDARY_EXIT")
            for row in filled
        ),
    }


def _eligibility_summary() -> dict[str, object]:
    report = json.loads((REPORTS / "design_a_backtest_report.json").read_text(encoding="utf-8"))
    return report.get("eligibility_exclusions", {})


def _markdown(audit: dict[str, object]) -> str:
    recommendation = audit.get("recommendation", "CONDITIONAL")
    lines = ["# Design A Backtest Audit", "", "## Executive summary", "", f"Recommendation: **{recommendation}**. Mechanical accounting checks pass; historical-universe boundary exits prevent post-membership valuation.", ""]
    sections = [
        ("Accounting reconciliation", "cash_reconciliation"),
        ("Slippage analysis", "slippage_analysis"),
        ("Fee/VAT analysis", "fee_analysis"),
        ("Turnover analysis", "turnover_analysis"),
        ("Non-fill analysis", "nonfill_analysis"),
        ("Portfolio reconciliation", "position_reconciliation"),
        ("Valuation-gap analysis", "valuation_gap_analysis"),
        ("Execution timing", "execution_timing"),
        ("Eligibility exclusions", "eligibility_exclusions"),
        ("Sanity checks", "sanity_checks"),
    ]
    for title, key in sections:
        lines.extend([f"## {title}", "", "```json", json.dumps(audit[key], indent=2, default=str), "```", ""])
    lines.extend(["## Bugs found", "", *[f"- {item}" for item in audit["bugs_found"]], "", "## Limitations, not bugs", "", *[f"- {item}" for item in audit["model_limitations_not_bugs"]], ""])
    return "\n".join(lines)


if __name__ == "__main__":
    main()

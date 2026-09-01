"""Transaction cost calculations for commissions and VAT."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class TransactionCosts:
    """Commission, VAT, and total fee breakdown for a transaction."""

    commission: Decimal
    vat: Decimal
    total_fees: Decimal


def calculate_transaction_costs(
    order_value: Decimal,
    commission_rate: Decimal = Decimal("0.00157"),
    vat_rate: Decimal = Decimal("0.07"),
) -> TransactionCosts:
    """Calculate commission and VAT for an executed order value."""

    commission = order_value * commission_rate
    vat = commission * vat_rate
    total_fees = commission + vat
    return TransactionCosts(commission=commission, vat=vat, total_fees=total_fees)
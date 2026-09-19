"""Labels for future observed-book versus daily-bar comparisons."""
from __future__ import annotations


def classify_daily_book(daily_fill: bool | None, book_fill: bool | None) -> str:
    if daily_fill is None or book_fill is None:
        return "INSUFFICIENT_DATA"
    if daily_fill and book_fill:
        return "BOTH_FILL"
    if daily_fill:
        return "DAILY_ONLY"
    if book_fill:
        return "BOOK_ONLY"
    return "NEITHER"

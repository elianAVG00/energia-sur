"""Exact CU06 bill input primitives, independent of transport and storage."""

import re
from datetime import date

_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}\Z", re.ASCII)


def calendar_date(value: str) -> date:
    """Parse a calendar date without introducing a timezone."""
    if not isinstance(value, str) or _DATE.fullmatch(value) is None:
        raise ValueError("Invalid date.")
    try:
        return date.fromisoformat(value)
    except ValueError:
        raise ValueError("Invalid date.") from None


def period(start: str, end: str) -> tuple[date, date]:
    """Validate inclusive bill-period boundaries."""
    first, last = calendar_date(start), calendar_date(end)
    if first > last:
        raise ValueError("Invalid period.")
    return first, last


def decimal_value(value: str, scale: int) -> str:
    """Validate a nonnegative decimal without float conversion or rounding."""
    if scale not in (2, 3) or not isinstance(value, str):
        raise ValueError("Invalid decimal.")
    if re.fullmatch(rf"[0-9]{{1,18}}(?:\.[0-9]{{1,{scale}}})?", value, re.ASCII) is None:
        raise ValueError("Invalid decimal.")
    whole, dot, fraction = value.partition(".")
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    return whole + ("." + fraction if dot and fraction else "")


def overlaps(start: date, end: date, other_start: date, other_end: date) -> bool:
    """Check whether two valid inclusive periods share a date."""
    return start <= other_end and other_start <= end

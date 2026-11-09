"""CU07 exact comparison domain, independent of transport and storage."""

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import MAX_EMAX, MIN_EMIN, Decimal, localcontext
from typing import Literal

from app.diary import BUENOS_AIRES

WINDOW_DAYS = 7
Outcome = Literal["recorded_higher", "billed_higher", "equal"]


class DecreasingReading(Exception):
    """The selected end reading is lower than the start reading."""


@dataclass(frozen=True, slots=True)
class Values:
    recorded_kwh: str
    difference_kwh: str
    outcome: Outcome


def local_date(instant: datetime) -> date:
    """Return the Buenos Aires calendar date of an aware instant."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Instant must be timezone-aware.")
    try:
        return instant.astimezone(BUENOS_AIRES).date()
    except (OverflowError, ValueError):
        raise ValueError("Instant is outside the supported range.") from None


def _shift(boundary: date, days: int) -> date:
    try:
        return boundary + timedelta(days=days)
    except OverflowError:
        return date.min if days < 0 else date.max


def window(boundary: date) -> tuple[date, date]:
    """Return the inclusive +/-7-day local window, clamped to valid dates."""
    return _shift(boundary, -WINDOW_DAYS), _shift(boundary, WINDOW_DAYS)


def in_window(local: date, boundary: date) -> bool:
    first, last = window(boundary)
    return first <= local <= last


def canonical(value: Decimal) -> str:
    """Format an exact decimal without floating point or rounding."""
    text = format(value, "f")
    whole, dot, fraction = text.partition(".")
    negative = whole.startswith("-")
    if negative:
        whole = whole[1:]
    whole = whole.lstrip("0") or "0"
    fraction = fraction.rstrip("0")
    result = whole + ("." + fraction if dot and fraction else "")
    if negative and result != "0":
        return "-" + result
    return result


def _digit_count(value: Decimal) -> int:
    return len(format(value, "f"))


def compare_values(start: Decimal, end: Decimal, billed: Decimal) -> Values:
    """Compute recorded consumption and the exact absolute difference.

    Raises DecreasingReading when the end value is lower than the start value;
    callers must not produce a comparison in that case. The arithmetic uses a
    per-call precision large enough for the accepted CU05 digit domain so the
    process-wide 28-digit default cannot round large readings.
    """
    if end < start:
        raise DecreasingReading
    with localcontext() as context:
        context.prec = max(28, _digit_count(start), _digit_count(end),
                           _digit_count(billed)) + 10
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        recorded = end - start
        difference = abs(recorded - billed)
        if recorded > billed:
            outcome: Outcome = "recorded_higher"
        elif recorded < billed:
            outcome = "billed_higher"
        else:
            outcome = "equal"
        return Values(canonical(recorded), canonical(difference), outcome)

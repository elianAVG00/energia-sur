"""CU08 deterministic consumption evolution and estimation, without transport or storage.

The estimate base is exactly the last chronological interval (the two most recent
readings by ``recorded_at`` UTC). A decreasing last interval yields no estimate and
never falls back to older intervals. Historical decreasing intervals remain visible
as not calculable. All arithmetic uses ``Decimal`` at a per-call precision; values
are canonical decimal strings, rounded to two decimals only at the presentation
boundary.
"""

from dataclasses import dataclass
from datetime import date, datetime
from decimal import MAX_EMAX, MIN_EMIN, Decimal, localcontext

from app.diary import BUENOS_AIRES

SECONDS_PER_DAY = Decimal("86400")
MIN_POSITIVE_DISPLAY = Decimal("0.005")  # half-up two-decimal rounding threshold


@dataclass(frozen=True, slots=True)
class Reading:
    id: str
    recorded_at: datetime
    value_kwh: Decimal


@dataclass(frozen=True, slots=True)
class Interval:
    start: Reading
    end: Reading
    calculable: bool
    consumption_kwh: str | None
    daily_average_kwh_day: str | None
    sub_day: bool
    below_minimum: bool


@dataclass(frozen=True, slots=True)
class Estimate:
    days: int
    daily_average_kwh_day: str
    estimate_kwh: str
    sub_day: bool
    below_minimum: bool
    daily_average_below_minimum: bool
    start: Reading
    end: Reading


def local_date(instant: datetime) -> date:
    """Return the Buenos Aires calendar date of an aware instant."""
    if instant.tzinfo is None or instant.utcoffset() is None:
        raise ValueError("Instant must be timezone-aware.")
    try:
        return instant.astimezone(BUENOS_AIRES).date()
    except (OverflowError, ValueError):
        raise ValueError("Instant is outside the supported range.") from None


def _digits(value: Decimal) -> int:
    return len(value.as_tuple().digits)


def canonical(value: Decimal) -> str:
    """Format an exact decimal without floating point or rounding."""
    with localcontext() as context:
        context.prec = _digits(value) + 2
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
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


def _elapsed_seconds(start: datetime, end: datetime) -> int:
    """Whole seconds between two second-resolution aware instants."""
    delta = end - start
    return delta.days * 86400 + delta.seconds


def below_minimum(value: Decimal) -> bool:
    """True when a positive value rounds to ``0.00`` at two decimals (half-up)."""
    return Decimal("0") < value < MIN_POSITIVE_DISPLAY


def _daily_average(consumption: Decimal, seconds: int) -> Decimal:
    if seconds <= 0:
        raise ValueError("Interval must have a positive duration.")
    with localcontext() as context:
        context.prec = max(28, _digits(consumption)) + 16
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        return (consumption * SECONDS_PER_DAY) / Decimal(seconds)


def _subtract(a: Decimal, b: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = max(28, _digits(a), _digits(b)) + 2
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        return a - b


def _multiply(a: Decimal, b: Decimal) -> Decimal:
    with localcontext() as context:
        context.prec = max(28, _digits(a) + _digits(b)) + 2
        context.Emax = MAX_EMAX
        context.Emin = MIN_EMIN
        return a * b


def _ordered(readings: list[Reading]) -> list[Reading]:
    return sorted(readings, key=lambda reading: reading.recorded_at)


def build_intervals(readings: list[Reading]) -> list[Interval]:
    """Compute the chronological per-reading intervals, newest interval last."""
    ordered = _ordered(readings)
    intervals: list[Interval] = []
    for previous, current in zip(ordered, ordered[1:]):
        seconds = _elapsed_seconds(previous.recorded_at, current.recorded_at)
        sub_day = seconds < 86400
        if current.value_kwh < previous.value_kwh:
            intervals.append(Interval(previous, current, False, None, None, sub_day, False))
            continue
        consumption = _subtract(current.value_kwh, previous.value_kwh)
        average = _daily_average(consumption, seconds)
        intervals.append(Interval(
            previous, current, True, canonical(consumption), canonical(average),
            sub_day, below_minimum(average),
        ))
    return intervals


def build_estimate(readings: list[Reading], days: int) -> Estimate | None:
    """Estimate from the last chronological interval, without older fallbacks.

    Returns ``None`` when there are fewer than two readings or the last interval is
    decreasing. ``days`` must already be within 1..90 (transport validates it).
    """
    ordered = _ordered(readings)
    if len(ordered) < 2:
        return None
    previous, current = ordered[-2], ordered[-1]
    if current.value_kwh < previous.value_kwh:
        return None
    seconds = _elapsed_seconds(previous.recorded_at, current.recorded_at)
    consumption = _subtract(current.value_kwh, previous.value_kwh)
    average = _daily_average(consumption, seconds)
    estimate = _multiply(average, Decimal(days))
    return Estimate(
        days=days, daily_average_kwh_day=canonical(average),
        estimate_kwh=canonical(estimate), sub_day=seconds < 86400,
        below_minimum=below_minimum(estimate),
        daily_average_below_minimum=below_minimum(average), start=previous, end=current,
    )

"""CU09 temporal rules and reports, without transport, storage or authorization.

Callers must resolve authorization before loading a single domicile's records.
The domicile check below prevents accidental mixed-domicile aggregation; it does
not establish ownership. Identity and optional text are retained without imposing
an unapproved transport format or length policy.

Records validate their intrinsic dates independently of a clock. Mutations must
also call ``validate_for_save`` with a trusted captured backend time. Reporting
does not repeat that mutation check against a historical generation time.
"""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal
from zoneinfo import ZoneInfo

BUENOS_AIRES = ZoneInfo("America/Argentina/Buenos_Aires")
_ONE_MINUTE = timedelta(minutes=1)
# Approved minimum local date: offsets from 1970 onward are whole minutes, so
# exact transport and integer-minute totals need no historical rounding policy.
_MINIMUM_LOCAL = datetime(1970, 1, 1, tzinfo=BUENOS_AIRES)
_MINIMUM_INSTANT = _MINIMUM_LOCAL.astimezone(UTC)


def _in_buenos_aires(value: datetime, field: str) -> datetime:
    """Resolve an aware, existent instant through UTC, preserving historical rules."""
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field} must be timezone-aware.")
    try:
        instant = value.astimezone(UTC)
        round_trip = instant.astimezone(value.tzinfo)
        local = instant.astimezone(BUENOS_AIRES)
    except (OverflowError, ValueError):
        raise ValueError(f"{field} is outside the supported datetime representation.") from None
    if round_trip.replace(tzinfo=None) != value.replace(tzinfo=None):
        raise ValueError(f"{field} must identify an existent local time.")
    return local


def _minute_in_buenos_aires(value: datetime, field: str) -> datetime:
    """Reject subminute or pre-1970 Buenos Aires input instead of rounding it."""
    local = _in_buenos_aires(value, field)
    if local.second != 0 or local.microsecond != 0:
        raise ValueError(f"{field} must have Buenos Aires minute precision.")
    if local.astimezone(UTC) < _MINIMUM_INSTANT:
        raise ValueError(
            f"{field} must be at or after 1970-01-01 00:00 Buenos Aires."
        )
    return local


@dataclass(frozen=True, slots=True)
class Interruption:
    """Immutable stored-record value; construction alone does not authorize a save.

    Dates are normalized to the named Buenos Aires zone. A stored record can be
    loaded without comparing its dates to a report's generation time. Creation,
    correction and closure additionally require ``validate_for_save``.
    """

    id: str
    domicile_id: str
    start_at: datetime
    end_at: datetime | None = None
    observations: str | None = None
    complaint_number: str | None = None

    def __post_init__(self) -> None:
        start = _minute_in_buenos_aires(self.start_at, "start_at")
        end = (
            _minute_in_buenos_aires(self.end_at, "end_at")
            if self.end_at is not None
            else None
        )
        if end is not None and end.astimezone(UTC) <= start.astimezone(UTC):
            raise ValueError("end_at must be strictly after start_at.")
        object.__setattr__(self, "start_at", start)
        object.__setattr__(self, "end_at", end)

    @property
    def status(self) -> Literal["ongoing", "closed"]:
        """Keep the recorded lifecycle independent of any effective report end."""
        return "ongoing" if self.end_at is None else "closed"


def validate_for_save(record: Interruption, *, now: datetime) -> Interruption:
    """Validate a proposed complete replacement using trusted backend time.

    This pure check does not persist, close, reopen or reassign records. A later
    mutation service must enforce ownership, lifecycle and concurrency policies
    and persist only after all checks succeed. Failure cannot change the frozen
    input; success returns it unchanged.
    """
    instant = _in_buenos_aires(now, "now").astimezone(UTC)
    if record.start_at.astimezone(UTC) > instant:
        raise ValueError("start_at must not be in the future.")
    if record.end_at is not None and record.end_at.astimezone(UTC) > instant:
        raise ValueError("end_at must not be in the future.")
    return record


@dataclass(frozen=True, slots=True)
class ReportPeriod:
    """Positive minute-boundary query range; a future query end is permitted."""

    start_at: datetime
    end_at: datetime

    def __post_init__(self) -> None:
        start = _minute_in_buenos_aires(self.start_at, "period.start_at")
        end = _minute_in_buenos_aires(self.end_at, "period.end_at")
        if end.astimezone(UTC) <= start.astimezone(UTC):
            raise ValueError("period.end_at must be strictly after period.start_at.")
        object.__setattr__(self, "start_at", start)
        object.__setattr__(self, "end_at", end)


@dataclass(frozen=True, slots=True)
class ReportRow:
    """An original record and its positive clipped interval, not a stored closure.

    UI/PDF adapters use the original record's dates, text and status. In
    particular, a missing ``interruption.end_at`` remains ongoing and must be
    presented as "En curso" by the PDF adapter, never as ``overlap_end_at``.
    Overlapping rows are retained; their individual spans must not be summed.
    """

    interruption: Interruption
    overlap_start_at: datetime
    overlap_end_at: datetime


@dataclass(frozen=True, slots=True)
class DiaryReport:
    """Single-generation report data shared by future UI and PDF adapters."""

    domicile_id: str
    period: ReportPeriod
    generated_at: datetime
    rows: tuple[ReportRow, ...]
    total_minutes: int

    @property
    def hours(self) -> int:
        """Whole hours in the union total, without a 24-hour wrap."""
        return self.total_minutes // 60

    @property
    def minutes(self) -> int:
        """Minute remainder accompanying ``hours``."""
        return self.total_minutes % 60


def _union_minutes(segments: list[tuple[datetime, datetime]]) -> int:
    """Union UTC intervals with exact timedelta arithmetic, not floating point."""
    if not segments:
        return 0
    segments.sort()
    current_start, current_end = segments[0]
    total = timedelta()
    for start, end in segments[1:]:
        if start <= current_end:
            current_end = max(current_end, end)
        else:
            total += current_end - current_start
            current_start, current_end = start, end
    total += current_end - current_start
    minutes, remainder = divmod(total, _ONE_MINUTE)
    if remainder:
        # The 1970 local-date floor excludes historical second-level offsets;
        # keep this guard so no unapproved rounding can enter through another path.
        raise ValueError("The report duration must span whole elapsed minutes.")
    return minutes


def generate_report(
    *,
    domicile_id: str,
    interruptions: Iterable[Interruption],
    period: ReportPeriod,
    clock: Callable[[], datetime],
) -> DiaryReport:
    """Summarize an already-authorized single-domicile consistent read.

    The boundary invokes the trusted backend clock exactly once, converts it to
    Buenos Aires and floors only that generation time to a minute. Transport
    must never select this clock from request data. The caller supplies records
    from one consistent read; this function performs no database or other I/O.

    Closed cuts use their stored end, even when inspecting a historical report
    clock. Only ongoing cuts are capped by generation. All cuts are clipped to
    the query period; only positive intersections produce rows or contribute to
    the same-domicile union. No record is mutated or implicitly closed.

    The approved 1970 local-date floor excludes legacy second-level offset
    transitions; a fractional-minute total still raises ValueError as defense in
    depth rather than applying an unapproved rounding policy.
    """
    generated_at = _in_buenos_aires(clock(), "clock").replace(
        second=0, microsecond=0
    )
    generated_instant = generated_at.astimezone(UTC)
    period_start = period.start_at.astimezone(UTC)
    period_end = period.end_at.astimezone(UTC)
    rows: list[ReportRow] = []
    segments: list[tuple[datetime, datetime]] = []

    for record in interruptions:
        if record.domicile_id != domicile_id:
            raise ValueError("All report records must belong to the selected domicile.")
        start = max(record.start_at.astimezone(UTC), period_start)
        effective_end = (
            record.end_at.astimezone(UTC)
            if record.end_at is not None
            else generated_instant
        )
        end = min(effective_end, period_end)
        if end <= start:
            continue
        segments.append((start, end))
        rows.append(
            ReportRow(
                interruption=record,
                overlap_start_at=start.astimezone(BUENOS_AIRES),
                overlap_end_at=end.astimezone(BUENOS_AIRES),
            )
        )

    rows.sort(
        key=lambda row: row.interruption.start_at.astimezone(UTC), reverse=True
    )
    return DiaryReport(
        domicile_id=domicile_id,
        period=period,
        generated_at=generated_at,
        rows=tuple(rows),
        total_minutes=_union_minutes(segments),
    )

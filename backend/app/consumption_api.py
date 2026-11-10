"""CU08 read-only consumption evolution and estimation transport."""

from datetime import UTC, date, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import consumption
from app.api import DB, Auth, no_cache
from app.models import Meter, MeterReading

router = APIRouter(dependencies=[Depends(no_cache)])
_MISSING = "El recurso no está disponible."
_INVALID = "Revisá los datos ingresados."


class IntervalOut(BaseModel):
    start_reading_id: str
    end_reading_id: str
    start_at: str
    end_at: str
    start_local_date: str
    end_local_date: str
    start_value_kwh: str
    end_value_kwh: str
    consumption_kwh: str | None
    daily_average_kwh_day: str | None
    calculable: bool
    sub_day: bool
    below_minimum: bool


class EvolutionOut(BaseModel):
    meter_id: str
    intervals: list[IntervalOut]


class EstimateOut(BaseModel):
    meter_id: str
    status: Literal["available"] = "available"
    days: int
    daily_average_kwh_day: str
    estimate_kwh: str
    orientative: Literal[True] = True
    below_minimum: bool
    daily_average_below_minimum: bool
    sub_day: bool
    base_start_reading_id: str
    base_end_reading_id: str
    base_start_at: str
    base_end_at: str


class EstimateUnavailableOut(BaseModel):
    meter_id: str
    status: Literal["base_unavailable"] = "base_unavailable"
    reason: Literal["insufficient_readings", "decreasing_latest"]


def own_meter(db: Session, account_id: str, meter_id: str) -> Meter:
    meter = db.scalar(select(Meter).where(
        Meter.id == meter_id, Meter.account_id == account_id,
    ))
    if meter is None:
        raise HTTPException(404, _MISSING)
    return meter


def _readings(db: Session, meter_id: str) -> list[consumption.Reading]:
    rows = db.scalars(select(MeterReading).where(
        MeterReading.meter_id == meter_id,
    ).order_by(MeterReading.recorded_at, MeterReading.id))
    return [consumption.Reading(row.id, row.recorded_at, row.value_kwh) for row in rows]


def _instant(value: datetime) -> str:
    instant = value.astimezone(UTC)
    return instant.isoformat().replace("+00:00", "Z")


def _interval_out(item: consumption.Interval) -> IntervalOut:
    return IntervalOut(
        start_reading_id=item.start.id, end_reading_id=item.end.id,
        start_at=_instant(item.start.recorded_at), end_at=_instant(item.end.recorded_at),
        start_local_date=consumption.local_date(item.start.recorded_at).isoformat(),
        end_local_date=consumption.local_date(item.end.recorded_at).isoformat(),
        start_value_kwh=consumption.canonical(item.start.value_kwh),
        end_value_kwh=consumption.canonical(item.end.value_kwh),
        consumption_kwh=item.consumption_kwh,
        daily_average_kwh_day=item.daily_average_kwh_day,
        calculable=item.calculable, sub_day=item.sub_day,
        below_minimum=item.below_minimum,
    )


def _overlaps(item: consumption.Interval, start: date | None, end: date | None) -> bool:
    start_local = consumption.local_date(item.start.recorded_at)
    end_local = consumption.local_date(item.end.recorded_at)
    if start is not None and end_local < start:
        return False
    if end is not None and start_local > end:
        return False
    return True


@router.get("/meters/{meter_id}/consumption-evolution", response_model=EvolutionOut)
def consumption_evolution(
    meter_id: str,
    actor: Auth,
    db: DB,
    from_: Annotated[date | None, Query(alias="from")] = None,
    to: Annotated[date | None, Query()] = None,
) -> EvolutionOut:
    own_meter(db, actor.account.id, meter_id)
    if from_ is not None and to is not None and from_ > to:
        raise HTTPException(422, _INVALID)
    intervals = consumption.build_intervals(_readings(db, meter_id))
    if from_ is not None or to is not None:
        intervals = [item for item in intervals if _overlaps(item, from_, to)]
    return EvolutionOut(meter_id=meter_id, intervals=[_interval_out(item) for item in intervals])


@router.get("/meters/{meter_id}/consumption-estimate",
            response_model=EstimateOut | EstimateUnavailableOut)
def consumption_estimate(
    meter_id: str,
    actor: Auth,
    db: DB,
    days: Annotated[int, Query(ge=1, le=90)],
) -> EstimateOut | EstimateUnavailableOut:
    own_meter(db, actor.account.id, meter_id)
    readings = _readings(db, meter_id)
    if len(readings) < 2:
        return EstimateUnavailableOut(meter_id=meter_id, reason="insufficient_readings")
    estimate = consumption.build_estimate(readings, days)
    if estimate is None:
        return EstimateUnavailableOut(meter_id=meter_id, reason="decreasing_latest")
    return EstimateOut(
        meter_id=meter_id, days=estimate.days,
        daily_average_kwh_day=estimate.daily_average_kwh_day,
        estimate_kwh=estimate.estimate_kwh,
        below_minimum=estimate.below_minimum,
        daily_average_below_minimum=estimate.daily_average_below_minimum,
        sub_day=estimate.sub_day,
        base_start_reading_id=estimate.start.id, base_end_reading_id=estimate.end.id,
        base_start_at=_instant(estimate.start.recorded_at),
        base_end_at=_instant(estimate.end.recorded_at),
    )

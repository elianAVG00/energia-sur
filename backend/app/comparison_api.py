"""CU07 read-only candidate and comparison transport."""

from datetime import UTC, date, datetime, time, timedelta
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import comparison
from app.api import DB, Auth, no_cache
from app.diary import BUENOS_AIRES
from app.models import ElectricityBill, Meter, MeterReading

router = APIRouter(dependencies=[Depends(no_cache)])
_MISSING = "El recurso no está disponible."
_INVALID = "Revisá los datos ingresados."
_CONFIRM = ("Las fechas de las lecturas no coinciden con el período facturado. "
            "Confirmá la comparación aproximada.")


class CandidateOut(BaseModel):
    reading_id: str
    recorded_at: str
    local_date: str
    value_kwh: str
    version: int


class CandidatesOut(BaseModel):
    bill_id: str
    meter_id: str
    period_start: str
    period_end: str
    billed_kwh: str
    start_candidates: list[CandidateOut]
    end_candidates: list[CandidateOut]


class ComparisonOut(BaseModel):
    bill_id: str
    meter_id: str
    period_start: str
    period_end: str
    billed_kwh: str
    status: Literal["comparable", "no_comparison"]
    reason: Literal["decreasing_reading"] | None = None
    exact: bool
    start_reading: CandidateOut | None = None
    end_reading: CandidateOut | None = None
    recorded_kwh: str | None = None
    difference_kwh: str | None = None
    outcome: Literal["recorded_higher", "billed_higher", "equal"] | None = None


def own_bill(db: Session, account_id: str, meter_id: str, bill_id: str) -> ElectricityBill:
    row = db.scalar(select(ElectricityBill).join(Meter).where(
        Meter.id == meter_id, Meter.account_id == account_id,
        ElectricityBill.meter_id == meter_id, ElectricityBill.id == bill_id,
    ))
    if row is None:
        raise HTTPException(404, _MISSING)
    return row


def own_reading(db: Session, meter_id: str, reading_id: str) -> MeterReading:
    row = db.scalar(select(MeterReading).where(
        MeterReading.meter_id == meter_id, MeterReading.id == reading_id,
    ))
    if row is None:
        raise HTTPException(404, _MISSING)
    return row


def candidate_out(row: MeterReading) -> CandidateOut:
    return CandidateOut(
        reading_id=row.id,
        recorded_at=row.recorded_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        local_date=comparison.local_date(row.recorded_at).isoformat(),
        value_kwh=comparison.canonical(row.value_kwh),
        version=row.version,
    )


def candidates(db: Session, meter_id: str, boundary: date) -> list[CandidateOut]:
    first, last = comparison.window(boundary)
    try:
        lower = datetime.combine(first, time.min, tzinfo=BUENOS_AIRES).astimezone(UTC)
        upper = (datetime.max.replace(tzinfo=UTC) if last >= date.max
                 else datetime.combine(last + timedelta(days=1), time.min,
                                       tzinfo=BUENOS_AIRES).astimezone(UTC))
    except (OverflowError, ValueError):
        return []
    rows = db.scalars(select(MeterReading).where(
        MeterReading.meter_id == meter_id,
        MeterReading.recorded_at >= lower,
        MeterReading.recorded_at < upper,
    ).order_by(MeterReading.recorded_at, MeterReading.id))
    result: list[CandidateOut] = []
    for row in rows:
        try:
            local = comparison.local_date(row.recorded_at)
        except ValueError:
            continue
        if comparison.in_window(local, boundary):
            result.append(candidate_out(row))
    return result


def _billed(bill: ElectricityBill) -> str:
    return comparison.canonical(bill.value_kwh)


@router.get("/meters/{meter_id}/bills/{bill_id}/comparison-candidates",
            response_model=CandidatesOut)
def comparison_candidates(
    meter_id: str, bill_id: str, actor: Auth, db: DB,
) -> CandidatesOut:
    bill = own_bill(db, actor.account.id, meter_id, bill_id)
    return CandidatesOut(
        bill_id=bill.id, meter_id=bill.meter_id,
        period_start=bill.period_start.isoformat(), period_end=bill.period_end.isoformat(),
        billed_kwh=_billed(bill),
        start_candidates=candidates(db, meter_id, bill.period_start),
        end_candidates=candidates(db, meter_id, bill.period_end),
    )


@router.get("/meters/{meter_id}/bills/{bill_id}/comparison", response_model=ComparisonOut)
def compare(
    meter_id: str, bill_id: str, start_reading_id: str, end_reading_id: str,
    actor: Auth, db: DB, confirm_approximate: bool = False,
) -> ComparisonOut | JSONResponse:
    bill = own_bill(db, actor.account.id, meter_id, bill_id)
    start = own_reading(db, meter_id, start_reading_id)
    end = own_reading(db, meter_id, end_reading_id)
    if start.id == end.id:
        raise HTTPException(422, _INVALID)
    try:
        start_local = comparison.local_date(start.recorded_at)
        end_local = comparison.local_date(end.recorded_at)
    except ValueError:
        raise HTTPException(422, _INVALID) from None
    if (not comparison.in_window(start_local, bill.period_start)
            or not comparison.in_window(end_local, bill.period_end)):
        raise HTTPException(422, _INVALID)
    if start_local > end_local:
        raise HTTPException(422, _INVALID)
    exact = start_local == bill.period_start and end_local == bill.period_end
    if not exact and not confirm_approximate:
        return JSONResponse(status_code=409, headers={"Cache-Control": "no-store"}, content={
            "detail": _CONFIRM,
            "code": "CONFIRMATION_REQUIRED",
            "period_start": bill.period_start.isoformat(),
            "period_end": bill.period_end.isoformat(),
            "start_local_date": start_local.isoformat(),
            "end_local_date": end_local.isoformat(),
            "start_candidates": [item.model_dump() for item in
                                 candidates(db, meter_id, bill.period_start)],
            "end_candidates": [item.model_dump() for item in
                               candidates(db, meter_id, bill.period_end)],
        })
    start_out = candidate_out(start)
    end_out = candidate_out(end)
    billed = _billed(bill)
    try:
        values = comparison.compare_values(start.value_kwh, end.value_kwh, bill.value_kwh)
    except comparison.DecreasingReading:
        return ComparisonOut(
            bill_id=bill.id, meter_id=bill.meter_id,
            period_start=bill.period_start.isoformat(), period_end=bill.period_end.isoformat(),
            billed_kwh=billed, status="no_comparison", reason="decreasing_reading",
            exact=exact, start_reading=start_out, end_reading=end_out,
        )
    return ComparisonOut(
        bill_id=bill.id, meter_id=bill.meter_id,
        period_start=bill.period_start.isoformat(), period_end=bill.period_end.isoformat(),
        billed_kwh=billed, status="comparable", reason=None, exact=exact,
        start_reading=start_out, end_reading=end_out,
        recorded_kwh=values.recorded_kwh, difference_kwh=values.difference_kwh,
        outcome=values.outcome,
    )

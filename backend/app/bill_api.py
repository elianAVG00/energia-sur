"""Owner-scoped CU06 HTTP transport and private file coordination."""

import os
from contextlib import contextmanager
from typing import Iterator, Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, ValidationError
from sqlalchemy import select, text
from sqlalchemy.engine import RootTransaction
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.api import DB, Auth, Writer, no_cache
from app.bill_confirmation import file_digest
from app.bill_files import LOCK_KEY, locked_directory, publish, read
from app.bill_pdf import InvalidBillPdf, validate_bill_pdf
from app.bill_store import (
    BillIdempotencyKeyReused,
    BillInput,
    BillOverlapConfirmationRequired,
    BillVersionConflict,
    DuplicateBill,
    prepare_bill,
    stage_bill,
)
from app.bills import decimal_value, period
from app.db import get_engine
from app.models import ElectricityBill, Meter
from app.photo_validation import InvalidPhoto, PhotoTooLarge, decode_photo
from app.photo_worker import PhotoWorkerFailed, validate_photo_bounded
from app.reading_api import request_body
from app.reading_store import validate_key

router = APIRouter(dependencies=[Depends(no_cache)])
_UNAVAILABLE = "El servicio no está disponible temporalmente."
_INVALID = "Revisá los datos ingresados."
_MISSING = "El recurso no está disponible."


class BillCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    period_start: str
    period_end: str
    value_kwh: str
    amount_ars: str | None
    file_base64: str
    overlap_token: str | None = None


class BillEdit(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    period_start: str
    period_end: str
    value_kwh: str
    amount_ars: str | None
    version: int
    file_action: Literal["keep", "replace"]
    file_base64: str | None = None
    overlap_token: str | None = None


def _own_meter(db: Session, account_id: str, meter_id: str) -> None:
    if db.scalar(select(Meter.id).where(Meter.id == meter_id, Meter.account_id == account_id)) is None:
        raise HTTPException(404, _MISSING)


def _own_bill(db: Session, account_id: str, meter_id: str, bill_id: str) -> ElectricityBill:
    row = db.scalar(select(ElectricityBill).join(Meter).where(
        Meter.id == meter_id, Meter.account_id == account_id,
        ElectricityBill.meter_id == meter_id, ElectricityBill.id == bill_id,
    ))
    if row is None:
        raise HTTPException(404, _MISSING)
    return row


def _out(row: ElectricityBill) -> dict[str, object]:
    return {
        "id": row.id, "meter_id": row.meter_id,
        "period_start": row.period_start.isoformat(), "period_end": row.period_end.isoformat(),
        "value_kwh": decimal_value(format(row.value_kwh, "f"), 3),
        "amount_ars": None if row.amount_ars is None else decimal_value(format(row.amount_ars, "f"), 2),
        "file_type": row.file_type, "version": row.version,
    }


def _configuration() -> tuple[str, bytes]:
    directory = os.environ.get("CU06_BILL_DIR", "/var/lib/energia-sur/bills")
    secret = os.environ.get("CU06_CONFIRMATION_SECRET", "").encode("utf-8")
    if not os.path.isabs(directory) or len(secret) < 32:
        raise HTTPException(503, _UNAVAILABLE)
    return directory, secret


@contextmanager
def _guard() -> Iterator[tuple[Session, RootTransaction]]:
    """Retain the session advisory lock until the filesystem lock is released."""
    connection = get_engine().connect()
    locked = False
    try:
        transaction = connection.begin()
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
        locked = True
        with Session(bind=connection) as db:
            yield db, transaction
    finally:
        if locked and not connection.invalidated:
            try:
                connection.rollback()
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
                connection.commit()
            except SQLAlchemyError:
                connection.invalidate()
        connection.close()


def _decode(value: str) -> tuple[bytes, str]:
    try:
        data = decode_photo(value)
        if data.startswith(b"%PDF-"):
            validate_bill_pdf(data)
            return data, "application/pdf"
        info = validate_photo_bounded(data)
        if info.content_type not in ("image/jpeg", "image/png"):
            raise InvalidPhoto("Unsupported file.")
        return data, info.content_type
    except PhotoTooLarge:
        raise HTTPException(413, "El archivo es demasiado grande.") from None
    except (InvalidPhoto, InvalidBillPdf, PhotoWorkerFailed):
        raise HTTPException(422, _INVALID) from None


def _payload(model: BillCreate | BillEdit) -> tuple[BillInput, bytes | None, str | None]:
    try:
        start, end = period(model.period_start, model.period_end)
        kwh = decimal_value(model.value_kwh, 3)
        amount = None if model.amount_ars is None else decimal_value(model.amount_ars, 2)
        action: Literal["create", "keep", "replace"] = (
            "create" if isinstance(model, BillCreate) else model.file_action
        )
        if isinstance(model, BillEdit) and (model.version < 1 or
                ((model.file_base64 is None) != (model.file_action == "keep"))):
            raise ValueError("Invalid file action or version.")
        data, content_type = (None, None) if model.file_base64 is None else _decode(model.file_base64)
        return BillInput(start, end, kwh, amount, action,
                         None if data is None else file_digest(data), model.overlap_token), data, content_type
    except ValueError:
        raise HTTPException(422, _INVALID) from None


def _write(account_id: str, meter_id: str, bill_id: str | None, model: BillCreate | BillEdit,
           key: str | None) -> dict[str, object] | JSONResponse:
    if bill_id is None:
        try:
            validate_key(key or "")
        except ValueError:
            raise HTTPException(422, _INVALID) from None
    directory, secret = _configuration()
    try:
        with _guard() as (db, transaction):
            # Admission is serialized before expensive file decoding across instances.
            payload, data, content_type = _payload(model)
            with locked_directory(directory) as directory_fd:
                try:
                    prepared, replay = prepare_bill(
                        db, account_id=account_id, meter_id=meter_id, payload=payload,
                        secret=secret, bill_id=bill_id,
                        version=model.version if isinstance(model, BillEdit) else None, key=key,
                    )
                    if replay is not None:
                        return replay
                    if prepared is None:
                        raise RuntimeError("Missing prepared bill.")
                    name = publish(directory_fd, data) if data is not None else None
                    result = stage_bill(db, prepared, file_key=name, file_type=content_type)
                    db.flush()
                    connection = db.connection()
                    try:
                        transaction.commit()
                    except SQLAlchemyError:
                        connection.invalidate()
                        raise HTTPException(503, _UNAVAILABLE) from None
                    return result
                except BillOverlapConfirmationRequired as error:
                    return JSONResponse(status_code=409, headers={"Cache-Control": "no-store"}, content={
                        "detail": "Confirmá los períodos superpuestos.",
                        "code": "OVERLAP_CONFIRMATION_REQUIRED", "overlap_token": error.token,
                        "overlaps": [{"id": item.bill_id, "version": item.version,
                                      "period_start": item.start.isoformat(),
                                      "period_end": item.end.isoformat()} for item in error.overlaps],
                    })
    except DuplicateBill:
        return _conflict("DUPLICATE_BILL")
    except BillVersionConflict:
        return _conflict("VERSION_CONFLICT")
    except BillIdempotencyKeyReused:
        return _conflict("IDEMPOTENCY_KEY_REUSED")
    except IntegrityError as error:
        if getattr(getattr(error.orig, "diag", None), "constraint_name", None) == "uq_bill_meter_period":
            return _conflict("DUPLICATE_BILL")
        raise
    except (OSError, ValueError, RuntimeError):
        raise HTTPException(503, _UNAVAILABLE) from None


def _conflict(code: str) -> JSONResponse:
    return JSONResponse(status_code=409, headers={"Cache-Control": "no-store"},
                        content={"detail": "El registro entra en conflicto.", "code": code})


@router.get("/meters/{meter_id}/bills")
def list_bills(meter_id: str, actor: Auth, db: DB) -> list[dict[str, object]]:
    _own_meter(db, actor.account.id, meter_id)
    rows = db.scalars(select(ElectricityBill).where(ElectricityBill.meter_id == meter_id)
                      .order_by(ElectricityBill.period_start.desc(), ElectricityBill.id))
    return [_out(row) for row in rows]


@router.get("/meters/{meter_id}/bills/{bill_id}")
def get_bill(meter_id: str, bill_id: str, actor: Auth, db: DB) -> dict[str, object]:
    return _out(_own_bill(db, actor.account.id, meter_id, bill_id))


@router.get("/meters/{meter_id}/bills/{bill_id}/file")
def get_file(meter_id: str, bill_id: str, actor: Auth, db: DB) -> Response:
    _own_bill(db, actor.account.id, meter_id, bill_id)
    directory, _ = _configuration()
    try:
        with _guard() as (db, _transaction):
            with locked_directory(directory) as directory_fd:
                row = _own_bill(db, actor.account.id, meter_id, bill_id)
                data, content_type = read(directory_fd, row.file_key), row.file_type
                if content_type not in ("application/pdf", "image/jpeg", "image/png"):
                    raise ValueError("Invalid stored MIME type.")
    except (OSError, ValueError):
        raise HTTPException(503, _UNAVAILABLE) from None
    return Response(data, media_type=content_type, headers={
        "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff",
        "Content-Disposition": 'attachment; filename="bill"',
    })


@router.post("/meters/{meter_id}/bills", status_code=201)
async def create_bill(meter_id: str, request: Request, actor: Writer, db: DB) -> object:
    account_id = actor.account.id
    await run_in_threadpool(_own_meter, db, account_id, meter_id)
    # Return the request connection before acquiring the storage-guard connection.
    await run_in_threadpool(db.rollback)
    try:
        model = BillCreate.model_validate(await request_body(request))
    except ValidationError:
        raise HTTPException(422, _INVALID) from None
    return await run_in_threadpool(_write, account_id, meter_id, None, model,
                                   request.headers.get("idempotency-key", ""))


@router.patch("/meters/{meter_id}/bills/{bill_id}")
async def edit_bill(meter_id: str, bill_id: str, request: Request, actor: Writer, db: DB) -> object:
    account_id = actor.account.id
    await run_in_threadpool(_own_bill, db, account_id, meter_id, bill_id)
    await run_in_threadpool(db.rollback)
    try:
        model = BillEdit.model_validate(await request_body(request))
    except ValidationError:
        raise HTTPException(422, _INVALID) from None
    return await run_in_threadpool(_write, account_id, meter_id, bill_id, model, None)

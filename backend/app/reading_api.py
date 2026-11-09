"""CU05 reading transport: ownership, idempotency and private photo lifecycle."""

import json
from datetime import UTC
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.api import DB, Auth, Writer, no_cache, now
from app.models import Meter, MeterReading
from app.ocr_worker import (
    OCR_FALLBACK_MESSAGE,
    InvalidOcrCrop,
    OcrSuggestion,
    OcrWorkerFailed,
    private_ocr_runtime,
    recognize_region,
)
from app.photo_files import locked_directory
from app.photo_store import (
    PhotoConfigurationError,
    PhotoGuard,
    cleanup_candidate,
    owned_photo,
    photo_directory,
    photo_guard,
    publish_photo,
    read_photo,
    referenced_photo_keys,
)
from app.photo_validation import InvalidPhoto, PhotoInfo, PhotoTooLarge, decode_photo
from app.photo_worker import PhotoWorkerFailed, validate_photo_bounded
from app.reading_store import (
    ReadingVersionConflict,
    create_reading,
    edit_reading,
    prepare_creation,
    stage_creation,
)
from app.readings import canonical_kwh

router = APIRouter(dependencies=[Depends(no_cache)])
STORAGE_UNAVAILABLE = "El servicio no está disponible temporalmente."


class ReadingOut(BaseModel):
    id: str
    meter_id: str
    recorded_at: str
    value_kwh: str
    has_photo: bool
    version: int


class ReadingInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    recorded_at: str
    value_kwh: str
    confirmed: Literal[True]
    photo_base64: str | None

    @field_validator("confirmed", mode="before")
    @classmethod
    def explicit_confirmation(cls, value: object) -> bool:
        if value is not True:
            raise ValueError("Explicit confirmation is required.")
        return True


class ReadingEdit(ReadingInput):
    version: int
    photo_action: Literal["keep", "remove", "replace"]


class OcrCrop(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    x: int
    y: int
    width: int
    height: int


class OcrInput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    photo_base64: str
    crop: OcrCrop


class OcrOut(BaseModel):
    status: Literal["abstained"] = "abstained"
    value_kwh: None = None
    message: str = OCR_FALLBACK_MESSAGE


class OcrSuggestionOut(BaseModel):
    status: Literal["suggested"] = "suggested"
    value_kwh: str


class DuplicateReading(Exception):
    """A meter already has a reading at the supplied instant."""


async def request_body(request: Request) -> object:
    if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
        raise HTTPException(415, "Tipo de contenido no admitido.")
    body = bytearray()
    async for chunk in request.stream():
        if len(body) + len(chunk) > 7_000_000:
            raise HTTPException(413, "La solicitud es demasiado grande.")
        body.extend(chunk)
    try:
        return json.loads(body)
    except (ValueError, UnicodeError, RecursionError):
        raise HTTPException(422, "Revisá los datos ingresados.") from None


def parse_input(model: type[ReadingInput], data: object) -> ReadingInput:
    try:
        return model.model_validate(data)
    except ValidationError:
        raise HTTPException(422, "Revisá los datos ingresados.") from None


def check_integrity(error: IntegrityError, db: DB) -> None:
    name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
    db.rollback()
    if name == "uq_reading_meter_instant":
        raise DuplicateReading from None
    raise error


def own_meter(db: DB, actor: Auth, meter_id: str) -> Meter:
    meter = db.scalar(select(Meter).where(Meter.id == meter_id, Meter.account_id == actor.account.id))
    if meter is None:
        raise HTTPException(404, "El recurso no está disponible.")
    return meter


def reading_out(row: MeterReading) -> ReadingOut:
    integer, separator, fraction = format(row.value_kwh, "f").partition(".")
    if separator and any(digit != "0" for digit in fraction):
        raise ValueError("Stored reading is not integral.")
    return ReadingOut(
        id=row.id, meter_id=row.meter_id,
        recorded_at=row.recorded_at.astimezone(UTC).isoformat().replace("+00:00", "Z"),
        value_kwh=canonical_kwh(integer),
        has_photo=row.photo_key is not None, version=row.version,
    )


def photo_metadata(payload: ReadingInput) -> tuple[bytes, PhotoInfo] | None:
    """Decode and validate optional photo bytes in a bounded worker."""
    if payload.photo_base64 is None:
        return None
    try:
        data = decode_photo(payload.photo_base64)
        return data, validate_photo_bounded(data)
    except PhotoTooLarge:
        raise HTTPException(413, "La fotografía es demasiado grande.") from None
    except (InvalidPhoto, PhotoWorkerFailed):
        raise HTTPException(422, "Revisá los datos ingresados.") from None


@router.get("/meters/{meter_id}/readings", response_model=list[ReadingOut])
def list_readings(meter_id: str, actor: Auth, db: DB) -> list[ReadingOut]:
    own_meter(db, actor, meter_id)
    rows = db.scalars(select(MeterReading).where(MeterReading.meter_id == meter_id)
                      .order_by(MeterReading.recorded_at.desc()))
    return [reading_out(row) for row in rows]


@router.get("/meters/{meter_id}/readings/{reading_id}", response_model=ReadingOut)
def get_reading(meter_id: str, reading_id: str, actor: Auth, db: DB) -> ReadingOut:
    own_meter(db, actor, meter_id)
    row = db.scalar(select(MeterReading).where(
        MeterReading.meter_id == meter_id, MeterReading.id == reading_id,
    ))
    if row is None:
        raise HTTPException(404, "El recurso no está disponible.")
    return reading_out(row)


@router.get("/meters/{meter_id}/readings/{reading_id}/photo")
async def get_photo(meter_id: str, reading_id: str, actor: Auth) -> Response:
    try:
        result = await run_in_threadpool(read_photo, actor.account.id, meter_id, reading_id)
    except (OSError, ValueError, PhotoConfigurationError):
        # A missing, unmanaged or misconfigured object needs recovery; never expose details.
        raise HTTPException(503, STORAGE_UNAVAILABLE) from None
    if result is None:
        raise HTTPException(404, "El recurso no está disponible.")
    data, content_type = result
    return Response(data, media_type=content_type, headers={
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/meters/{meter_id}/readings", status_code=201, response_model=ReadingOut)
async def post_reading(meter_id: str, request: Request, actor: Writer, db: DB) -> ReadingOut:
    await run_in_threadpool(own_meter, db, actor, meter_id)
    payload = parse_input(ReadingInput, await request_body(request))
    key = request.headers.get("idempotency-key", "")
    photo = await run_in_threadpool(photo_metadata, payload) if payload.photo_base64 is not None else None
    if photo is None:
        return await run_in_threadpool(_post_reading, meter_id, key, payload, actor, db)
    data, info = photo
    return await run_in_threadpool(_post_photo, meter_id, key, payload, actor, data, info)


def _post_reading(meter_id: str, key: str, payload: ReadingInput, actor: Auth, db: DB) -> ReadingOut:
    try:
        result = create_reading(
            db, account_id=actor.account.id, meter_id=meter_id,
            key=key, recorded_at=payload.recorded_at,
            value_kwh=payload.value_kwh, photo=None, photo_key=None, photo_type=None, now=now(),
        )
        db.commit()
        return ReadingOut.model_validate(result)
    except IntegrityError as error:
        check_integrity(error, db)
        raise
    except ValueError:
        db.rollback()
        raise HTTPException(422, "Revisá los datos ingresados.") from None


def _post_photo(
    meter_id: str, key: str, payload: ReadingInput, actor: Auth, data: bytes, info: PhotoInfo,
) -> ReadingOut:
    try:
        with photo_guard() as guard:
            with locked_directory(photo_directory()) as directory:
                return _create_with_photo(guard, directory, meter_id, key, payload, actor, data, info)
    except PhotoConfigurationError:
        raise HTTPException(503, STORAGE_UNAVAILABLE) from None
    except ValueError:
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    except OSError:
        raise HTTPException(503, STORAGE_UNAVAILABLE) from None


def _create_with_photo(
    guard: PhotoGuard, directory: int, meter_id: str, key: str, payload: ReadingInput,
    actor: Auth, data: bytes, info: PhotoInfo,
) -> ReadingOut:
    with guard.session() as db:
        own_meter(db, actor, meter_id)
        prepared, replay = prepare_creation(
            db, account_id=actor.account.id, meter_id=meter_id, key=key,
            recorded_at=payload.recorded_at, value_kwh=payload.value_kwh, photo=data,
        )
        if replay is not None:
            guard.rollback()
            return ReadingOut.model_validate(replay)
        name = publish_photo(directory, data)
        try:
            result = stage_creation(db, prepared=prepared, photo_key=name,
                                    photo_type=info.content_type, now=now())
        except IntegrityError as error:
            constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            guard.rollback()
            cleanup_candidate(directory, name)
            if constraint == "uq_reading_meter_instant":
                raise DuplicateReading from None
            raise
        except BaseException:
            guard.rollback()
            cleanup_candidate(directory, name)
            raise
        try:
            guard.commit()
        except SQLAlchemyError:
            guard.unknown_commit()
            raise HTTPException(503, STORAGE_UNAVAILABLE) from None
        return ReadingOut.model_validate(result)


@router.post("/meters/{meter_id}/readings/ocr", response_model=OcrOut | OcrSuggestionOut)
async def ocr_reading(
    meter_id: str, request: Request, actor: Writer, db: DB,
) -> OcrOut | OcrSuggestionOut:
    await run_in_threadpool(own_meter, db, actor, meter_id)
    if not private_ocr_runtime():
        return OcrOut()
    try:
        payload = OcrInput.model_validate(await request_body(request))
    except ValidationError:
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    try:
        data = await run_in_threadpool(decode_photo, payload.photo_base64)
    except PhotoTooLarge:
        raise HTTPException(413, "La fotografía es demasiado grande.") from None
    except InvalidPhoto:
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    crop = payload.crop
    try:
        result = await run_in_threadpool(
            recognize_region, data, crop.x, crop.y, crop.width, crop.height,
        )
    except (InvalidPhoto, InvalidOcrCrop):
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    except (OSError, OcrWorkerFailed, RuntimeError):
        return OcrOut()
    if isinstance(result, OcrSuggestion):
        return OcrSuggestionOut(value_kwh=result.value_kwh)
    return OcrOut()


@router.patch("/meters/{meter_id}/readings/{reading_id}", response_model=ReadingOut)
async def patch_reading(
    meter_id: str, reading_id: str, request: Request, actor: Writer, db: DB,
) -> ReadingOut:
    await run_in_threadpool(own_meter, db, actor, meter_id)
    data = await request_body(request)
    return await run_in_threadpool(_patch_reading, meter_id, reading_id, data, actor, db)


def _patch_reading(meter_id: str, reading_id: str, data: object, actor: Auth, db: DB) -> ReadingOut:
    row = db.scalar(select(MeterReading).where(
        MeterReading.meter_id == meter_id, MeterReading.id == reading_id,
    ))
    if row is None:
        raise HTTPException(404, "El recurso no está disponible.")
    if not isinstance(data, dict) or type(data.get("version")) is not int:
        raise HTTPException(422, "Revisá los datos ingresados.")
    if data["version"] != row.version:
        raise ReadingVersionConflict
    try:
        payload = ReadingEdit.model_validate(data)
    except ValidationError:
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    if payload.photo_action == "keep":
        if payload.photo_base64 is not None:
            raise HTTPException(422, "Revisá los datos ingresados.")
        try:
            changed = edit_reading(
                db, meter_id=meter_id, reading_id=reading_id, version=payload.version,
                recorded_at=payload.recorded_at, value_kwh=payload.value_kwh, now=now(),
            )
            result = reading_out(changed)
            db.commit()
            return result
        except IntegrityError as error:
            check_integrity(error, db)
            raise
        except ValueError:
            db.rollback()
            raise HTTPException(422, "Revisá los datos ingresados.") from None
    if payload.photo_action == "remove" and payload.photo_base64 is not None:
        raise HTTPException(422, "Revisá los datos ingresados.")
    if payload.photo_action == "replace" and payload.photo_base64 is None:
        raise HTTPException(422, "Revisá los datos ingresados.")
    return _patch_photo(meter_id, reading_id, payload, actor)


def _patch_photo(
    meter_id: str, reading_id: str, payload: ReadingEdit, actor: Auth,
) -> ReadingOut:
    photo = photo_metadata(payload) if payload.photo_action == "replace" else None
    data, info = (photo if photo is not None else (None, None))
    try:
        with photo_guard() as guard:
            with locked_directory(photo_directory()) as directory:
                return _apply_photo_patch(guard, directory, meter_id, reading_id, payload,
                                          actor, data, info)
    except PhotoConfigurationError:
        raise HTTPException(503, STORAGE_UNAVAILABLE) from None
    except ValueError:
        raise HTTPException(422, "Revisá los datos ingresados.") from None
    except OSError:
        raise HTTPException(503, STORAGE_UNAVAILABLE) from None


def _apply_photo_patch(
    guard: PhotoGuard, directory: int, meter_id: str, reading_id: str, payload: ReadingEdit,
    actor: Auth, data: bytes | None, info: PhotoInfo | None,
) -> ReadingOut:
    with guard.session() as db:
        row = owned_photo(db, actor.account.id, meter_id, reading_id)
        if row is None:
            guard.rollback()
            raise HTTPException(404, "El recurso no está disponible.")
        if payload.version != row.version:
            guard.rollback()
            raise ReadingVersionConflict
        previous = row.photo_key
        replacing = payload.photo_action == "replace"
        name = publish_photo(directory, data) if replacing and data is not None else None
        try:
            changed = edit_reading(
                db, meter_id=meter_id, reading_id=reading_id, version=payload.version,
                recorded_at=payload.recorded_at, value_kwh=payload.value_kwh, now=now(),
                change_photo=True,
                photo_key=name if replacing else None,
                photo_type=info.content_type if replacing and info is not None else None,
            )
            response = reading_out(changed)
        except IntegrityError as error:
            constraint = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
            guard.rollback()
            if name is not None:
                cleanup_candidate(directory, name)
            if constraint == "uq_reading_meter_instant":
                raise DuplicateReading from None
            raise
        except BaseException:
            guard.rollback()
            if name is not None:
                cleanup_candidate(directory, name)
            raise
        try:
            guard.commit()
        except SQLAlchemyError:
            guard.unknown_commit()
            raise HTTPException(503, STORAGE_UNAVAILABLE) from None
        if previous is not None and previous != name:
            with guard.session() as check:
                removed = previous not in referenced_photo_keys(check)
            if removed:
                cleanup_candidate(directory, previous)
        return response

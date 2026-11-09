"""CU05 transactional creation primitives; callers own commit and photo lifecycle."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.engine import RootTransaction
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransaction

from app import readings
from app.db import DatabaseUnavailable
from app.management import MissingResource
from app.models import Meter, MeterReading, ReadingCreation, identifier


class IdempotencyKeyReused(Exception):
    """An existing creation attempt has different inputs."""


class ReadingVersionConflict(Exception):
    """The submitted reading version is stale."""


@dataclass(frozen=True, slots=True)
class PreparedCreation:
    account_id: str
    meter_id: str
    key: str
    recorded_at: str
    value_kwh: str
    fingerprint: str
    has_photo: bool
    transaction: SessionTransaction
    connection_transaction: RootTransaction


def validate_key(value: str) -> str:
    try:
        parsed = UUID(value)
    except (ValueError, AttributeError):
        raise ValueError("Invalid idempotency key.") from None
    if str(parsed) != value:
        raise ValueError("Invalid idempotency key.")
    return value


def create_reading(
    db: Session, *, account_id: str, meter_id: str, key: str, recorded_at: str,
    value_kwh: str, photo: bytes | None, photo_key: str | None, photo_type: str | None,
    now: datetime,
) -> dict[str, object]:
    """Stage a reading and its replay record in one caller-owned transaction.

    The caller must coordinate photo publication, commit, and failure handling;
    no file bytes are written or deleted by this function.
    """
    prepared, replay = prepare_creation(
        db, account_id=account_id, meter_id=meter_id, key=key, recorded_at=recorded_at,
        value_kwh=value_kwh, photo=photo,
    )
    if replay is not None:
        return replay
    return stage_creation(db, prepared=prepared, photo_key=photo_key, photo_type=photo_type, now=now)


def prepare_creation(
    db: Session, *, account_id: str, meter_id: str, key: str, recorded_at: str,
    value_kwh: str, photo: bytes | None,
) -> tuple[PreparedCreation, dict[str, object] | None]:
    """Acquire the D15 transaction lock and inspect replay before publishing bytes.

    Caller must retain the same transaction until stage/commit or rollback.
    """
    if db.in_nested_transaction():
        raise RuntimeError("Creation does not support nested transactions.")
    meter = db.scalar(select(Meter).where(Meter.id == meter_id, Meter.account_id == account_id))
    if meter is None:
        raise MissingResource
    # A fresh statement snapshot after the advisory lock is necessary for replay.
    connection = db.connection()
    if connection.in_nested_transaction():
        raise RuntimeError("Creation does not support nested connection transactions.")
    if connection.get_isolation_level() != "READ COMMITTED":
        raise DatabaseUnavailable("CU05 requires READ COMMITTED transaction isolation.")
    validate_key(key)
    value = readings.canonical_kwh(value_kwh)
    fingerprint = readings.creation_fingerprint(recorded_at, value_kwh, photo)
    # PostgreSQL owns this lock for the transaction, including concurrent retries.
    db.execute(text("SELECT pg_advisory_xact_lock(hashtextextended(:scope, 0))"),
               {"scope": f"cu05:{account_id}:{meter_id}:{key}"})
    transaction = db.get_transaction()
    if transaction is None or not transaction.is_active:
        raise RuntimeError("Creation transaction is unavailable.")
    connection_transaction = connection.get_transaction()
    if connection_transaction is None or not connection_transaction.is_active:
        raise RuntimeError("Creation connection transaction is unavailable.")
    attempt = db.get(ReadingCreation, (account_id, meter_id, key))
    prepared = PreparedCreation(account_id, meter_id, key, recorded_at, value, fingerprint,
                                photo is not None, transaction, connection_transaction)
    if attempt is not None:
        if attempt.fingerprint != fingerprint:
            raise IdempotencyKeyReused
        return prepared, dict(attempt.response)
    return prepared, None


def stage_creation(
    db: Session, *, prepared: PreparedCreation, photo_key: str | None,
    photo_type: str | None, now: datetime,
) -> dict[str, object]:
    """Stage a non-replay under the transaction lock held by prepare_creation."""
    connection = db.connection()
    if (db.in_nested_transaction() or connection.in_nested_transaction()
            or db.get_transaction() is not prepared.transaction
            or not prepared.transaction.is_active
            or connection.get_transaction() is not prepared.connection_transaction
            or not prepared.connection_transaction.is_active):
        raise RuntimeError("Creation transaction changed before staging.")
    instant = readings.reading_instant(prepared.recorded_at, now=now)
    if (not prepared.has_photo and (photo_key is not None or photo_type is not None)) or (
        prepared.has_photo and (photo_key is None or photo_type is None)
    ):
        raise ValueError("Inconsistent photo metadata.")
    row = MeterReading(
        id=identifier(), meter_id=prepared.meter_id, recorded_at=instant,
        value_kwh=Decimal(prepared.value_kwh), photo_key=photo_key, photo_type=photo_type, version=1,
    )
    response: dict[str, object] = {
        "id": row.id, "meter_id": prepared.meter_id,
        "recorded_at": instant.isoformat().replace("+00:00", "Z"),
        "value_kwh": prepared.value_kwh, "has_photo": photo_key is not None, "version": 1,
    }
    db.add(row)
    db.flush()
    db.add(ReadingCreation(
        account_id=prepared.account_id, meter_id=prepared.meter_id, idempotency_key=prepared.key,
        fingerprint=prepared.fingerprint, reading_id=row.id, response=response,
    ))
    db.flush()
    return response


def edit_reading(
    db: Session, *, meter_id: str, reading_id: str, version: int,
    recorded_at: str, value_kwh: str, now: datetime, change_photo: bool = False,
    photo_key: str | None = None, photo_type: str | None = None,
) -> MeterReading:
    """Stage a version-qualified edit; the caller authorizes and commits."""
    value = readings.canonical_kwh(value_kwh)
    instant = readings.reading_instant(recorded_at, now=now)
    statement = update(MeterReading).where(
        MeterReading.id == reading_id, MeterReading.meter_id == meter_id,
        MeterReading.version == version,
    ).values(recorded_at=instant, value_kwh=Decimal(value),
             version=MeterReading.version + 1)
    if change_photo:
        statement = statement.values(photo_key=photo_key, photo_type=photo_type)
    row = db.scalars(statement.returning(MeterReading)).one_or_none()
    if row is None:
        existing = db.scalar(select(MeterReading.id).where(
            MeterReading.id == reading_id, MeterReading.meter_id == meter_id,
        ))
        if existing is None:
            raise MissingResource
        raise ReadingVersionConflict
    return row

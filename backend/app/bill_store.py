"""CU06 transaction primitives; callers coordinate private files and commit.

Every writer must hold the CU06 database advisory and filesystem locks before
calling these functions, then retain the same transaction until commit or
rollback. This module does not publish, remove, or reconcile attachments.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Literal

from sqlalchemy import select
from sqlalchemy.engine import RootTransaction
from sqlalchemy.orm import Session
from sqlalchemy.orm.session import SessionTransaction

from app.bill_confirmation import Confirmation, Overlap, confirmation_token, matches_confirmation
from app.management import MissingResource
from app.models import BillCreation, ElectricityBill, Meter, identifier
from app.reading_store import validate_key


class DuplicateBill(Exception):
    """Another bill already has the exact period."""


class BillVersionConflict(Exception):
    """A correction does not target the current bill version."""


class BillIdempotencyKeyReused(Exception):
    """A committed creation key was reused for a different request."""


class BillOverlapConfirmationRequired(Exception):
    """The proposed bill requires a fresh confirmation of the overlap set."""

    def __init__(self, overlaps: tuple[Overlap, ...], token: str) -> None:
        super().__init__("Overlap confirmation required.")
        self.overlaps = overlaps
        self.token = token


@dataclass(frozen=True, slots=True)
class BillInput:
    """Already validated, canonical values and decoded-file digest."""

    start: date
    end: date
    value_kwh: str
    amount_ars: str | None
    file_action: Literal["create", "replace", "keep"]
    file_digest: str | None
    overlap_token: str | None


@dataclass(frozen=True, slots=True)
class PreparedBill:
    """A checked write whose caller still owns the meter lock and transaction."""

    account_id: str
    meter_id: str
    payload: BillInput
    bill: ElectricityBill | None
    key: str | None
    fingerprint: str | None
    transaction: SessionTransaction
    connection_transaction: RootTransaction


def creation_fingerprint(meter_id: str, payload: BillInput) -> str:
    """Fingerprint a create including its confirmation state, not base64 spelling."""
    value = ["cu06-create-v1", meter_id, payload.start.isoformat(), payload.end.isoformat(),
             payload.value_kwh, payload.amount_ars, payload.file_action, payload.file_digest,
             payload.overlap_token]
    encoded = json.dumps(value, ensure_ascii=True, separators=(",", ":")).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def prepare_bill(
    db: Session, *, account_id: str, meter_id: str, payload: BillInput, secret: bytes,
    bill_id: str | None = None, version: int | None = None, key: str | None = None,
) -> tuple[PreparedBill | None, dict[str, object] | None]:
    """Lock the owned meter and check replay, version, duplicate and overlaps.

    The caller must verify ownership before processing an HTTP request body,
    validate all input and acquire the outer CU06 storage locks first.
    """
    if db.in_nested_transaction():
        raise RuntimeError("Nested transactions are unsupported.")
    meter = db.scalar(select(Meter).where(Meter.id == meter_id, Meter.account_id == account_id)
                      .with_for_update())
    if meter is None:
        raise MissingResource
    transaction = db.get_transaction()
    if transaction is None or not transaction.is_active:
        raise RuntimeError("Bill transaction is unavailable.")
    if db.connection().get_isolation_level() != "READ COMMITTED":
        raise RuntimeError("Bill writes require READ COMMITTED isolation.")
    connection = db.connection()
    if connection.in_nested_transaction():
        raise RuntimeError("Nested connection transactions are unsupported.")
    connection_transaction = connection.get_transaction()
    if connection_transaction is None or not connection_transaction.is_active:
        raise RuntimeError("Bill connection transaction is unavailable.")

    fingerprint = None
    bill = None
    if bill_id is None:
        if key is None or payload.file_action != "create" or version is not None:
            raise ValueError("Invalid bill creation.")
        validate_key(key)
        fingerprint = creation_fingerprint(meter_id, payload)
        existing = db.get(BillCreation, (account_id, meter_id, key))
        if existing is not None:
            if existing.fingerprint != fingerprint:
                raise BillIdempotencyKeyReused
            return None, dict(existing.response)
    else:
        if key is not None or version is None or payload.file_action == "create":
            raise ValueError("Invalid bill correction.")
        bill = db.scalar(select(ElectricityBill).where(
            ElectricityBill.id == bill_id, ElectricityBill.meter_id == meter_id,
        ))
        if bill is None:
            raise MissingResource
        if bill.version != version:
            raise BillVersionConflict

    rows = list(db.scalars(select(ElectricityBill).where(
        ElectricityBill.meter_id == meter_id,
        ElectricityBill.period_start <= payload.end,
        ElectricityBill.period_end >= payload.start,
    )))
    rows = [row for row in rows if row.id != bill_id]
    if any(row.period_start == payload.start and row.period_end == payload.end for row in rows):
        raise DuplicateBill
    snapshot = tuple(sorted(
        (Overlap(row.id, row.version, row.period_start, row.period_end) for row in rows),
        key=lambda item: item.bill_id,
    ))
    confirmation = Confirmation(
        account_id, meter_id, "create" if bill_id is None else "edit", bill_id, version,
        payload.start, payload.end, payload.value_kwh, payload.amount_ars,
        payload.file_action, payload.file_digest, snapshot,
    )
    if snapshot and (payload.overlap_token is None or not matches_confirmation(
        secret, confirmation, payload.overlap_token,
    )):
        raise BillOverlapConfirmationRequired(snapshot, confirmation_token(secret, confirmation))
    # A previously issued token is stale even when all overlaps disappeared.
    if (not snapshot and payload.overlap_token is not None
            and not matches_confirmation(secret, confirmation, payload.overlap_token)):
        raise BillOverlapConfirmationRequired(snapshot, confirmation_token(secret, confirmation))
    return PreparedBill(account_id, meter_id, payload, bill, key, fingerprint,
                        transaction, connection_transaction), None


def stage_bill(
    db: Session, prepared: PreparedBill, *, file_key: str | None, file_type: str | None,
) -> dict[str, object]:
    """Stage the bill and replay response, without committing or deleting files."""
    connection = db.connection()
    if (db.in_nested_transaction() or connection.in_nested_transaction()
            or db.get_transaction() is not prepared.transaction
            or not prepared.transaction.is_active
            or connection.get_transaction() is not prepared.connection_transaction
            or not prepared.connection_transaction.is_active):
        raise RuntimeError("Bill transaction changed before staging.")
    payload = prepared.payload
    if payload.file_action == "keep":
        if file_key is not None or file_type is not None or prepared.bill is None:
            raise ValueError("Invalid retained file.")
    elif not file_key or file_type not in ("application/pdf", "image/jpeg", "image/png"):
        raise ValueError("Invalid file metadata.")
    bill = prepared.bill
    if bill is None:
        if file_key is None or file_type is None:
            raise ValueError("Missing file metadata.")
        bill = ElectricityBill(id=identifier(), meter_id=prepared.meter_id,
                               file_key=file_key, file_type=file_type, version=1)
        db.add(bill)
    else:
        bill.version += 1
        if payload.file_action == "replace":
            if file_key is None or file_type is None:
                raise ValueError("Missing replacement metadata.")
            bill.file_key, bill.file_type = file_key, file_type
    bill.period_start, bill.period_end = payload.start, payload.end
    bill.value_kwh = Decimal(payload.value_kwh)
    bill.amount_ars = Decimal(payload.amount_ars) if payload.amount_ars is not None else None
    db.flush()
    result: dict[str, object] = {
        "id": bill.id, "meter_id": bill.meter_id,
        "period_start": bill.period_start.isoformat(), "period_end": bill.period_end.isoformat(),
        "value_kwh": payload.value_kwh, "amount_ars": payload.amount_ars,
        "file_type": bill.file_type, "version": bill.version,
    }
    if prepared.key is not None and prepared.fingerprint is not None:
        db.add(BillCreation(account_id=prepared.account_id, meter_id=prepared.meter_id,
                            idempotency_key=prepared.key, fingerprint=prepared.fingerprint,
                            bill_id=bill.id, response=result))
        db.flush()
    return result

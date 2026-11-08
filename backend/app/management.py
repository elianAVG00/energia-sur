"""Owner-scoped CU04 persistence and atomic optimistic corrections."""

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Domicile, Meter


class MissingResource(Exception):
    """The requested resource is not available to this account."""


class VersionConflict(Exception):
    """An owned row no longer has the submitted version."""


class DuplicateMeter(Exception):
    """The account already owns this normalized meter number."""


def domicile(db: Session, account_id: str, domicile_id: str) -> Domicile:
    row = db.scalar(select(Domicile).where(
        Domicile.id == domicile_id, Domicile.account_id == account_id,
    ))
    if row is None:
        raise MissingResource
    return row


def meter(db: Session, account_id: str, domicile_id: str, meter_id: str) -> Meter:
    row = db.scalar(select(Meter).where(
        Meter.id == meter_id, Meter.domicile_id == domicile_id, Meter.account_id == account_id,
    ))
    if row is None:
        raise MissingResource
    return row


def meters(db: Session, account_id: str, domicile_id: str) -> list[Meter]:
    domicile(db, account_id, domicile_id)
    return list(db.scalars(select(Meter).where(
        Meter.account_id == account_id, Meter.domicile_id == domicile_id,
    ).order_by(Meter.meter_number, Meter.id)))


def commit_meter(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        db.rollback()
        if name == "uq_meter_account_normalized":
            raise DuplicateMeter from None
        raise
    except Exception:
        db.rollback()
        raise


def create_meter(
    db: Session, account_id: str, domicile_id: str, number: str, alias: str | None,
) -> Meter:
    domicile(db, account_id, domicile_id)
    row = Meter(account_id=account_id, domicile_id=domicile_id, meter_number=number, alias=alias)
    db.add(row)
    commit_meter(db)
    return row


def correct_domicile(
    db: Session, account_id: str, domicile_id: str, address: str, version: int,
) -> Domicile:
    try:
        row = db.scalars(update(Domicile).where(
            Domicile.id == domicile_id, Domicile.account_id == account_id,
            Domicile.version == version,
        ).values(display_address=address, version=Domicile.version + 1).returning(Domicile)).one_or_none()
        if row is None:
            domicile(db, account_id, domicile_id)
            raise VersionConflict
        db.expunge(row)
        db.commit()
        return row
    except Exception:
        db.rollback()
        raise


def correct_meter(
    db: Session, account_id: str, domicile_id: str, meter_id: str,
    number: str, alias: str | None, version: int,
) -> Meter:
    try:
        row = db.scalars(update(Meter).where(
            Meter.id == meter_id, Meter.domicile_id == domicile_id,
            Meter.account_id == account_id, Meter.version == version,
        ).values(meter_number=number, alias=alias, version=Meter.version + 1)
            .returning(Meter)).one_or_none()
        if row is None:
            meter(db, account_id, domicile_id, meter_id)
            raise VersionConflict
        db.expunge(row)
        commit_meter(db)
        return row
    except IntegrityError as error:
        name = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        db.rollback()
        if name == "uq_meter_account_normalized":
            raise DuplicateMeter from None
        raise
    except Exception:
        db.rollback()
        raise

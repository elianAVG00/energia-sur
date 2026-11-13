"""Persisted per-source refresh intervals with safe reads and atomic updates."""

import logging

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import SourceConfig

_LOGGER = logging.getLogger(__name__)

ALLOWED_INTERVALS = frozenset({300, 600, 900, 1800, 3600})
DEFAULT_INTERVAL = 300
SOURCE_KEYS = ("outages", "scheduled_works")


class InvalidInterval(ValueError):
    """The requested interval is not in the approved set."""


class VersionConflict(Exception):
    """The submitted configuration version is no longer current."""


class SourceBusy(Exception):
    """An acquisition for the source already holds its advisory lock."""


def is_allowed(interval_seconds: int) -> bool:
    return interval_seconds in ALLOWED_INTERVALS


def get_interval(source_key: str) -> int:
    """Return the stored interval, falling back to the safe default on any failure.

    A missing row, a missing table or an unexpected value is logged and does not
    raise, so a scheduler cycle can always continue.
    """
    try:
        with Session(get_engine()) as db:
            value = db.scalar(select(SourceConfig.interval_seconds).where(
                SourceConfig.source_key == source_key,
            ))
    except Exception as error:
        _LOGGER.warning("Source interval read failed (%s).", type(error).__name__)
        return DEFAULT_INTERVAL
    if value is None:
        _LOGGER.warning("Source interval row is missing; using the default.")
        return DEFAULT_INTERVAL
    if not is_allowed(value):
        _LOGGER.warning("Source interval is not allowed; using the default.")
        return DEFAULT_INTERVAL
    return int(value)


def get_config(db: Session, source_key: str) -> SourceConfig | None:
    return db.get(SourceConfig, source_key)


def set_interval(
    db: Session, source_key: str, interval_seconds: int, version: int,
) -> SourceConfig:
    """Apply an interval only when the submitted version is still current."""
    if not is_allowed(interval_seconds):
        raise InvalidInterval
    row = db.scalars(update(SourceConfig).where(
        SourceConfig.source_key == source_key,
        SourceConfig.version == version,
    ).values(
        interval_seconds=interval_seconds,
        version=SourceConfig.version + 1,
    ).returning(SourceConfig)).one_or_none()
    if row is None:
        db.rollback()
        raise VersionConflict
    db.expunge(row)
    db.commit()
    return row

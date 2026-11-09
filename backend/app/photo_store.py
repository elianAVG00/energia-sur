"""CU05 private photo volume: locking, publication and reference-checked cleanup.

The caller must acquire the PostgreSQL advisory lock before the filesystem lock;
:func:`photo_guard` and :func:`locked_directory` already enforce that order.
"""

import logging
import os
import re
import stat
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Iterator

from sqlalchemy import select, text
from sqlalchemy.engine import Connection, RootTransaction
from sqlalchemy.orm import Session

from app.db import get_engine
from app.models import Meter, MeterReading
from app.photo_files import locked_directory, publish
from app.photo_reconciliation import PhotoRecoveryRequired, plan_recovery

_LOGGER = logging.getLogger(__name__)
DEFAULT_PHOTO_DIRECTORY = "/var/lib/energia-sur/photos"


class PhotoConfigurationError(RuntimeError):
    """The photo directory configuration is unusable; never disclose its value."""


def photo_directory() -> str:
    """Return the configured absolute photo directory without creating it."""
    path = os.environ.get("CU05_PHOTO_DIR", DEFAULT_PHOTO_DIRECTORY)
    if not os.path.isabs(path):
        raise PhotoConfigurationError("Photo directory must be absolute.")
    return path


# Fixed deployment-wide lock key; never varies between workers or maintenance passes.
_LOCK_KEY = 7_201_526_505
_OBJECT = re.compile(r"cu05-[0-9a-f]{32}\Z", re.ASCII)
_TEMPORARY = re.compile(r"\.cu05-[0-9a-f]{32}\.tmp\Z", re.ASCII)
_MAX_READ_BYTES = 5_000_000


@dataclass
class PhotoGuard:
    """A retained connection holding the session advisory lock."""

    connection: Connection
    transaction: RootTransaction
    uncertain: bool = False

    def session(self) -> Session:
        return Session(bind=self.connection)

    def commit(self) -> None:
        self.transaction.commit()

    def rollback(self) -> None:
        if self.transaction.is_active:
            self.transaction.rollback()

    def unknown_commit(self) -> None:
        """Mark an indeterminate commit and stop reusing this connection."""
        self.uncertain = True
        try:
            self.connection.invalidate()
        except Exception:
            pass


@contextmanager
def photo_guard() -> Iterator[PhotoGuard]:
    """Acquire the PostgreSQL session advisory lock on a retained connection."""
    connection = get_engine().connect()
    transaction = connection.begin()
    try:
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": _LOCK_KEY})
    except BaseException:
        connection.close()
        raise
    guard = PhotoGuard(connection, transaction)
    try:
        yield guard
    finally:
        if not guard.uncertain:
            try:
                guard.rollback()
            except Exception:
                _LOGGER.warning("Photo transaction rollback failed; connection invalidated.")
                try:
                    connection.invalidate()
                except Exception:
                    pass
            # Release even if rollback failed; the connection is discarded on error.
            try:
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": _LOCK_KEY})
            except Exception:
                _LOGGER.warning("Photo lock release failed; connection invalidated.")
                try:
                    connection.invalidate()
                except Exception:
                    pass
        try:
            connection.close()
        except Exception:
            pass


def _regular_name(name: str) -> bool:
    return bool(_OBJECT.match(name) or _TEMPORARY.match(name))


def _unlink_managed(directory: int, name: str) -> bool:
    """Remove one managed regular file without following symlinks."""
    if not _regular_name(name):
        raise ValueError("Unexpected managed photo name.")
    info = os.stat(name, dir_fd=directory, follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("Managed photo entry is not a regular file.")
    os.unlink(name, dir_fd=directory)
    return True


def _read_managed(directory: int, name: str) -> bytes:
    if not _OBJECT.match(name):
        raise ValueError("Unexpected photo name.")
    descriptor = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory)
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_size > _MAX_READ_BYTES:
            raise ValueError("Unreadable photo object.")
        data = b""
        while True:
            chunk = os.read(descriptor, 65_536)
            if not chunk:
                break
            data += chunk
        return data
    finally:
        os.close(descriptor)


def owned_photo(db: Session, account_id: str, meter_id: str, reading_id: str) -> MeterReading | None:
    """Recheck meter/reading ownership and the current association under lock."""
    return db.scalar(select(MeterReading).join(Meter).where(
        MeterReading.id == reading_id,
        MeterReading.meter_id == meter_id,
        Meter.account_id == account_id,
        Meter.id == meter_id,
    ))


def read_photo(account_id: str, meter_id: str, reading_id: str) -> tuple[bytes, str] | None:
    """Read a private photo while both locks remain held.

    The bytes are materialized under the locks (bounded by the 5 MB cap), so no
    reader can observe an association and then open an already-deleted object.
    """
    with photo_guard() as guard:
        with locked_directory(photo_directory()) as directory:
            with guard.session() as db:
                row = owned_photo(db, account_id, meter_id, reading_id)
                if row is None or row.photo_key is None or row.photo_type is None:
                    guard.rollback()
                    return None
                data = _read_managed(directory, row.photo_key)
                photo_type = row.photo_type
            guard.rollback()
            return data, photo_type


def publish_photo(directory: int, data: bytes) -> str:
    """Publish one immutable object; caller holds both locks and owns commit."""
    return publish(directory, data)


def cleanup_candidate(directory: int, name: str) -> bool:
    """Remove one object only after a committed-reference check by the caller."""
    try:
        return _unlink_managed(directory, name)
    except (OSError, ValueError):
        _LOGGER.warning("Photo cleanup skipped for an unmanaged or missing object.")
        return False


def referenced_photo_keys(db: Session) -> set[str]:
    return {key for key in db.scalars(
        select(MeterReading.photo_key).where(MeterReading.photo_key.is_not(None)),
    ) if key is not None}


def reconcile_photos() -> None:
    """Best-effort startup pass; deletes only proven unreferenced managed files."""
    with photo_guard() as guard:
        with locked_directory(photo_directory()) as directory:
            with guard.session() as db:
                references = referenced_photo_keys(db)
                try:
                    plan = plan_recovery(directory, references)
                except PhotoRecoveryRequired:
                    _LOGGER.warning("Photo recovery required; no files were removed.")
                    guard.rollback()
                    return
            removed = False
            for name in sorted(plan.temporary_files | plan.unreferenced_objects):
                if name in references:
                    continue
                removed = cleanup_candidate(directory, name) or removed
            if removed:
                os.fsync(directory)
            guard.rollback()

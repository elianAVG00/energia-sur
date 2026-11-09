"""CU06 reference-checked recovery; mirrors the conservative CU05 pattern."""

import logging
import os
import re
import stat
from collections.abc import Iterable

from sqlalchemy import select, text
from sqlalchemy.orm import Session

from app.bill_files import LOCK_KEY, locked_directory
from app.db import get_engine
from app.models import ElectricityBill

_LOGGER = logging.getLogger(__name__)
_OBJECT = re.compile(r"cu06-[0-9a-f]{32}\Z", re.ASCII)
_TEMPORARY = re.compile(r"\.cu06-[0-9a-f]{32}\.tmp\Z", re.ASCII)
DEFAULT_DIRECTORY = "/var/lib/energia-sur/bills"


class BillRecoveryRequired(Exception):
    """A reference or managed entry prevents safe cleanup."""


def bill_directory() -> str:
    """Return the configured absolute CU06 directory without creating it."""
    path = os.environ.get("CU06_BILL_DIR", DEFAULT_DIRECTORY)
    if not os.path.isabs(path):
        raise ValueError("Bill directory must be absolute.")
    return path


def _is_regular(directory: int, name: str) -> bool:
    return stat.S_ISREG(os.stat(name, dir_fd=directory, follow_symlinks=False).st_mode)


def plan_recovery(directory: int, references: Iterable[str]) -> tuple[set[str], set[str]]:
    refs = frozenset(references)
    if any(_OBJECT.fullmatch(name) is None for name in refs):
        raise BillRecoveryRequired("Invalid bill reference.")
    objects: set[str] = set()
    temporary: set[str] = set()
    for name in os.listdir(directory):
        if _OBJECT.fullmatch(name):
            objects.add(name)
        elif _TEMPORARY.fullmatch(name):
            temporary.add(name)
        else:
            continue
        if not _is_regular(directory, name):
            raise BillRecoveryRequired("Managed bill entry is not a regular file.")
    if not refs.issubset(objects):
        raise BillRecoveryRequired("A referenced bill file is missing.")
    return objects - refs, temporary


def _references(db: Session) -> set[str]:
    return {key for key in db.scalars(select(ElectricityBill.file_key)) if key is not None}


def _unlink(directory: int, name: str) -> bool:
    if _OBJECT.fullmatch(name) is None and _TEMPORARY.fullmatch(name) is None:
        raise BillRecoveryRequired("Unexpected bill entry.")
    if not _is_regular(directory, name):
        raise BillRecoveryRequired("Managed bill entry is not a regular file.")
    os.unlink(name, dir_fd=directory)
    return True


def reconcile_bills() -> None:
    """Remove only proven-unreferenced CU06 objects under both locks.

    Startup or an explicit local pass calls this before serving writes. The
    advisory lock serializes with every bill writer, so an object published by
    an unfinished transaction is never a candidate. Missing references or
    unreadable topology fail closed without deleting anything.
    """
    connection = get_engine().connect()
    locked = False
    try:
        connection.begin()
        connection.execute(text("SELECT pg_advisory_lock(:key)"), {"key": LOCK_KEY})
        locked = True
        with locked_directory(bill_directory()) as directory:
            with Session(bind=connection) as db:
                references = _references(db)
                try:
                    candidates, temporary = plan_recovery(directory, references)
                except BillRecoveryRequired:
                    _LOGGER.warning("Bill recovery required; no files were removed.")
                    return
            removed = False
            for name in sorted(candidates | temporary):
                if name in references:
                    continue
                removed = _unlink(directory, name) or removed
            if removed:
                os.fsync(directory)
        connection.rollback()
    finally:
        if locked and not connection.invalidated:
            try:
                connection.rollback()
                connection.execute(text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY})
                connection.commit()
            except Exception:
                connection.invalidate()
        connection.close()

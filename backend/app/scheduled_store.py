"""PostgreSQL persistence and refresh orchestration for CU02 scheduled works.

CU02 keeps its own snapshots, rows, run history and advisory lock. It reuses the
unchanged ENRE transport from CU01 but never CU01's parser, tables or lock.
"""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text, update
from sqlalchemy.orm import Session

from app.db import get_engine
from app.enre_client import FEED_URL, EnreError, fetch_feed
from app.models import ScheduledFetchRun, ScheduledSnapshot, ScheduledWork
from app.scheduled_parser import (
    ScheduledFeed,
    ScheduledParseError,
    ScheduledSchemaError,
    parse_scheduled,
)

_LOGGER = logging.getLogger(__name__)

LOCK_KEY = 0x43553032  # "CU02"
RETAINED_SNAPSHOTS = 24
RETAINED_RUNS = timedelta(days=30)


def _now() -> datetime:
    return datetime.now(UTC)


def record_run(
    outcome: str,
    *,
    started_at: datetime,
    http_status: int | None = None,
    detail_code: str | None = None,
    content_sha256: str | None = None,
) -> None:
    """Persist one acquisition outcome without storing any payload bytes."""
    with Session(get_engine()) as db:
        db.add(ScheduledFetchRun(
            started_at=started_at,
            finished_at=_now(),
            outcome=outcome,
            http_status=http_status,
            detail_code=detail_code,
            content_sha256=content_sha256,
        ))
        db.flush()
        db.execute(delete(ScheduledFetchRun).where(
            ScheduledFetchRun.started_at < _now() - RETAINED_RUNS,
        ))
        db.commit()


def refresh_once() -> str:
    """Run one CU02 refresh under a dedicated-connection advisory lock."""
    started_at = _now()
    with get_engine().connect() as lock_connection:
        acquired = lock_connection.execute(
            text("SELECT pg_try_advisory_lock(:key)"), {"key": LOCK_KEY},
        ).scalar_one()
        lock_connection.commit()
        if not acquired:
            record_run("skipped_locked", started_at=started_at)
            return "skipped_locked"
        try:
            return _refresh_locked(started_at)
        finally:
            try:
                lock_connection.execute(
                    text("SELECT pg_advisory_unlock(:key)"), {"key": LOCK_KEY},
                )
                lock_connection.commit()
            except Exception as error:
                lock_connection.invalidate()
                _LOGGER.warning("Scheduled-works lock release failed (%s).",
                                type(error).__name__)


def _refresh_locked(started_at: datetime) -> str:
    try:
        fetched = fetch_feed()
    except EnreError as error:
        record_run(
            error.code,
            started_at=started_at,
            http_status=getattr(error, "status", None),
            detail_code=type(error).__name__,
        )
        return error.code
    try:
        feed = parse_scheduled(fetched.text)
    except (ScheduledParseError, ScheduledSchemaError) as error:
        record_run(
            error.code,
            started_at=started_at,
            http_status=fetched.status,
            detail_code=type(error).__name__,
        )
        return error.code

    digest = hashlib.sha256(fetched.text.encode("utf-8")).hexdigest()
    checked_at = _now()
    with Session(get_engine()) as db:
        current = db.scalar(select(ScheduledSnapshot).where(ScheduledSnapshot.is_current))
        if current is not None and current.content_sha256 == digest:
            if fetched.last_modified is not None:
                current.source_last_modified = fetched.last_modified
            current.fetched_at = checked_at
            current.last_checked_at = checked_at
            outcome = "not_modified"
        else:
            _store_snapshot(db, feed, fetched.last_modified, digest, checked_at)
            _prune(db)
            outcome = "ok"
        db.commit()
    record_run(
        outcome,
        started_at=started_at,
        http_status=fetched.status,
        content_sha256=digest,
    )
    return outcome


def _store_snapshot(
    db: Session,
    feed: ScheduledFeed,
    last_modified: datetime | None,
    digest: str,
    checked_at: datetime,
) -> None:
    db.execute(update(ScheduledSnapshot).where(
        ScheduledSnapshot.is_current,
    ).values(is_current=False))
    snapshot = ScheduledSnapshot(
        source="ENRE",
        source_url=FEED_URL,
        source_last_modified=last_modified,
        source_reported_time=feed.source_reported_time,
        fetched_at=checked_at,
        last_checked_at=checked_at,
        content_sha256=digest,
        is_current=True,
        row_counts=dict(feed.row_counts),
        unverified_collections=list(feed.unverified_collections),
        comunicados_present=feed.comunicados_present,
    )
    db.add(snapshot)
    db.flush()
    db.add_all([
        ScheduledWork(
            snapshot_id=snapshot.id,
            category=row.category,
            partido=row.partido,
            localidad=row.localidad,
            partido_key=row.partido_key,
            localidad_key=row.localidad_key,
            subestacion_alimentador=row.subestacion_alimentador,
            affected_users=row.affected_users,
            restoration_estimate_text=row.restoration_estimate_text,
        )
        for row in feed.rows
    ])


def _prune(db: Session) -> None:
    keep = list(db.scalars(
        select(ScheduledSnapshot.id).order_by(
            ScheduledSnapshot.is_current.desc(),
            ScheduledSnapshot.fetched_at.desc(),
            ScheduledSnapshot.id,
        ).limit(RETAINED_SNAPSHOTS),
    ))
    current_id = db.scalar(
        select(ScheduledSnapshot.id).where(ScheduledSnapshot.is_current),
    )
    if current_id is not None and current_id not in keep:
        keep = keep[:RETAINED_SNAPSHOTS - 1] + [current_id]
    if keep:
        db.execute(delete(ScheduledSnapshot).where(ScheduledSnapshot.id.not_in(keep)))


def current_snapshot(db: Session) -> ScheduledSnapshot | None:
    return db.scalar(select(ScheduledSnapshot).where(ScheduledSnapshot.is_current))


def latest_source_status(db: Session) -> str:
    """Public status from the latest attempt, excluding a lock-skipped run.

    No successful CU02 acquisition is known means degraded, never a synthetic ok.
    """
    run = db.scalar(
        select(ScheduledFetchRun).where(
            ScheduledFetchRun.outcome != "skipped_locked",
        ).order_by(
            ScheduledFetchRun.started_at.desc(), ScheduledFetchRun.id.desc(),
        ).limit(1),
    )
    if run is not None and run.outcome in {"ok", "not_modified"}:
        return "ok"
    return "degraded"

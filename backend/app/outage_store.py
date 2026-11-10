"""PostgreSQL persistence and refresh orchestration for CU01 snapshots."""

import hashlib
import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import delete, select, text, update
from sqlalchemy.orm import Session

from app.db import get_engine
from app.enre_client import FEED_URL, EnreError, fetch_feed
from app.enre_parser import EnreFeed, EnreParseError, EnreSchemaError, parse_feed
from app.models import OutageFetchRun, OutageReport, OutageSnapshot

_LOGGER = logging.getLogger(__name__)

LOCK_KEY = 0x43553031  # "CU01"
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
        db.add(OutageFetchRun(
            started_at=started_at,
            finished_at=_now(),
            outcome=outcome,
            http_status=http_status,
            detail_code=detail_code,
            content_sha256=content_sha256,
        ))
        db.flush()
        db.execute(delete(OutageFetchRun).where(
            OutageFetchRun.started_at < _now() - RETAINED_RUNS,
        ))
        db.commit()


def refresh_once() -> str:
    """Run one refresh under a dedicated-connection advisory lock."""
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
                _LOGGER.warning("Outage lock release failed (%s).",
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
        feed = parse_feed(fetched.text)
    except (EnreParseError, EnreSchemaError) as error:
        record_run(
            error.code,
            started_at=started_at,
            http_status=fetched.status,
            detail_code=type(error).__name__,
        )
        return error.code

    digest = hashlib.sha256(fetched.text.encode("utf-8")).hexdigest()
    if feed.degraded:
        record_run(
            "source_degraded",
            started_at=started_at,
            http_status=fetched.status,
            detail_code="degraded_totals",
            content_sha256=digest,
        )
        return "source_degraded"

    checked_at = _now()
    with Session(get_engine()) as db:
        current = db.scalar(select(OutageSnapshot).where(OutageSnapshot.is_current))
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
    feed: EnreFeed,
    last_modified: datetime | None,
    digest: str,
    checked_at: datetime,
) -> None:
    db.execute(update(OutageSnapshot).where(
        OutageSnapshot.is_current,
    ).values(is_current=False))
    snapshot = OutageSnapshot(
        distributor=feed.distributor,
        source_url=FEED_URL,
        source_last_modified=last_modified,
        source_reported_time=feed.source_reported_time,
        fetched_at=checked_at,
        last_checked_at=checked_at,
        content_sha256=digest,
        is_current=True,
        total_users_without=feed.total_users_without,
        total_users_with=feed.total_users_with,
        users_affected_yesterday=feed.users_affected_yesterday,
        row_counts=dict(feed.row_counts),
    )
    db.add(snapshot)
    db.flush()
    db.add_all([
        OutageReport(
            snapshot_id=snapshot.id,
            category=row.category,
            partido=row.partido,
            localidad=row.localidad,
            partido_key=row.partido_key,
            localidad_key=row.localidad_key,
            subestacion_alimentador=row.subestacion_alimentador,
            affected_users=row.affected_users,
            normalizacion=row.normalizacion,
        )
        for row in feed.rows
    ])


def _prune(db: Session) -> None:
    keep = list(db.scalars(
        select(OutageSnapshot.id).order_by(
            OutageSnapshot.is_current.desc(),
            OutageSnapshot.fetched_at.desc(),
            OutageSnapshot.id,
        ).limit(RETAINED_SNAPSHOTS),
    ))
    current_id = db.scalar(select(OutageSnapshot.id).where(OutageSnapshot.is_current))
    if current_id is not None and current_id not in keep:
        keep = keep[:RETAINED_SNAPSHOTS - 1] + [current_id]
    if keep:
        db.execute(delete(OutageSnapshot).where(OutageSnapshot.id.not_in(keep)))


def current_snapshot(db: Session) -> OutageSnapshot | None:
    return db.scalar(select(OutageSnapshot).where(OutageSnapshot.is_current))


def latest_source_status(db: Session) -> str:
    """Public status from the latest attempt, excluding a lock-skipped run."""
    run = db.scalar(
        select(OutageFetchRun).where(
            OutageFetchRun.outcome != "skipped_locked",
        ).order_by(
            OutageFetchRun.started_at.desc(), OutageFetchRun.id.desc(),
        ).limit(1),
    )
    if run is None or run.outcome in {"ok", "not_modified"}:
        return "ok"
    return "degraded"

"""Admin-only supervision of the existing CU01/CU02 ENRE source refresh."""

import os
from datetime import UTC, datetime
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import outage_store, scheduled_store, source_config
from app.api import DB, Actor, Auth, Writer, no_cache
from app.models import (
    OutageFetchRun,
    OutageSnapshot,
    ScheduledFetchRun,
    ScheduledSnapshot,
    SourceConfig,
)

router = APIRouter(dependencies=[Depends(no_cache)])

SourceKey = Literal["outages", "scheduled_works"]
_SOURCE_KEYS: tuple[SourceKey, ...] = ("outages", "scheduled_works")
_ENABLED_ENV = {
    "outages": "OUTAGE_SCHEDULER_ENABLED",
    "scheduled_works": "SCHEDULED_WORKS_SCHEDULER_ENABLED",
}
_SUCCESS_OUTCOMES = frozenset({"ok", "not_modified"})
_FORBIDDEN = "No tenés permisos para administrar las fuentes."
_MISSING = "El recurso no está disponible."


class SourceStatusOut(BaseModel):
    key: SourceKey
    scheduler_enabled: bool
    interval_seconds: int
    version: int
    last_attempt_at: str | None
    last_attempt_outcome: str | None
    last_attempt_error: str | None
    last_success_at: str | None
    last_skipped_locked_at: str | None


class SourcesOut(BaseModel):
    sources: list[SourceStatusOut]


class IntervalInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    interval_seconds: Literal[300, 600, 900, 1800, 3600]
    version: int = Field(strict=True, gt=0)


class IntervalOut(BaseModel):
    key: SourceKey
    interval_seconds: int
    version: int


class RefreshOut(BaseModel):
    key: SourceKey
    outcome: str
    http_status: int | None
    detail_code: str | None
    started_at: str | None
    finished_at: str | None


def require_admin(actor: Auth) -> Actor:
    if actor.account.role != "admin":
        raise HTTPException(403, _FORBIDDEN)
    return actor


Admin = Annotated[Actor, Depends(require_admin)]


def admin_writer(actor: Writer) -> Actor:
    if actor.account.role != "admin":
        raise HTTPException(403, _FORBIDDEN)
    return actor


AdminWriter = Annotated[Actor, Depends(admin_writer)]


def _source(key: str) -> SourceKey:
    if key == "outages":
        return "outages"
    if key == "scheduled_works":
        return "scheduled_works"
    raise HTTPException(404, _MISSING)


def _instant(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _scheduler_enabled(key: SourceKey) -> bool:
    return os.environ.get(_ENABLED_ENV[key], "false").lower() in {"1", "true", "yes"}


def _latest_outage_run(db: Session, *, skipped: bool) -> OutageFetchRun | None:
    condition = (OutageFetchRun.outcome == "skipped_locked" if skipped
                 else OutageFetchRun.outcome != "skipped_locked")
    return db.scalar(select(OutageFetchRun).where(condition).order_by(
        OutageFetchRun.started_at.desc(), OutageFetchRun.id.desc(),
    ).limit(1))


def _latest_scheduled_run(db: Session, *, skipped: bool) -> ScheduledFetchRun | None:
    condition = (ScheduledFetchRun.outcome == "skipped_locked" if skipped
                 else ScheduledFetchRun.outcome != "skipped_locked")
    return db.scalar(select(ScheduledFetchRun).where(condition).order_by(
        ScheduledFetchRun.started_at.desc(), ScheduledFetchRun.id.desc(),
    ).limit(1))


def _latest_run(
    db: Session, key: SourceKey, *, skipped: bool,
) -> OutageFetchRun | ScheduledFetchRun | None:
    if key == "outages":
        return _latest_outage_run(db, skipped=skipped)
    return _latest_scheduled_run(db, skipped=skipped)


def _snapshot(db: Session, key: SourceKey) -> OutageSnapshot | ScheduledSnapshot | None:
    if key == "outages":
        return outage_store.current_snapshot(db)
    return scheduled_store.current_snapshot(db)


def _config(db: Session, key: SourceKey) -> SourceConfig:
    row = source_config.get_config(db, key)
    if row is None:
        raise HTTPException(503, "La configuración de la fuente no está disponible.")
    return row


def _status(db: Session, key: SourceKey) -> SourceStatusOut:
    config = _config(db, key)
    run = _latest_run(db, key, skipped=False)
    skipped = _latest_run(db, key, skipped=True)
    snapshot = _snapshot(db, key)
    outcome = run.outcome if run is not None else None
    error: str | None = None
    if outcome is not None and outcome not in _SUCCESS_OUTCOMES:
        error = (run.detail_code if run is not None else None) or outcome
    last_success = snapshot.last_checked_at if snapshot is not None else None
    last_skipped = skipped.started_at if skipped is not None else None
    return SourceStatusOut(
        key=key,
        scheduler_enabled=_scheduler_enabled(key),
        interval_seconds=config.interval_seconds,
        version=config.version,
        last_attempt_at=_instant(run.started_at if run is not None else None),
        last_attempt_outcome=outcome,
        last_attempt_error=error,
        last_success_at=_instant(last_success),
        last_skipped_locked_at=_instant(last_skipped),
    )


@router.get("/admin/sources", response_model=SourcesOut)
def list_sources(actor: Admin, db: DB) -> SourcesOut:
    """Return the real state of both supervised sources; no CSRF is required."""
    return SourcesOut(sources=[_status(db, key) for key in _SOURCE_KEYS])


@router.post("/admin/sources/{key}/refresh", response_model=RefreshOut)
def refresh_source(key: str, actor: AdminWriter, db: DB) -> RefreshOut:
    """Run one synchronous retry through the shared acquisition path."""
    source = _source(key)
    outcome = (outage_store.refresh_now() if source == "outages"
               else scheduled_store.refresh_now())
    run = _latest_run(db, source, skipped=False)
    return RefreshOut(
        key=source,
        outcome=outcome,
        http_status=run.http_status if run is not None else None,
        detail_code=run.detail_code if run is not None else None,
        started_at=_instant(run.started_at if run is not None else None),
        finished_at=_instant(run.finished_at if run is not None else None),
    )


@router.patch("/admin/sources/{key}/interval", response_model=IntervalOut)
def update_interval(
    key: str, payload: IntervalInput, actor: AdminWriter, db: DB,
) -> IntervalOut:
    """Apply one interval atomically when the submitted version is current."""
    source = _source(key)
    _config(db, source)
    row = source_config.set_interval(
        db, source, payload.interval_seconds, payload.version,
    )
    return IntervalOut(
        key=source, interval_seconds=row.interval_seconds, version=row.version,
    )

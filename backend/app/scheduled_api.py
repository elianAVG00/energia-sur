"""Public CU02 scheduled-works query transport."""

from datetime import UTC, datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api import DB, no_cache
from app.coverage import CoverageCatalog, load_catalog
from app.enre_client import FEED_URL
from app.enre_parser import normalized_key
from app.models import ScheduledSnapshot, ScheduledWork
from app.scheduled_store import current_snapshot, latest_source_status

router = APIRouter(dependencies=[Depends(no_cache)])

_INVALID = "Revisá los datos ingresados."
_MAX_NAME = 120
_FRESH_SECONDS = 15 * 60
_STALE_SECONDS = 60 * 60

CoverageStatus = Literal["covered", "out_of_coverage", "coverage_unverified"]
Freshness = Literal["fresh", "stale", "unavailable"]
Granularity = Literal["localidad", "partido"]
State = Literal[
    "out_of_coverage", "unavailable", "stale", "works_reported", "no_works",
    "coverage_unverified",
]
Limitation = Literal[
    "dates_not_published", "reason_not_published", "proximity_not_available",
    "announced_works_not_displayed",
]


class WorkOut(BaseModel):
    category: Literal["maintenance"]
    partido: str
    localidad: str | None
    subestacion_alimentador: str | None
    affected_users: int | None
    restoration_estimate_text: str | None
    reason_text: str | None
    planned_start_at: str | None
    planned_end_at: str | None


class LocalidadAreaOut(BaseModel):
    localidad: str | None
    coverage: CoverageStatus
    reported: bool


class PartidoAreaOut(BaseModel):
    partido: str
    localidades: list[LocalidadAreaOut]


class AreasOut(BaseModel):
    coverage_version: str | None
    coverage_retrieved_on: str | None
    areas: list[PartidoAreaOut]


class CoverageOut(BaseModel):
    partido: str
    localidad: str | None
    status: CoverageStatus


class ScheduledWorksOut(BaseModel):
    state: State
    source_status: Literal["ok", "degraded"]
    freshness: Freshness
    granularity: Granularity
    source: str
    source_url: str
    fetched_at: str | None
    source_updated_at: str | None
    source_reported_time: str | None
    coverage: CoverageOut
    limitations: list[Limitation]
    works: list[WorkOut] | None


def _clean(value: str, limit: int = _MAX_NAME) -> str:
    if len(value) > limit:
        raise HTTPException(422, _INVALID)
    if any(ord(character) < 32 or ord(character) == 127 for character in value):
        raise HTTPException(422, _INVALID)
    cleaned = " ".join(value.split())
    if not cleaned:
        raise HTTPException(422, _INVALID)
    return cleaned


def _instant(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _freshness(snapshot: ScheduledSnapshot | None, now: datetime) -> Freshness:
    if snapshot is None or snapshot.source_last_modified is None:
        return "unavailable"
    age = (now - snapshot.source_last_modified).total_seconds()
    if age <= _FRESH_SECONDS:
        return "fresh"
    if age <= _STALE_SECONDS:
        return "stale"
    return "unavailable"


def _state(freshness: Freshness, coverage: CoverageStatus, has_rows: bool,
           source_status: str) -> State:
    if coverage == "out_of_coverage":
        return "out_of_coverage"
    if freshness == "unavailable":
        return "unavailable"
    if freshness == "stale":
        return "stale"
    if has_rows:
        return "works_reported"
    if source_status == "degraded" and coverage == "covered":
        return "unavailable"
    if coverage == "covered":
        return "no_works"
    return "coverage_unverified"


def _limitations(snapshot: ScheduledSnapshot | None) -> list[Limitation]:
    values: list[Limitation] = [
        "dates_not_published", "reason_not_published", "proximity_not_available",
    ]
    if snapshot is not None and snapshot.comunicados_present:
        values.append("announced_works_not_displayed")
    return values


def _areas(db: Session, catalog: CoverageCatalog) -> AreasOut:
    snapshot = current_snapshot(db)
    reported: dict[tuple[str, str | None], str | None] = {}
    row_partidos: dict[str, str] = {}
    if snapshot is not None:
        rows = db.scalars(select(ScheduledWork).where(
            ScheduledWork.snapshot_id == snapshot.id,
        ).order_by(ScheduledWork.partido_key, ScheduledWork.localidad_key))
        for row in rows:
            reported[(row.partido_key, row.localidad_key)] = row.localidad
            row_partidos[row.partido_key] = row.partido

    partido_labels: dict[str, str] = {}
    buckets: dict[str, dict[str | None, LocalidadAreaOut]] = {}
    for (partido_key, localidad_key), entry in catalog.entries.items():
        partido_labels.setdefault(partido_key, entry.partido)
        buckets.setdefault(partido_key, {})[localidad_key] = LocalidadAreaOut(
            localidad=entry.localidad,
            coverage=cast(CoverageStatus, entry.status),
            reported=(partido_key, localidad_key) in reported,
        )
    for partido_key, label in row_partidos.items():
        partido_labels.setdefault(partido_key, label)
    for (partido_key, localidad_key), localidad_label in reported.items():
        bucket = buckets.setdefault(partido_key, {})
        previous = bucket.get(localidad_key)
        bucket[localidad_key] = LocalidadAreaOut(
            localidad=previous.localidad if previous is not None else localidad_label,
            coverage=(previous.coverage if previous is not None
                      else "coverage_unverified"),
            reported=True,
        )
    return AreasOut(
        coverage_version=catalog.version or None,
        coverage_retrieved_on=catalog.retrieved_on or None,
        areas=[
            PartidoAreaOut(
                partido=partido_labels.get(partido_key, partido_key.upper()),
                localidades=list(bucket.values()),
            )
            for partido_key, bucket in buckets.items()
        ],
    )


def _work_out(row: ScheduledWork) -> WorkOut:
    return WorkOut(
        category="maintenance",
        partido=row.partido,
        localidad=row.localidad,
        subestacion_alimentador=row.subestacion_alimentador,
        affected_users=row.affected_users,
        restoration_estimate_text=row.restoration_estimate_text,
        reason_text=None,
        planned_start_at=None,
        planned_end_at=None,
    )


def _payload(result: ScheduledWorksOut) -> JSONResponse:
    content = result.model_dump()
    if content["works"] is None:
        content.pop("works")
    return JSONResponse(
        content=content,
        headers={"Cache-Control": "no-store"},
    )


@router.get("/scheduled-works/areas", response_model=AreasOut)
def scheduled_areas(db: DB) -> AreasOut:
    return _areas(db, load_catalog())


@router.get("/scheduled-works", response_model=ScheduledWorksOut)
def scheduled_works(
    partido: Annotated[str, Query()],
    db: DB,
    localidad: Annotated[str | None, Query()] = None,
) -> Response:
    partido_value = _clean(partido)
    localidad_value = _clean(localidad) if localidad is not None else None
    snapshot = current_snapshot(db)
    rows: list[ScheduledWork] = []
    if snapshot is not None:
        statement = select(ScheduledWork).where(
            ScheduledWork.snapshot_id == snapshot.id,
            ScheduledWork.partido_key == normalized_key(partido_value),
        )
        if localidad_value is not None:
            statement = statement.where(
                ScheduledWork.localidad_key == normalized_key(localidad_value),
            )
        rows = list(db.scalars(statement.order_by(
            ScheduledWork.category, ScheduledWork.localidad_key, ScheduledWork.id,
        )))

    freshness = _freshness(snapshot, datetime.now(UTC))
    coverage = cast(CoverageStatus, load_catalog().classify(partido_value, localidad_value))
    source_status = cast(Literal["ok", "degraded"], latest_source_status(db))
    state = _state(freshness, coverage, bool(rows), source_status)
    if state == "works_reported" or (state in {"stale", "unavailable"} and rows):
        works: list[WorkOut] | None = [_work_out(row) for row in rows]
    elif state == "no_works":
        works = []
    else:
        works = None

    result = ScheduledWorksOut(
        state=state,
        source_status=source_status,
        freshness=freshness,
        granularity="localidad" if localidad_value is not None else "partido",
        source="ENRE",
        source_url=snapshot.source_url if snapshot is not None else FEED_URL,
        fetched_at=_instant(snapshot.fetched_at) if snapshot is not None else None,
        source_updated_at=(
            _instant(snapshot.source_last_modified) if snapshot is not None else None
        ),
        source_reported_time=(
            snapshot.source_reported_time if snapshot is not None else None
        ),
        coverage=CoverageOut(
            partido=partido_value, localidad=localidad_value, status=coverage,
        ),
        limitations=_limitations(snapshot),
        works=works,
    )
    return _payload(result)

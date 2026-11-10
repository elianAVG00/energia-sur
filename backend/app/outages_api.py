"""Public CU01 outage query and GeoRef resolution transport."""

import threading
import time
from datetime import UTC, datetime
from typing import Annotated, Literal, cast

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from app import georef
from app.api import DB, no_cache
from app.coverage import CoverageCatalog, load_catalog
from app.enre_client import FEED_URL
from app.enre_parser import normalized_key
from app.models import OutageReport, OutageSnapshot
from app.outage_store import current_snapshot, latest_source_status

router = APIRouter(dependencies=[Depends(no_cache)])

_INVALID = "Revisá los datos ingresados."
_GEO_UNAVAILABLE = "El servicio de ubicación no está disponible. Intentá nuevamente."
_GEO_NOT_FOUND = "No pudimos ubicar la dirección. Probá con partido y localidad."
_GEO_OUTSIDE = "La ubicación está fuera del área consultada."
_MAX_NAME = 120
_MAX_ADDRESS = 300
_FRESH_SECONDS = 15 * 60
_STALE_SECONDS = 60 * 60
_RATE_LIMIT = 20
_RATE_WINDOW_SECONDS = 60.0

Category = Literal["medium_voltage", "low_voltage", "preventive"]
CoverageStatus = Literal["covered", "out_of_coverage", "coverage_unverified"]
Freshness = Literal["fresh", "stale", "unavailable"]
Granularity = Literal["localidad", "partido"]
State = Literal[
    "geographic_error", "out_of_coverage", "unavailable", "stale",
    "reported", "no_reports", "coverage_unverified",
]

_rate_hits: dict[str, list[float]] = {}
_rate_lock = threading.Lock()


def reset_rate_limit() -> None:
    """Clear the in-process resolve limiter (used by tests and by operators)."""
    with _rate_lock:
        _rate_hits.clear()


def _allow(client: str) -> bool:
    now = time.monotonic()
    with _rate_lock:
        hits = [
            hit for hit in _rate_hits.get(client, [])
            if now - hit < _RATE_WINDOW_SECONDS
        ]
        if len(hits) >= _RATE_LIMIT:
            _rate_hits[client] = hits
            return False
        hits.append(now)
        if len(_rate_hits) > 1024:
            expired = [
                key for key, values in _rate_hits.items()
                if not values or now - values[-1] >= _RATE_WINDOW_SECONDS
            ]
            for key in expired:
                _rate_hits.pop(key, None)
        _rate_hits[client] = hits
        return True


def _too_many() -> JSONResponse:
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas solicitudes. Intentá nuevamente en un minuto."},
        headers={"Retry-After": "60", "Cache-Control": "no-store"},
    )


class OutageOut(BaseModel):
    category: Category
    partido: str
    localidad: str | None
    subestacion_alimentador: str | None
    affected_users: int | None
    normalizacion: str | None


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


class OutagesOut(BaseModel):
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
    totals_scope: Literal["edesur"]
    total_users_without: int | None
    total_users_with: int | None
    users_affected_yesterday: int | None
    outages: list[OutageOut] | None


class ResolveInput(BaseModel):
    address: str
    partido: str | None = None
    localidad: str | None = None


class CoordinatesInput(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class ResolveZoneOut(BaseModel):
    partido: str
    localidad: str | None
    granularity: Granularity
    coverage: CoverageStatus


class ResolveOut(BaseModel):
    status: Literal["resolved", "candidates"]
    zone: ResolveZoneOut | None = None
    candidates: list[ResolveZoneOut] | None = None


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


def _freshness(snapshot: OutageSnapshot | None, now: datetime) -> Freshness:
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
        return "reported"
    if source_status == "degraded" and coverage == "covered":
        return "unavailable"
    if coverage == "covered":
        return "no_reports"
    return "coverage_unverified"


def _known_areas(db: Session) -> georef.KnownAreas:
    snapshot = current_snapshot(db)
    if snapshot is None:
        return {}
    rows = db.scalars(select(OutageReport).where(
        OutageReport.snapshot_id == snapshot.id,
    ))
    known: georef.KnownAreas = {}
    for row in rows:
        if row.localidad_key is not None and row.localidad is not None:
            known[(row.partido_key, row.localidad_key)] = row.localidad
    return known


def _areas(db: Session, catalog: CoverageCatalog) -> AreasOut:
    snapshot = current_snapshot(db)
    reported: dict[tuple[str, str | None], str | None] = {}
    row_partidos: dict[str, str] = {}
    if snapshot is not None:
        rows = db.scalars(select(OutageReport).where(
            OutageReport.snapshot_id == snapshot.id,
        ).order_by(OutageReport.partido_key, OutageReport.localidad_key))
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


def _zone_out(zone: georef.Zone) -> ResolveZoneOut:
    return ResolveZoneOut(
        partido=zone.partido,
        localidad=zone.localidad,
        granularity=cast(Granularity, zone.granularity),
        coverage=cast(CoverageStatus, zone.coverage),
    )


def _resolve_response(zones: list[georef.Zone]) -> ResolveOut:
    if len(zones) == 1:
        return ResolveOut(status="resolved", zone=_zone_out(zones[0]))
    return ResolveOut(
        status="candidates",
        candidates=[_zone_out(zone) for zone in zones],
    )


def _geo_message(error: georef.GeorefError) -> str:
    if error.reason == "not_found":
        return _GEO_NOT_FOUND
    if error.reason == "outside_scope":
        return _GEO_OUTSIDE
    return _GEO_UNAVAILABLE


def _client(request: Request) -> str:
    # Single-instance deployment: the limiter keys on the socket peer. A proxy
    # that rewrites the peer makes all visitors share a bucket; do not trust
    # X-Forwarded-For without an explicit trusted-proxy configuration.
    return request.client.host if request.client is not None else "unknown"


@router.get("/outages/areas", response_model=AreasOut)
def outage_areas(db: DB) -> AreasOut:
    return _areas(db, load_catalog())


@router.get("/outages", response_model=OutagesOut, response_model_exclude_none=True)
def current_outages(
    partido: Annotated[str, Query()],
    db: DB,
    localidad: Annotated[str | None, Query()] = None,
) -> OutagesOut:
    partido_value = _clean(partido)
    localidad_value = _clean(localidad) if localidad is not None else None
    snapshot = current_snapshot(db)
    rows: list[OutageReport] = []
    if snapshot is not None:
        statement = select(OutageReport).where(
            OutageReport.snapshot_id == snapshot.id,
            OutageReport.partido_key == normalized_key(partido_value),
        )
        if localidad_value is not None:
            statement = statement.where(
                OutageReport.localidad_key == normalized_key(localidad_value),
            )
        rows = list(db.scalars(statement.order_by(
            OutageReport.category, OutageReport.localidad_key, OutageReport.id,
        )))

    freshness = _freshness(snapshot, datetime.now(UTC))
    coverage = cast(CoverageStatus, load_catalog().classify(partido_value, localidad_value))
    source_status = cast(Literal["ok", "degraded"], latest_source_status(db))
    state = _state(freshness, coverage, bool(rows), source_status)
    if rows and state in {"reported", "stale", "unavailable"}:
        payload: list[OutageOut] | None = [
            OutageOut(
                category=cast(Category, row.category),
                partido=row.partido,
                localidad=row.localidad,
                subestacion_alimentador=row.subestacion_alimentador,
                affected_users=row.affected_users,
                normalizacion=row.normalizacion,
            )
            for row in rows
        ]
    elif state == "no_reports":
        payload = []
    else:
        payload = None

    return OutagesOut(
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
        totals_scope="edesur",
        total_users_without=snapshot.total_users_without if snapshot is not None else None,
        total_users_with=snapshot.total_users_with if snapshot is not None else None,
        users_affected_yesterday=(
            snapshot.users_affected_yesterday if snapshot is not None else None
        ),
        outages=payload,
    )


@router.post("/outages/resolve", response_model=ResolveOut,
             response_model_exclude_none=True)
def resolve_outage_address(
    payload: ResolveInput, request: Request, db: DB,
) -> ResolveOut | JSONResponse:
    if not _allow(_client(request)):
        return _too_many()
    address = _clean(payload.address, _MAX_ADDRESS)
    partido_hint = _clean(payload.partido) if payload.partido is not None else None
    localidad_hint = _clean(payload.localidad) if payload.localidad is not None else None
    try:
        zones = georef.resolve_address(
            address, load_catalog(), _known_areas(db),
            partido_hint=partido_hint, localidad_hint=localidad_hint,
        )
    except georef.GeorefError as error:
        raise HTTPException(422, _geo_message(error)) from None
    return _resolve_response(zones)


@router.post("/outages/resolve-location", response_model=ResolveOut,
             response_model_exclude_none=True)
def resolve_outage_location(
    payload: CoordinatesInput, request: Request, db: DB,
) -> ResolveOut | JSONResponse:
    if not _allow(_client(request)):
        return _too_many()
    try:
        zone = georef.resolve_location(
            payload.lat, payload.lon, load_catalog(), _known_areas(db),
        )
    except georef.GeorefError as error:
        raise HTTPException(422, _geo_message(error)) from None
    return ResolveOut(status="resolved", zone=_zone_out(zone))

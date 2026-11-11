"""Read-only LangChain tools and a deterministic router for CU01/CU02 data."""

from __future__ import annotations

import json
import unicodedata
from dataclasses import asdict, dataclass
from datetime import UTC, datetime

from langchain_core.tools import tool
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.coverage import load_catalog
from app.db import get_engine
from app.enre_client import FEED_URL
from app.enre_parser import normalized_key
from app.models import OutageReport, ScheduledWork
from app.outage_store import current_snapshot as outage_snapshot
from app.outage_store import latest_source_status as outage_status
from app.public_reads import (
    freshness,
    outage_state,
    scheduled_limitations,
    scheduled_state,
)
from app.scheduled_store import current_snapshot as scheduled_snapshot
from app.scheduled_store import latest_source_status as scheduled_status

_SCHEDULED_TERMS = ("trabajo", "mantenimiento", "programad", "obra")
_OUTAGE_TERMS = (
    "corte", "cortes", "sin luz", "sin suministro", "suministro", "restablec",
    "hay luz", "no tengo luz", "se fue la luz",
)
_GUIDE_TERMS = (
    "como", "donde", "telefono", "pago", "pagar", "factura", "tarifa", "subsidio",
    "tramite", "reclamo", "canal", "whatsapp", "oficina", "titularidad", "recs",
    "electrodependiente", "ahorro", "eficiencia", "led", "kwh", "consumo", "deuda",
    "vencida", "turno", "que es", "garantia", "beneficio", "descuento",
)


def _norm(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return "".join(c for c in decomposed if not unicodedata.combining(c)).lower().strip()


def _instant(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def _outage_row(row: OutageReport) -> dict[str, object]:
    return {
        "category": row.category,
        "partido": row.partido,
        "localidad": row.localidad,
        "subestacion_alimentador": row.subestacion_alimentador,
        "affected_users": row.affected_users,
        "normalizacion": row.normalizacion,
    }


def _scheduled_row(row: ScheduledWork) -> dict[str, object]:
    return {
        "category": "maintenance",
        "partido": row.partido,
        "localidad": row.localidad,
        "subestacion_alimentador": row.subestacion_alimentador,
        "affected_users": row.affected_users,
        "restoration_estimate_text": row.restoration_estimate_text,
        "reason_text": None,
        "planned_start_at": None,
        "planned_end_at": None,
    }


@dataclass(frozen=True)
class OutageResult:
    state: str
    freshness: str
    coverage: str
    source_status: str
    source: str
    source_url: str
    fetched_at: str | None
    source_updated_at: str | None
    zone: str
    outages: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class ScheduledResult:
    state: str
    freshness: str
    coverage: str
    source_status: str
    source: str
    source_url: str
    fetched_at: str | None
    source_updated_at: str | None
    zone: str
    limitations: tuple[str, ...]
    works: tuple[dict[str, object], ...]


@dataclass(frozen=True)
class Plan:
    use_guide: bool
    use_outages: bool
    use_scheduled: bool
    zone: tuple[str, str | None] | None


def lookup_current_outages(partido: str, localidad: str | None = None) -> OutageResult:
    with Session(get_engine()) as db:
        snapshot = outage_snapshot(db)
        rows: list[OutageReport] = []
        if snapshot is not None:
            statement = select(OutageReport).where(
                OutageReport.snapshot_id == snapshot.id,
                OutageReport.partido_key == normalized_key(partido),
            )
            if localidad is not None:
                statement = statement.where(
                    OutageReport.localidad_key == normalized_key(localidad),
                )
            rows = list(db.scalars(statement.order_by(
                OutageReport.category, OutageReport.localidad_key, OutageReport.id,
            )))
        fresh = freshness(
            snapshot.source_last_modified if snapshot is not None else None,
            datetime.now(UTC),
        )
        coverage = load_catalog().classify(partido, localidad)
        status = outage_status(db)
        state = outage_state(fresh, coverage, bool(rows), status)
        payload = (
            tuple(_outage_row(row) for row in rows)
            if state in {"reported", "stale", "unavailable"} else ()
        )
        return OutageResult(
            state=state,
            freshness=fresh,
            coverage=coverage,
            source_status=status,
            source="ENRE",
            source_url=snapshot.source_url if snapshot is not None else FEED_URL,
            fetched_at=_instant(snapshot.fetched_at) if snapshot is not None else None,
            source_updated_at=(
                _instant(snapshot.source_last_modified) if snapshot is not None else None
            ),
            zone=partido if localidad is None else f"{partido} / {localidad}",
            outages=payload,
        )


def lookup_scheduled_works(
    partido: str, localidad: str | None = None,
) -> ScheduledResult:
    with Session(get_engine()) as db:
        snapshot = scheduled_snapshot(db)
        rows: list[ScheduledWork] = []
        if snapshot is not None:
            statement = select(ScheduledWork).where(
                ScheduledWork.snapshot_id == snapshot.id,
                ScheduledWork.partido_key == normalized_key(partido),
            )
            if localidad is not None:
                statement = statement.where(
                    ScheduledWork.localidad_key == normalized_key(localidad),
                )
            rows = list(db.scalars(statement.order_by(
                ScheduledWork.category, ScheduledWork.localidad_key, ScheduledWork.id,
            )))
        fresh = freshness(
            snapshot.source_last_modified if snapshot is not None else None,
            datetime.now(UTC),
        )
        coverage = load_catalog().classify(partido, localidad)
        status = scheduled_status(db)
        state = scheduled_state(fresh, coverage, bool(rows), status)
        payload = (
            tuple(_scheduled_row(row) for row in rows)
            if state in {"works_reported", "stale", "unavailable"} else ()
        )
        return ScheduledResult(
            state=state,
            freshness=fresh,
            coverage=coverage,
            source_status=status,
            source="ENRE",
            source_url=snapshot.source_url if snapshot is not None else FEED_URL,
            fetched_at=_instant(snapshot.fetched_at) if snapshot is not None else None,
            source_updated_at=(
                _instant(snapshot.source_last_modified) if snapshot is not None else None
            ),
            zone=partido if localidad is None else f"{partido} / {localidad}",
            limitations=tuple(scheduled_limitations(
                snapshot.comunicados_present if snapshot is not None else False,
            )),
            works=payload,
        )


def resolve_zone(text: str) -> tuple[str, str | None] | None:
    """Match a mentioned zone against the catalog and both current snapshots."""
    lowered = _norm(text)
    catalog = load_catalog()
    partido_match: str | None = None
    for (_, localidad_key), entry in catalog.entries.items():
        if entry.localidad and _norm(entry.localidad) in lowered:
            return (entry.partido, entry.localidad)
        if _norm(entry.partido) in lowered:
            partido_match = entry.partido
    if partido_match is not None:
        return (partido_match, None)
    with Session(get_engine()) as db:
        snapshot = outage_snapshot(db)
        if snapshot is not None:
            for row in db.scalars(select(OutageReport).where(
                OutageReport.snapshot_id == snapshot.id,
            )):
                if row.localidad and _norm(row.localidad) in lowered:
                    return (row.partido, row.localidad)
                if _norm(row.partido) in lowered:
                    partido_match = row.partido
        scheduled = scheduled_snapshot(db)
        if scheduled is not None:
            for work in db.scalars(select(ScheduledWork).where(
                ScheduledWork.snapshot_id == scheduled.id,
            )):
                if work.localidad and _norm(work.localidad) in lowered:
                    return (work.partido, work.localidad)
                if _norm(work.partido) in lowered:
                    partido_match = partido_match or work.partido
    return (partido_match, None) if partido_match is not None else None


def plan_question(text: str) -> Plan:
    lowered = _norm(text)
    use_scheduled = any(term in lowered for term in _SCHEDULED_TERMS)
    use_outages = any(term in lowered for term in _OUTAGE_TERMS)
    use_guide = (
        any(term in lowered for term in _GUIDE_TERMS)
        or not (use_outages or use_scheduled)
    )
    zone = resolve_zone(text) if (use_outages or use_scheduled) else None
    return Plan(
        use_guide=use_guide,
        use_outages=use_outages,
        use_scheduled=use_scheduled,
        zone=zone,
    )


@tool
def current_outages(partido: str, localidad: str | None = None) -> str:
    """Consultar cortes actuales informados por ENRE para un partido/localidad."""
    return json.dumps(
        asdict(lookup_current_outages(partido, localidad)), ensure_ascii=False,
    )


@tool
def scheduled_works(partido: str, localidad: str | None = None) -> str:
    """Consultar trabajos de mantenimiento informados por ENRE (alcance U22)."""
    return json.dumps(
        asdict(lookup_scheduled_works(partido, localidad)), ensure_ascii=False,
    )


TOOLS = [current_outages, scheduled_works]

"""Independent JSON5 parsing and normalization of ENRE scheduled works.

CU02 reads only ``cortesProgramados``. ``cortesComunicados`` is counted and
flagged but never normalized because no populated payload has been observed.
Remote JavaScript is never executed; the wrapper is stripped and the literal is
parsed as data with JSON5.
"""

import re
import unicodedata
from dataclasses import dataclass

import json5

from app.enre_parser import normalized_key

_WRAPPER = re.compile(r"\A\s*var\s+data\s*=\s*(\{.*\})\s*;?\s*\Z", re.DOTALL)
_THOUSANDS = re.compile(r"\A\d{1,3}(?:\.\d{3})+\Z")
_DIGITS = re.compile(r"\A\d+\Z")

_MAX_NAME = 120
_MAX_DETAIL = 200
_MAX_TEXT = 120

_NUMERIC_SENTINELS = {"", "-", "--:--", "n/a", "sin datos"}

_SOURCE = "cortesProgramados"
_UNOBSERVED = "cortesComunicados"


class ScheduledParseError(Exception):
    code = "parse_error"


class ScheduledSchemaError(Exception):
    code = "schema_error"


@dataclass(frozen=True)
class ScheduledRow:
    category: str
    partido: str
    localidad: str | None
    partido_key: str
    localidad_key: str | None
    subestacion_alimentador: str | None
    affected_users: int | None
    restoration_estimate_text: str | None


@dataclass(frozen=True)
class ScheduledFeed:
    distributor: str
    source_reported_time: str | None
    rows: tuple[ScheduledRow, ...]
    row_counts: dict[str, object]
    unverified_collections: list[str]
    comunicados_present: bool


def _text(value: object, field: str, limit: int, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise ScheduledSchemaError(f"{field} is missing")
        return None
    if not isinstance(value, str):
        raise ScheduledSchemaError(f"{field} is not text")
    cleaned = " ".join(unicodedata.normalize("NFC", value).split())
    if not cleaned:
        if required:
            raise ScheduledSchemaError(f"{field} is empty")
        return None
    if len(cleaned) > limit:
        raise ScheduledSchemaError(f"{field} is too long")
    if any(ord(character) < 32 for character in cleaned):
        raise ScheduledSchemaError(f"{field} contains a control character")
    return cleaned


def _count(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise ScheduledSchemaError(f"{field} is not a count")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        cleaned = value.strip()
        if cleaned.casefold() in _NUMERIC_SENTINELS:
            return None
        if _THOUSANDS.match(cleaned):
            cleaned = cleaned.replace(".", "")
        if not _DIGITS.match(cleaned):
            raise ScheduledSchemaError(f"{field} is not a non-negative integer")
        number = int(cleaned)
    else:
        raise ScheduledSchemaError(f"{field} is not a count")
    if number < 0:
        raise ScheduledSchemaError(f"{field} is negative")
    return number


def _reported_time(value: object) -> str | None:
    text = _text(value, "ultimaActualizacion", 16)
    if text is None or text in {"-", "--:--"}:
        return None
    return text


def _object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise ScheduledSchemaError(f"{field} is not an object")
    result: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str):
            raise ScheduledSchemaError(f"{field} has a non-text key")
        result[raw_key] = raw_value
    return result


def _row(item: object) -> ScheduledRow:
    row = _object(item, f"{_SOURCE} row")
    partido = _text(row.get("partido"), "partido", _MAX_NAME, required=True)
    if partido is None:  # pragma: no cover - required=True already raised
        raise ScheduledSchemaError("partido is missing")
    localidad = _text(row.get("localidad"), "localidad", _MAX_NAME)
    return ScheduledRow(
        category="maintenance",
        partido=partido,
        localidad=localidad,
        partido_key=normalized_key(partido),
        localidad_key=normalized_key(localidad) if localidad is not None else None,
        subestacion_alimentador=_text(
            row.get("subestacion_alimentador"), "subestacion_alimentador", _MAX_DETAIL,
        ),
        affected_users=_count(row.get("usuarios"), "usuarios"),
        restoration_estimate_text=_text(
            row.get("normalizacion"), "normalizacion", _MAX_TEXT,
        ),
    )


def parse_scheduled(text: str) -> ScheduledFeed:
    """Parse one ENRE payload without executing remote code."""
    match = _WRAPPER.match(text)
    if match is None:
        raise ScheduledParseError("ENRE payload is not a var data literal")
    try:
        raw: object = json5.loads(match.group(1))
    except Exception as error:
        raise ScheduledParseError("ENRE payload is not valid JSON5") from error
    data = _object(raw, "ENRE payload")

    empresa = _text(data.get("empresa"), "empresa", 32, required=True)
    if empresa is None:  # pragma: no cover - required=True already raised
        raise ScheduledSchemaError("empresa is missing")
    distributor = empresa.upper()
    if distributor != "EDESUR":
        raise ScheduledSchemaError("ENRE payload is not an Edesur feed")

    if _SOURCE not in data:
        raise ScheduledSchemaError(f"{_SOURCE} is missing")
    collection = data.get(_SOURCE)
    if not isinstance(collection, list):
        raise ScheduledSchemaError(f"{_SOURCE} is not a list")
    rows = tuple(_row(item) for item in collection)

    row_counts: dict[str, object] = {"maintenance": len(rows)}
    unverified: list[str] = []
    comunicados_present = False
    raw_comunicados = data.get(_UNOBSERVED)
    if isinstance(raw_comunicados, list):
        row_counts["comunicados"] = len(raw_comunicados)
        comunicados_present = len(raw_comunicados) > 0
        if comunicados_present:
            unverified.append(_UNOBSERVED)
    else:
        # Missing or non-list: recorded and never treated as an empty agenda.
        row_counts["comunicados"] = 0
        unverified.append(_UNOBSERVED)

    return ScheduledFeed(
        distributor=distributor,
        source_reported_time=_reported_time(data.get("ultimaActualizacion")),
        rows=rows,
        row_counts=row_counts,
        unverified_collections=unverified,
        comunicados_present=comunicados_present,
    )

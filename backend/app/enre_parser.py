"""Strict JSON5 parsing and normalization of the ENRE data literal.

The feed is a JavaScript assignment (`var data = {...}`) whose object literal is
valid JSON5: unquoted keys and single-quoted strings. Remote code is never
executed; the wrapper is stripped and the literal is parsed as data.
"""

import re
import unicodedata
from dataclasses import dataclass

import json5

_WRAPPER = re.compile(r"\A\s*var\s+data\s*=\s*(\{.*\})\s*;?\s*\Z", re.DOTALL)
_THOUSANDS = re.compile(r"\A\d{1,3}(?:\.\d{3})+\Z")
_DIGITS = re.compile(r"\A\d+\Z")

_MAX_NAME = 120
_MAX_DETAIL = 200
_MAX_TEXT = 120

_NUMERIC_SENTINELS = {"", "-", "--:--", "n/a", "sin datos"}

_CATEGORIES = (
    ("cortesServicioMedia", "medium_voltage"),
    ("cortesServicioBaja", "low_voltage"),
    ("cortesPreventivos", "preventive"),
)


class EnreParseError(Exception):
    code = "parse_error"


class EnreSchemaError(Exception):
    code = "schema_error"


@dataclass(frozen=True)
class EnreRow:
    category: str
    partido: str
    localidad: str | None
    partido_key: str
    localidad_key: str | None
    subestacion_alimentador: str | None
    affected_users: int | None
    normalizacion: str | None


@dataclass(frozen=True)
class EnreFeed:
    distributor: str
    total_users_without: int | None
    total_users_with: int | None
    users_affected_yesterday: int | None
    source_reported_time: str | None
    rows: tuple[EnreRow, ...]
    row_counts: dict[str, object]
    degraded: bool


def normalized_key(value: str) -> str:
    """Comparison key: NFC, case-folded, trimmed and single-spaced."""
    return " ".join(unicodedata.normalize("NFC", value).strip().casefold().split())


def _text(value: object, field: str, limit: int, *, required: bool = False) -> str | None:
    if value is None:
        if required:
            raise EnreSchemaError(f"{field} is missing")
        return None
    if not isinstance(value, str):
        raise EnreSchemaError(f"{field} is not text")
    cleaned = " ".join(unicodedata.normalize("NFC", value).split())
    if not cleaned:
        if required:
            raise EnreSchemaError(f"{field} is empty")
        return None
    if len(cleaned) > limit:
        raise EnreSchemaError(f"{field} is too long")
    if any(ord(character) < 32 for character in cleaned):
        raise EnreSchemaError(f"{field} contains a control character")
    return cleaned


def _count(value: object, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool):
        raise EnreSchemaError(f"{field} is not a count")
    if isinstance(value, int):
        number = value
    elif isinstance(value, str):
        cleaned = value.strip()
        if cleaned.casefold() in _NUMERIC_SENTINELS:
            return None
        if _THOUSANDS.match(cleaned):
            cleaned = cleaned.replace(".", "")
        if not _DIGITS.match(cleaned):
            raise EnreSchemaError(f"{field} is not a non-negative integer")
        number = int(cleaned)
    else:
        raise EnreSchemaError(f"{field} is not a count")
    if number < 0:
        raise EnreSchemaError(f"{field} is negative")
    return number


def _reported_time(value: object) -> str | None:
    text = _text(value, "ultimaActualizacion", 16)
    if text is None or text in {"-", "--:--"}:
        return None
    return text


def _is_degraded(value: object) -> bool:
    return isinstance(value, str) and value.strip().casefold() in {"n/a", "-"}


def _object(value: object, field: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise EnreSchemaError(f"{field} is not an object")
    result: dict[str, object] = {}
    for raw_key, raw_value in value.items():
        if not isinstance(raw_key, str):
            raise EnreSchemaError(f"{field} has a non-text key")
        result[raw_key] = raw_value
    return result


def _row(item: object, category: str) -> EnreRow:
    row = _object(item, f"{category} row")
    partido = _text(row.get("partido"), "partido", _MAX_NAME, required=True)
    if partido is None:  # pragma: no cover - required=True already raised
        raise EnreSchemaError("partido is missing")
    localidad = _text(row.get("localidad"), "localidad", _MAX_NAME)
    return EnreRow(
        category=category,
        partido=partido,
        localidad=localidad,
        partido_key=normalized_key(partido),
        localidad_key=normalized_key(localidad) if localidad is not None else None,
        subestacion_alimentador=_text(
            row.get("subestacion_alimentador"), "subestacion_alimentador", _MAX_DETAIL,
        ),
        affected_users=_count(row.get("usuarios"), "usuarios"),
        normalizacion=_text(row.get("normalizacion"), "normalizacion", _MAX_TEXT),
    )


def parse_feed(text: str) -> EnreFeed:
    """Parse and normalize one ENRE payload without executing remote code."""
    match = _WRAPPER.match(text)
    if match is None:
        raise EnreParseError("ENRE payload is not a var data literal")
    try:
        raw: object = json5.loads(match.group(1))
    except Exception as error:
        raise EnreParseError("ENRE payload is not valid JSON5") from error
    data = _object(raw, "ENRE payload")

    empresa = _text(data.get("empresa"), "empresa", 32, required=True)
    if empresa is None:  # pragma: no cover - required=True already raised
        raise EnreSchemaError("empresa is missing")
    distributor = empresa.upper()
    if distributor != "EDESUR":
        raise EnreSchemaError("ENRE payload is not an Edesur feed")

    raw_without = data.get("totalUsuariosSinSuministro")
    if raw_without is None:
        raise EnreSchemaError("totalUsuariosSinSuministro is missing")
    if isinstance(raw_without, str) and raw_without.strip().casefold() in {"", "sin datos"}:
        raise EnreSchemaError("totalUsuariosSinSuministro is not a count")
    rows: list[EnreRow] = []
    row_counts: dict[str, object] = {}
    for source, category in _CATEGORIES:
        if source not in data:
            raise EnreSchemaError(f"{source} is missing")
        collection = data.get(source)
        if not isinstance(collection, list):
            raise EnreSchemaError(f"{source} is not a list")
        row_counts[category] = len(collection)
        rows.extend(_row(item, category) for item in collection)

    return EnreFeed(
        distributor=distributor,
        total_users_without=_count(raw_without, "totalUsuariosSinSuministro"),
        total_users_with=_count(data.get("totalUsuariosConSuministro"),
                                "totalUsuariosConSuministro"),
        users_affected_yesterday=_count(data.get("totalUsuariosAyer"), "totalUsuariosAyer"),
        source_reported_time=_reported_time(data.get("ultimaActualizacion")),
        rows=tuple(rows),
        row_counts=row_counts,
        degraded=_is_degraded(raw_without),
    )

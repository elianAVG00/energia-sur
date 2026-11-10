"""Central GeoRef adapter for CU01, scoped to Buenos Aires and CABA.

Addresses and coordinates travel in request bodies and are never logged or
persisted. GeoRef is the only geocoding provider; an inadequate contract stops
the affected operation instead of substituting another provider.
"""

import math
import re
from dataclasses import dataclass

import httpx

from app.coverage import CoverageCatalog
from app.enre_parser import normalized_key

BASE_URL = "https://apis.datos.gob.ar/georef/api"
TIMEOUT_SECONDS = 8.0
MAX_CANDIDATES = 5
_AV_PREFIX = re.compile(r"(?i)^(av\.?|avenida)\s+")
_SCOPED_PROVINCES = {"06", "02"}

KnownAreas = dict[tuple[str, str], str]


class GeorefError(Exception):
    """GeoRef failure with a public reason code and no upstream detail."""

    reason = "unavailable"


class GeorefUnavailable(GeorefError):
    reason = "unavailable"


class GeorefNotFound(GeorefError):
    reason = "not_found"


class GeorefOutsideScope(GeorefError):
    reason = "outside_scope"


@dataclass(frozen=True)
class Zone:
    partido: str
    localidad: str | None
    granularity: str
    coverage: str


def _obj(value: object) -> dict[str, object] | None:
    if not isinstance(value, dict):
        return None
    result: dict[str, object] = {}
    for key, item in value.items():
        if isinstance(key, str):
            result[key] = item
    return result


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned or None


def _nested(value: dict[str, object], *keys: str) -> object:
    current: object = value
    for key in keys:
        current_object = _obj(current)
        if current_object is None:
            return None
        current = current_object.get(key)
    return current


def _items(value: object) -> list[dict[str, object]]:
    if not isinstance(value, list):
        return []
    items: list[dict[str, object]] = []
    for raw in value:
        item = _obj(raw)
        if item is not None:
            items.append(item)
    return items


def _get(path: str, params: dict[str, str]) -> dict[str, object]:
    try:
        response = httpx.get(
            f"{BASE_URL}/{path}", params=params, timeout=TIMEOUT_SECONDS,
            headers={
                "Accept": "application/json",
                "User-Agent": "EnergiaSur/1.0 (proyecto educativo)",
            },
            trust_env=False,
        )
        response.raise_for_status()
        body: object = response.json()
    except httpx.HTTPError as error:
        raise GeorefUnavailable("GeoRef request failed") from error
    except ValueError as error:
        raise GeorefUnavailable("GeoRef response is not JSON") from error
    payload = _obj(body)
    if payload is None:
        raise GeorefUnavailable("GeoRef response is not an object")
    return payload


def _map_localidad(partido: str, raw: str | None, catalog: CoverageCatalog,
                   known: KnownAreas) -> str | None:
    if raw is None:
        return None
    partido_key = normalized_key(partido)
    localidad_key = normalized_key(raw)
    label = known.get((partido_key, localidad_key))
    if label is not None:
        return label
    return catalog.label(partido, raw)


def _zone(partido_raw: str, localidad_raw: str | None, province: str,
          catalog: CoverageCatalog, known: KnownAreas) -> Zone:
    if province == "02":
        partido = "CAPITAL"
        localidad = None
    else:
        partido = partido_raw.strip().upper()
        localidad = _map_localidad(partido, localidad_raw, catalog, known)
    granularity = "localidad" if localidad is not None else "partido"
    return Zone(
        partido=partido,
        localidad=localidad,
        granularity=granularity,
        coverage=catalog.classify(partido, localidad),
    )


def _zone_from_address(item: dict[str, object], catalog: CoverageCatalog,
                       known: KnownAreas) -> Zone | None:
    province = _text(_nested(item, "provincia", "id"))
    if province not in _SCOPED_PROVINCES:
        return None
    partido_raw = _text(_nested(item, "departamento", "nombre"))
    if partido_raw is None:
        return None
    localidad_raw = _text(_nested(item, "localidad_censal", "nombre"))
    return _zone(partido_raw, localidad_raw, province, catalog, known)


def _matches(zone: Zone, partido_hint: str | None, localidad_hint: str | None) -> bool:
    if partido_hint is not None and normalized_key(zone.partido) != normalized_key(partido_hint):
        return False
    if localidad_hint is not None:
        return (zone.localidad is not None
                and normalized_key(zone.localidad) == normalized_key(localidad_hint))
    return True


def _dedupe(zones: list[Zone]) -> list[Zone]:
    seen: set[tuple[str, str | None]] = set()
    result: list[Zone] = []
    for zone in zones:
        key = (normalized_key(zone.partido),
               normalized_key(zone.localidad) if zone.localidad is not None else None)
        if key in seen:
            continue
        seen.add(key)
        result.append(zone)
    return result


def resolve_address(address: str, catalog: CoverageCatalog, known: KnownAreas, *,
                    partido_hint: str | None = None,
                    localidad_hint: str | None = None) -> list[Zone]:
    """Resolve an address to zones, retrying without a leading 'Av.' prefix."""
    queries = [address]
    stripped = _AV_PREFIX.sub("", address).strip()
    if stripped and stripped.casefold() != address.casefold():
        queries.append(stripped)
    for query in queries:
        zones: list[Zone] = []
        for province in sorted(_SCOPED_PROVINCES):
            payload = _get("direcciones", {
                "direccion": query,
                "provincia": province,
                "max": str(MAX_CANDIDATES),
            })
            for item in _items(payload.get("direcciones")):
                zone = _zone_from_address(item, catalog, known)
                if zone is not None and _matches(zone, partido_hint, localidad_hint):
                    zones.append(zone)
        deduped = _dedupe(zones)
        if deduped:
            return deduped
    raise GeorefNotFound("no address candidates")


def resolve_location(lat: float, lon: float, catalog: CoverageCatalog,
                     known: KnownAreas) -> Zone:
    """Reverse-geocode a consented position to a partido (localidad if known)."""
    if (not math.isfinite(lat) or not math.isfinite(lon)
            or not -90 <= lat <= 90 or not -180 <= lon <= 180):
        raise GeorefOutsideScope("invalid coordinates")
    payload = _get("ubicacion", {"lat": f"{lat}", "lon": f"{lon}"})
    ubicacion = _obj(payload.get("ubicacion"))
    if ubicacion is None:
        raise GeorefNotFound("no location")
    province = _text(_nested(ubicacion, "provincia", "id"))
    partido_raw = _text(_nested(ubicacion, "departamento", "nombre"))
    if province not in _SCOPED_PROVINCES or partido_raw is None:
        raise GeorefOutsideScope("location outside the scoped area")
    localidad_raw = _text(_nested(ubicacion, "localidad", "nombre"))
    return _zone(partido_raw, localidad_raw, province, catalog, known)

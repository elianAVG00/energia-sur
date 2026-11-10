"""Versioned Edesur coverage catalog: covered, out_of_coverage or unverified.

Absence from the catalog means ``coverage_unverified``; ``out_of_coverage`` is
only asserted for an explicit entry with documented provenance.
"""

import json
import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from app.enre_parser import normalized_key

_LOGGER = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent / "data" / "edesur_coverage.2026-11-10.json"
_STATUSES = {"covered", "out_of_coverage"}
_MAX_NAME = 200


class CoverageCatalogError(ValueError):
    """The versioned catalog is missing or malformed."""


@dataclass(frozen=True)
class CoverageEntry:
    partido: str
    localidad: str | None
    status: str


@dataclass(frozen=True)
class CoverageCatalog:
    version: str
    retrieved_on: str
    source: str
    entries: dict[tuple[str, str | None], CoverageEntry]

    def classify(self, partido: str, localidad: str | None) -> str:
        """Classify a zone; absence is unverified, never out of coverage.

        A localidad query only matches a localidad entry: a partido-level entry
        does not silently cover localidades the catalog does not list.
        """
        partido_key = normalized_key(partido)
        if localidad is not None:
            entry = self.entries.get((partido_key, normalized_key(localidad)))
        else:
            entry = self.entries.get((partido_key, None))
        return entry.status if entry is not None else "coverage_unverified"

    def has_localidad(self, partido: str, localidad: str) -> bool:
        return (normalized_key(partido), normalized_key(localidad)) in self.entries

    def label(self, partido: str, localidad: str) -> str | None:
        entry = self.entries.get((normalized_key(partido), normalized_key(localidad)))
        return entry.localidad if entry is not None else None


def _text(value: object, field: str, limit: int = _MAX_NAME) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CoverageCatalogError(f"{field} is missing")
    cleaned = value.strip()
    if len(cleaned) > limit:
        raise CoverageCatalogError(f"{field} is too long")
    if any(ord(character) < 32 for character in cleaned):
        raise CoverageCatalogError(f"{field} contains a control character")
    return cleaned


def _load(path: Path) -> CoverageCatalog:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CoverageCatalogError("coverage catalog cannot be read") from error
    if not isinstance(raw, dict):
        raise CoverageCatalogError("coverage catalog is not an object")
    version = _text(raw.get("version"), "version", 32)
    retrieved_on = _text(raw.get("retrieved_on"), "retrieved_on", 32)
    source = _text(raw.get("source"), "source", 500)
    entries_raw = raw.get("entries")
    if not isinstance(entries_raw, list):
        raise CoverageCatalogError("entries must be a list")
    entries: dict[tuple[str, str | None], CoverageEntry] = {}
    for item in entries_raw:
        if not isinstance(item, dict):
            raise CoverageCatalogError("entry is not an object")
        partido = _text(item.get("partido"), "partido")
        status = _text(item.get("status"), "status", 32)
        if status not in _STATUSES:
            raise CoverageCatalogError("unknown coverage status")
        raw_localidad = item.get("localidad")
        localidad = _text(raw_localidad, "localidad") if raw_localidad is not None else None
        key = (normalized_key(partido),
               normalized_key(localidad) if localidad is not None else None)
        if key in entries:
            raise CoverageCatalogError("duplicate coverage entry")
        entries[key] = CoverageEntry(partido=partido, localidad=localidad, status=status)
    return CoverageCatalog(
        version=version, retrieved_on=retrieved_on, source=source, entries=entries,
    )


@lru_cache(maxsize=4)
def load_catalog(path: str | None = None) -> CoverageCatalog:
    """Load the versioned catalog, failing safe to unverified on error."""
    try:
        return _load(Path(path) if path else CATALOG_PATH)
    except CoverageCatalogError as error:
        _LOGGER.warning("Coverage catalog unavailable (%s).", type(error).__name__)
        return CoverageCatalog(
            version="unavailable", retrieved_on="", source="",
            entries={},
        )

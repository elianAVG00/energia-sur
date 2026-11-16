"""Persistent shared territorial catalog for CU01 and CU02."""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import TypedDict, cast
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.engine import Connection
from sqlalchemy.orm import Session

from app.coverage import CoverageCatalog, CoverageCatalogError, CoverageEntry
from app.enre_parser import normalized_key
from app.models import (
    TerritorialCatalogMetadata,
    TerritorialLocality,
    TerritorialLocalitySource,
    TerritorialNameAlias,
    TerritorialParty,
)

CATALOG_PATH = Path(__file__).parent / "data" / "territorial_catalog_georef_v2_1.json"
CATALOG_KEY = "edesur-territory"
APPROVED_PARTIES = {
    "Almirante Brown", "Avellaneda", "Berazategui", "Cañuelas",
    "Esteban Echeverría", "Ezeiza", "Florencio Varela", "Lanús",
    "Lomas de Zamora", "Presidente Perón", "Quilmes", "San Vicente",
}


class PartySeed(TypedDict):
    party: str
    id: str


class LocalitySeed(TypedDict):
    partido: str
    partido_georef_id: str
    georef_id: str
    nombre: str
    categoria: str
    localidad_censal_id: str
    localidad_censal: str
    selectable: bool
    selector_review: str | None


class AliasSeed(TypedDict):
    kind: str
    source_label: str
    partido: str
    localidad: str | None
    status: str
    evidence: str


class CatalogSeed(TypedDict):
    version: str
    retrieved_at: str
    source: str
    concession_source: str
    province_id: str
    parties: list[PartySeed]
    records: list[LocalitySeed]
    enre_aliases: list[AliasSeed]


def locality_identity(party_georef_id: str, name: str) -> str:
    """Build a stable, party-scoped identifier for one canonical locality name."""
    return f"{party_georef_id}:{normalized_key(name)}"


def _read_seed(path: Path = CATALOG_PATH) -> CatalogSeed:
    try:
        raw: object = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise CoverageCatalogError("territorial catalog seed cannot be read") from error
    if not isinstance(raw, dict):
        raise CoverageCatalogError("territorial catalog seed is not an object")
    parties = raw.get("parties")
    records = raw.get("records")
    aliases = raw.get("enre_aliases")
    if (not isinstance(parties, list) or not isinstance(records, list)
            or not isinstance(aliases, list)):
        raise CoverageCatalogError("territorial catalog seed has an invalid shape")
    if len(parties) != 12 or len(records) != 99:
        raise CoverageCatalogError("territorial catalog seed has unexpected totals")
    party_names = {
        item.get("party") for item in parties if isinstance(item, dict)
        if isinstance(item.get("party"), str)
    }
    if party_names != APPROVED_PARTIES:
        raise CoverageCatalogError("territorial catalog parties do not match approved scope")
    if any(
        not isinstance(row, dict) or row.get("partido") not in APPROVED_PARTIES
        or not isinstance(row.get("georef_id"), str)
        or not isinstance(row.get("nombre"), str)
        or not isinstance(row.get("categoria"), str)
        for row in records
    ):
        raise CoverageCatalogError("territorial catalog locality record is malformed")
    if any(
        not isinstance(row, dict) or row.get("partido") not in APPROVED_PARTIES
        or row.get("kind") not in {"party", "locality"}
        or row.get("status") not in {"verified", "unresolved"}
        for row in aliases
    ):
        raise CoverageCatalogError("territorial catalog alias record is malformed")
    # The structural checks above establish these nested shapes; verify all
    # fields subsequently consumed before exposing the typed seed.
    if not all(isinstance(raw.get(key), str) and raw[key] for key in (
        "version", "retrieved_at", "source", "concession_source", "province_id",
    )):
        raise CoverageCatalogError("territorial catalog metadata is malformed")
    for party in parties:
        if (not isinstance(party, dict) or not isinstance(party.get("party"), str)
                or not isinstance(party.get("id"), str)):
            raise CoverageCatalogError("territorial party record is malformed")
    for row in records:
        if (not isinstance(row, dict) or not isinstance(row.get("partido_georef_id"), str)
                or not isinstance(row.get("localidad_censal_id"), str)
                or not isinstance(row.get("localidad_censal"), str)
                or not isinstance(row.get("selectable"), bool)
                or (row.get("selector_review") is not None
                    and not isinstance(row.get("selector_review"), str))):
            raise CoverageCatalogError("territorial locality metadata is malformed")
    for row in aliases:
        if (not isinstance(row, dict) or not isinstance(row.get("source_label"), str)
                or not isinstance(row.get("evidence"), str)
                or (row.get("localidad") is not None
                    and not isinstance(row.get("localidad"), str))):
            raise CoverageCatalogError("territorial alias metadata is malformed")
    return cast(CatalogSeed, raw)


def seed_catalog(connection: Connection, path: Path = CATALOG_PATH) -> None:
    """Idempotently seed the curated GeoRef capture and observed ENRE aliases."""
    raw = _read_seed(path)
    retrieved_at = datetime.fromisoformat(str(raw["retrieved_at"]).replace("Z", "+00:00"))

    metadata = {
        "catalog_key": CATALOG_KEY,
        "version": str(raw["version"]),
        "retrieved_at": retrieved_at,
        "source_url": str(raw["source"]),
        "concession_source_url": str(raw["concession_source"]),
        "province_id": str(raw["province_id"]),
    }
    connection.execute(
        insert(TerritorialCatalogMetadata)
        .values(metadata)
        .on_conflict_do_update(
            index_elements=[TerritorialCatalogMetadata.catalog_key],
            set_={key: value for key, value in metadata.items() if key != "catalog_key"},
        ),
    )

    party_ids: dict[str, str] = {}
    for party_seed in raw["parties"]:
        party_name = party_seed["party"]
        party_id = party_seed["id"]
        party_ids[party_name] = party_id
        party_values: dict[str, object] = {
            "georef_id": party_id,
            "name": party_name,
            "normalized_name": normalized_key(party_name),
            "coverage_status": "covered",
        }
        connection.execute(
            insert(TerritorialParty)
            .values(party_values)
            .on_conflict_do_update(
                index_elements=[TerritorialParty.georef_id],
                set_={key: value for key, value in party_values.items()
                      if key != "georef_id"},
            ),
        )

    grouped: dict[tuple[str, str], list[LocalitySeed]] = defaultdict(list)
    for locality_seed in raw["records"]:
        party_id = locality_seed["partido_georef_id"]
        if party_ids.get(locality_seed["partido"]) != party_id:
            raise CoverageCatalogError("GeoRef party ID does not match seed party")
        grouped[(party_id, normalized_key(locality_seed["nombre"]))].append(locality_seed)

    locality_ids: dict[tuple[str, str], str] = {}
    for (party_id, normalized_name), sources in grouped.items():
        source = next((item for item in sources if item["selectable"]), sources[0])
        locality_id = locality_identity(party_id, str(source["nombre"]))
        locality_ids[(party_id, normalized_name)] = locality_id
        locality_values: dict[str, object] = {
            "id": locality_id,
            "party_georef_id": party_id,
            "name": str(source["nombre"]),
            "normalized_name": normalized_name,
            "coverage_status": "coverage_unverified",
            "selectable": any(bool(item["selectable"]) for item in sources),
        }
        connection.execute(
            insert(TerritorialLocality)
            .values(locality_values)
            .on_conflict_do_update(
                index_elements=[TerritorialLocality.id],
                set_={key: value for key, value in locality_values.items() if key != "id"},
            ),
        )

    for (party_id, normalized_name), sources in grouped.items():
        locality_id = locality_ids[(party_id, normalized_name)]
        for source in sources:
            source_values: dict[str, object] = {
                "georef_id": str(source["georef_id"]),
                "locality_id": locality_id,
                "name": str(source["nombre"]),
                "category": str(source["categoria"]),
                "localidad_censal_id": source.get("localidad_censal_id"),
                "localidad_censal": source.get("localidad_censal"),
                "selector_review": source.get("selector_review"),
            }
            connection.execute(
                insert(TerritorialLocalitySource)
                .values(source_values)
                .on_conflict_do_update(
                    index_elements=[TerritorialLocalitySource.georef_id],
                    set_={key: value for key, value in source_values.items()
                          if key != "georef_id"},
                ),
            )

    for alias_seed in raw["enre_aliases"]:
        party_name = alias_seed["partido"]
        party_id = party_ids[party_name]
        locality_name = alias_seed["localidad"]
        kind = alias_seed["kind"]
        status = alias_seed["status"]
        alias_locality_id: str | None = (
            locality_ids[(party_id, normalized_key(locality_name))]
            if kind == "locality" and status == "verified"
            and locality_name is not None else None
        )
        alias_values: dict[str, object] = {
            "kind": kind,
            "source_label": alias_seed["source_label"],
            "normalized_source_key": normalized_key(alias_seed["source_label"]),
            "party_georef_id": party_id,
            "locality_id": alias_locality_id,
            "status": status,
            "evidence": alias_seed["evidence"],
        }
        connection.execute(
            insert(TerritorialNameAlias)
            .values(alias_values)
            .on_conflict_do_update(
                constraint="uq_territorial_alias_kind_party_key",
                set_={key: value for key, value in alias_values.items()
                      if key not in {"kind", "party_georef_id",
                                     "normalized_source_key"}},
            ),
        )


def load_catalog(db: Session) -> CoverageCatalog:
    """Load canonical selector entries and verified ENRE aliases from PostgreSQL."""
    metadata = db.get(TerritorialCatalogMetadata, CATALOG_KEY)
    if metadata is None:
        raise CoverageCatalogError("territorial catalog has not been seeded")

    parties = list(db.scalars(select(TerritorialParty).order_by(
        TerritorialParty.normalized_name,
    )))
    localities = list(db.scalars(
        select(TerritorialLocality).where(TerritorialLocality.selectable.is_(True))
        .order_by(TerritorialLocality.party_georef_id,
                  TerritorialLocality.normalized_name),
    ))
    aliases = list(db.scalars(select(TerritorialNameAlias)))
    party_by_id = {row.georef_id: row for row in parties}
    entries: dict[tuple[str, str | None], CoverageEntry] = {}
    party_labels: dict[str, str] = {}
    party_ids_by_key: dict[str, str] = {}
    for party in parties:
        key = party.normalized_name
        party_labels[key] = party.name
        party_ids_by_key[key] = party.georef_id
        entries[(key, None)] = CoverageEntry(
            partido=party.name, localidad=None, status=party.coverage_status,
        )
    locality_name_by_id: dict[str, str] = {}
    for locality in localities:
        party = party_by_id[locality.party_georef_id]
        party_key = party.normalized_name
        locality_name_by_id[locality.id] = locality.normalized_name
        entries[(party_key, locality.normalized_name)] = CoverageEntry(
            partido=party.name, localidad=locality.name,
            status=locality.coverage_status,
        )

    party_aliases: dict[str, str] = {}
    locality_aliases: dict[tuple[str, str], str] = {}
    party_query_keys: dict[str, set[str]] = defaultdict(set)
    locality_query_keys: dict[tuple[str, str], set[str]] = defaultdict(set)
    for party in parties:
        party_query_keys[party.normalized_name].add(party.normalized_name)
    for (party_key, locality_key), entry in entries.items():
        if locality_key is not None:
            locality_query_keys[(party_key, locality_key)].add(locality_key)

    for alias in aliases:
        if alias.status != "verified":
            continue
        target_party = party_by_id[alias.party_georef_id]
        target_party_key = target_party.normalized_name
        if alias.kind == "party":
            party_aliases[alias.normalized_source_key] = target_party_key
            party_query_keys[target_party_key].add(alias.normalized_source_key)
        elif alias.locality_id is not None:
            target_locality_key = locality_name_by_id.get(alias.locality_id)
            if target_locality_key is not None:
                locality_aliases[
                    (target_party_key, alias.normalized_source_key)
                ] = target_locality_key
                locality_query_keys[
                    (target_party_key, target_locality_key)
                ].add(alias.normalized_source_key)

    return CoverageCatalog(
        version=metadata.version,
        retrieved_on=metadata.retrieved_at.astimezone(
            ZoneInfo("America/Argentina/Buenos_Aires"),
        ).date().isoformat(),
        source=metadata.source_url,
        entries=entries,
        party_labels=party_labels,
        party_ids=party_ids_by_key,
        party_aliases=party_aliases,
        locality_aliases=locality_aliases,
        party_query_keys={key: frozenset(value)
                          for key, value in party_query_keys.items()},
        locality_query_keys={key: frozenset(value)
                             for key, value in locality_query_keys.items()},
    )

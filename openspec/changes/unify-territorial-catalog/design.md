# Design

## Context

See `proposal.md` for motivation and the spec deltas for externally visible behavior. CU01 and CU02 currently duplicate area-list assembly in `backend/app/outages_api.py` and `backend/app/scheduled_api.py`; each combines the same file-backed partial catalog with its own current ENRE snapshot. `backend/app/coverage.py` loads `backend/app/data/edesur_coverage.2026-11-10.json`. ENRE rows retain original party/locality labels and store comparison keys produced by `backend/app/enre_parser.py`. `backend/app/georef.py` currently resolves addresses and coordinates through GeoRef API v1 and maps locality labels using the coverage catalog plus snapshot-derived names.

The approved territorial boundary is the twelve named Buenos Aires partidos in the 2023 ENRE Edesur audit. CABA/CAPITAL is excluded from both selectors. GeoRef v2.1 `/localidades` queries for those departments returned 99 records across the 12 parties on 2026-11-15, with duplicate canonical names in six parties; after de-duplicating names within each party, 93 options remain before any individually justified exceptional-record exclusion. Results include multiple GeoRef categories, IDs, and levels. For example, Avellaneda includes the unusual `Área Reserva Cinturón Ecológico`; it requires a documented usefulness review rather than a category-wide exclusion. ENRE fixture observations include the GeoRef-matched `Glew`, `Longchamps`, `San José`/`SAN JOSE`, `Banfield`, `Monte Grande`, `Guernica`, and `Alejandro Korn`, and unresolved `Santa Anita` and `Zona Rural`. These fixtures are observations, not a complete live ENRE inventory.

## Goals / Non-Goals

**Goals:**

- Store the approved party/locality catalog and source-name equivalences in PostgreSQL, with stable provenance and repeatable seeding.
- Make the CU01 and CU02 area responses derive their options exclusively from the shared catalog.
- Keep GeoRef geography distinct from locality-level Edesur service evidence.
- Preserve ENRE row labels and query semantics while matching canonical selections to verified source variants.
- Keep address and consented geolocation resolution compatible with catalog identifiers and party/locality filters.

**Non-Goals:**

- Change ENRE acquisition intervals, locks, snapshot retention, categories, or the rows returned by outage/work queries.
- Add CABA or infer its Edesur-covered neighborhoods.
- Treat all GeoRef localities in a concession partido as individually served by Edesur.
- Fetch GeoRef live during application startup, migration, or public selector requests.
- Invent GeoRef mappings for unresolved ENRE observations.

## Decisions

### PostgreSQL is the selector source of truth

Add shared catalog tables to the existing Alembic/SQLAlchemy persistence model. The proposed logical model is:

- Parties: canonical display label, GeoRef department identity where available, approved concession-source provenance, and stable normalized key.
- GeoRef locality records: party relationship, GeoRef ID, canonical name, original category, and source/retrieval metadata. Keep source records even when two IDs/categories collapse to one displayed name.
- Selectable locality identities: one per normalized canonical name within a party, linked to all contributing GeoRef records.
- Source-name equivalences: source (`ENRE` or GeoRef), original observed label/key, target party/locality when verified, verification provenance, and an explicit unresolved state when no safe target exists.

The exact SQLAlchemy class/table names can follow existing `es_*` conventions during implementation; this design requires uniqueness by party plus canonical key, not global locality name. Homonyms such as Gerli and Canning remain distinct across parties.

**Alternative considered:** continue loading a JSON catalog or merge database snapshots in the API. Rejected because the user approved PostgreSQL as the shared persistent source, and snapshot-derived options are the cause of inconsistent selectors.

### Seed a reviewed GeoRef capture; do not make requests as a migration side effect

Use the official ENRE 2023 Edesur audit for the 12-party boundary and GeoRef v2.1 `/localidades` query results for locality data. Store the curated capture, GeoRef IDs/categories, query scope, source URLs, and retrieval date in an additive migration/seed. Use deterministic unique keys and PostgreSQL conflict handling so repeating the seed does not duplicate or erase records. Do not make network requests from Alembic or app startup.

The captured API response has 99 source rows and 93 unique names after deduplication within parties. Preserve all source IDs/categories behind each displayed name. Review special records individually: no category is excluded globally; retain a record unless its specific data shows it is not a useful selector geography, and document any such exclusion and reason. The first review candidate is `Área Reserva Cinturón Ecológico` in Avellaneda. CABA is not queried or seeded as a selector party.

**Alternative considered:** query GeoRef at every startup or selector load. Rejected because it makes selector availability dependent on an external service and gives no stable data version; migrations must be deterministic and offline-safe.

### Keep canonical labels separate from source labels and aliases

Use a shared comparison key based on Unicode decomposition with combining-mark removal, case folding, trimming, and collapsing whitespace. Keep canonical GeoRef party/locality display labels and original ENRE labels unchanged. Apply this deterministic normalization to both selector values and ENRE party/locality labels. Add explicit verified aliases for non-mechanical equivalences such as `PTE PERON` → `Presidente Perón`; do not use fuzzy matching to assign a canonical locality.

Seed verified equivalents only where the ENRE label unambiguously identifies a GeoRef entry within the same party. Initial fixture evidence supports `SAN JOSE` ↔ `San José`, `ESTEBAN ECHEVERRIA` ↔ `Esteban Echeverría`, `PTE PERON` ↔ `Presidente Perón`, and case/diacritic-insensitive matches such as `Monte Grande`, `Glew`, `Banfield`, `Guernica`, `Alejandro Korn`, and `Longchamps`. Confirm every equivalence against the full source data before seeding.

Record `Santa Anita` (Cañuelas) and `Zona Rural` (Lomas de Zamora) as observed unresolved ENRE values, with no canonical GeoRef target. Preserve their original snapshot labels. Party-level queries continue to include matching rows; an exact locality query may match an unresolved source value only by its own normalized raw label, never by a guessed substitute.

To retain compatibility with already stored ENRE snapshots, add a data migration that recomputes stored party/locality comparison keys from the preserved original labels using the new mechanical normalization. Keep the original labels and snapshot content unchanged. Explicit party aliases remain a query-time equivalence step, not a rewrite of source data.

**Alternative considered:** replace ENRE labels with GeoRef canonical labels or update only new snapshots. Rejected because it loses source fidelity or leaves existing snapshots unmatchable by the newly canonical selector values.

### Share catalog assembly, preserve current endpoints and isolate report data

Create one backend catalog repository/service used by both `GET /outages/areas` and `GET /scheduled-works/areas`; keep both existing URLs and their current outer response shape where compatible. Build party/locality choices only from PostgreSQL catalog rows. Do not query outage/work rows to add options or to mark options reported; remove the snapshot-derived `reported` field from locality-area options if retaining it would require consulting a snapshot. Preserve the existing catalog metadata and coverage fields where their semantics remain valid, and update frontend runtime validators accordingly.

Keep `GET /outages` and `GET /scheduled-works` backed by their current independent ENRE snapshots. Resolve incoming canonical names and verified aliases to stored comparison keys; do not change the categories, source freshness, or provenance logic. Keep GeoRef address/GPS resolution in the backend and make its output resolve against the shared catalog. The current address and reverse-geocoding adapter is pinned to GeoRef API v1 while the official landing page recommends v2.1; inspect the v2.1 address/location contract and make only the compatibility changes needed for existing address/GPS flows in this change, without adding a provider or dependency.

**Alternative considered:** collapse the two public area endpoints into one endpoint. Rejected to avoid an unnecessary API/UI transport change; shared implementation and identical options provide the required consistency.

### Preserve uncertainty for empty results

Keep existing result-state precedence and freshness behavior. For a fresh snapshot with no matching row, keep the current `no_reports`/`no_works` eligibility rules; make the user-facing copy say that no matching record was reported in the latest update, not that supply is uninterrupted or that a planned work cannot exist. For stale, unavailable, or unverified results, retain those states and their existing safeguards; do not convert them to an empty success.

GeoRef membership alone does not set locality coverage to `covered`. Preserve verified service evidence only where the existing catalog/source supports it; otherwise the locality remains `coverage_unverified`, which must not produce a claim of no reports.

**Alternative considered:** mark every GeoRef locality covered because its partido is in the concession list. Rejected because the approved evidence establishes party-level concession scope, not service to every GeoRef locality.

## Risks / Trade-offs

- [GeoRef returns administrative components, entities and other heterogeneous records] → Preserve category and ID; group duplicate names per party; review exceptional rows individually and record exclusions.
- [Locality presence may be mistaken for Edesur service] → Keep GeoRef provenance separate from coverage evidence and preserve `coverage_unverified` unless independently supported.
- [ENRE names may drift or remain outside GeoRef] → Use explicit versioned aliases, keep original labels, test unresolved raw-name matching, and never fuzzy-map unresolved values.
- [Re-keying persisted ENRE rows may affect historical matching] → Retain source labels, test migration over both current and retained snapshots, and provide a downgrade that recomputes the prior comparison key from those labels.
- [GeoRef v1 may be discontinued] → Validate current address and reverse-geocoding contracts against official v2.1 documentation and run compatibility tests before changing the adapter.
- [Catalog and ENRE data can evolve at different times] → Persist source retrieval metadata and keep independent refresh lifecycles; do not imply that catalog refresh updates outage/work snapshots or vice versa.

## Migration Plan

1. Add the next Alembic revision after `0008_cu10` to create the catalog and equivalence tables, constraints/indexes, and deterministic seed records; seed with conflict-safe upserts.
2. In the same or a dedicated subsequent revision, recompute existing `es_outage_reports` and `es_scheduled_works` comparison keys from original labels under the new key function. Do not alter report/work labels or snapshot data.
3. Deploy shared catalog reads for both area endpoints, query-time alias resolution, and frontend validators/copy. Keep API paths stable; remove snapshot dependencies from area-list construction.
4. Verify both selectors and address/GPS resolution against the migrated catalog and synthetic snapshots before enabling the new path in a deployment.
5. Rollback: deploy the prior app version and downgrade the new revision only if its downgrade safely removes catalog-only tables and restores old comparison keys from preserved labels. No outage/work rows or snapshots are deleted. Do not execute migrations as part of this proposal.

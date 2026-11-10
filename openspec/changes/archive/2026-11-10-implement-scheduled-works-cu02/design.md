# Design

## Context

CU01 is archived and provides the verified ENRE transport (`app/enre_client.py`),
normalization helpers (`app/enre_parser.normalized_key`), the GeoRef adapter
(`app/georef.py`), the versioned coverage catalog (`app/coverage.py`), the FastAPI
lifespan scheduler pattern and the public shell. U22 establishes the definitive CU02
scope: public consultation of the maintenance works ENRE reports for Edesur, reusing
those pieces without changing their contracts. See proposal.md - Why for motivation
and scope.

**Verified source contract (2026-11-10 live, plus archived captures 2019-2026):**
`cortesProgramados[]` rows carry `partido` (required), `localidad`,
`subestacion_alimentador`, `usuarios` (string, thousands may use a dot) and
`normalizacion` (string; `'Sin datos'`, an `H:MM` time, or a full
`YYYY-MM-DD HH:MM`). No row ever carried a start time, a reason, coordinates or an
identifier. The feed-level `ultimaActualizacion` (ART `H:MM`) is the source-reported
time. `cortesComunicados` was `[]` in every observed payload; its populated shape is
unverified. The feed has no ETag and only `Last-Modified` as an absolute timestamp.

## Goals / Non-Goals

**Goals:** public zone query of reported maintenance works; explicit provenance,
publication freshness and unpublished-field limits; independent persistence and
refresh; no change to CU01 behavior.

**Non-Goals:** date filters, upcoming/in-progress classification, planned start/end,
reasons, distance or coordinates, Edesur agenda, CU10 administration, coverage
expansion, deduplication.

## Decisions

### D1 - ENRE-only acquisition with a counted, unobserved collection

CU02 fetches `https://www.enre.gov.ar/paginacorte/js/data_EDS.js` through the
unchanged `enre_client.fetch_feed()`. `cortesProgramados` is required and must be a
list. `cortesComunicados` is optional: a missing or non-list value is recorded under
`unverified_collections`, and a non-empty list is recorded as
`comunicados_present: true` but its rows are neither normalized nor emitted. This
keeps the capability honest and makes future work observable without guessing a shape.

### Acquisition reuse (simplest maintainable option)

Evaluated two ways to share the ENRE polling with CU01:

- **Shared fetch, fan-out to both parsers.** Would need CU01's `refresh_once` to expose
  the raw body to CU02, coupling CU02's parse/schema failures to the CU01 refresh and
  requiring a change to `outage_store.py`. Rejected: it violates the "do not modify
  CU01" constraint and joins failure domains.
- **Independent refresh reusing the transport only.** CU02 runs its own scheduler task
  that calls the unchanged `fetch_feed()` and then its own parser, store and run
  history, under its own advisory lock. Chosen: transport reuse with independent
  parse/persist/error handling, matching D4. Cost is one extra ENRE request every five
  minutes (two total), acceptable for a public feed already fetched on that cadence.

`app/enre_client.py` is not modified; `scheduled_parser.py` contains its own
validators and imports only the deterministic `normalized_key` helper (already shared
by CU01's `coverage.py` and `outages_api.py`). That import is a pure, stable transform
and does not couple CU02's parse, persistence or error handling to CU01's.

### D2/D7 - Territory and coverage

The query requires `partido` and accepts an optional `localidad`, with the same
length/control-character validation and NFC/case-fold matching as CU01. Address and
device-location modes reuse the existing `POST /outages/resolve` and
`POST /outages/resolve-location` endpoints unchanged. Coverage uses `load_catalog()`
read-only: `covered`, `out_of_coverage` only for explicit entries, otherwise
`coverage_unverified`; no entry is added. `GET /scheduled-works/areas` returns catalog
entries plus localidades present in the current snapshot, with `reported` meaning
"has an informed work".

### D3 - No dated behavior (out of scope)

No `from`/`to` parameters, no ordering by an invented date, no
`upcoming`/`in_progress` label and no planned start/end. The API returns
`planned_start_at: null` and `planned_end_at: null` for every row because the source
does not publish them. `normalizacion` is stored as `restoration_estimate_text` after
NFC and whitespace normalization and is never parsed into an instant, even when it
contains a full date-time. The original dated proposal is preserved in U22 as
historical context; it is not a pending requirement of this capability.

### D4 - Independent persistence and refresh

Additive migration `0006_cu02`:

- `es_scheduled_snapshots`: `id`, `source`, `source_url`, `source_last_modified`,
  `source_reported_time`, `fetched_at`, `last_checked_at`, `content_sha256`,
  `is_current`, `row_counts` (JSON), `unverified_collections` (JSON),
  `comunicados_present` (boolean). Partial unique index on `WHERE is_current`.
- `es_scheduled_works`: `snapshot_id`, `category` (`maintenance` only), `partido`,
  `localidad`, `partido_key`, `localidad_key`, `subestacion_alimentador`,
  `affected_users`, `restoration_estimate_text`.
- `es_scheduled_fetch_runs`: `started_at`, `finished_at`,
  `outcome` (`ok|not_modified|http_error|tls_error|parse_error|schema_error|source_degraded|timeout|skipped_locked`;
  `source_degraded` is retained in the schema for compatibility but no longer emitted),
  `http_status`, `detail_code`, `content_sha256`.

Refresh runs every five minutes from the lifespan
(`SCHEDULED_WORKS_REFRESH_SECONDS`, `SCHEDULED_WORKS_SCHEDULER_ENABLED`), under a
dedicated-connection `pg_try_advisory_lock(0x43553032)` released in `finally`. A
loser records `skipped_locked`. An unchanged content hash records `not_modified` and
refreshes the source timestamps. A failure, timeout or unknown schema keeps the last
valid snapshot. The feed's current-outage totals are deliberately ignored, so a
sentinel in `totalUsuariosSinSuministro` cannot freeze CU02 or mark it degraded.
Retention keeps 24 snapshots including the current one and 30 days of runs. The
public `source_status` is `ok` only when the latest non-`skipped_locked` run is
`ok`/`not_modified`, otherwise `degraded`.

### D5/D6 - Only published fields, with provenance

Each work returns `category: "maintenance"`, `partido`, `localidad`,
`subestacion_alimentador`, `affected_users`, `restoration_estimate_text` and
`reason_text: null`. The response carries a `limitations` array:
`dates_not_published`, `reason_not_published`, `proximity_not_available`, and
`announced_works_not_displayed` (the last only when `cortesComunicados` is
non-empty). The UI renders "No publicado por la fuente" for a null reason and
"Hora estimada de normalización (informada por el ENRE)" for the published,
normalized text.
Rows are never deduplicated and affected users are never summed by zone; the feed's
official totals are not exposed because they describe current outages, not scheduled
works.

### D8 - Public view

Add a third shell view "Trabajos" next to "Cortes" and "Mi cuenta"; the default
remains "Mi cuenta" so CU09 end-to-end is unchanged. The panel has a partido
selector, an optional localidad selector, the normalized text filter, the address
search and the consented location button copied in behavior from CU01, and **no date
inputs**. It renders the states, provenance, coverage and limitations. The browser
calls only `/api/scheduled-works/*` plus the existing `/api/outages/resolve*`
endpoints; never ENRE or GeoRef directly.

### Normative states and freshness

State precedence: `out_of_coverage` -> `unavailable` -> `stale` ->
`works_reported` -> `no_works` -> `coverage_unverified`. An unresolved address or
position is an HTTP 422 from the shared resolve endpoints, not a result state.
Snapshot-based states return HTTP 200; `503` only for database unavailability; `422`
for invalid input. `no_works` requires a `covered` area and a fresh snapshot with
zero maintenance rows; with the current catalog that means a covered **localidad**,
because the catalog has no partido-level entries. A degraded source never yields
`no_works`.

Freshness is `fresh <= 15 min`, `stale <= 60 min`, `unavailable > 60 min` or no valid
snapshot, computed from `source_last_modified`. Freshness describes the
**publication**, not the validity of a work: it never implies that a work is
cancelled, finished or upcoming.

### Public API contract (sketch)

- `GET /scheduled-works/areas` -> `{ coverage_version, coverage_retrieved_on,
  areas: [{ partido, localidades: [{ localidad, coverage, reported }] }] }`.
- `GET /scheduled-works?partido=<required>&localidad=<optional>` ->
  `{ state, source_status, freshness, granularity, source, source_url, fetched_at,
  source_updated_at, source_reported_time, coverage: { partido, localidad, status },
  limitations: [...], works: [{ category, partido, localidad,
  subestacion_alimentador, affected_users, restoration_estimate_text, reason_text,
  planned_start_at, planned_end_at }] }`. The `works` array is `[]` only for
  `no_works` and omitted for `out_of_coverage` and `coverage_unverified`.

## Risks / Trade-offs

- [Out-of-scope items could be mistaken for pending work] -> explicit non-goals, U22,
  fiche note and no date UI.
- [Unobserved `cortesComunicados`] -> counted and hidden; a future capability would
  need a real capture.
- [Partial coverage catalog] -> unverified zones stay unverified; no negative invention.
- [Two ENRE fetches per cycle] -> accepted for an independent failure domain.
- [Publication age mistaken for event validity] -> UI copy and spec state the limit.
- [Shell change] -> additive third view, account default preserved, CU09 regression.

## Migration Plan

Additive `0006_cu02` only; no backfill and no change to CU01 tables. Rollback drops
the three tables and unregisters the router and view.

## Open Questions

None for the definitive scope. The unobserved `cortesComunicados` shape and the Edesur
agenda are operational facts outside this capability; enabling them would require a
new change with real evidence. No dated behavior is promised here.

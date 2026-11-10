# Spec Delta

## Purpose

Provide public, read-only queries for ENRE-reported scheduled maintenance works in a
zone, served from a cached snapshot with provenance, publication freshness,
three-valued coverage and explicit limits for fields the source does not publish.
This capability intentionally excludes a future agenda, date filters, planned
start/end, reasons and distance. They are **out of scope** for this capability; the
original proposal is preserved in the CU02 fiche, with the redefinition recorded in
U22, not as a pending requirement.

## ADDED Requirements

### Requirement: Query scheduled works without an account

The system SHALL allow a visitor to query reported scheduled works without signing in.
Trace: SR01, CU02-R1 (definitive scope, U22), D1.

#### Scenario: Visitor queries a known area
- **GIVEN** a fresh cached snapshot containing a maintenance work for partido "ALMIRANTE BROWN" and localidad "GLEW"
- **WHEN** a visitor queries that partido and localidad without an account
- **THEN** the matching work, its source and its update date are visible

### Requirement: Accept a partido with an optional localidad

A query SHALL require a partido and SHALL accept an optional localidad. A localidad
without a partido SHALL be rejected, values over 120 characters or containing control
characters SHALL be rejected, and the response SHALL state the granularity actually
matched. Trace: D2, D7, AGENTS.md.

#### Scenario: Localidad requires a partido
- **GIVEN** a request that supplies a localidad but no partido
- **WHEN** the request is made
- **THEN** it is rejected with HTTP 422 and no work list is returned

#### Scenario: Overlong input is rejected
- **GIVEN** a partido value longer than 120 characters
- **WHEN** the query is made
- **THEN** the request is rejected and no snapshot lookup is performed

### Requirement: Match queries by normalized names

The system SHALL compare partido and localidad after NFC normalization, case folding
and trimming, and SHALL preserve the original labels in the response. Trace: D2.

#### Scenario: Case differences still match
- **GIVEN** a snapshot row with partido "SAN VICENTE"
- **WHEN** a visitor queries partido "san vicente"
- **THEN** the row matches and the response preserves the original "SAN VICENTE" label

### Requirement: Serve queries from the cached snapshot

The system SHALL serve scheduled-work queries from the persisted snapshot and SHALL
NOT call the ENRE endpoint at query time. Trace: D4, SR03.

#### Scenario: Source unavailable but cache is served
- **GIVEN** a valid cached snapshot and an unreachable ENRE endpoint
- **WHEN** a visitor queries an area
- **THEN** the cached snapshot is returned with its provenance and a freshness that reflects the stale source

### Requirement: Publish only fields the source provides

The result SHALL expose `planned_start_at` and `planned_end_at` as null, and
`reason_text` as null when the source does not publish a reason. The response SHALL
carry a `limitations` array that includes `dates_not_published`,
`reason_not_published` and `proximity_not_available`. Trace: D3, D5, SR03.

#### Scenario: Missing dates are not fabricated
- **GIVEN** a work whose only temporal value is `normalizacion: 'Sin datos'`
- **WHEN** the work is returned
- **THEN** both planned instants are null and the `dates_not_published` limitation is present

#### Scenario: Restoration estimate is not a planned end
- **GIVEN** a work whose `normalizacion` is the text `2026-01-14 15:33`
- **WHEN** the work is returned
- **THEN** `restoration_estimate_text` is that published text after NFC and whitespace normalization and `planned_end_at` remains null

### Requirement: Include source provenance and publication freshness

Every result SHALL include the source name, source URL, UTC fetch time, the source
update time derived from `Last-Modified` when present (nullable), the reported time,
the freshness class and `source_status`. Trace: SR03, D4.

#### Scenario: Provenance is visible
- **GIVEN** a valid snapshot acquired from the ENRE feed
- **WHEN** an area is queried
- **THEN** the result shows the ENRE source, the feed URL, the UTC fetch time, the source update time, the freshness class and the source status

### Requirement: Classify freshness without inferring event validity

The system SHALL classify freshness as `fresh` when the source update time is at most
15 minutes old, `stale` when older than 15 but at most 60 minutes, and `unavailable`
when older than 60 minutes, when no valid snapshot exists, or when the source
timestamp cannot be determined. Freshness SHALL NOT assert that a work is cancelled,
completed or upcoming. Trace: D3, D5.

#### Scenario: Stale publication is not a cancellation
- **GIVEN** a snapshot whose source update time is 30 minutes old
- **WHEN** a work is returned
- **THEN** freshness is `stale`, the work is still shown and no temporal state is asserted

#### Scenario: Missing source timestamp is not invented
- **GIVEN** a source response without a usable `Last-Modified` header
- **WHEN** the snapshot is stored
- **THEN** the snapshot is classified `unavailable` and no source update time is fabricated

### Requirement: Return a normative result state

Every result SHALL expose exactly one state in precedence order: `out_of_coverage`,
`unavailable`, `stale`, `works_reported`, `no_works`, `coverage_unverified`.
Snapshot-based states SHALL return HTTP 200, `works: []` SHALL accompany only
`no_works`, `503` SHALL be reserved for database unavailability, and an unresolved
zone SHALL be HTTP 422 before a result state. Trace: D4, D5, D7.

#### Scenario: No works only with a fresh covered localidad
- **GIVEN** a fresh snapshot, covered localidad "BERAZATEGUI" and no maintenance rows
- **WHEN** the area is queried
- **THEN** the state is `no_works` with an empty `works` array

#### Scenario: Unverified coverage is not empty
- **GIVEN** a fresh snapshot with no rows for an area absent from the coverage catalog
- **WHEN** the area is queried
- **THEN** the state is `coverage_unverified` and the `works` array is omitted

### Requirement: Preserve the last valid snapshot across failures

The system SHALL retain the last valid snapshot when a refresh fails, times out or
yields an unknown schema, and SHALL NOT replace it with an empty list. A degraded
CU02 acquisition SHALL be exposed as `source_status: degraded` and SHALL never
produce `no_works`. The feed's current-outage totals SHALL NOT change CU02 freshness
or source status. Trace: D4, SR03.

#### Scenario: Failed refresh keeps the snapshot
- **GIVEN** a valid snapshot and a subsequent refresh that fails
- **WHEN** an area is queried
- **THEN** the previous snapshot is served and the result is not shown as `no_works`

#### Scenario: Sentinel totals do not freeze works
- **GIVEN** a payload whose `totalUsuariosSinSuministro` is "N/A" and whose `cortesProgramados` is valid
- **WHEN** the refresh runs
- **THEN** the works are stored and the acquisition is not marked degraded

### Requirement: Emit only maintenance works and never invent announced works

The system SHALL emit rows only from `cortesProgramados` with category `maintenance`.
It SHALL count `cortesComunicados` and record whether it is present, but SHALL NOT
emit its rows while no populated shape has been observed, and SHALL expose
`announced_works_not_displayed` when the collection is non-empty. Rows SHALL NOT be
deduplicated and affected users SHALL NOT be summed by zone. Trace: D1, D6, U22.

#### Scenario: Empty comunicados costs nothing
- **GIVEN** a payload with `cortesComunicados: []`
- **WHEN** the snapshot is stored
- **THEN** the maintenance works are persisted and the `announced_works_not_displayed` limitation is absent

#### Scenario: Populated comunicados are not guessed
- **GIVEN** a payload with an unexpected non-empty `cortesComunicados`
- **WHEN** the snapshot is stored
- **THEN** the maintenance works are still stored, `comunicados_present` is recorded and the `announced_works_not_displayed` limitation is exposed while its rows are not emitted

### Requirement: Classify coverage in three values with a read-only catalog

The system SHALL classify a zone as `covered`, `out_of_coverage` or
`coverage_unverified` using the CU01 coverage catalog without adding entries; absence
from the catalog SHALL be `coverage_unverified`, never `out_of_coverage`. Trace: D7.

#### Scenario: Unknown area is not reported as clear
- **GIVEN** a fresh snapshot with no rows for an area absent from the coverage catalog
- **WHEN** the area is queried
- **THEN** the state is `coverage_unverified` and the result does not report "no works"

### Requirement: Refresh periodically with an independent lock

The system SHALL refresh about every five minutes under a CU02-specific PostgreSQL
advisory lock, SHALL record `skipped_locked` when it cannot acquire the lock, and SHALL
keep its own snapshot and run history separate from CU01. Trace: D4.

#### Scenario: Concurrent refresh writes once
- **GIVEN** two simultaneous CU02 refresh attempts
- **WHEN** the periodic refresh runs
- **THEN** one refresh persists a snapshot and the other records a `skipped_locked` run and writes no snapshot

### Requirement: Provide an independent public view without date filters

The system SHALL expose a public "Trabajos" view that reuses the shell, shows
partido/localidad selection, provenance, coverage and limitations, offers no date
input, and calls only the application API. Trace: D8, D2.

#### Scenario: Visitor sees the definitive scope
- **GIVEN** a visitor without a session
- **WHEN** the "Trabajos" view is opened
- **THEN** the panel shows reported works with "No publicado por la fuente" for the reason and no date filter

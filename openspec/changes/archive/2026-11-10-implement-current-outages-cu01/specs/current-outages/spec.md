# Spec Delta

## Purpose

Provide public, read-only queries for ENRE-reported current Edesur electricity outages in a zone, served from a cached snapshot with source provenance, freshness, verifiable coverage and geographic-coverage limits.

## ADDED Requirements

### Requirement: Query current outages without an account
The system SHALL allow a visitor to query currently reported outages without signing in. Trace: SR01, CU01-R1, D11.

#### Scenario: Visitor queries a known area
- **GIVEN** a fresh cached snapshot containing a reported outage for partido "LOMAS DE ZAMORA" and localidad "BANFIELD"
- **WHEN** a visitor queries that partido and localidad without an account
- **THEN** the matching reported outage, its source and its update date are visible

### Requirement: Accept a partido with an optional localidad
A query SHALL require a partido and SHALL accept an optional localidad; a localidad without a partido SHALL be rejected, and the response SHALL state the granularity actually matched. Trace: D2, T1.

#### Scenario: Partido-only query
- **GIVEN** a fresh snapshot with rows for localidades "BANFIELD" and "TEMPERLEY" under partido "LOMAS DE ZAMORA"
- **WHEN** a visitor queries only the partido
- **THEN** both localidades' rows are returned labelled as a partido-level match, without summing them

#### Scenario: Localidad requires a partido
- **GIVEN** a query that supplies a localidad but no partido
- **WHEN** the request is made
- **THEN** the request is rejected and no outage list is returned

### Requirement: Match queries by normalized names
The system SHALL compare partido and localidad after NFC normalization, case folding and trimming, and SHALL preserve the original labels in the response. Trace: D2, T1.

#### Scenario: Case differences still match
- **GIVEN** a snapshot row with partido "LOMAS DE ZAMORA"
- **WHEN** a visitor queries partido "lomas de zamora"
- **THEN** the row matches and the response preserves the original "LOMAS DE ZAMORA" label

### Requirement: Serve outage queries from the cached snapshot
The system SHALL serve outage queries from the persisted snapshot and SHALL NOT call the ENRE endpoint at query time. Trace: D5, D6, SR03.

#### Scenario: Source unavailable but cache is served
- **GIVEN** a valid cached snapshot exists and the ENRE endpoint is unreachable
- **WHEN** a visitor queries an area
- **THEN** the cached snapshot is returned with its provenance and a freshness that reflects the stale source

### Requirement: Include source provenance in every result
Every successful outage result SHALL include the source name, source URL, UTC fetch time, the source update time derived from `Last-Modified` when present (nullable), the optional reported time, the freshness class and the `source_status`. Trace: SR03, D5, D8.

#### Scenario: Provenance is visible
- **GIVEN** a valid snapshot acquired from the ENRE feed
- **WHEN** a visitor queries an area
- **THEN** the result shows the ENRE source, the feed URL, the UTC fetch time, the source update time, the freshness class and the source status

### Requirement: Classify snapshot freshness by age
The system SHALL classify a snapshot as fresh when its source update time is at most 15 minutes old, stale when older than 15 minutes but at most 60 minutes, and unavailable when older than 60 minutes, when no valid snapshot exists, or when the source timestamp cannot be determined. Trace: D8.

#### Scenario: Age thresholds
- **GIVEN** a snapshot whose source update time is 10 minutes old, then 30 minutes old, then 90 minutes old
- **WHEN** an area is queried
- **THEN** the freshness is respectively fresh, stale and unavailable

#### Scenario: Missing source timestamp is not invented
- **GIVEN** a source response without a usable `Last-Modified` header
- **WHEN** the snapshot is stored
- **THEN** the snapshot is classified unavailable and no source update time is fabricated

### Requirement: Return a normative result state
Every outage result SHALL expose exactly one state — `geographic_error`, `out_of_coverage`, `unavailable`, `stale`, `reported`, `no_reports` or `coverage_unverified` — in that precedence order, plus `source_status` (`ok|degraded`). Snapshot-based states SHALL return HTTP 200. The `outages` array SHALL be `[]` only for `no_reports` and omitted for `geographic_error`, `out_of_coverage` and `coverage_unverified`. Trace: D11, D8.

#### Scenario: Stale and unavailable are distinct
- **GIVEN** a stale snapshot and, separately, no valid snapshot
- **WHEN** an area is queried in each case
- **THEN** the system returns the stale state in the first case and the unavailable state in the second, both with HTTP 200

#### Scenario: Reported rows are shown even when coverage is unverified
- **GIVEN** a fresh snapshot with a reported outage for an area absent from the coverage catalog
- **WHEN** the area is queried
- **THEN** the state is `reported` and the rows are visible, with the coverage marked `coverage_unverified`

#### Scenario: Unresolved zone is a geographic error
- **GIVEN** an address or position that GeoRef cannot resolve
- **WHEN** the zone is resolved
- **THEN** the result is `geographic_error` with HTTP 422 and no outage list

#### Scenario: Database unavailable is an error, not a state
- **GIVEN** the snapshot store cannot be read
- **WHEN** an area is queried
- **THEN** the system returns HTTP 503 without inventing a state

### Requirement: Preserve the last valid snapshot across failures
The system SHALL retain the last valid snapshot when a refresh fails, times out, or yields an unknown schema, and SHALL NOT replace it with an empty list. Trace: D5, D8, SR03.

#### Scenario: Failed refresh keeps the snapshot
- **GIVEN** a valid snapshot and a subsequent refresh that fails
- **WHEN** an area is queried
- **THEN** the previous snapshot is still served and is not shown as an empty result

### Requirement: Treat a degraded source as degraded
The system SHALL treat a source response that signals "not updating" (for example an "N/A" total) as a degraded source, keep the last valid snapshot, expose `source_status: degraded` and never present it as no outages. Trace: D8, SR03.

#### Scenario: N/A total does not become an empty result
- **GIVEN** a valid snapshot followed by a feed response whose total users without supply is "N/A"
- **WHEN** the feed is refreshed and an area is queried
- **THEN** the last valid snapshot is retained, `source_status` is degraded, and the result is not shown as no reports

### Requirement: Show only current-outage categories
The system SHALL return only the `medium_voltage`, `low_voltage` and `preventive` categories, and SHALL NOT return programmed or comunicado records, which are outside CU01. Trace: D3.

#### Scenario: Programmed records are excluded
- **GIVEN** a snapshot containing medium-voltage, low-voltage and programmed records
- **WHEN** an area is queried
- **THEN** the medium-voltage and low-voltage records are returned and the programmed records are excluded

### Requirement: Present official totals with distributor-wide scope
The system SHALL present the official totals labelled as distributor-wide and SHALL present each record's affected-user figure as published, without summing records by locality or deduplicating via unverified heuristics. Trace: D10.

#### Scenario: Totals are not local
- **GIVEN** a snapshot with an official total and per-record affected-user figures
- **WHEN** a locality is queried
- **THEN** the total is labelled distributor-wide and each record's figure is shown as-is

### Requirement: Never infer supply from absence of reports
The system SHALL NOT present an empty result as a guarantee of supply, and SHALL return `no_reports` only for a covered area with a fresh valid snapshot lacking records. Trace: CU01-R2, SR03.

#### Scenario: Empty only with a fresh, covered snapshot
- **GIVEN** a fresh valid snapshot, a covered area and no records for that area
- **WHEN** the area is queried
- **THEN** the system reports no outages for that area without claiming uninterrupted supply

### Requirement: Limit matching to zone granularity
The system SHALL match outages at partido and localidad granularity only and SHALL NOT assert supply status for an individual address or meter. Trace: CU01-R2, D2.

#### Scenario: Zone-level result is not address-level
- **GIVEN** a reported outage for a locality
- **WHEN** a visitor queries that locality
- **THEN** the system reports the zone-level outage and does not state that any individual address has or lacks power

### Requirement: Resolve an address to a zone via GeoRef
The system SHALL resolve an address through a backend GeoRef adapter scoped to Buenos Aires or CABA, SHALL present multiple candidates for selection when the address is ambiguous, SHALL degrade to a partido-level match when no localidad is resolved, and SHALL return `geographic_error` on failure. Trace: D2, T1.

#### Scenario: Address resolves to its locality
- **GIVEN** an address that GeoRef resolves to partido "Lomas de Zamora" and localidad "Banfield"
- **WHEN** the actor queries that address
- **THEN** the system queries the Banfield zone and presents the result as a zone match

#### Scenario: Ambiguous address is not guessed
- **GIVEN** an address that GeoRef resolves to more than one candidate
- **WHEN** the actor queries that address
- **THEN** the system asks the actor to select a candidate and does not query an outage area until one is chosen

#### Scenario: Throttled resolution asks to retry
- **GIVEN** an actor exceeding the resolve rate limit
- **WHEN** a resolution is requested
- **THEN** the system returns 429 with `Retry-After`, does not call GeoRef, and the UI shows a retry message

### Requirement: Resolve device location with consent
When an actor explicitly grants location, the system SHALL reverse-geocode the position through the backend to a partido (and a localidad only when the geocoder returns one), SHALL query that zone, and SHALL NOT persist or log the personal coordinates. Trace: D9, T1.

#### Scenario: Location resolves to a partido
- **GIVEN** a consented position that reverse-geocodes to partido "Lomas de Zamora" with no localidad
- **WHEN** the actor queries by device location
- **THEN** the system queries that partido at partido-level granularity and stores no coordinates

#### Scenario: Denied consent does not trigger a fallback query
- **GIVEN** an actor who denies the location permission
- **WHEN** the location mode is used
- **THEN** the system performs no location query, does not repeat the permission request, and offers the other query modes

### Requirement: Classify coverage in three values
The system SHALL classify a zone as `covered`, `out_of_coverage` or `coverage_unverified` using a versioned coverage catalog with documented provenance and verification date; a zone absent from the catalog SHALL be `coverage_unverified`, never `out_of_coverage`. Trace: D4, T2.

#### Scenario: Unknown area is not reported as clear
- **GIVEN** a fresh snapshot with no rows for an area absent from the coverage catalog
- **WHEN** the area is queried
- **THEN** the system returns `coverage_unverified` and does not report "no outages"

#### Scenario: Areas list is independent of reports
- **GIVEN** a coverage catalog and a snapshot with no records for a covered locality
- **WHEN** the areas list is requested
- **THEN** the covered locality is still selectable and, when queried, returns `no_reports`

### Requirement: Validate query inputs
The system SHALL validate inputs for length and allowed characters: partido and localidad SHALL be at most 120 characters, an address SHALL be at most 300 characters, and control characters SHALL be rejected without querying the source. Trace: AGENTS.md, D11.

#### Scenario: Overlong input is rejected
- **GIVEN** a partido value longer than 120 characters
- **WHEN** the query is made
- **THEN** the request is rejected with a validation error and no snapshot lookup is performed

### Requirement: Refresh the snapshot periodically without concurrent runs
The system SHALL refresh the snapshot about every five minutes and SHALL prevent simultaneous refreshes, recording `skipped_locked` for a refresh that cannot acquire the lock. Trace: D5, D6.

#### Scenario: Concurrent refresh writes once
- **GIVEN** two refresh attempts start at the same time
- **WHEN** the periodic refresh runs
- **THEN** one refresh persists a snapshot and the other records a `skipped_locked` run and writes no snapshot

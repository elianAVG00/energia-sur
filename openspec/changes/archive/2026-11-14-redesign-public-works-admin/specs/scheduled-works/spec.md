# Spec Delta

## MODIFIED Requirements

### Requirement: Provide an independent public view without date filters

The system SHALL expose a public "Trabajos" view inside the shared shell with labelled partido/localidad selection, address and device-location assistance, explicit initial, loading, empty, error, stale, unavailable, degraded and coverage states, provenance, coverage and limitations. It SHALL offer no date input or temporal filter, SHALL identify planned start/end as not published, and SHALL keep the works table and controls usable at narrow widths. Trace: D8, D2, D3, U22.

#### Scenario: Visitor sees the definitive scope

- **GIVEN** a visitor without a session
- **WHEN** the "Trabajos" view is opened
- **THEN** the panel shows reported works with "No publicado por la fuente" for the reason and no date filter

#### Scenario: Search and address assistance are separate

- **GIVEN** a visitor opens the "Trabajos" view
- **WHEN** the view renders
- **THEN** a "Consultar trabajos" card exposes the zone filter, partido, optional localidad, "Consultar trabajos" and "Usar mi ubicación"
- **AND** a "Buscar por dirección" card exposes the address field, "Buscar dirección", the privacy note and any candidate zones

#### Scenario: Unpublished dates and reasons stay explicit

- **GIVEN** a works result whose source does not publish planned dates or a reason
- **WHEN** the result is rendered
- **THEN** planned start and end are shown as not published and the reason shows "No publicado por la fuente"
- **AND** no date is invented and no date input or Desde/Hasta filter is rendered

#### Scenario: State, coverage and provenance stay distinguishable

- **GIVEN** a result that is stale, degraded or has unverified coverage
- **WHEN** the result is rendered
- **THEN** granularity, coverage, freshness and source status are presented as distinct labels
- **AND** the works are not hidden and no absence of works is asserted

#### Scenario: Narrow viewport keeps works usable

- **GIVEN** a viewport of 390, 820 or 1440 px
- **WHEN** the works view and its result are rendered
- **THEN** the page has no horizontal scrollbar and the works table scrolls inside its own accessible region
- **AND** the search, address and result controls remain reachable by keyboard

# territorial-catalog Specification

## Purpose

Provide one persistent, provenance-bearing territorial catalog for the CU01 and CU02 public selectors. The catalog distinguishes official geographic identity from evidence that Edesur serves an individual locality.

## Requirements

### Requirement: Restrict the selector catalog to the approved Buenos Aires partidos
The shared catalog SHALL contain the twelve partidos in the approved Edesur concession list and SHALL exclude CABA/CAPITAL from CU01 and CU02 selectors.

#### Scenario: Selectors use the approved party set
- **WHEN** either public area list is requested
- **THEN** it contains Almirante Brown, Avellaneda, Berazategui, Cañuelas, Esteban Echeverría, Ezeiza, Florencio Varela, Lanús, Lomas de Zamora, Presidente Perón, Quilmes and San Vicente, and contains no CABA/CAPITAL option

### Requirement: Persist one shared catalog independently of ENRE snapshots
The system SHALL serve CU01 and CU02 party/locality options from the same persistent catalog, regardless of outage or scheduled-work snapshot contents.

#### Scenario: Both selectors have identical territorial options
- **WHEN** CU01 and CU02 area lists are requested with different ENRE snapshots or with no report rows
- **THEN** both responses expose the same party/locality hierarchy and labels

### Requirement: Preserve GeoRef identity and distinguish locality from service coverage
Catalog localities SHALL retain their GeoRef identifiers, canonical names, categories and source provenance. A locality's presence in GeoRef SHALL NOT by itself assert that Edesur serves that locality.

#### Scenario: GeoRef locality is not individual coverage evidence
- **GIVEN** a GeoRef locality is in the shared selector catalog without separate locality-level service evidence
- **WHEN** its coverage is presented or used to determine an empty-query result
- **THEN** the system does not treat GeoRef membership alone as verified Edesur coverage

### Requirement: Deduplicate displayed locality names only within a partido
The system SHALL expose one selector option for duplicate canonical locality names within the same partido while retaining the source identifiers and categories, and SHALL preserve homonymous locality options belonging to different partidos.

#### Scenario: Duplicate source records within a party
- **GIVEN** GeoRef returns the same canonical locality name more than once within one partido under different identifiers or categories
- **WHEN** the selector options are constructed
- **THEN** the name appears once for that partido and all contributing GeoRef identifiers and categories remain available as catalog provenance

#### Scenario: Homonymous localities in different parties
- **GIVEN** GeoRef returns the name "Gerli" or "Canning" for more than one partido
- **WHEN** the selector options are constructed
- **THEN** each occurrence remains selectable under its own partido

### Requirement: Resolve only verified source-name equivalences
The system SHALL map an ENRE party or locality label to a canonical catalog entry only through a verified equivalence or an unambiguous normalized-name match, and SHALL preserve the original ENRE label in reported records.

#### Scenario: Verified spelling or abbreviation variant
- **GIVEN** an ENRE label has a documented equivalence to a GeoRef catalog entry
- **WHEN** a selector-originated or geographic-resolution query is matched to ENRE rows
- **THEN** the row is found through that equivalence while the response retains the original ENRE label

#### Scenario: No guessed equivalence
- **GIVEN** an observed ENRE locality such as "Santa Anita" or "Zona Rural" has no verified GeoRef equivalence
- **WHEN** catalog equivalences are loaded
- **THEN** no canonical GeoRef locality is assigned to it and the observed unresolved value remains documented

### Requirement: Review exceptional GeoRef entries before selector inclusion
The system SHALL assess unusual GeoRef records for selector usefulness without excluding records solely by category, and SHALL record the rationale for any record excluded from user-facing options.

#### Scenario: Unusual geographic record is reviewed
- **GIVEN** a GeoRef result is an unusual record such as "Área Reserva Cinturón Ecológico"
- **WHEN** the seed's selector entries are approved
- **THEN** the record is included or excluded based on a documented usefulness review rather than an automatic category filter

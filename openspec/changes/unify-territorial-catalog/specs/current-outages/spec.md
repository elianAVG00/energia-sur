# Spec Delta

## ADDED Requirements

### Requirement: Keep the CU01 area selector independent of outage reports
The CU01 area list SHALL be built from the shared persistent territorial catalog and SHALL not add, remove or rename party/locality options according to current or historical outage snapshots.

#### Scenario: Outage snapshot is empty
- **GIVEN** the shared catalog is seeded and the current outage snapshot has no rows
- **WHEN** a visitor opens the CU01 area selector
- **THEN** the same approved parties and localities remain selectable as when outage rows exist

### Requirement: Describe an empty outage query without implying uninterrupted supply
When no matching outage row is returned, CU01 SHALL describe the absence as no matching report in the latest available snapshot, identify its freshness or unavailability, and SHALL NOT guarantee that there is no interruption.

#### Scenario: Fresh snapshot has no matching row
- **GIVEN** a query for a catalog party or locality has no matching row in a fresh snapshot
- **WHEN** CU01 presents the query result
- **THEN** it says no matching outage was reported in the latest update and does not claim uninterrupted supply

#### Scenario: No row in a stale or unavailable snapshot
- **GIVEN** a query has no matching row and the latest snapshot is stale or unavailable
- **WHEN** CU01 presents the query result
- **THEN** it preserves the stale or unavailable state and does not describe the area as having no outage

### Requirement: Match canonical selector zones to verified ENRE name variants
CU01 SHALL resolve party and locality values selected from the shared catalog to matching ENRE snapshot rows through verified equivalences while preserving source labels in returned outage records.

#### Scenario: Catalog name differs from ENRE spelling
- **GIVEN** a catalog locality has a verified ENRE equivalence for spelling, accent or abbreviation
- **WHEN** a visitor queries that catalog locality
- **THEN** matching outage rows are returned using the unchanged ENRE party and locality labels

#### Scenario: Unresolved ENRE locality is not guessed
- **GIVEN** an outage row contains an observed locality with no verified catalog equivalence
- **WHEN** a visitor queries its party or the exact observed locality
- **THEN** party-level results remain available and the locality is not silently mapped to a different catalog locality

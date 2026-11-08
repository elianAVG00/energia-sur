# account-domiciles Specification

## Purpose

Provide the smallest account-owned domicile registration and selection capability
needed for CU09 without implementing CU04's full address and meter management.

## Requirements

### Requirement: Register and select an own-account domicile for CU09

The system SHALL support registering, listing and selecting a domicile associated
with the authenticated account for CU09. Domiciles SHALL have a stable reference
and display address. No meter SHALL be required for this diary prerequisite.

#### Scenario: AD-S01 Own domicile prerequisite without a meter
- **GIVEN** an authenticated account with no registered domicile
- **WHEN** it registers a domicile using the accepted input contract and selects it
- **THEN** that domicile is available for its CU09 records without registering a meter

#### Scenario: AD-S02 List only the acting account's registered domiciles
- **GIVEN** accounts A and B have separately registered domiciles D and E
- **WHEN** A requests its selectable domiciles
- **THEN** D is available and B's E is not exposed or selectable as A's domicile

### Requirement: A saved cut requires a registered own-account domicile

The system SHALL NOT save a CU09 cut without selecting a domicile registered in
the authenticated account. Selecting another account's domicile SHALL NOT bypass
this requirement.

#### Scenario: CU09-S03 Missing or foreign domicile cannot save
- **GIVEN** A has registered D and B has registered E
- **WHEN** A saves a valid cut with D, with no domicile, or with E
- **THEN** only the D case satisfies the domicile precondition and can save; the other two do not save

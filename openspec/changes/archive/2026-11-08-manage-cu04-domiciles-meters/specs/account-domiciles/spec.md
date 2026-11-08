# Spec Delta

## ADDED Requirements

### Requirement: Correct an owned domicile without moving history
The owner SHALL correct a domicile using an atomic version-qualified write, preserving ID, owner and linked interruptions. Every success, including unchanged input, increments the version exactly once and returns it. A stale version SHALL return 409 `VERSION_CONFLICT` without mutation. Future PDFs use the current address. Trace: CU04-S02, Q09, U12.

#### Scenario: Address correction preserves CU09 history
- **GIVEN** A owns domicile D with a saved cut and address `Old address`
- **WHEN** A corrects the address to `New address` with the current version and later exports the cut
- **THEN** D and the cut keep their IDs and association, and the newly generated PDF displays `New address`

#### Scenario: Stale correction
- **GIVEN** an owned domicile at version 1 has been successfully corrected to version 2
- **WHEN** the owner submits a correction based on version 1
- **THEN** the request returns 409 and the current address and version remain unchanged

#### Scenario: Changed and unchanged current versions
- **GIVEN** an owned domicile at version 1
- **WHEN** the owner changes its address with version 1, then sends the same address with version 2
- **THEN** the responses succeed with versions 2 and 3 respectively, each incrementing exactly once

#### Scenario: Stale unchanged address cannot overwrite a concurrent edit
- **GIVEN** an owner reads address X at version 1 and another request changes it to Y at version 2
- **WHEN** the owner submits X and version 1
- **THEN** the request returns 409 `VERSION_CONFLICT`, and Y and version 2 remain unchanged

#### Scenario: Competing domicile corrections
- **GIVEN** two independent requests with the same current domicile version
- **WHEN** they perform PATCH concurrently
- **THEN** exactly one succeeds with the incremented version and the other returns 409 `VERSION_CONFLICT`, without lost updates

#### Scenario: Foreign missing and failed domicile writes
- **GIVEN** an unrelated account, a missing domicile and an owned domicile
- **WHEN** that account patches the foreign or missing domicile, or an owned correction fails during writing
- **THEN** both foreign and missing requests return indistinguishable 404 without disclosure, and the failed write leaves address and version unchanged

### Requirement: Preserve duplicate domicile registration
The system SHALL continue to permit duplicate display addresses, including within one account. The UI SHALL warn on an exact match after trimming against a loaded address in the same account, without blocking creation or correction. No legal-address validation is implied. Trace: Q08.

#### Scenario: Duplicate warning is nonblocking
- **GIVEN** A has an existing domicile with display address `Example 1`
- **WHEN** A enters ` Example 1 ` in a new domicile form
- **THEN** the interface warns and A can still create a separate domicile with a distinct ID

### Requirement: Protect domicile management
Only the owning account SHALL consult editable domicile details or correct them. An absent or foreign domicile SHALL return the same 404 without disclosure. The existing opaque session SHALL be required, and authenticated writes SHALL require trusted Origin and session CSRF. Trace: SR02, Q03.

#### Scenario: Foreign domicile correction and security checks
- **GIVEN** A owns D and B is another account
- **WHEN** B reads editable details or attempts to correct D
- **THEN** each request returns 404 and D remains unchanged
- **WHEN** A attempts a correction with invalid CSRF or untrusted Origin
- **THEN** the request returns 403 and D and its version remain unchanged

### Requirement: Preserve existing domicile API and lifecycle
Existing domicile registration and listing contracts SHALL remain compatible, including meter-free use and stable IDs. This change SHALL NOT offer domicile deletion, transfer or merging. Trace: AD-S01, AD-S02, CU09-S03, Q09.

#### Scenario: Existing client and domicile survive migration
- **GIVEN** an existing account with a domicile and linked CU09 cuts
- **WHEN** the additive migration is applied and the existing client lists and selects that domicile without a meter
- **THEN** its existing response fields, ID, cuts and owner remain available without requiring a meter or changing the client payload

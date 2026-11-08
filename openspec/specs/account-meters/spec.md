# account-meters Specification

## Purpose

Enable account holders to register, consult and correct their own domiciles' meters without exposing other accounts' personal records.

## Requirements

### Requirement: Register and list meters for an owned domicile
The system SHALL allow the owner of a domicile to register and list zero or more meters for it. Each meter SHALL have a stable ID, exactly one domicile, a meter number and an optional alias. Registering a domicile or using CU09 SHALL NOT require a meter. Trace: CU04-S01, Q08.

#### Scenario: Register and list two meters
- **GIVEN** account A owns domicile D with no meters
- **WHEN** A registers two distinct valid meter numbers on D and lists its meters
- **THEN** both meters appear with distinct stable IDs and domicile D, and D remains usable without any meter before registration

### Requirement: Validate meter input
The system SHALL reject non-ASCII and controls in meter numbers, trim ASCII spaces at the ends, require 1–120 printable ASCII characters after trimming, and preserve leading zeros, internal spaces and punctuation. Alias SHALL be null or trimmed text up to 120 characters, allowing Spanish accents but rejecting NUL and controls; blank becomes null. Invalid input SHALL return 422 without mutation. Trace: U12.

#### Scenario: Preserve a valid identifier and optional alias
- **WHEN** the owner submits number `  001-Ab  ` and a blank alias
- **THEN** the stored number is `001-Ab`, the alias is null and the leading zeros and hyphen are retained

#### Scenario: Reject invalid number or alias
- **WHEN** the owner submits a blank or over-120-character number, a number containing NUL, control or non-ASCII text, or an alias over 120 characters or containing NUL or a control
- **THEN** the request returns 422 and no meter is created or changed

#### Scenario: Spanish alias does not affect uniqueness
- **WHEN** the owner registers number `001` with alias ` Medidor eléctrico `
- **THEN** the stored alias is `Medidor eléctrico`, and it does not determine meter uniqueness

### Requirement: Enforce account-scoped meter number uniqueness
The system SHALL reject a meter number already registered to the same account after ASCII-space trim and ASCII lowercase comparison, including across domiciles and concurrent writes. It SHALL permit the same number on another account without exposing that account's data. A duplicate write SHALL return 409 with `code: DUPLICATE_METER` without mutation. Trace: Q08, U12.

#### Scenario: Duplicates across owned domiciles
- **GIVEN** A owns domiciles D and E and D has meter `Ab-01`
- **WHEN** A registers ` ab-01 ` on E or changes another meter to that number
- **THEN** each request returns 409 without changing existing data

#### Scenario: Independent accounts and concurrent writes
- **GIVEN** A and B are unrelated and A has meter `X01`
- **WHEN** B registers `x01` and two simultaneous A requests each register a previously unused `Y02`
- **THEN** B succeeds without learning A's records and exactly one of A's concurrent requests succeeds while the other receives 409

### Requirement: Owner-only meter access and mutation
Meter operations SHALL require the existing authenticated session and enforce ownership through the meter's domicile. An absent, foreign or mismatched domicile or meter SHALL return the same 404 without disclosure. Authenticated writes SHALL require trusted Origin and session CSRF, returning 403 when either is invalid. Trace: SR02, Q03.

#### Scenario: Foreign and mismatched resources
- **GIVEN** A owns D and its meter M, and B owns E
- **WHEN** B lists or creates under D, or reads or corrects M under D or E
- **THEN** each request returns 404 without meter data or mutation

#### Scenario: Reject missing CSRF or untrusted Origin
- **GIVEN** an authenticated owner and an owned domicile and meter
- **WHEN** meter creation or correction is requested with a missing or invalid CSRF token or an untrusted Origin
- **THEN** the request returns 403 and all meter records and versions remain unchanged

### Requirement: Correct a meter without changing its identity
The owner SHALL correct number and alias using an atomic version-qualified write, preserving ID and domicile. Every success, including unchanged input, increments the version exactly once and returns it. A stale version SHALL return 409 `VERSION_CONFLICT` without mutation. No deletion, transfer or physical replacement is offered. Trace: CU04-S02, Q09, U12.

#### Scenario: Correct data and reject stale edits
- **GIVEN** an owned meter at version 1
- **WHEN** the owner corrects its number or alias at version 1 and then submits another correction based on version 1
- **THEN** the first correction preserves the ID and domicile and advances the version; the second returns 409 without overwriting it

#### Scenario: Changed and unchanged current versions
- **GIVEN** an owned meter at version 1
- **WHEN** the owner changes its alias with version 1, then sends the same number and alias with version 2
- **THEN** the responses succeed with versions 2 and 3 respectively, each incrementing exactly once

#### Scenario: Stale unchanged meter cannot overwrite a concurrent edit
- **GIVEN** an owner reads meter fields X at version 1 and another request changes them to Y at version 2
- **WHEN** the owner submits X and version 1
- **THEN** the request returns 409 `VERSION_CONFLICT`, and Y and version 2 remain unchanged

#### Scenario: Competing meter corrections
- **GIVEN** two independent requests with the same current meter version
- **WHEN** they perform PATCH concurrently
- **THEN** exactly one succeeds with the incremented version and the other returns 409 `VERSION_CONFLICT`, without lost updates

#### Scenario: Foreign missing and failed meter writes
- **GIVEN** an unrelated account, a missing meter and an owned meter
- **WHEN** that account patches the foreign or missing meter, or an owned correction fails during writing
- **THEN** both foreign and missing requests return indistinguishable 404 without disclosure, and the failed write leaves all meter fields and version unchanged

### Requirement: Return machine-readable CU04 conflicts
CU04 409 responses SHALL be JSON with string `detail` and stable `code`, either `DUPLICATE_METER` or `VERSION_CONFLICT`. The frontend SHALL distinguish recovery by code, not message text. Existing CU09 error contracts SHALL remain unchanged. Trace: U12.

#### Scenario: Distinguish conflicts
- **WHEN** a same-account duplicate is submitted or a stale CU04 edit is submitted
- **THEN** the responses contain respectively `DUPLICATE_METER` or `VERSION_CONFLICT`, and the UI offers the appropriate distinct recovery without relying on message text

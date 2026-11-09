# CU06 electricity bills

## Purpose

Enable account holders to maintain private electricity bills and supporting files for their own meters.

## ADDED Requirements

### Requirement: Record an owned meter's bill
The system SHALL allow an account holder to create and list bills for an owned meter, requiring start and end calendar dates, nonnegative billed kWh with at most three decimal places, and one PDF, JPG or PNG file; an ARS amount is optional. Trace: CU06-R1, SR02, user CU06 decisions.

#### Scenario: Create with or without amount
- **WHEN** the owner creates valid bills for an owned meter with distinct periods, one with an ARS amount and one without
- **THEN** each bill and its file are associated with that meter and its domicile, and the omitted amount remains null

#### Scenario: Reject invalid required values
- **WHEN** the owner supplies a missing date, start after end, negative or more than three decimal places of kWh, or no file
- **THEN** the request is rejected without creating or changing a bill

### Requirement: Preserve exact period boundaries and values
The system SHALL retain both calendar dates without timezone conversion and exact decimal values without rounding. The proposed ARS validation accepts nonnegative amounts with at most two decimal places. Trace: CU07-R1/Q13 and CU06 user decisions; ARS sign is proposed for Review.

#### Scenario: Same day and fractional consumption
- **WHEN** the owner records start and end `2026-11-07`, `1.125` kWh and amount `0.01`
- **THEN** both dates and the exact supplied numeric values are retained

#### Scenario: Reject invalid amount
- **WHEN** the owner submits a negative ARS amount or one with more than two decimal places
- **THEN** the system rejects the request without mutation

### Requirement: Reject identical periods per meter
The system SHALL reject a new or corrected bill with the same meter, start date and end date as another bill, including concurrent requests. The same period on a different owned meter SHALL be allowed. Trace: CU06 user decisions.

#### Scenario: Concurrent duplicates
- **WHEN** two requests with distinct idempotency keys concurrently create an identical period for one meter
- **THEN** exactly one succeeds and the other returns a duplicate conflict without mutation

#### Scenario: Idempotent retry
- **WHEN** the owner retries the same committed create with the same idempotency key and payload
- **THEN** the original successful response is returned without creating another bill

#### Scenario: Correction collides
- **WHEN** an owner corrects a bill to the identical period of another bill on the same meter
- **THEN** the correction is rejected and both bills and their files remain unchanged

### Requirement: Confirm overlapping periods
The system SHALL warn before saving a non-identical overlapping period for the same meter and permit explicit confirmation. Proposed inclusive bounds treat a shared endpoint as overlapping. The system SHALL recheck under concurrency and SHALL NOT save when the confirmed overlap set is stale. Trace: CU06 user decisions; inclusive boundaries are proposed for Review.

#### Scenario: Overlap confirmed
- **GIVEN** a bill from November 1 through November 7
- **WHEN** the owner proposes November 7 through November 10, reviews the warning and confirms the current overlap set
- **THEN** both bills are retained

#### Scenario: Concurrent new overlap
- **WHEN** an overlap is added or changed after warning but before confirmation
- **THEN** the confirmation does not save and the owner must review the current overlap set

#### Scenario: Edit excludes itself
- **WHEN** a bill is corrected without overlapping any other bill
- **THEN** the bill itself does not trigger an overlap warning

### Requirement: Correct a bill without changing its identity
The owner SHALL correct period, billed kWh, amount and replace the file, preserving bill and meter identity. No bill deletion, domicile change or meter reassignment SHALL be offered. Each successful correction SHALL check and advance the version; stale corrections SHALL fail without mutation. Trace: CU06 user decisions; versioning proposed for Review.

#### Scenario: Correct and retain file
- **WHEN** the owner corrects a current bill's values while retaining its file
- **THEN** the same bill ID, meter and file remain, and its version advances

#### Scenario: Competing corrections
- **WHEN** two corrections use the same current version
- **THEN** at most one succeeds and the stale request returns a version conflict without overwriting it

### Requirement: Validate supported private files
The system SHALL accept only actual PDF, JPEG or PNG files, require one file per bill, reject malformed, unsafe or unsupported inputs, and enforce the proposed limit of 5,000,000 decoded file bytes. It SHALL limit validation resource use and SHALL NOT extract bill fields or transfer files externally. Trace: CU06 user decisions, SR04; precise byte and safety policy proposed for Review.

#### Scenario: Size and content validation
- **WHEN** the owner submits a supported file of at most 5,000,000 bytes that passes the reviewed content and resource-safety policy
- **THEN** it can be stored; a larger file, malformed file or disguised unsupported format is rejected without mutation

#### Scenario: Encrypted PDF
- **WHEN** the owner submits an encrypted PDF under the proposed PDF policy
- **THEN** the file is rejected without mutation

### Requirement: Protect bill resources
The system SHALL authorize bill and file operations through the meter's owning account, prevent cross-account disclosure, and require trusted Origin and CSRF for authenticated writes. Missing, foreign and mismatched resources SHALL be indistinguishable. Private responses SHALL NOT be cached. Trace: SR02/SR04 and CU06 user decisions.

#### Scenario: Cross-account and request security
- **WHEN** another account lists, retrieves, creates or edits a foreign bill or downloads its file, or a write lacks valid Origin or CSRF
- **THEN** access is denied without leaking data or mutating the bill; foreign and missing resources yield indistinguishable 404 responses and invalid request security yields 403

### Requirement: Preserve file availability during replacement and recovery
The system SHALL preserve the previously committed file until its replacement commits, retain potentially live files when the commit outcome is unknown, and remove an object only after its unreferenced status is established. A restart SHALL retain access to committed files. Trace: CU06 file replacement and privacy decisions; recovery protocol proposed for Review.

#### Scenario: Rolled-back replacement
- **WHEN** file replacement fails before commit or definitely rolls back
- **THEN** the previous bill version and file remain available

#### Scenario: Unknown commit and recovery
- **WHEN** the database connection is lost during commit and its outcome is unknown
- **THEN** both candidate files are retained until resolution and only proven unreferenced objects are eligible for cleanup

#### Scenario: Restart after successful replacement
- **WHEN** a replacement commits and the application restarts with its database and private volume intact
- **THEN** the owner can retrieve the committed replacement and other accounts cannot

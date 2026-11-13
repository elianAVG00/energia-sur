# Spec Delta

## MODIFIED Requirements

### Requirement: Refresh periodically with an independent lock

The system SHALL refresh at approximately the CU10-configured interval (default five
minutes) under a CU02-specific PostgreSQL advisory lock, SHALL record `skipped_locked` when
it cannot acquire the lock, and SHALL keep its own snapshot and run history separate from
CU01. Trace: U22 D4; U24 D3/D4.

#### Scenario: Concurrent refresh writes once

- **GIVEN** two simultaneous CU02 refresh attempts
- **WHEN** the periodic refresh runs
- **THEN** one refresh persists a snapshot and the other records a `skipped_locked` run and writes no snapshot

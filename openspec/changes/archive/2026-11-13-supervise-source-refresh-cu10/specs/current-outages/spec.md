# Spec Delta

## MODIFIED Requirements

### Requirement: Refresh the snapshot periodically without concurrent runs

The system SHALL refresh the snapshot at approximately the CU10-configured interval
(default five minutes) and SHALL prevent simultaneous refreshes, recording `skipped_locked`
for a refresh that cannot acquire the lock. Trace: U16 D5/D6; U24 D3/D4.

#### Scenario: Concurrent refresh writes once

- **GIVEN** two refresh attempts start at the same time
- **WHEN** the periodic refresh runs
- **THEN** one refresh persists a snapshot and the other records a `skipped_locked` run and writes no snapshot

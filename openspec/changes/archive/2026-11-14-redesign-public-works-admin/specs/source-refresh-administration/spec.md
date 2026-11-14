# Spec Delta

## MODIFIED Requirements

### Requirement: Expose a minimal admin-only view

The frontend SHALL expose one admin view with one card per ENRE source showing the real state, last attempt and outcome, last successful update, error when present, lock contention, the configured interval and whether automatic scheduling is enabled. Each card SHALL group a retry and the validated 5/10/15/30/60-minute selector, SHALL distinguish failure from success without simulating a refresh, and SHALL handle 401, 403 and 409. Trace: CU10-R1, U24 D2/D7.

#### Scenario: Administrator sees real state and controls

- **GIVEN** an authenticated administrator
- **WHEN** the admin view is opened
- **THEN** both source cards show the real state, a retry button and the interval selector with the five allowed values
- **AND** each card presents the last attempt, outcome, last successful update, current interval and scheduling configuration as distinct fields

#### Scenario: Failure stays distinct from the last success

- **GIVEN** a source with a prior successful check and a later failed attempt
- **WHEN** the administrator reads the source card
- **THEN** the failure and its error are visually distinct from the previous successful check
- **AND** no successful refresh is simulated or implied

#### Scenario: Only the existing administrative controls are present

- **GIVEN** an authenticated administrator
- **WHEN** a source card is rendered
- **THEN** its only actions are the retry control and the validated interval selector with its save control
- **AND** no role, enablement, backoff, logging or data-entry tool is added

#### Scenario: Non-admin does not see the admin view

- **GIVEN** an authenticated non-admin
- **WHEN** the application shell is rendered
- **THEN** the administrative navigation entry is not shown, and a direct endpoint call still returns HTTP 403

#### Scenario: A concurrent retry is shown as a conflict

- **GIVEN** an administrator whose retry is rejected because an acquisition is active
- **WHEN** the view receives HTTP 409 `SOURCE_BUSY`
- **THEN** it reports the active execution and does not display a successful refresh

#### Scenario: Narrow viewport keeps the admin view usable

- **GIVEN** a viewport of 390, 820 or 1440 px
- **WHEN** the admin view is rendered
- **THEN** the source cards stack without horizontal overflow
- **AND** the retry and interval controls remain reachable by keyboard

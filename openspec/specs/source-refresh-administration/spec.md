# source-refresh-administration Specification

## Purpose
Provide an administrator-only layer to observe automatic ENRE source refresh, request a
synchronous retry and configure the refresh interval per source, without duplicating the
CU01/CU02 acquisition or changing their public query contracts.

## Requirements

### Requirement: Restrict source administration to administrators

The system SHALL allow only authenticated accounts with the `admin` role to read source
status, trigger a retry or change an interval. Unauthenticated requests SHALL return HTTP
401 and authenticated non-admin requests SHALL return HTTP 403. Access SHALL be enforced
by the server, independent of any client-supplied role. Trace: CU10-R1, U24 D2, Q21.

#### Scenario: Unauthenticated request is rejected

- **GIVEN** no valid session cookie
- **WHEN** a source status, retry or interval request is made
- **THEN** the server responds HTTP 401 and returns no administrative data

#### Scenario: Authenticated non-admin is rejected

- **GIVEN** an authenticated account whose role is `user`
- **WHEN** it calls any administrative endpoint directly
- **THEN** the server responds HTTP 403 and performs no retry or configuration change

#### Scenario: A client-supplied role is not trusted

- **GIVEN** an authenticated `user` account that forges an `admin` role in the request or
  in local frontend state
- **WHEN** it calls an administrative endpoint
- **THEN** the server still responds HTTP 403 because authorization uses the stored
  account role

### Requirement: Provision roles only through controlled backend commands

A role change SHALL occur only through a controlled backend provisioning command. No
request or UI SHALL set a role, no account SHALL self-assign `admin`, and no
role-management interface SHALL exist. Trace: CU10-R1, U24 D1.

#### Scenario: No request can change a role

- **GIVEN** an authenticated account, including an administrator
- **WHEN** any API request is sent with a role field or target role
- **THEN** the server ignores or rejects it and the stored role is unchanged

#### Scenario: Promotion is an operator action

- **GIVEN** an existing account and an operator
- **WHEN** the operator runs the controlled promotion command
- **THEN** only that account's role becomes `admin` and no password or other data changes

### Requirement: Report each source's real refresh state

The status response SHALL report, per source, the last real attempt time and outcome, the
last successful check time, the last-attempt error when present, the configured interval,
the last skipped-lock time when present, and whether automatic scheduling is enabled.
Values SHALL derive from existing records without inventing a success. Trace: CU10-R1,
U24 D7, SR03.

#### Scenario: Successful attempt is shown

- **GIVEN** a source whose latest attempt succeeded
- **WHEN** an administrator reads the source status
- **THEN** the last attempt, its successful outcome and the last successful check are
  shown with their real timestamps

#### Scenario: Failed attempt preserves the last success

- **GIVEN** a source with a prior successful check and a later failed attempt
- **WHEN** an administrator reads the source status
- **THEN** the failure and its error are shown and the previous successful check is still
  reported, not presented as a recent success

#### Scenario: Lock contention stays visible

- **GIVEN** repeated automatic runs that cannot acquire the source lock
- **WHEN** an administrator reads the source status
- **THEN** the last skipped-lock time is reported so the contention is not hidden

### Requirement: Retry a source synchronously without duplicating acquisition

A manual retry SHALL run the same acquisition used by the automatic scheduler and SHALL
return the real persisted outcome. A completed attempt, including a failed one, SHALL
return HTTP 200 with its outcome; the server SHALL reserve 5xx for transport or database
failure and SHALL NOT simulate a successful refresh. Trace: CU10-R1, U24 D5, SR05.

#### Scenario: Manual retry runs the shared acquisition

- **GIVEN** an idle source and an administrator
- **WHEN** the administrator requests a retry
- **THEN** the shared acquisition runs once and its real outcome is returned with HTTP 200

#### Scenario: Manual retry failure returns its real outcome

- **GIVEN** a source with a valid snapshot and an acquisition that fails
- **WHEN** the administrator requests a retry
- **THEN** HTTP 200 carries the failed outcome and error, and the previous valid snapshot
  remains the reported last success

### Requirement: Reject concurrent retries with 409 Conflict

A retry SHALL acquire the source's existing PostgreSQL advisory lock. When an automatic or
manual acquisition already holds it, the retry SHALL return HTTP 409 with code
`SOURCE_BUSY`, SHALL NOT enqueue a new job, SHALL NOT interrupt the running acquisition
and SHALL NOT record an artificial run. Trace: CU10-R1, U24 D5.

#### Scenario: Retry during an active acquisition returns 409

- **GIVEN** a source acquisition currently holding its advisory lock
- **WHEN** an administrator requests a retry for that source
- **THEN** the server responds HTTP 409 with `SOURCE_BUSY`, reports that an execution is
  active, and creates no additional run record

#### Scenario: Sources update independently

- **GIVEN** an active acquisition for one source
- **WHEN** an administrator retries the other source
- **THEN** the other source runs because each source keeps its own lock

### Requirement: Configure intervals from the allowed set

The system SHALL accept only `interval_seconds` values of 300, 600, 900, 1800 or 3600
per source, SHALL validate the value on the server and in the database, and SHALL keep
the two sources independent. Trace: CU10-R1, U24 D4.

#### Scenario: A valid interval is persisted

- **GIVEN** an administrator and a source
- **WHEN** the administrator selects one of the five allowed intervals
- **THEN** the new interval is stored and returned for that source only

#### Scenario: An invalid interval is rejected

- **GIVEN** an administrator and a source
- **WHEN** a value outside the allowed set is sent directly to the API
- **THEN** the server responds HTTP 422 and stores nothing

### Requirement: Detect concurrent interval changes with optimistic versioning

An interval update SHALL carry the current configuration version and SHALL apply
atomically. An update based on a stale version SHALL return HTTP 409 with code
`VERSION_CONFLICT` and SHALL NOT overwrite the newer value, and the client SHALL be able
to reload the current configuration. Trace: CU10-R1, U24 D6.

#### Scenario: Two administrators change the same interval

- **GIVEN** two administrators holding the same configuration version
- **WHEN** both submit a different interval
- **THEN** one update succeeds and the other returns HTTP 409 with `VERSION_CONFLICT`
  without overwriting the stored value

#### Scenario: Reload exposes the current version

- **GIVEN** a rejected stale update
- **WHEN** the administrator reloads the source status
- **THEN** the current interval and version are returned for a fresh attempt

### Requirement: Apply intervals dynamically and persist them

The scheduler SHALL read the configured interval each cycle so a change applies at the
next cycle without restarting the backend, and the value SHALL survive a restart. A
configuration read failure, including a missing row or table, SHALL fall back to a safe
default and SHALL NOT stop the scheduler. Trace: CU10-R1, U24 D3/D4.

#### Scenario: A changed interval applies without restart

- **GIVEN** a running scheduler and an administrator who changes the interval
- **WHEN** the next scheduling cycle reads the configuration
- **THEN** the new interval governs that cycle without restarting the backend

#### Scenario: Configuration survives a restart

- **GIVEN** a configured interval
- **WHEN** the backend restarts
- **THEN** the scheduler reads the same persisted interval

#### Scenario: Configuration failure does not stop the scheduler

- **GIVEN** a temporary failure while reading the configuration, including a missing row
  or table
- **WHEN** a scheduling cycle runs
- **THEN** the scheduler uses a safe default for that cycle, logs it, and continues running

### Requirement: Protect administrative mutations

Retry and interval updates SHALL require the trusted Origin and a valid CSRF token in
addition to admin authorization, reusing the existing session protections. Read-only
status SHALL NOT require a CSRF token. Trace: CU10-R1, U24 D2, SR02.

#### Scenario: Missing CSRF token is rejected

- **GIVEN** an authenticated administrator
- **WHEN** a retry or interval update omits the CSRF token
- **THEN** the server responds HTTP 403 and performs no change

#### Scenario: Untrusted Origin is rejected

- **GIVEN** an authenticated administrator
- **WHEN** a mutation arrives from an Origin outside the allowlist
- **THEN** the server responds HTTP 403 and performs no change

### Requirement: Preserve public source behavior

Configuring an interval SHALL NOT change CU01/CU02 public endpoints, response shapes,
states or freshness thresholds. The five-minute default SHALL preserve current behavior;
a longer interval SHALL only be reflected through the existing freshness classification,
which can reach `unavailable` when the publication age exceeds sixty minutes. Trace: U16
D8, Q07, U24 D4/D7.

#### Scenario: Default preserves current behavior

- **GIVEN** the seeded five-minute default
- **WHEN** CU01/CU02 are queried
- **THEN** their responses, states and freshness behave as before this change

#### Scenario: A long interval does not alter the public contract

- **GIVEN** an administrator sets a sixty-minute interval
- **WHEN** CU01/CU02 are queried
- **THEN** their response contract and thresholds are unchanged, and the publication may
  be classified `unavailable` when its real age exceeds sixty minutes

### Requirement: Expose a minimal admin-only view

The frontend SHALL expose one admin view with one card per ENRE source showing the real
state, a retry button and a validated interval selector, visible only to administrators,
and SHALL handle 401, 403 and 409 without simulating a successful refresh. Trace:
CU10-R1, U24 D2/D7.

#### Scenario: Administrator sees real state and controls

- **GIVEN** an authenticated administrator
- **WHEN** the admin view is opened
- **THEN** both source cards show the real state, a retry button and the interval selector
  with the five allowed values

#### Scenario: Non-admin does not see the admin view

- **GIVEN** an authenticated non-admin
- **WHEN** the application shell is rendered
- **THEN** the administrative navigation entry is not shown, and a direct endpoint call
  still returns HTTP 403

#### Scenario: A concurrent retry is shown as a conflict

- **GIVEN** an administrator whose retry is rejected because an acquisition is active
- **WHEN** the view receives HTTP 409 `SOURCE_BUSY`
- **THEN** it reports the active execution and does not display a successful refresh

### Requirement: Keep administration out of the assistant and public tools

The administrative status, retry and interval operations SHALL NOT be exposed to the
assistant, chatbot tools or any public surface. Trace: Q21, AGENTS.md.

#### Scenario: The assistant cannot administer sources

- **GIVEN** a chat session, authenticated or not
- **WHEN** it asks to retry a source or change an interval
- **THEN** no administrative operation runs and the assistant reports that it cannot
  perform it

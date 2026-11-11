# frontend-shell Specification

## Purpose

Provide consistent accessible presentation and form feedback across Energía Sur,
adopting CU09 first while reserving the future CU03 assistant integration.

## Requirements

### Requirement: Shared accessible application layout

The application SHALL render CU09 inside one shared root layout, retaining its
accessible controls, visible keyboard focus, loading/error states and health panel.
The layout SHALL remain usable on narrow viewports without hiding diary actions.
This requirement follows U09's reusable-frontend direction.

#### Scenario: CU09 remains usable in the common shell
- **GIVEN** an authenticated account with its own domicile
- **WHEN** the diary is opened at desktop or narrow viewport width
- **THEN** domicile selection, diary actions, summary and PDF controls are reachable with labeled controls, visible focus and a horizontally scrollable table when necessary

### Requirement: Reusable form feedback preserves backend authority

Forms SHALL expose labeled fields and associated validation errors, prevent
duplicate submissions while pending, and display backend failures without losing
recoverable user drafts. Client-side validation SHALL NOT replace server-side
ownership, Buenos Aires date validation or summary calculations.

#### Scenario: Invalid form receives accessible feedback
- **GIVEN** a CU09 form with a missing required field or over-limit text
- **WHEN** the user attempts to submit
- **THEN** the invalid field has an associated error and no mutation is sent until the form is valid

#### Scenario: Correction conflict preserves recovery
- **GIVEN** another writer updated the cut after the editor was opened
- **WHEN** the user submits a correction and receives 409
- **THEN** the draft is not silently retried or overwritten and explicit discard/reload opens the current persisted version with reset form values

### Requirement: Preserve the CU09 vertical slice during adoption

The shared frontend SHALL preserve CU09's accepted account/domicile isolation,
create/list/correct/close flows, period summaries and authenticated PDF download.
It SHALL render authoritative backend totals and preserve the 1970 local-date
floor, optional fields, version-conflict recovery and cancellation behavior.

#### Scenario: Owner completes the diary workflow
- **GIVEN** an authenticated synthetic account and its own registered domicile
- **WHEN** the user creates overlapping/open cuts, corrects and closes records, queries a period and downloads a PDF
- **THEN** the original CU09 oracles remain satisfied, the downloaded PDF contains the correct Unicode fields and totals, and a second account cannot read or mutate those records

### Requirement: Single deferred floating-chat mount

The root layout SHALL contain exactly one floating-chat integration mount across login
and authenticated CU09 views. When the CU03 runtime and provider configuration are
available, the mount SHALL accept messages and stream answers through the dedicated
assistant client; when the runtime, provider or configuration is unavailable, it SHALL
clearly communicate an unavailable or static fallback state, SHALL NOT fabricate answers,
and SHALL NOT connect to an unapproved provider.

#### Scenario: One functional mount when CU03 is available

- **GIVEN** the CU03 runtime and provider configuration are available
- **WHEN** the user opens login, enters CU09 or switches domiciles
- **THEN** there is exactly one floating chat mount, it accepts messages and streams answers through the dedicated client

#### Scenario: Shell reserves CU03 without pretending it is implemented

- **GIVEN** the CU03 runtime, provider or configuration is unavailable
- **WHEN** the user opens login, enters CU09 or switches domiciles
- **THEN** there is only one root chat mount with an explicit unavailable or static fallback state and no fabricated answer

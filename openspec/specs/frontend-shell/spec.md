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

The root layout SHALL contain exactly one floating-chat integration mount across
login and authenticated CU09 views. Until CU03 implements the runtime, it SHALL
clearly communicate unavailability, SHALL NOT accept/send messages or generate
answers, and SHALL NOT connect to LangChain, model providers or streaming APIs.

#### Scenario: Shell reserves CU03 without pretending it is implemented
- **GIVEN** CU03 runtime integration has not been implemented
- **WHEN** the user opens login, enters CU09 or switches domiciles
- **THEN** there is only one root chat mount with an explicit unavailable state and no chat/model/network request or stored conversation

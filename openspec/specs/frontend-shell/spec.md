# frontend-shell Specification

## Purpose

Provide consistent accessible presentation and form feedback across Energía Sur,
adopting CU09 first while reserving the future CU03 assistant integration.

## Requirements

### Requirement: Shared accessible application layout

Every view, including CU09, SHALL render inside one shared root layout with header, main and footer landmarks, accessible controls, visible focus and loading/error states, and SHALL stay usable on narrow viewports without hiding diary actions. The main content SHALL be centred with a maximum width of about 1200 px. No view SHALL display backend technical status, health-check responses, development notices or a manual re-check control. Technical health stays verifiable over HTTP (U09, U26).

#### Scenario: CU09 remains usable in the common shell
- **GIVEN** an authenticated account with its own domicile
- **WHEN** the diary is opened at desktop or narrow viewport width
- **THEN** domicile selection, diary actions, summary and PDF controls are reachable with labeled controls, visible focus and a horizontally scrollable table when necessary

#### Scenario: Technical health status is absent from every view
- **GIVEN** any public, authenticated or administrative view of the application
- **WHEN** the view is rendered
- **THEN** no API health panel, health-check JSON, development-environment notice or manual re-check control is present
- **AND** the layout does not request `/api/health` on its own

#### Scenario: Technical health remains verifiable outside the interface
- **GIVEN** the local environment is running
- **WHEN** a developer checks the backend health directly or through the same-origin proxy
- **THEN** the retained endpoint still returns its technical response
- **AND** no user-facing screen is required to obtain that result

#### Scenario: Every view shares header, main and footer landmarks
- **GIVEN** a visitor opens login, Cortes, Trabajos or the account view, signed in or not
- **WHEN** the view is rendered
- **THEN** exactly one header, one main and one footer landmark are present
- **AND** the main content stays centred within the shared container at desktop and narrow widths

#### Scenario: Keyboard users skip repeated navigation
- **GIVEN** a keyboard user starts at the top of any view
- **WHEN** the user tabs to the first focusable element and activates it
- **THEN** focus moves to the main content, past the repeated header navigation

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

### Requirement: Header identity and horizontal navigation

The shared header SHALL identify Energía Sur and SHALL expose the current sections as horizontal, keyboard-operable navigation named Cortes, Trabajos, Mi cuenta and, for administrators only, Administración. The active section SHALL expose `aria-current="page"`. Narrow viewports SHALL keep each applicable section reachable without a sidebar. When signed in, the header SHALL expose one Cerrar sesión control that keeps the existing logout behaviour.

#### Scenario: Active section is announced
- **GIVEN** a user has opened one of the available sections
- **WHEN** the header renders
- **THEN** only that section exposes `aria-current="page"`
- **AND** the section names remain Cortes, Trabajos and Mi cuenta

#### Scenario: Administration is visible only to administrators
- **GIVEN** a signed-in account whose role is not admin
- **WHEN** the header renders
- **THEN** no Administración navigation control is present
- **AND** an admin account does see it and can open the admin view

#### Scenario: Narrow viewport keeps navigation reachable
- **GIVEN** a viewport about 390 px wide
- **WHEN** the header renders
- **THEN** every applicable section control is visible and keyboard reachable
- **AND** no sidebar or collapsed menu is required to reach them

#### Scenario: One working logout control
- **GIVEN** a signed-in user
- **WHEN** the header renders
- **THEN** exactly one Cerrar sesión control is present
- **AND** activating it performs the existing logout behaviour

#### Scenario: Anonymous visitor has no logout
- **GIVEN** a visitor without a session
- **WHEN** the header renders
- **THEN** no Cerrar sesión control is present

### Requirement: Cohesive citizen-facing visual system

Public, authenticated and administrative views SHALL use the approved light palette: primary #0D6177, background #F8FAFC, surface #FFFFFF and foreground #0F172A, with system typography and visible focus. Buttons, inputs, cards and tables SHALL share consistent radius, spacing and contrast through the local shadcn/ui primitives. No UI framework, component registry or font dependency SHALL be added.

#### Scenario: Approved palette resolves in the interface
- **GIVEN** any public, authenticated or administrative view
- **WHEN** the visual tokens are applied
- **THEN** primary, background, surface and foreground resolve to the approved values
- **AND** no dark-mode variant, external font or new dependency is introduced

#### Scenario: Layout avoids horizontal overflow
- **GIVEN** a viewport of 390, 820 or 1440 px
- **WHEN** the view is rendered
- **THEN** the page has no horizontal scrollbar
- **AND** content stays inside the centred container

#### Scenario: Shared controls keep one visual language
- **GIVEN** buttons, inputs, cards and tables rendered in any view
- **WHEN** their presentation is compared
- **THEN** they share the token-defined radius, spacing and contrast
- **AND** their public interfaces and behavior are unchanged

### Requirement: Informational footer

The shared layout SHALL render a footer landmark with static Energía Sur attribution and the public source note for outages and works. The footer SHALL NOT expose backend health, development-environment details or session controls.

#### Scenario: Footer closes every view without technical detail
- **GIVEN** any public, authenticated or administrative view
- **WHEN** the view is rendered
- **THEN** the footer shows the portal identity and public source note
- **AND** it shows no health status, environment notice or session control

#### Scenario: Footer stays free of session controls
- **GIVEN** a signed-in or anonymous user
- **WHEN** the footer renders
- **THEN** it contains no logout or login control
- **AND** the header remains the only place for session actions

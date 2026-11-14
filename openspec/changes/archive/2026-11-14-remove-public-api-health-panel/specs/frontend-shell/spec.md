# Spec Delta

## MODIFIED Requirements

### Requirement: Shared accessible application layout

The application SHALL render CU09 inside one shared root layout with accessible
controls, visible keyboard focus and loading/error states, and SHALL stay usable on
narrow viewports without hiding diary actions. No public, authenticated or
administrative view SHALL display backend technical status, health-check responses,
development notices or a manual re-check control. Technical health stays verifiable
through the retained HTTP endpoint and infrastructure tooling (U09, U26).

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

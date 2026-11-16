# account-workspace Specification

## Purpose

Define the presentation contract of the authenticated "Mi cuenta" area so that
CU04-CU09 keep their accepted behavior while sharing one ordered, accessible and
responsive workspace with visible active context.

## Requirements

### Requirement: Organize Mi cuenta by scope and active context

Mi cuenta SHALL organize the authenticated workspace into labelled sections for domiciles, meters, cuts, readings, bills and consumption. Domicile actions SHALL work without a meter; readings, bills, comparison and consumption SHALL require a selected meter owned through the selected domicile. Every existing control SHALL remain rendered and operable; no section SHALL be hidden behind tabs, accordions or routes. Trace: CU04-CU09, U31.

#### Scenario: Sections follow scope order
- **GIVEN** an authenticated owner with a domicile and two meters
- **WHEN** Mi cuenta renders
- **THEN** the six labelled sections are present and the meter-scoped sections use the selected meter

#### Scenario: Domicile without a meter
- **GIVEN** an owner with a domicile and no meters
- **WHEN** the workspace renders
- **THEN** the diary and domicile management remain usable and the meter-scoped sections show a no-meter state without inventing data

#### Scenario: No domicile
- **GIVEN** an owner without domiciles
- **WHEN** the workspace renders
- **THEN** only the registration path and its guidance are shown and no diary or meter operation is offered

#### Scenario: Controls are not hidden
- **GIVEN** any authenticated owner
- **WHEN** the workspace renders
- **THEN** the accepted forms and actions are present without switching tabs or opening accordions

### Requirement: Show the active context and preserve the accepted contracts

Mi cuenta SHALL display the selected domicile and the selected meter as visible context, SHALL NOT nest a card inside another card, and SHALL preserve every existing control id, label, accessible name, message, handler, ownership rule, calculation and API contract. Trace: U31, Q03, Q09.

#### Scenario: Context and isolation
- **GIVEN** an owner selected a domicile and a meter
- **WHEN** a meter-scoped section renders
- **THEN** the context shows that domicile and meter and no data from another meter is displayed

#### Scenario: Flat card hierarchy
- **WHEN** the workspace renders
- **THEN** no card contains another card and each section is distinguishable

#### Scenario: Contracts preserved
- **WHEN** the redesign is applied
- **THEN** ids, labels, messages and handlers are unchanged and no adapter, state, schema or store file changes

### Requirement: Accessible and responsive account presentation

Mi cuenta SHALL keep one h1 and one labelled section heading per section, with the existing card headings retained at their accepted level, visible focus, labelled controls and the existing status text, SHALL avoid horizontal document overflow at 390, 820 and 1440 px, and SHALL keep each table inside its focusable horizontal scroll region. It SHALL NOT add aria-live regions or change the shared table label. Trace: U31, frontend-shell.

#### Scenario: Three widths
- **GIVEN** a viewport of 390, 820 or 1440 px
- **WHEN** Mi cuenta renders
- **THEN** the document has no horizontal scrollbar and tables scroll inside their own region

#### Scenario: In-page navigation is keyboard operable
- **GIVEN** a keyboard user on Mi cuenta
- **WHEN** the user focuses the "Índice de Mi cuenta" links
- **THEN** each link reaches its labelled section and the header navigation stays the only "Secciones" navigation

#### Scenario: No new announcements
- **WHEN** sections load or fail
- **THEN** only the pre-existing status and alert text is announced

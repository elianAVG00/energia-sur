# Design

## Context

The authenticated area is composed by `Workspace` (domicile list, selection and
creation plus the CU09 diary) and `DomicileManagement` (address, meters, meter
selection and the CU05/CU06/CU08 cards). The current DOM nests feature cards
inside the CU04 card, the page title names only CU09, and the selected meter is
local state of `DomicileManagement`, never shown as the context of the sections
it feeds. The shared shell, palette, local primitives, request scopes, session
store and adapters are already implemented and archived (U27-U30).

Constraints: React 19 + Vite + TypeScript, Tailwind CSS 4 semantic tokens, local
shadcn/ui primitives, Playwright via the pinned Docker verification image.
`readingMeter` is local UI state; Zustand only stores the session and the
selected domicile. CU09 must work without a meter. M2, M3, the assistant overlay
and stale/unavailable totals are pre-existing findings outside this change.

## Goals / Non-Goals

**Goals:**

- Establish the "Mi cuenta" frame: one `h1`, six labelled sections, an in-page
  index and a visual hierarchy consistent with CU01/CU02/CU10.
- Deliver the frame in Stage A without touching adapters, state helpers,
  schemas, stores, requests, ownership, calculations or the shared shell.
- Remove the main card nesting for the reorganized sections.
- Keep every accepted control, message, draft and isolation rule.

**Non-Goals:**

- Lifting or moving the meter selector, adding the "Contexto de trabajo" panel,
  or splitting CU04 into Domicilios/Medidores (Stage B).
- Redesigning the inside of Lecturas, Facturas, Comparación, Consumo or Diario
  (Stages C, D, E).
- Tabs, accordions, routes, new dependencies, dark mode or new shared UI
  primitives.
- Fixing M2, M3, the assistant overlay, stale/unavailable totals, hosting or
  the CU03 retention policy.

## Decisions

### D1 - One change with verifiable stages

CU04-CU09 share the same composition root and the same context decision, so six
independent changes would rewrite the same root six times and duplicate the shell
verification. The change keeps the archived pattern: one change, stage-scoped
authorization (U31 for Stage 0/A), scope lock and gates per stage.

### D2 - Single page with an in-page index; no tabs or accordions

Tabs would hide five sections and break the accepted suites that assume the
workspace is rendered after login or meter selection (`cu04`, `cu05-history`,
`cu08`, `cu09`), would unmount forms and lose drafts, and would require a router
or tab state. Accordions hide primary forms and break the "all controls remain
visible" rule. The index uses anchor links only: no hidden content, no state, no
draft loss. Its accessible name is "Índice de Mi cuenta" because the header
navigation is already named "Secciones" and `redesign-shell.spec.ts` matches that
name by substring.

### D3 - Stage A composition keeps existing owners

`AccountWorkspace` replaces `Workspace` as the account entry point and keeps the
domicile list, selection and creation logic verbatim. During Stage A,
`DomicileManagement` owned the address, the meters and `readingMeter`, and rendered
the meter-scoped sections inside the CU04 card. Stage B (D14) lifts the selection
into `AccountWorkspace`, extracts address management into `DomicileAddress`, keeps
meter fetching and management in `DomicileManagement`, and lets the container
render the meter-scoped sections. `DiarySection` extracts the existing
`DiaryWorkspace` and wraps it in the "Cortes e interrupciones" section.

Section order is Domicilios, Medidores, Cortes e interrupciones, Lecturas, Facturas
and Consumo y estimación. Stage A rendered "Cortes e interrupciones" last because
the meter state still lived in the CU04 card; Stage B delivers the final order.

### D4 - Section wrapper without an extra card layer

`AccountSection` renders a semantic `<section>` with an `h2` (`aria-labelledby`)
and an optional description, not a `Card`. Feature cards stay single-layer, so
the frame adds headings and spacing without creating a card inside a card.
`ConsumptionPanel` keeps its internal cards until Stage D; the structural test
therefore scopes the "no nested card" assertion to the sections reorganized in
Stage A.

### D5 - Domicilios section

The section keeps the creation form, duplicate warning, empty-state guidance and
notices. The `selected-domicile` selector moves to the context panel (D14) and is
not duplicated here. Address correction is owned by `DomicileAddress`, which
fetches `GET /domiciles/{id}/management`, patches the address and preserves the
accepted conflict/discard behavior.

### D6 - Medidores section

`DomicileManagement` owns only the meter list, the create/edit form and the
meter-specific duplicate, conflict, retry and discard states. It reports the
loaded list to `AccountWorkspace` through a typed `onMetersChange` callback and
does not render a selector. The `reading-meter` selector moves to the context
panel (D14) and is not duplicated here.

### D7 - Meter-scoped sections and no-meter state

`AccountWorkspace` renders Lecturas, Facturas and Consumo as sections so anchors
are stable and features are discoverable. Without a selected meter they show a
neutral guidance paragraph and no table or control; with a meter they render the
existing `ReadingHistory`, `BillHistory` and `ConsumptionPanel` unchanged and keyed
by `generation:domicile:meter`. `ConsumptionPanel`'s inner title became "Consumo
del medidor" so "Consumo y estimación" remains a single heading for the section.

### D8 - Cortes section

`DiarySection` keeps the CU09 handlers, state, conflict recovery, table, summary
and PDF unchanged, wrapped in the "Cortes e interrupciones" section. It does not
require a meter and stays reachable when the domicile has none.

### D9 - Title and navigation

`VIEWS.account.title` becomes "Mi cuenta" and its description lists the area
content. The header title change is asserted by four existing test lines in two
files; those are the only test edits allowed by this change. The account line
"Cuenta: {username}" is preserved.

### D10 - Accessibility and announcements

One `h1` from the layout and one labelled section `h2` per section; the existing
`CardTitle` headings keep their accepted `h2` level because changing the shared
primitive is out of scope (see D12). Visible focus, existing
`aria-describedby`/`aria-invalid`, and no new `aria-live` region. The shared
`Table` label is untouched (M3). The index is a `nav` with an explicit name.

### D11 - Evidence and gates

A gated `visual-capture-account.spec.ts` (`VISUAL_CAPTURE=1`, `VISUAL_DIR`) mocks
the authenticated API with synthetic data and captures eight scenes at
1440x900, 820x1180 and 390x844, using waits that are stable before and after
Stage A. Baseline `before/` is captured before any UI edit; Stage A writes
`etapa-a/`. A new `redesign-account.spec.ts` adds cross-cutting checks.

### D12 - Stage mapping for the change-level spec

The delta spec describes the final behavior of the whole change; the tasks and
this mapping define what each stage delivers. The archive is not attempted until
every row is done.

| Spec requirement or scenario | Stage |
| --- | --- |
| Six labelled sections, index, title, no hidden controls, no-domicile and no-meter states | A |
| Selected domicile and visible meter context; final section order with "Cortes e interrupciones" after "Medidores" | B (implemented) |
| "No card contains another card" in every section (ConsumptionPanel still nests internally) | D |
| Accessible section headings, existing card headings retained at level 2, responsive widths | A, maintained through B-E |

`AccountSection` uses a larger `h2` than `CardTitle` so the section hierarchy is
visually distinct without changing the shared primitive. Giving card titles an
`h3` level is a shared-component change for a later, separately authorized
change; it is not fixed here.

### D13 - No-meter guidance never asserts unverified data

The Medidores section only shows "No hay medidores registrados. El domicilio puede
usarse sin medidor." after a successful load with an empty list; while loading it
shows "Cargando medidores…" and after a failed load it shows the error with
"Reintentar administración". The meter-scoped sections never claim the absence of
meters: they show neutral guidance that points to the Medidores section and keeps
the diary available, whether the list is empty, loading or failed.

### D14 - Stage B meter ownership and reset (implemented)

`AccountWorkspace` is the single owner of the active meter selection. The selected
id and the meter list are stored with the scope key `${generation}:${selectedDomicileId}`;
values from a previous scope are ignored during render, so a domicile or account
change resets the meter synchronously without an effect, without a stale frame and
without adding the state to Zustand. `DomicileManagement` remains the only owner of
the meter request (`GET /domiciles/{id}/meters`) and the create/edit mutations, and
reports the list and a discriminated `loading | ready | failed` status through a
typed callback; the parent never fetches a second list. The parent validates the
selected id against that scoped list before rendering meter-scoped features.
`DomicileAddress` owns the single address request. The context panel renders the
only `selected-domicile` and `reading-meter` selectors.

This differs from the Stage A ownership note (D3): the address left
`DomicileManagement` so it can live in the Domicilios section while meters stay in
Medidores without duplicating requests or rendering one component in two places.
The parent mirrors the meter list solely to present its selector and never mutates
that list. This split duplicates some request/error/conflict state-machine code
between `DomicileAddress` and `DomicileManagement`; consolidation remains deferred
because it would add a shared abstraction outside this presentation-only step.
The context and meter-scoped guidance distinguish loading, failed, empty and
unselected states. Identically named retry/discard actions remain in their
respective sections to preserve established accessible names.

## Risks / Trade-offs

- Moving the feature cards out of the CU04 card could remount forms and lose
  drafts -> preserve component identity and verify CU04 draft recovery; the
  domicile-registration draft also survives a domicile switch.
- Duplicate headings break strict locators ("Domicilios", "Consumo y
  estimación") -> remove the duplicated `CardTitle`/`h3` and rename the
  consumption card title.
- A new navigation name could collide with "Secciones" -> named "Índice de Mi
  cuenta".
- Extra tables in the no-meter state would break `cu09`'s `tbody tr` count -> the
  no-meter state renders no table.
- The `h1` rename edits closed shell tests -> only the four title assertions
  change, and `frontend-shell` does not mandate the text.
- Consumption still nests cards until Stage D -> the structural assertion is
  scoped and the limitation is recorded.
- Stale Vite module graph in Docker -> rebuild/recreate the frontend service and
  verify the served component before E2E and captures.

## Migration Plan

No data or API migration. Stage 0 adds artifacts, decision U31, the capture
harness and baseline evidence. Stage A changes composition, the account title,
the index and the section wrappers only. Rollback is a revert of the affected
frontend files; behavior and contracts remain untouched. No commit, push or
archive is part of this change.

## Open Questions

Stage B is implemented and recorded in D14/U32. Stage C is implemented and
reviewed as recorded in D15/U33/U34. Stage D is implemented and passed runtime
gates; its actual supplied diff received independent static review under U35
with no blocking findings. Stage E is authorized and implemented under U35.
QA-INT-CU04-08 remains deferred.

### D15 — Stage C review and Stage D presentation boundaries

U34 authorizes Stage D only after the independent reviewer inspected the supplied
Stage C diffs for `ReadingForm.tsx`, `ReadingHistory.tsx` and `BillHistory.tsx`
against their current source and the CU05/CU06/CU07 contracts. The reviewer found
no confirmed Stage C-attributable defect. This was a static diff review; it did
not run application gates or remove the separate seeded-QA blocker.

Stage D changes presentation only in `BillComparison.tsx` and
`ConsumptionPanel.tsx`. CU07 remains launched by the existing bill-row
“Comparar” action in `BillHistory`; its selected bill, candidate matching,
confirmation, API requests, outcomes, messages, units and calculation behavior
remain unchanged. The comparison is a labelled, bordered subpanel inside the
existing Facturas feature card, not another Card.

CU08 keeps the existing date inputs, request effect/key, interval data,
estimation action and calculation/display helpers. Its simple bars already
belong to the feature; Stage D makes those existing bars responsive but does
not introduce a new graph or charting dependency. Real interval kWh,
daily-average kWh/day and the estimate remain separate semantic subpanels.
Estimate base timestamps are presented in `America/Argentina/Buenos_Aires` from
existing response fields; no projection or other business calculation is
added. Neither component changes meter ownership, component keys, cancellation,
stores or state helpers.

### D16 — Stage E CU09 presentation boundaries (implemented)

U35 authorizes Stage E after task 6.12's independent review of the actual
Stage D diff passed. `DiarySection` keeps its request lanes, selected-domicile
scope, forms, drafts, conflict recovery, validation feedback, summary payload,
PDF adapter and download behavior. `forms.tsx` changes only the visual wrapper
around the existing cut-registration/correction and closure forms; their
schemas, field ids, labels, submit/cancel handlers and values remain unchanged.

The "Cortes e interrupciones" section has one principal `Card`. Its internal
registration/correction, history, closure and period-summary blocks use
headings, dividers and lightweight panels rather than nested cards. The
existing six history columns and their rows remain unchanged; no duration is
calculated or added. The shared Table primitive is not modified; its existing
focusable horizontal-scroll region contains the diary table.

The period summary continues to display backend-provided totals and the
overlap-safe message; open cuts, clipping, minute precision and date validation
remain in existing API/backend paths. PDF generation stays on the accepted
endpoint and adapter. CU09 remains domicile/account scoped and does not depend
on a selected meter. Synthetic tests exercise account/domicile switches and
accepted mock results but do not replace seeded backend/PDF acceptance.

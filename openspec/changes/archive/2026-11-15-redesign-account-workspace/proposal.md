# Proposal

## Why

The authenticated "Mi cuenta" area hosts CU04-CU09 in one long page: the CU04
management card contains the CU05, CU06 and CU08 cards, CU08 nests three more
cards, and the CU07 comparison renders as an unlabelled block inside the CU06
list. The active meter is selected inside the CU04 card and never shown as the
context of the meter-scoped sections, while the page title names only the CU09
diary. The result is inconsistent with the archived CU01/CU02/CU10 redesigns and
hard to scan at 390 px.

## What Changes

- Add one presentation-only account workspace with six labelled sections in
  dependency order: Domicilios, Medidores, Cortes e interrupciones, Lecturas,
  Facturas and Consumo y estimación. Stage A rendered "Cortes e interrupciones"
  last; Stage B delivers this final order.
- Add a visible "Contexto de trabajo" panel, with a single domicile selector and a
  single meter selector, that shows the active domicile and meter as text.
- Rename the account view title from "Diario de interrupciones" to "Mi cuenta"
  and add an "Índice de Mi cuenta" in-page navigation with anchors, not tabs,
  accordions or routes.
- Split the CU04 management into a Domicilios section (registration and address
  correction) and a Medidores section (list, create and correct), with the
  meter-scoped sections rendered as siblings, never inside another card.
- Rename the consumption card title to "Consumo del medidor" so the section name
  "Consumo y estimación" stays unique; its internal redesign remains Stage D.
- Keep CU09 usable without any meter and keep every existing id, label,
  accessible name, message, handler, request, validation, calculation,
  ownership rule, form draft and API contract.
- Add a gated synthetic capture spec plus cross-cutting regression tests.

Stage 0 (preparation, artifacts, decision U31 and baseline evidence) and Stage A
(account frame, title, index and section composition) are the only stages
authorized by this delivery. Stages B-E keep their own authorization gate.

No **BREAKING** API, dependency or contract change. Presentation only.

## Capabilities

### New Capabilities

- `account-workspace`: organization by scope, visible active context, preserved
  controls and responsive/accessible presentation of the authenticated area.

### Modified Capabilities

- `meter-readings`: the meter-isolation requirement refers to the CU04
  management view; it now refers to the Mi cuenta meter selector. Behavior, ids
  and tests are unchanged.

## Impact

- Frontend: new `frontend/src/features/account/AccountWorkspace.tsx` and
  `AccountSection.tsx`; new `frontend/src/features/domiciles/DomicileAddress.tsx`;
  `frontend/src/features/diary/Workspace.tsx` (replaced by `AccountWorkspace`),
  `frontend/src/features/diary/DiarySection.tsx`,
  `frontend/src/features/domiciles/DomicileManagement.tsx`,
  `frontend/src/features/consumption/ConsumptionPanel.tsx` (card title only) and
  `frontend/src/App.tsx` (account title only).
- Tests: new `frontend/e2e/redesign-account.spec.ts` and
  `frontend/e2e/visual-capture-account.spec.ts`; title assertions in
  `frontend/e2e/cu01.spec.ts` and `frontend/e2e/redesign-shell.spec.ts`.
- Documentation: `docs/STATE.md`, `docs/use-cases/decisions.md` (U31),
  `docs/ai-engineering/redesign-account-workspace.md`,
  `docs/frontend-foundation.md` and `README.md`.
- Unchanged: backend, `features/*/api.ts`, `features/*/state.ts`,
  `features/*/schemas.ts`, `diaryApi.ts`, `diaryState.ts`, `lib/http*`, Zustand
  stores, `useRequestScope.ts`, layout/header/footer, chat mount, visual tokens,
  dependencies, CU01-CU03/CU10 and the active OpenSpec changes.

## Approval and execution boundary

U31 records the approved plan, the "Mi cuenta" title decision and the Stage 0/A
authorization. Stage B requires a separate explicit authorization after Stage A
is verified. No commit, push, archive or deployment is authorized. QA-INT-CU04-08
remains pending and is not claimed as passing.

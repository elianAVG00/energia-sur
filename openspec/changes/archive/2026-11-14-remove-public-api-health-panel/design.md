# Design

## Context

The accepted `frontend-shell` requirement stated that the shared layout must retain
"loading/error states and health panel". When the panel was introduced, it was the
only real frontend/backend connectivity proof available. Since then, CU01–CU10 provide
real feature paths, and technical health is covered by HTTP checks, Docker health
probes and `scripts/Test-HealthProxy.ps1`.

At the start of this change `main` was clean and one commit ahead of `origin/main`
(`593fed2`). Two changes were active: `docker-development-environment` (with open tasks
7.1 and 7.2) and `configure-readonly-development-mcp`. OpenSpec 1.16.1 with the
installed `spec-driven` schema is used.

The user approved decision set D1–D7 on 2026-11-14. This change implements only the
D1-D2-D3-authorized part: remove the visible health panel and reconcile specifications.
D4 (chat FAB), D6 (logout in header) and the visual redesign are explicitly deferred,
and D5 chooses an incremental sequence where the shell and CU01 redesign come later in
a separate change.

## Goals / Non-Goals

**Goals**

- Remove the panel from the rendered tree in every view, without CSS hiding.
- Remove the panel-only modules and their exclusive tests.
- Eliminate the automatic `/api/health` request that only existed for the panel.
- Reconcile `frontend-shell` and the `development-environment` delta so no accepted
  requirement still demands a visible technical screen.
- Preserve all feature behavior, transport, state and API contracts.

**Non-Goals**

- No visual redesign, header, navigation, chat launcher or CU01 layout work.
- No backend, endpoint, proxy, Compose or health-check logic change.
- No archive of `docker-development-environment` or
  `configure-readonly-development-mcp`; no task 7.1/7.2 completion.
- No routing, dependency, font or design-token change.

## Decisions

### U26 - Technical health is not user-interface content

Recorded in `docs/use-cases/decisions.md` (U25 was already assigned to CU10, so the
next available identifier is used). The product rule is: the backend technical state is
not displayed in public, authenticated or administrative screens; the health endpoint
remains for HTTP verification, Docker infrastructure and technical diagnosis.

### D1 - Option A applied to the in-flight Docker change

The `development-environment` capability exists only as a delta inside the active
`docker-development-environment` change, not as a main spec. Therefore this change
declares a delta only for `frontend-shell`, and the conflicting requirement inside the
active Docker change is corrected in place:

- The requirement keeps its name and purpose (health verification must be real, not a
  fixture) but its acceptance is expressed over HTTP (`GET /health` and `/api/health`)
  instead of a screen.
- The backend contract requirement (`GET /health` returning `{"status":"ok"}`) is
  untouched.
- No other `development-environment` requirement is modified, no task is checked, and
  the change is not archived. Because the requirement text changes, its two completed
  implementation tasks (3.2, 5.1/5.2 evidence) remain historical records of what was
  built and verified at the time; the open verification tasks 7.1 and 7.2 stay open and
  must re-verify the amended wording against the final state.

### D2 - No router, navigation unchanged

The existing `<button>`-based navigation stays as is. This change does not touch
`App.tsx` navigation, so `getByRole('button', { name: ... })` selectors and
`aria-current` behavior are preserved.

## Dependency analysis (verified before removal)

| Question | Finding |
| --- | --- |
| Render site | `frontend/src/layouts/AppLayout.tsx` lines 2 and 12: single mount point, inside the root layout, so it appears on every view |
| State | Local `useReducer(healthReducer)` plus an abort `useRef`; no Zustand, context or props |
| Service | `frontend/src/health.ts` fetches `/api/health` with a 5 s timeout and validates the exact `{"status":"ok"}` body |
| Other consumers | `health.ts` and `healthState.ts` are imported only by `HealthPanel.tsx` and by `tests/health.test.ts` / `tests/healthState.test.ts` |
| Functional coupling | None: no auth, CSRF, session, CU01–CU10 or assistant module reads the response |
| Backend | `backend/app/main.py` `GET /health` is unchanged and used by Compose health checks and `scripts/Test-HealthProxy.ps1` |
| Panel-only frontend check | The layout's automatic `/api/health` request disappears with the component; nothing else must be disabled |
| End-to-end tests | No e2e asserts the panel text. `cu01`, `cu02`, `cu03`, `cu03-auth` and `cu10` only contain defensive `/api/health` mock branches, which become inert and stay harmless |

## Removal approach

1. Remove the import and element from `AppLayout.tsx`; the layout keeps
   `<main>`/`<h1>`/children/`ChatMount`.
2. Delete `HealthPanel.tsx`, `health.ts`, `healthState.ts`.
3. Delete the two exclusive unit test files.
4. Delete the `.health-panel` style block in `styles.css`, keeping `@theme` and base
   rules intact.
5. Keep the `/api` proxy, backend endpoint and the scripts' checks untouched; only
   the obsolete "Follow the README browser steps" closing message of
   `Test-HealthProxy.ps1` is corrected, because that browser step no longer exists.

## Verification strategy

- Static gates: `npm run typecheck`, `npm run lint`, `npm test`, `npm run build`.
- Structural gate: `openspec validate --all --strict` (all changes and specs).
- Focused E2E: Cortes, Trabajos and Mi cuenta (anonymous and authenticated when the
  local stack is available), asserting the panel texts are absent, navigation still
  works, and no `/api/health` request is issued by the layout. Existing defensive mocks
  are extended with a positive assertion instead of being deleted.
- Technical health: `scripts/Test-HealthProxy.ps1` outcome or an equivalent HTTP check
  (`GET /health`, `GET /api/health`) proves the retained endpoint; if the stack is not
  running this is reported as BLOCKED, never PASS.
- Regression breadth is limited to the shell and CU01/CU02/CU09 navigation paths.
  Broader CU04–CU08/CU10 coverage is not required because no functional module changes;
  any environment-dependent spec that cannot run stays BLOCKED (including the deferred
  QA-INT-CU04-08 set).

## Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Deleting the health tests looks like weakening coverage | The tests exercised a removed feature; the retained HTTP contract is verified by script/HTTP checks and the spec delta states the new expectation explicitly |
| E2E suites rely on the panel or on `/api/health` mocks | No test asserts the panel; mocks stay and a no-request assertion is added |
| Docker change regains a contradiction at archive time | Its delta is corrected in the same change, with no task checked, no archive and an explicit decision record |
| Accidental scope creep into the deferred redesign | Only the removal and reconciliation files are edited; `App.tsx`, tokens and screens are untouched |
| Environment unavailable for E2E | Report BLOCKED with the exact command and what could not be executed |

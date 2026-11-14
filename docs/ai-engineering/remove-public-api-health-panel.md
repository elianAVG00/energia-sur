# Public API health panel removal

## Links

- [Change proposal](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/proposal.md),
  [design](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/design.md),
  [tasks](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/tasks.md),
  [spec delta](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/specs/frontend-shell/spec.md)
- [Decision U26](../use-cases/decisions.md)
- [Frontend shell spec](../../openspec/specs/frontend-shell/spec.md)
- [Docker environment delta (corrected)](../../openspec/changes/docker-development-environment/specs/development-environment/spec.md)

## Goal

Remove the visible "Conexión con la API" panel from every Energía Sur view without
changing backend behavior, API contracts or feature logic, and reconcile the
specifications that required it. Deferred work (header/navigation redesign, chat FAB,
CU01 visual layout, initial landing change) is explicitly out of scope.

## User instructions used

The 2026-11-14 BUILD instruction authorized: creating the bounded change
`remove-public-api-health-panel`, removing the panel and its exclusive modules/tests,
keeping `GET /health`, the Vite proxy and the technical scripts, correcting only the
affected `development-environment` requirement inside the active Docker change, not
completing its open tasks, not archiving any change, recording the decision, and running
the static plus focused E2E checks. It also confirmed D1-D7 (no router, system fonts,
chat FAB later, incremental visual work, logout later, landing unchanged).

## Contradiction found before implementation

The accepted `frontend-shell` requirement demanded that the shared layout retain a
"health panel". At the same time, the still-active `docker-development-environment`
change required a technical screen that displays verified backend success and a visible
error when only `backend` is stopped. Removing the panel therefore contradicted two
specification sources, not just the implementation. `development-environment` existed
only as a delta in that active change, so a `REMOVED` operation from the new change
could not have been applied before it was archived.

Resolution (U26, D1 option A): the new change declares the `frontend-shell` modification,
and the Docker delta was edited in place so the same intent is expressed over HTTP. No
Docker task was checked, and neither active change was archived.

## Implementation

| Area | Change |
| --- | --- |
| `frontend/src/layouts/AppLayout.tsx` | Removed the `HealthPanel` import and element; the layout keeps `main`, `h1`, children and the single `ChatMount` |
| `frontend/src/HealthPanel.tsx` | Deleted |
| `frontend/src/health.ts`, `frontend/src/healthState.ts` | Deleted after confirming their only consumers were the panel and their own tests |
| `frontend/tests/health.test.ts`, `frontend/tests/healthState.test.ts` | Deleted (13 tests for removed code) |
| `frontend/src/styles.css` | Removed the `.health-panel` block and its compatibility comment; tokens and base rules untouched |
| `frontend/e2e/cu01.spec.ts` | Added two focused regression tests: public sections and authenticated shell render without the panel and issue no `/api/health` request |

Unchanged on purpose: backend `GET /health`, Vite `/api` proxy, Compose files,
`scripts/Test-HealthProxy.ps1`, session/CSRF transport, Zustand stores, Zod schemas, the
assistant runtime and every CU01-CU10 HTTP contract.

## Checks

The host has Node 24.11.1 / npm 11.6.2 with an empty `frontend/node_modules` and
`engine-strict=true` against the pinned 24.22.2 / 11.19.1 engines, so the documented
pinned path was used: a `verification`-target image built from `frontend/Dockerfile`
(`node:24.22.2-bookworm-slim`, npm 11.19.1) and the commands were executed inside it.

| Check | Command | Result |
| --- | --- | --- |
| Image build (installs deps, builds, tests, lints) | `docker build --target verification -t energia-sur-frontend-checks:health-removal frontend` | PASS (exit 0) |
| Typecheck | `npm run typecheck` (pinned image) | PASS |
| Lint | `npm run lint` (pinned image) | PASS: 0 warnings, 0 errors, 91 files |
| Unit tests | `npm test` (pinned image) | PASS: 117/117, 0 failed, 0 skipped, ~1.1 s |
| Production build | `npm run build` (pinned image) | PASS (exit 0); pre-existing rolldown "use client" directive notice |
| OpenSpec strict | `openspec validate --all --strict` | PASS: 16/16 items (both active changes included) |
| Focused E2E | `npx playwright test e2e/cu01.spec.ts e2e/cu02.spec.ts` against the running frontend container | PASS: 16/16 in 11.0 s, including the 2 new panel/health-request tests and the authenticated shell |
| Health endpoint | `GET http://127.0.0.1:8000/health`, `GET http://127.0.0.1:5173/api/health` | PASS: both `{"status":"ok"}` |
| Source scan | search for `HealthPanel`, `fetchHealth`, `healthReducer`, `healthState` in `frontend/src` and `frontend/tests` | PASS: no references remain |

New E2E assertions: the public shell visits Cortes, Trabajos and Mi cuenta, and the
authenticated shell visits the diary, Cortes and Mi cuenta; each step asserts that the
"Conexión con la API" heading, the "Volver a comprobar" button and the development copy
are absent, and that zero `/api/health` requests originate from the layout.

## Problem encountered during verification

The Compose `frontend` service mounts `./frontend/src:/app/src:ro`. After deleting the
modules, Vite kept serving a stale transform that still imported `HealthPanel`, so the
running dev server returned a module for a deleted file. The container source was
already correct (`grep` inside the container showed no reference); restarting only
`energia-sur-frontend-1` cleared the transform cache, after which the served layout had
zero `HealthPanel` references. This is a dev-server cache effect of the bind mount, not
an application defect, but it must be remembered when reviewing in a running stack.

## Closure review and archive (2026-11-14)

The full diff was reviewed against the BUILD report. No accidental code change or
unrelated behavior change was found. Two documentation defects were corrected before
archiving:

- `README.md` still contained an `Acceptance A - manual browser verification` procedure
  asking to click **Volver a comprobar**, a control that no longer exists. It now
  documents direct/proxied HTTP success, stop-`backend` failure and restore.
- `scripts/Test-HealthProxy.ps1` ended with `UI ACCEPTANCE PENDING ... Follow the README
  browser steps`. Its checks are untouched; only that closing message now states that
  health is not an interface contract (U26).

Focused verification rerun on the real working tree, inside
`energia-sur-frontend-checks:health-removal` (pinned Node 24.22.2 / npm 11.19.1):

| Check | Command | Result |
| --- | --- | --- |
| Typecheck, lint, unit tests | `npm run typecheck && npm run lint && npm test` | PASS: 0 warnings/0 errors on 91 files; 117/117 tests |
| Production build | `npm run build` | PASS (exit 0); pre-existing rolldown "use client" notices |
| Focused E2E | `npx playwright test e2e/cu01.spec.ts e2e/cu02.spec.ts` with `E2E_BASE_URL=http://127.0.0.1:5173` and `--network host` | PASS: 16/16 in 9.1 s |
| Health endpoints | `GET http://127.0.0.1:8000/health`, `GET http://127.0.0.1:5173/api/health` | PASS: both `{"status":"ok"}` |
| OpenSpec strict before archive | `openspec validate --all --strict` | PASS: 16/16 |
| Archive | `openspec archive remove-public-api-health-panel --yes` | PASS: archived as `2026-11-14-remove-public-api-health-panel`; `frontend-shell` 1 requirement replaced, +2 scenarios |
| OpenSpec strict after archive | `openspec validate --all --strict` | First attempt FAILED: the merged requirement exceeded 500 characters (`frontend-shell` warning). Archive reverted, delta tightened with no semantic loss, re-archived; final PASS 15/15 |

E2E environment note: the first attempt used the Compose hostname `frontend:5173`.
Vite rejects that unknown host, and reaching the dev server by container IP worked for
14/16 tests but broke the two geolocation tests, because a plain HTTP IP origin is not
a secure context. Running the Playwright container with `--network host` against
`http://127.0.0.1:5173` satisfies the secure-context requirement and the suite passed
16/16. This is a harness/origin constraint, not an application defect.

Archive scope: only `remove-public-api-health-panel` was archived. In
`openspec/specs/frontend-shell/spec.md` only `Shared accessible application layout`
was replaced (0 requirements added or removed, +2 scenarios); the other three
requirements are unchanged. `docker-development-environment` keeps tasks 7.1/7.2 open,
its amended requirement text, and no task was checked; `configure-readonly-development-mcp`
was not touched.

Strict-validation finding after the first archive: the change delta was valid, but the
merged main-spec requirement was longer than 500 characters, which strict spec
validation rejects with a warning. Because nothing had been committed, the archive was
moved back, `openspec/specs/frontend-shell/spec.md` was restored to its pre-archive
state and the delta requirement was tightened (480 characters) without removing any
normative clause: the layout obligations, the prohibition of technical status in every
view and the retained HTTP verifiability all remain, now supported by the three
scenarios. The change was then re-archived and strict validation passed 15/15. This is
recorded because it is a schema-level constraint, not a behavior change.

## Not executed

- Full integral CU01-CU10 regression and real-backend authorized flows (no functional
  module changed; the focused mocked suites and static gates were judged sufficient).
- `scripts/Test-HealthProxy.ps1` end-to-end run (it stops and restores `backend`); the
  direct and proxied health responses were verified instead. The script keeps its
  checks and remains the technical check; only its closing message was corrected.
- `cu09.spec.ts`, which needs the synthetic QA state. Its pre-CU03 assertion that the
  chat mount contains a disabled button remains pre-existing debt, outside this scope.
- The deferred QA-INT-CU04-08 seeded set remains deferred.

## Risks and follow-ups

- 13 unit tests were deleted because they covered the removed feature. The retained
  contract is verified by HTTP and stated in the reconciled specs; this is not a
  weakened application test.
- The `docker-development-environment` requirement keeps its historical name
  ("Real frontend health display and failure state") to avoid a rename on a capability
  that exists only as a delta, while its normative text is now HTTP-based. Its open
  tasks 7.1/7.2 must re-verify that amended wording before that change can be archived.
- The deferred redesign (shell, navigation, chat, CU01) and the landing decision remain
  separate changes.

## Git

Closed with one local commit, `refactor(frontend): remove public API health panel`,
containing the panel removal, the reconciled Docker delta, the `frontend-shell` main
spec update produced by the archive, the README/frontend-foundation/decisions
documentation, the `Test-HealthProxy.ps1` message fix and this record. The archive
directory `openspec/changes/archive/2026-11-14-remove-public-api-health-panel/` is part
of that commit. No push was performed; the earlier local commit `593fed2` also remains
unpushed.

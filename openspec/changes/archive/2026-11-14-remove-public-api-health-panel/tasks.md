# Tasks

Evidence: [`docs/ai-engineering/remove-public-api-health-panel.md`](../../../../docs/ai-engineering/remove-public-api-health-panel.md).

## 1. Baseline and dependency confirmation

- [x] 1.1 Record branch/working-tree baseline and the pending local commit without committing or pushing. — `main...origin/main [ahead 1]`, HEAD `593fed2`; clean tree before edits.
- [x] 1.2 Re-confirm the health panel's mount point, state, service and test consumers before editing. — Single mount in `AppLayout.tsx`; `health.ts`/`healthState.ts` used only by `HealthPanel.tsx` and their two test files; no auth/CU/assistant consumer.

## 2. Spec reconciliation

- [x] 2.1 Add the `frontend-shell` delta removing the visible health-panel requirement and state the retained HTTP verification. — `specs/frontend-shell/spec.md` (MODIFIED, 3 scenarios).
- [x] 2.2 Correct only the `Real frontend health display and failure state` requirement and its scenarios in the active `docker-development-environment` delta, expressing acceptance over HTTP. — Requirement text, Acceptance A and new "Technical health status stays out of every application view" scenario; backend contract requirement untouched.
- [x] 2.3 Keep `docker-development-environment` tasks 7.1 and 7.2 open, do not archive it and do not touch `configure-readonly-development-mcp`. — 7.1/7.2 remain `[ ]`; no archive; MCP change unmodified.
- [x] 2.4 Record decision U26 in `docs/use-cases/decisions.md`. — U25 was already taken by CU10; the next free identifier was used and the substitution is stated in the record.

## 3. Frontend removal

- [x] 3.1 Remove the `HealthPanel` import and element from `frontend/src/layouts/AppLayout.tsx`. — Import and `<HealthPanel />` gone; layout keeps `main`/`h1`/children/`ChatMount`.
- [x] 3.2 Delete `frontend/src/HealthPanel.tsx`, `frontend/src/health.ts` and `frontend/src/healthState.ts`. — Deleted.
- [x] 3.3 Delete the exclusive unit tests `frontend/tests/health.test.ts` and `frontend/tests/healthState.test.ts`. — Deleted (13 tests for removed code).
- [x] 3.4 Remove the `.health-panel` style block from `frontend/src/styles.css` without affecting other rules. — Panel block and its compatibility comment removed; `@theme` and base layer intact.
- [x] 3.5 Confirm no remaining source, test or configuration reference to the removed modules. — `HealthPanel|fetchHealth|healthReducer|healthState` scan over `frontend/src` and `frontend/tests` returns nothing; only inert defensive `/api/health` mocks remain in e2e.

## 4. Static verification

Executed inside the pinned `verification` target of `frontend/Dockerfile` (Node 24.22.2 / npm 11.19.1), because the host has Node 24.11.1 / npm 11.6.2 and `engine-strict=true` with an empty `node_modules`.

- [x] 4.1 `npm run typecheck` in `frontend/`. — PASS.
- [x] 4.2 `npm run lint` in `frontend/`. — PASS: 0 warnings, 0 errors, 91 files.
- [x] 4.3 `npm test` in `frontend/`. — PASS: 117/117, 0 failed, 0 skipped.
- [x] 4.4 `npm run build` in `frontend/`. — PASS (exit 0); pre-existing rolldown "use client" directive notice only.
- [x] 4.5 `openspec validate --all --strict`. — PASS: 16/16 (both active changes and all main specs).

## 5. Focused end-to-end verification

- [x] 5.1 Cortes, Trabajos and Mi cuenta render without the panel, without the texts "Conexión con la API"/"Volver a comprobar" and without layout-originated `/api/health` requests. — PASS: new `cu01.spec.ts` tests for the public shell (all three sections) and the authenticated shell; zero `/api/health` requests observed.
- [x] 5.2 Existing navigation between the three sections still works, including the authenticated account state when the local stack is available. — PASS: `cu01.spec.ts` + `cu02.spec.ts` 16/16 against the running frontend container, including the authenticated diary/Cortes/Mi cuenta path.
- [x] 5.3 Retained technical health verification responds correctly (`GET /health` and proxied `/api/health`), or is recorded as BLOCKED with the exact command if the stack is unavailable. — PASS: `http://127.0.0.1:8000/health` and `http://127.0.0.1:5173/api/health` both `{"status":"ok"}`. `scripts/Test-HealthProxy.ps1` was not run (it stops and restores `backend`); it is unchanged and remains the technical check.

Not executed, and not reported as PASS: full integral CU01–CU10 regression, real-backend authorized flows, `cu09.spec.ts` (needs synthetic QA state) and the deferred QA-INT-CU04-08 set. No functional module changed, so the focused suites were judged sufficient.

## 6. Documentation and close

- [x] 6.1 Update `docs/STATE.md`. — Updated 2026-11-14, 60 lines, panel section plus revised blockers/next actions.
- [x] 6.2 Update `docs/frontend-foundation.md` where it still expects a health panel regression check. — Item 6 now states health is not a UI contract and is verified over HTTP (U26).
- [x] 6.3 Write `docs/ai-engineering/remove-public-api-health-panel.md` with the original contradiction, decision, implementation, checks and redacted evidence. — Written and indexed in `README.md`.
- [x] 6.4 Report final Git status; no commit, push or archive. — Reported at the end of the BUILD session; the working tree was left uncommitted, `593fed2` unpushed and no archive performed.
- [x] 6.5 Reconcile the obsolete `Acceptance A - manual browser verification` README section and the `Test-HealthProxy.ps1` closing message with the amended HTTP acceptance. — README now documents direct/proxied HTTP success, stop-backend failure and restore; the script keeps its checks and only its final message no longer points to a removed browser step.

## 7. Review, archive and commit

- [x] 7.1 Review the full diff and rerun focused verification against the real working tree. — Diff reviewed: no code change outside the removal/reconciliation scope; `docs/STATE.md` only compacts older sections within its 60-line limit. `npm run typecheck`, `npm run lint` (0 warnings, 91 files) and `npm test` (117/117) PASS inside `energia-sur-frontend-checks:health-removal`; mocked `cu01.spec.ts` + `cu02.spec.ts` Playwright 16/16 against the running dev server; `GET /health` and `/api/health` both `{"status":"ok"}`; `openspec validate --all --strict` 16/16.
- [x] 7.2 Archive only `remove-public-api-health-panel`, verify the `frontend-shell` replacement and revalidate strictly. — First archive attempt merged a requirement longer than 500 characters, which strict spec validation rejects; nothing was committed, so the archive was reverted, the delta requirement was tightened without dropping a normative clause, and the change was re-archived as `2026-11-14-remove-public-api-health-panel`. Only `Shared accessible application layout` was replaced (+2 scenarios, 0 removed); `docker-development-environment` (tasks 7.1/7.2 open) and `configure-readonly-development-mcp` were untouched; strict validation 15/15 after the final archive.
- [x] 7.3 Update `docs/STATE.md` and the engineering record with the final archived paths, checks and limitations. — Done.
- [x] 7.4 Commit the change and its documentation reconciliation in one commit; no push. — Commit `refactor(frontend): remove public API health panel`; local only.

# CU10 source-refresh administration - engineering record

Updated: 2026-11-13. Status: **implemented, verified and archived** as
`2026-11-13-supervise-source-refresh-cu10`. No commit or push was performed.

## Goal and links

Add an administrator-only layer to observe the automatic ENRE source refresh, request a
synchronous retry and configure the refresh interval per source, reusing the CU01/CU02
schedulers, advisory locks, fetch runs and snapshots.

- Change: `openspec/changes/supervise-source-refresh-cu10/`
- Fiche: `docs/use-cases/cu10.md`; decisions: U24, Q21, Q22, Q04
- Shared rules: SR03, SR05
- Reused unchanged in contract: `openspec/specs/current-outages/spec.md`,
  `openspec/specs/scheduled-works/spec.md`

## Backend (BUILD 1)

- `backend/app/models.py`: `Account.role` (`user`/`admin`, default `user`) and
  `SourceConfig` (`source_key`, `interval_seconds`, `version`).
- `backend/migrations/versions/0008_cu10.py`: additive role column and `es_source_config`
  seeded with `('outages',300,1)` and `('scheduled_works',300,1)`.
- `backend/app/source_config.py`: allowed interval set, safe `get_interval` (300 fallback)
  and atomic `set_interval`.
- `backend/app/outage_store.py`, `backend/app/scheduled_store.py`: `refresh_now()` plus a
  shared lock wrapper; `refresh_once()` behavior preserved; a busy retry raises
  `SourceBusy` without recording a run.
- `backend/app/admin_api.py`: `GET /admin/sources`, `POST /admin/sources/{key}/refresh`,
  `PATCH /admin/sources/{key}/interval`; `require_admin`/`admin_writer`.
- `backend/app/main.py`: admin router, 409/422 handlers, per-cycle `next_interval` and
  `run_cycle` with safe fallback.
- `backend/app/api.py`, `backend/app/schemas.py`: additive `role` in the session/account
  response, failed closed to `user`.
- `backend/app/promote.py`: controlled promotion CLI; `provision.py` unchanged.

## Frontend (BUILD 2)

- `frontend/src/features/admin/api.ts`: typed guards for `SourcesOut`, `IntervalOut` and
  `RefreshOut`; shared client for reads/writes; a dedicated retry transport with a 25 s
  timeout.
- `frontend/src/features/admin/state.ts`: interval, source and outcome labels.
- `frontend/src/features/admin/AdminPanel.tsx`: two ENRE cards with real last attempt,
  outcome, last success, error, skipped-lock time, interval and scheduler configuration;
  interval selector with the five allowed values; synchronous retry; 401/403/409/422/timeout
  handling; conflict reload without overwrite; initial-load retry.
- `frontend/src/diaryApi.ts`: optional `role` in the session contract, validated when present.
- `frontend/src/lib/http.ts`: optional per-client timeout (default 10 s); used only for the
  CU10 retry (25 s).
- `frontend/src/lib/httpError.ts`: adds `SOURCE_BUSY` to the typed error code.
- `frontend/src/App.tsx`: `'admin'` view, conditional "Administración" nav and redirect for
  non-admins.
- `frontend/tests/admin-api.test.ts`, `frontend/tests/admin-state.test.ts`,
  `frontend/e2e/cu10.spec.ts`, `frontend/e2e/cu10-real.spec.ts`.
- `backend/tests/test_cu10_admin.py`: adds the controlled next-cycle test.

## Agents and tools used

- Primary agent: implementation, Docker-image checks, isolated PostgreSQL databases, Ruff,
  mypy, migrations, frontend typecheck/test/lint/build and Playwright.
- `reviewer` (read-only): independent audits of BUILD 1 (authorization, concurrency,
  data integrity) and BUILD 2 (contract compatibility, error/outcome handling, conflicts,
  timeout, regressions, architecture).
- `spec-analyst` (read-only) was used at proposal time.

## Review results and corrections

- BUILD 1: no BLOCKER/HIGH; MEDIUM/LOW findings addressed or documented.
- BUILD 2: no BLOCKER. The HIGH finding (25 s deadline not recorded and the foundation doc
  forbidding overrides) was addressed by recording the user-approved BUILD 2 deadline in
  U24 and updating `docs/frontend-foundation.md`. MEDIUM/LOW corrections: render
  `last_skipped_locked_at`, add an initial-load retry, remove the card-wide live region and
  duplicated labels, replace the DOM cast with an option lookup, branch the timeout copy
  for saves, and add role/cycle/timeout assertions.
- The reviewer noted the real-backend E2E gap; `cu10-real.spec.ts` now covers admin login,
  both cards, real status, a real interval PATCH, stale-version 409, missing-CSRF 403 and
  non-admin 403 with synthetic QA accounts.

## Checks performed (2026-11-13)

| Check | Result | Evidence |
| --- | --- | --- |
| Backend Ruff | PASS | image `energia-sur-backend-checks:cu10`, exit 0 |
| Backend mypy | PASS | 53 source files, exit 0 |
| CU10 backend tests | PASS | 30/30 `tests.test_cu10_admin` |
| Backend regression set | PASS | 190 tests (CU10+CU01+CU02+security+health+api+diary+CU03 tools/memory), 6 skipped live |
| CU04 backend | PASS | 25 tests, 1 skipped |
| Migration upgrade/downgrade/upgrade | PASS | 2 → 0 → 2 config rows; role column added/removed |
| `provision` + `promote` CLI | PASS | provision unchanged; role `user` → `admin`; hash unchanged |
| Frontend typecheck | PASS | `tsc --noEmit` |
| Frontend unit tests | PASS | 142/142 |
| Frontend lint | PASS | Oxlint, 0 warnings/errors |
| Frontend production build | PASS | image `energia-sur-frontend-checks:cu10` |
| Mocked CU10 Playwright | PASS | 9/9 |
| Real-backend CU10 Playwright | PASS | 1/1 with synthetic QA admin/user |
| Mocked navigation/auth regressions | PASS | CU01, CU02, CU03-auth, CU03 (18 tests) |
| `openspec validate --strict` | PASS | change valid |

## Archive

`openspec archive supervise-source-refresh-cu10 --yes` archived the change as
`openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/` and updated the main
specs: 12 requirements added to `openspec/specs/source-refresh-administration/spec.md` and
the cadence clause modified in `current-outages`/`scheduled-works` (no other requirement
changed). `openspec validate --all --strict` reports 15/15 items valid and the active-change
list no longer contains CU10. The archive retains proposal, design, tasks, README,
`.openspec.yaml` and the three spec deltas.

## Pre-existing failures (not CU10)

- 6 backend failures in CU05/CU06 bill/photo tests (bill 503s, OCR/log-count) reproduce
  identically on the pre-CU10 `cu03` image; not fixed here.
- 1 CU05 history E2E failure (`9007199254740993 kWh` still visible after switching meters)
  reproduces identically on the pre-CU10 `cu03` image.
- CU04/CU09 real Chromium specs need external QA state (`QA_USERNAME_A`, seeded state
  files) and were not run in this environment.

## Residual risks and limitations

- The synchronous retry can hold request/pool connections for the ENRE fetch duration;
  accepted for the admin-only two-source scope.
- A retry can outlast the 25 s client deadline (per-operation ENRE timeouts); a client
  timeout is reported as unconfirmed and followed by a real status GET, never as success or
  a failed acquisition.
- `RefreshOut` metadata is read from the latest run after the retry; a very close scheduler
  cycle could theoretically make a detail field refer to another run.
- PostgreSQL persistence across a restart is evidenced by the idempotent migration
  re-upgrade and the persisted `es_source_config` row; the per-cycle 300→600 read is
  covered by the bounded `run_cycle` test.
- A missing config row yields 503 on the admin status while the scheduler falls back to 300.
- `scheduler_enabled` reports configuration, not task liveness.
- The dev database now contains synthetic QA accounts (`cu10_qa_admin_*`, `cu10_qa_user_*`)
  created for the real E2E; no existing data or accounts were deleted.

## Task status

32/32 tasks complete and archived. Task 5.3 used the approved controlled-timing check
(same-process 300→600 next-cycle read) instead of a wall-clock 5/10-minute wait.

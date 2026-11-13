# Tasks

## 1. Persistence, migration and roles

- [x] 1.1 Add `role` to the `Account` model (Python `default="user"` and matching `server_default`) and `SourceConfig` to `models.py`, with `role IN ('user','admin')` and `interval_seconds IN (300,600,900,1800,3600)` constraints — PASS: models import; Ruff/mypy clean; constraints present
- [x] 1.2 Add additive Alembic migration `0008_cu10` adding `es_accounts.role` (`DEFAULT 'user'`) and creating `es_source_config`, seeded with `('outages',300,1)` and `('scheduled_works',300,1)` — PASS: upgrade seeded 2 rows; downgrade removed table/schema; re-upgrade restored 2 rows; applied additively to the dev database in BUILD 2
- [x] 1.3 Add a **new** `app/promote.py` CLI (`promote --username`) that sets `role='admin'` for an existing account and never accepts a role from arguments, leaving `app/provision.py` unchanged — PASS: existing `provision --password-stdin` works; promote changed only the role; password hash unchanged; missing username exits without creating
- [x] 1.4 Add backend tests for the migration, the untouched provision command and the promotion path — PASS: `tests.test_cu10_admin` migration/role/promote tests

## 2. ADMIN authorization

- [x] 2.1 Add `require_admin` (over `current`) and `admin_writer` (over `mutation`) that load the stored account role and return 403 for non-admins — PASS: 401 unauthenticated, 403 for `user`, success for `admin`
- [x] 2.2 Include `role` additively in `AccountOut`/`session_out` without changing existing fields — PASS: `/login` and `/session` expose `role`; existing session tests pass
- [x] 2.3 Add security tests proving a `user` cannot reach admin endpoints even when the request or frontend claims `admin`, and that the assistant has no admin tool — PASS: all admin routes 403 for `user`; `assistant_tools.TOOLS` is only `current_outages`/`scheduled_works`; real E2E confirms non-admin 403

## 3. Persistent configuration and optimistic control

- [x] 3.1 Add `app/source_config.py` with `ALLOWED_INTERVALS`, `get_interval` (safe `300` default for a read error, missing row, missing table or `None`) and `set_interval` (atomic `UPDATE ... WHERE version = :v RETURNING`) — PASS: allowed/invalid values, increment and fallback paths covered
- [x] 3.2 Define `SourceBusy` and `VersionConflict` in `source_config.py`/the stores and register 409 handlers with `SOURCE_BUSY` and `VERSION_CONFLICT` codes next to the existing handlers — PASS: both codes and `Cache-Control: no-store` asserted; stale update leaves the value unchanged
- [x] 3.3 Add PostgreSQL concurrency tests for two administrators changing the same interval and for per-source isolation — PASS: one winner/one 409; changing `outages` leaves `scheduled_works` unchanged

## 4. Manual retries with mutual exclusion

- [x] 4.1 Add `refresh_now()` and `SourceBusy` to `outage_store.py` and `scheduled_store.py`, reusing `_refresh_locked` and each store's existing advisory-lock key, and release the lock in `finally` — PASS: manual call runs the shared acquisition; a lost lock raises `SourceBusy` without writing a run
- [x] 4.2 Map `SourceBusy` to HTTP 409 with `code: "SOURCE_BUSY"` and no enqueue, and return HTTP 200 with the real persisted outcome for a completed attempt (including failures) — PASS: busy 409 with unchanged run count; failed acquisition returns 200 with its real outcome
- [x] 4.3 Add concurrency tests for scheduler-vs-manual and per-source independence — PASS: same source yields one run and a 409; the other source still runs

## 5. Dynamic interval integration in schedulers

- [x] 5.1 Extract a testable per-cycle function (`next_interval` + `run_cycle`) and replace the startup-only env read in `_outage_scheduler` and `_scheduled_works_scheduler` with a `get_interval` read inside each loop before `sleep` — PASS: bounded `run_cycle` test observes the configured interval
- [x] 5.2 Guard each cycle so a configuration read failure (including no row or missing table) falls back to `300`, is logged, and still reaches the sleep — PASS: `next_interval` fallback and `run_cycle` survive a failing refresh
- [x] 5.3 Verify persistence across a restart and record a manual runtime check — PASS (controlled timing per the user instruction): a bounded `run_cycle` test reads 300, applies a PATCH to 600 in the same process, and the second cycle reads 600; migration/CLI checks confirm persistence. No wall-clock 5/10-minute wait was used.

## 6. Administrative API

- [x] 6.1 Add `app/admin_api.py` with `GET /admin/sources` returning both sources' last attempt, outcome, last success (or null), error, interval/version, last skipped-lock time and scheduler-enabled flag derived from existing records — PASS: contract test covers success, failure and empty history
- [x] 6.2 Add `POST /admin/sources/{key}/refresh` running `refresh_now` in the threadpool and returning the real outcome — PASS: success and failure outcomes returned; last success preserved
- [x] 6.3 Add `PATCH /admin/sources/{key}/interval` using a strict schema (`interval_seconds` in the allowed set, `version > 0`, extra fields forbidden) — PASS: valid update, 422 invalid, 409 `VERSION_CONFLICT`
- [x] 6.4 Resolve `{key}` explicitly to `outages`/`scheduled_works` (unknown → 404 after authorization) and register the router with `no_cache` in `main.py` — PASS: unknown key 404, `no-store` present, `/health` independent
- [x] 6.5 Add API tests for 401, 403, CSRF and Origin — PASS: GET needs no CSRF; mutations without CSRF or with an untrusted Origin return 403; real E2E confirms CSRF 403

## 7. Administrative frontend

- [x] 7.1 Add `role` to the frontend `Account`/`Session` types and the `isSession` guard (frontend and backend deploy together) — PASS: optional role accepted for `user`/`admin`, unknown rejected; existing sessions without role still valid
- [x] 7.2 Add `features/admin/` pure modules for typed responses, strict runtime guards, interval validation and conflict/busy state, tested with Node — PASS: unit tests reject malformed payloads, invalid intervals and mismatched codes
- [x] 7.3 Add `AdminPanel` with two ENRE cards showing real state, timestamps, error, retry and a five-value interval selector — PASS: mocked Playwright renders both cards with real fields
- [x] 7.4 Add the `'admin'` view and a conditional "Administración" nav entry visible only to `role === 'admin'`, and document the reload needed after promotion — PASS: admin/user/anonymous mocked flows; promotion reload documented
- [x] 7.5 Handle 401, 403, 409 `VERSION_CONFLICT` and 409 `SOURCE_BUSY`, using a panel-specific 403 message and a documented longer deadline for the retry — PASS: mocked E2E covers conflict, busy, failure outcome and timeout; retry uses 25 s only

## 8. Backend, frontend and end-to-end tests

- [x] 8.1 Run the full backend suite on an isolated PostgreSQL, including the new CU10 tests — PASS: 30/30 CU10 tests; 6 pre-existing CU05/CU06 environment failures reproduced identically on the pre-CU10 image
- [x] 8.2 Run Ruff and mypy on the backend and lint/typecheck/build/tests on the frontend — PASS: Ruff/mypy; frontend typecheck, 142 tests, lint and production build
- [x] 8.3 Add Chromium flows for the admin panel against the real backend (promoting one synthetic QA account) plus mocked `SOURCE_BUSY` and a slow retry — PASS: mocked CU10 9/9 and real-backend CU10 admin flow 1/1 with synthetic QA admin/user; the real retry call was not invoked to avoid ENRE, and retry/timeout is covered by the mocked flow and backend tests

## 9. CU01/CU02 regression, independent review and documentation

- [x] 9.1 Re-run the CU01/CU02 backend and Chromium regression suites and verify no public contract change — PASS: 30 CU10 + 190-test backend regression set; mocked CU01/CU02/CU03 flows pass; CU05 history failure reproduced on the pre-CU10 image (pre-existing); CU04/CU09 real specs require external QA state
- [x] 9.2 Run an independent read-only review of authorization, data integrity, concurrency and scheduler changes — PASS: no BLOCKER/HIGH; HIGH/MEDIUM/LOW findings addressed or documented
- [x] 9.3 Run `openspec validate supervise-source-refresh-cu10 --strict` and update `docs/STATE.md`, `docs/use-cases/decisions.md` (U24), `docs/use-cases/cu10.md`, `docs/use-cases/shared-rules.md` and `docs/ai-engineering/supervise-source-refresh-cu10.md` with actual results — PASS: validation 1/1; docs updated

## Workflow follow-up

- Apply requires a subsequent explicit user request; BUILD ends at human review.
- Sync and Archive are performed only after the required verification gates pass and are authorized.

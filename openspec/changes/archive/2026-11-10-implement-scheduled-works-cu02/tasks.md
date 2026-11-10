# Tasks

## 0. Pre-build evidence and scope record

- [x] 0.1 Confirm U22, D1-D8 and the definitive-scope wording are recorded in `docs/use-cases/decisions.md` and the CU02 fiche — PASS: U22 with D1-D8 and the definitive scope; the original proposal is preserved as historical context; Q04/Q05 updated
- [x] 0.2 Capture a redacted live `data_EDS.js` payload containing at least one `cortesProgramados` row and add it as an official fixture — PASS: `backend/tests/fixtures/enre_data_eds_scheduled.js` (2026-11-10 11:08 ART, four rows)
- [x] 0.3 Add the 2026-01-14 archived capture whose `normalizacion` is a full date-time as a second fixture — PASS: `enre_data_eds_scheduled_dated.js` (excerpt, `2026-01-14 15:33`)
- [x] 0.4 Confirm `cortesComunicados` remains unobserved populated and no synthetic populated fixture is committed — PASS: `fixtures/README.md` records the provenance and the decision

## 1. Parser

- [x] 1.1 Add `app/scheduled_parser.py` that strips the `var data =` wrapper and parses with JSON5 without executing remote code — PASS: real captures parse; a non-literal payload raises `ScheduledParseError`
- [x] 1.2 Require `empresa == EDESUR` and a list `cortesProgramados`, and validate the row fields — PASS: missing required fields, invalid counts and a non-Edesur feed raise `ScheduledSchemaError`
- [x] 1.3 Record `cortesComunicados` presence and row count without normalizing its rows — PASS: empty, missing, non-list and non-empty cases never fail the maintenance parse
- [x] 1.4 Keep `normalizacion` as text after NFC/whitespace normalization, never as an instant — PASS: `2026-01-14 15:33` survives as text and `planned_end_at` stays null

## 2. Persistence

- [x] 2.1 Add SQLAlchemy models for `es_scheduled_snapshots`, `es_scheduled_works` and `es_scheduled_fetch_runs` — PASS: models import cleanly; `category = 'maintenance'` check
- [x] 2.2 Add the additive Alembic migration `0006_cu02` with the partial unique current-snapshot index — PASS: `alembic upgrade head` on a fresh PostgreSQL; a seeded CU01 row survived upgrade and `downgrade 0005_cu01`, and the CU02 tables were removed on downgrade
- [x] 2.3 Implement snapshot replacement, `not_modified` by `content_sha256`, run recording and retention — PASS: store tests cover 24-snapshot retention, a null `Last-Modified`, and 30-day run pruning

## 3. Refresh and concurrency

- [x] 3.1 Add the CU02 lifespan task gated by `SCHEDULED_WORKS_REFRESH_SECONDS` and `SCHEDULED_WORKS_SCHEDULER_ENABLED` — PASS: the app starts with the task disabled in tests and `/health` is independent
- [x] 3.2 Guard the refresh with `pg_try_advisory_lock(0x43553032)` on a dedicated connection released in `finally` — PASS: one winner, one `skipped_locked`, lock released after a failure and a restart
- [x] 3.3 Keep the last valid snapshot on failure, timeout or unknown schema; a sentinel current-outage total must not freeze CU02 — PASS: `source_degraded` is no longer produced by a sentinel total; parse/schema failures preserve the snapshot

## 4. Public read API

- [x] 4.1 Add `GET /scheduled-works/areas` and `GET /scheduled-works` as public `no_cache` routes — PASS: no session required, `Cache-Control: no-store` asserted
- [x] 4.2 Implement validation, normalized lookup, granularity, coverage, freshness, `source_status` and the state precedence — PASS: API tests cover works-reported, no-works, stale, unavailable, coverage-unverified, 422 and 503
- [x] 4.3 Return the fixed contract with null planned instants/reason, the published restoration text and `limitations`, without totals/coordinates/distance — PASS: contract test asserts every field and the `[]` vs omitted `works` rule
- [x] 4.4 Reject `localidad` without `partido`, overlong values and control characters with 422 — PASS: no store or ENRE access in those cases

## 5. Frontend view

- [x] 5.1 Add `frontend/src/features/scheduled-works/` with a typed client, runtime guard, state labels and panel — PASS: `npm test` and `npm run lint` pass in the pinned frontend image
- [x] 5.2 Implement partido/localidad selection, normalized filter, address search and consented location through the existing resolve endpoints — PASS: Chromium asserts address/location behavior and no direct ENRE/GeoRef request
- [x] 5.3 Render the states, provenance, coverage, "No publicado por la fuente" and the restoration label, with no date inputs — PASS: Chromium asserts the null-field copy and the absence of date controls
- [x] 5.4 Add the "Trabajos" view without a router, keeping the account view as default — PASS: CU01 and CU09 Chromium flows still pass

## 6. Verification gates

- [x] 6.1 Run backend tests for parser, store, retention, locks and API states on an isolated PostgreSQL — PASS: 30/30 CU02 tests (including one live ENRE test)
- [x] 6.2 Run `ruff check` and `mypy` on the backend and frontend lint/typecheck/build/tests — PASS: Ruff and mypy (41 files) clean; frontend image build runs typecheck, tests and lint successfully
- [x] 6.3 Run one Chromium acceptance flow plus the CU09 shell regression — PASS: 5/5 CU02 and 9/9 CU01 Chromium tests
- [x] 6.4 Run CU01 regression and one live ENRE refresh producing a valid CU02 snapshot — PASS: 25/25 CU01 outage tests, 26/26 CU01 territory tests (live ENRE/GeoRef) and the live CU02 test
- [x] 6.5 Run `openspec validate implement-scheduled-works-cu02 --strict` — PASS

## 7. Review and acceptance

- [x] 7.1 Run an independent read-only review of source honesty, CU01 isolation, public-endpoint safety and coverage guards — PASS: no BLOCKER/HIGH runtime defect; the documentation/review findings were corrected (task/state reconciliation, no-works localidad, CU02-only degradation, extra contract tests)
- [x] 7.2 Confirm the definitive scope is documented, the original proposal is preserved and no out-of-scope item is presented as pending — PASS: U22, the fiche and the spec record dates, proximity and the future agenda as out of scope, not pending

## Workflow follow-up

- Apply is authorized by a subsequent explicit user request; BUILD ends at human review.
- Sync and Archive are performed only after the required verification gates pass and are authorized; update the engineering record under `docs/ai-engineering/` at that point.

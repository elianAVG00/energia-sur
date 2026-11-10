# Tasks

## 0. Pre-build validation and approval record

- [x] 0.1 Capture a populated ENRE payload covering `cortesServicioMedia` and `cortesPreventivos` (and `cortesComunicados`) and record their real row shapes; verify only a populated capture resolves the unobserved categories, without assuming HTML columns are JS fields — ACCEPTED EXCEPTION (0.1 final decision, U20): no populated media/preventivo capture was observed; the parser tolerates unknown collections/extra keys, fails closed on invalid rows and preserves the last valid snapshot; synthetic fixtures only, no production claim.
- [x] 0.2 Prove JSON5 compatibility: add `json5`/`httpx` and assert `json5.loads` parses a redacted real capture (after stripping the `var data =` wrapper) plus empty/`N/A`/`'-'`/`'--:--'` fixtures; if it fails, record BLOCKED and request approval for the in-house tokenizer — do not substitute silently
- [x] 0.3 Verify the GeoRef→ENRE name mapping (departamento↔partido, localidad_censal/localidad↔localidad, CABA "CAPITAL") against real responses for the Edesur area, including the province scope and the no-localidad degradation; record the mapping rule or a BLOCKED status — DONE: verified against live GeoRef responses (Quilmes, Lomas de Zamora, CABA, Avellaneda); rule = normalized exact match + CABA→CAPITAL alias + localidad only when the catalog/snapshot knows it.
- [x] 0.4 Obtain the initial verified Edesur coverage catalog (partidos/localidades, source URL, retrieval date) and record its provenance; until supplied, `out_of_coverage` stays BLOCKED and the API returns `coverage_unverified` — ACCEPTED (0.4 final decision, U20): the versioned nine-localidad catalog with documented provenance is approved; unverified zones stay `coverage_unverified`, no coverage is expanded without evidence and no negative result is invented.
- [x] 0.5 Confirm D1–D11 and T1–T3 are recorded in `docs/use-cases/decisions.md` with the Q01/Q02/Q04/Q07 statuses, and verify no requirement traces to an open TBD that contradicts it

## 1. Dependencies

- [x] 1.1 Add pinned `httpx` and `json5` to `backend/pyproject.toml` with `uv add`, regenerate `uv.lock` with `uv lock`, then verify `uv sync --locked` succeeds and the image builds without drift
- [x] 1.2 Confirm no peer/type conflict for the backend after the additions; verify `uv run mypy app` and `uv run ruff check app` pass

## 2. Backend acquisition

- [x] 2.1 Add `app/enre_client.py` with an isolated `httpx` client (`ssl.SSLContext` with `check_hostname=True`, `CERT_REQUIRED`, `set_ciphers("DEFAULT@SECLEVEL=1")`, passed as `verify=<context>`, UA header, 20 s timeout, 256 KB cap, `Cache-Control: no-cache`, same-host redirects only); verify a live read-only fetch returns 200 from the container
- [x] 2.2 Add `app/enre_parser.py` that strips the `var data =` wrapper and parses the object literal with `json5`, rejecting any executable construct; verify the redacted fixture and the edge fixtures parse
- [x] 2.3 Add normalization (`NFC`, uppercase partido/localidad keys, thousands-dot numeric parsing, `N/A`/`'-'` degradation detection) and a validator that is strict on required fields and value ranges while tolerating additional unknown keys; verify extra-key fixtures still parse and missing-required fixtures produce `schema_error`

## 3. Persistence and migration

- [x] 3.1 Add SQLAlchemy models for `es_outage_snapshots` (including `last_checked_at` and `is_current`; public status derived from the latest run), `es_outage_reports` and `es_outage_fetch_runs` and verify the models import cleanly
- [x] 3.2 Add the additive Alembic migration `0005_cu01` with the three tables, indexes and the `is_current` partial unique index; verify `alembic upgrade head` succeeds on a fresh PostgreSQL and does not alter existing tables
- [x] 3.3 Implement `app/outage_store.py` upsert semantics (supersede previous snapshot, insert rows, write a run record) and verify an unchanged `content_sha256` records `not_modified` while updating `source_last_modified`/`fetched_at`/`last_checked_at` without duplicating rows or drifting to stale
- [x] 3.4 Implement bounded retention (current snapshot plus N recent, prune older snapshots/reports; 30-day fetch-run history) and verify the prune keeps the current snapshot and its rows

## 4. Scheduler and concurrency

- [x] 4.1 Add a 5-minute refresh task to the FastAPI lifespan using `run_in_threadpool`, with a scheduler enable/disable flag for tests; verify it starts/stops cleanly and the health endpoint stays independent
- [x] 4.2 Guard the refresh with `pg_try_advisory_lock` on a dedicated connection released by `pg_advisory_unlock` in `finally`; verify two concurrent attempts produce one persisted snapshot and a `skipped_locked` run for the loser, and that a restart does not leave the lock held
- [x] 4.3 Verify a failure/timeout/`N/A` keeps the last valid snapshot and writes the correct `outcome` run row; verify `no_reports` is never produced on a failed refresh

## 5. Public read API

- [x] 5.1 Add `app/outages_api.py` with public `GET /outages/areas` and `GET /outages?partido=…&localidad=…` (no `Auth`, `no_cache`), reading only the snapshot and catalog; verify a visitor reaches them without a session and they return `Cache-Control: no-store`
- [x] 5.2 Accept a required partido and an optional localidad, reject localidad without partido and overlong/control-character input (partido and localidad >120, address >300) with 422, and report the matched granularity; verify each case
- [x] 5.3 Implement freshness classification (including a missing/malformed `Last-Modified` yielding `unavailable`) and the normative `state` enum with precedence (`geographic_error`, `out_of_coverage`, `unavailable`, `stale`, `reported`, `no_reports`, `coverage_unverified`), returning HTTP 200 for snapshot-based states and 503 only for database unavailability, plus `source_status`; verify each state
- [x] 5.4 Enforce category scoping (`medium_voltage`/`low_voltage`/`preventive`), distributor-wide totals with `totals_scope`, zone-level matching and normalized lookup; verify programmed/comunicado rows are excluded, totals are labelled, and `no_reports` requires a fresh covered snapshot

## 6. Backend GeoRef adapter and coverage

- [x] 6.1 Add `app/georef.py` with forward lookup (province-scoped, multiple candidates, no-localidad degradation) and reverse lookup (departamento→partido, localidad only when present), addresses and coordinates sent in a body and never logged or persisted, and a per-client rate limit returning 429 with `Retry-After`; verify candidates, degradation, rate limiting and `geographic_error` — DONE: `app/georef.py` forward/reverse, Buenos Aires/CABA scope, candidate selection, partido degradation, body-only inputs and 429 rate limit.
- [x] 6.2 Load the versioned coverage catalog and expose the three-valued coverage through `/outages/areas` as catalog ∪ snapshot rows; verify a covered area with zero reports is selectable with `no_reports` — DONE: `app/coverage.py` plus the versioned catalog; `/outages/areas` is catalog ∪ snapshot and `/outages` uses three-valued coverage.

## 7. Frontend feature

- [x] 7.1 Add `frontend/src/features/outages/` (api client, store, panel) with the partido→optional-localidad selector and a normalized text search; verify the selectors render snapshot and catalog data — DONE: `features/outages/api.ts` + panel; partido→optional-localidad selector from `/outages/areas`, normalized "Buscar zona" filter and GeoRef address search.
- [x] 7.2 Render category chips, per-record cards (affected users, `subestacion_alimentador`, `normalizacion` verbatim), distributor-wide totals and the provenance header (ENRE link, ART reported time, UTC fetch time, freshness badge); verify each renders — DONE: category table, affected users, substation, verbatim normalización, Edesur-scope totals and provenance (source link, ART times, freshness/coverage badges).
- [x] 7.3 Implement the states (loading, reported, no reports, stale, unavailable, out-of-coverage, coverage unverified, geographic error) plus address input and consented geolocation; verify each state and input is reachable — `loading` is a UI state outside the normative enum — DONE: state headings/details, address candidates, consented geolocation, geographic/connection/429 messages; `loading` remains UI-only.
- [x] 7.4 Add the public view switch in `App.tsx`/`AppLayout.tsx` and the narrow public-POST allowlist in `lib/http.ts` (no CSRF; same-origin cookies unchanged) without a router; verify a visitor sees CU01 without a session, the authenticated CU09 view still renders, the resolve POSTs are not rejected, and the browser makes no direct ENRE or GeoRef request - DONE: "Cortes"/"Mi cuenta" switch without a router; allowlist for the two public POSTs; Chromium asserts no direct ENRE/GeoRef request.

## 8. Verification gates

- [x] 8.1 Add backend unit/API tests covering parsing (incl. extra keys), normalization, degradation and `source_status`, a missing `Last-Modified`, freshness thresholds, the state enum and HTTP semantics, category scoping, totals labelling, partido-only queries, advisory-lock concurrency, `skipped_locked`, snapshot preservation (the throttled-resolve 429 case belongs to task 6.1 and is not exercised here); verify `uv run pytest` passes on isolated PostgreSQL - PASS: 51/51 CU01 tests on a fresh PostgreSQL 18.6, including the env-gated live ENRE/GeoRef tests (the suite runs via `python -m unittest`; pytest is not a project dependency).
- [x] 8.2 Add frontend tests for the selectors, all states including `coverage_unverified`, the provenance header, category presentation and the resolve retry message; verify `npm test` passes - PASS: 106/106 Node tests for API/state/http contracts; selectors, provenance and state rendering are covered by the Chromium flows in 8.3.
- [x] 8.3 Run one Chromium acceptance flow (visitor sees reported / no-reports / stale without a session, no direct ENRE/GeoRef request) and a CU09 shell regression; verify both pass - PASS: 9/9 mocked CU01 Chromium flows, 1/1 real-backend CU01 smoke (partido-only, low-voltage omitted fields, covered no-reports) and the real CU09 E2E (1/1).
- [x] 8.4 Run `uv run ruff check` and `uv run mypy app` (zero new warnings), `npm run lint`, `npm run typecheck` and `npm run build`; verify PASS - backend Ruff/mypy PASS (38 files); BUILD 3 frontend 106/106 Node tests, Oxlint 0 warnings/errors, TypeScript and production build PASS.
- [x] 8.5 Run `openspec validate --strict` for this change; verify PASS with no delta/spec warnings — PASS.

## 9. Review and acceptance

- [x] 9.1 Confirm blockers 0.1-0.4 are either resolved or recorded as BLOCKED with evidence, and that the coverage/GeoRef modes are not presented as working when their contract is unverified — 0.1 and 0.4 are accepted as documented exceptions (U20); 0.3 DONE; the API returns three-valued coverage and never asserts out-of-coverage.
- [x] 9.2 Run a focused independent review of parser safety (no remote code execution), provenance/freshness correctness, public-endpoint isolation and the GeoRef/coverage guards; record PASS/FAIL/BLOCKED with evidence and correct any findings — PASS: independent reviews returned APPROVED for human review across BUILD 1–3; the BUILD 3 HIGH contract mismatch was fixed and re-confirmed.

## Workflow follow-up

- Apply is authorized by a subsequent explicit user request; PROPOSE ends at human approval.
- Sync and Archive are performed only after the required verification gates pass and are authorized; update the engineering record under `docs/ai-engineering/` at that point.

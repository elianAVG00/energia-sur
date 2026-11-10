# CU02 maintenance works consultation (definitive scope) - engineering record

Status: **COMPLETED / ARCHIVED (definitive scope U22)**; main spec synced; no push.
Change: [proposal](../../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/proposal.md),
[design](../../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/design.md),
[delta spec](../../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/specs/scheduled-works/spec.md),
[tasks](../../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/tasks.md).
Decisions: [U22](../use-cases/decisions.md#u22---cu02-definitive-scope-redefinition)
(definitive scope) and [U21](../use-cases/decisions.md#u21---cu02-reduced-scope-and-propose-authorization)
(historical reduction, D1-D8).

## Goal and approved scope

Show the ENRE-reported maintenance works (`cortesProgramados`) for a partido with an
optional localidad, with provenance, publication freshness, three-valued coverage and
explicit limits for unpublished fields. The definitive scope (U22) is public
consultation with partido/localidad filtering, address/GPS assistance, feeder, affected
users, published restoration estimate, provenance, coverage and availability.
`cortesComunicados` is counted and flagged but not displayed, and the Edesur
`outage-report` agenda is out of scope.

Future agenda, temporal filters, planned start/end, unpublished reasons and distances
are **out of scope by design**, not pending tasks. The original academic proposal is
preserved in the CU02 fiche; U21 records the historical reduction.

## Authorization and agents

- User BUILD instruction on 2026-11-10 authorized documentation plus implementation of
  the initial reduced scope (later redefined in U22), and resolved the pending decision
  to reuse `enre_parser.normalized_key` without duplicating it. The user's FINALIZE
  instruction redefined the definitive scope in U22; no new behavior was added.
- OpenCode implemented the change; an independent read-only `reviewer` audited it.
  `spec-analyst` had audited the scope during PLAN.
- Docker provided the pinned Python 3.13 / Node 24.22.2 runtimes, an ephemeral
  PostgreSQL 18.6 instance and Chromium.

## Implementation

- **Backend:** `app/scheduled_parser.py` (independent JSON5 parser for
  `cortesProgramados`), `app/scheduled_store.py` (snapshots, runs, retention, own
  advisory lock `0x43553032`), `app/scheduled_api.py` (`GET /scheduled-works`,
  `GET /scheduled-works/areas`), new models and additive migration `0006_cu02`.
  `app/main.py` adds a second lifespan task gated by
  `SCHEDULED_WORKS_SCHEDULER_ENABLED` / `SCHEDULED_WORKS_REFRESH_SECONDS`.
- **CU01 reuse:** the unchanged `enre_client.fetch_feed()` transport, the pure
  `normalized_key` helper, the GeoRef resolve endpoints and the coverage catalog in
  read-only mode. No CU01 parser, table, lock or endpoint was modified.
- **Frontend:** `frontend/src/features/scheduled-works/` (typed client, state labels,
  panel) and a third "Trabajos" view in `App.tsx`. The panel has no date inputs, reuses
  the address/GPS resolution and renders "No publicado por la fuente" for a missing
  reason. `lib/http.ts` was not changed because the two public resolve POSTs were
  already allowlisted by CU01.
- **Compose:** the backend service exposes the CU02 scheduler flags with a five-minute
  default; no new service, volume or dependency.

## Problems and corrections

- PLAN verified the Edesur agenda is unavailable (HTTP 500/timeout) and that
  `cortesComunicados` has never been observed populated; the definitive scope follows
  from that evidence, not from an implementation shortcut.
- First test run found three local defects: `works` was returned as `[]` for an
  `unavailable` snapshot with no rows, a fixture replacement dropped a JSON5 comma,
  and one `replace()` did not match the minified fixture spacing. All three were
  corrected and the 30 CU02 tests now pass.
- Independent review found no invented-data or blocker defect but required:
  reconciling `tasks.md`/STATE/fiche (this record); removing the CU01
  `totalUsuariosSinSuministro` degradation coupling so a sentinel total cannot freeze
  CU02; making `no_works` testable only through a covered localidad; adding
  `Cache-Control`, 503, null-`Last-Modified` and run-retention tests; removing the
  unreachable `geographic_error` from the CU02 state contract; and aligning the
  "verbatim" wording and the client fallback for a missing restoration text. All were
  applied and re-verified.

## Checks

| Check | Result |
|---|---|
| CU02 backend tests (`tests.test_cu02_scheduled_works`) | PASS 30/30, including one live ENRE test (`TEST_ENRE_LIVE=1`) |
| CU01 regression (`tests.test_cu01_outages`) | PASS 25/25 (live ENRE) |
| CU01 territory regression (`tests.test_cu01_territory`) | PASS 26/26 (live GeoRef) |
| CU09 diary unit tests | PASS |
| Ruff (`app tests migrations`) | PASS |
| mypy strict (`app`) | PASS, 41 files |
| Frontend image (typecheck, build, Node tests, Oxlint) | PASS |
| Chromium E2E (`e2e/cu02.spec.ts` + `e2e/cu01.spec.ts`) | PASS 14/14 (5 CU02 + 9 CU01) |
| Migration upgrade on fresh PostgreSQL | PASS, three CU02 tables |
| Additive check with a seeded CU01 row | PASS, row preserved after upgrade; downgrade drops only CU02 tables and preserves the row; re-upgrade PASS |
| `openspec validate implement-scheduled-works-cu02 --strict` | PASS |
| `openspec validate --specs --strict` after the definitive-scope sync | PASS, 10/10 specs |

Live evidence: the 2026-11-10 ENRE capture exposed four `cortesProgramados` rows, all
with `normalizacion: 'Sin datos'`; the 2026-01-14 archived capture exposed
`normalizacion: '2026-01-14 15:33'`, stored as text and never converted to an end.
No personal data is stored in the fixtures.

## Full-suite analysis (environmental)

The full backend suite was run against the isolated PostgreSQL instance:

- **Minimal verification container:** 398 tests, 30 errors and 3 failures. The errors
  are all in `test_photo_postgres`, which forces `CU05_PHOTO_DIR=/photo-tests`; the
  verification image does not create that directory (only the runtime target creates
  `/var/lib/energia-sur/photos`). The failures are in `test_bill_postgres`, which uses
  the default `/var/lib/energia-sur/bills`, also created only by the runtime target.
  The image user (10001) cannot create those root-level directories.
- **With storage directories mounted** (`/photo-tests` and `/bill-tests`): the 30
  errors and the bill-directory failures disappear. The remaining failures (5-7
  depending on the run) are all CU05/CU06 filesystem/OCR tests and vary because a
  Windows bind mount does not provide the Linux ownership, hard-link, `flock` and
  `fsync` semantics the private storage expects.
- **Conclusion:** the 3 failures and 30 errors are environmental, not CU02
  regressions. Reproducing the full suite green requires a native Linux volume (as in
  Compose) plus a working Tesseract/OCR fixture. No CU05 or CU06 code was modified;
  the targeted CU01, CU02 and CU09 suites pass.
- The known pre-existing CU05 OCR/red-fraction failures remain separate and are not
  fixed or hidden by this change.

## Out of scope and operational notes

Future agenda, temporal filters, planned start/end, unpublished reasons and distances
are **out of scope by design**, not pending tasks; ENRE does not publish them and no
value is invented. `cortesComunicados` is hidden until a populated shape is observed;
Edesur is out of scope; coverage remains the partial U20 catalog. Two conservative
edges are recorded: with no successful CU02 run, a fresh covered zero-row snapshot
reports `unavailable` rather than `no_works`; and a non-`EnreError` fetch exception is
logged by the scheduler without a run row, so freshness ages out instead of inventing
a result. Pre-existing CU05/CU06 full-suite failures are environmental (photo/bill
directories and secrets in the minimal verification container) and were not changed;
the targeted CU01/CU02/CU09 suites pass. The original dated proposal is preserved as
history in the fiche and U21; no teacher approval of the U22 redefinition is claimed.
A CU02-only commit was created; no push was performed.

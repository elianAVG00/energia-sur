# CU01 backend engineering record

Change: [`implement-current-outages-cu01`](../../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/)
Stage: BUILD 1–3 + final verification, synced and archived on 2026-11-10. Main spec:
[`current-outages`](../../openspec/specs/current-outages/spec.md). The unobserved
media/preventivo shapes (0.1) and the partial nine-localidad coverage catalog (0.4) are accepted
as documented exceptions (U20). Commit only; no push.

## Goal and accepted sources

- Public read-only CU01 outage queries from the ENRE Edesur feed, served from a cached snapshot.
- Accepted decisions D1–D11 and T1–T3 in
  [`docs/use-cases/decisions.md`](../use-cases/decisions.md) (U16); BUILD 1 authorization in U17.
- Artifacts: [proposal](../../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/proposal.md),
  [design](../../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/design.md),
  [delta spec](../../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/specs/current-outages/spec.md),
  [tasks](../../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/tasks.md).

## Agent and tool usage

- Primary implementer: OpenCode (this session). No functional code was delegated.
- Independent reviews: three planning reviews (M1–M11/m1–m7 → N1–N14) and one implementation
  review by separate reviewer sessions; findings were corrected in the same stage.
- Read-only evidence: live `GET` to `data_EDS.js` from the host and the backend container, and
  GeoRef probes (GeoRef probes are planning evidence only; GeoRef is not implemented in BUILD 1).
- Tools: Docker Desktop (verification image, ephemeral PostgreSQL 18.6), `uv` pinned in the
  backend image, `alembic`, `unittest`, Ruff, mypy, OpenSpec CLI 1.16.1.

## Prompt / work summary

1. Verify tasks 0.1–0.5: JSON5 proof against the live feed, dependency addition, decisions record.
2. Implement `enre_client`, `enre_parser`, `outage_store`, `outages_api`, models, migration
   `0005_cu01`, lifespan scheduler, Compose flags.
3. Add unit/API/concurrency/live tests and run the quality gates on an isolated database.
4. Fix review findings and record evidence; stop before BUILD 2.

## Decisions and approvals

- D1 legacy TLS isolated to the ENRE client, verification retained.
- D7 `httpx` + JSON5, gated on a real-fixture proof; no silent parser substitution.
- D5/D6 snapshot + run history + retention + dedicated-connection advisory lock.
- D8/D11 freshness and normative state; `source_status` derived from the latest non-skipped attempt.
- T1/T2 (GeoRef, coverage) are **not** implemented in BUILD 1; every area is `coverage_unverified`.

## Problems and corrections

- Default OpenSSL ciphers fail against the ENRE Domino server; `DEFAULT@SECLEVEL=1` works and keeps
  certificate/hostname verification. `httpx` receives the context as `verify=<context>`.
- JSON5 parses the live literal after stripping `var data =`; the committed redacted fixture and
  edge fixtures prove the dependency gate (task 0.2).
- First test run: 4 failures (Pydantic emitted `outages: null`, retention kept 25 rows, seeded
  digests prevented `not_modified`, test expectation for non-report areas). Fixed with
  `response_model_exclude_none`, current-first retention ordering, digest-accurate seeding and a
  corrected assertion.
- Implementation review (MAJOR): `source_status` returned `ok` after failed refreshes; missing
  edge tests. Fixed by mapping all non-ok/non-`not_modified` attempts to `degraded`, adding the
  missing tests, preserving a known timestamp on `not_modified`, pruning runs on every attempt,
  and making `_state` degradation-aware.
- MINOR review fixes: normalized-key grouping in `/outages/areas`, category CHECK constraint,
  scheduler interval guard, redirect port check, `trust_env=False`, tolerant lock release.
- Final reviewer confirmation: APPROVED for human review; the degraded-state override was narrowed
  to covered areas, a failure-outcome `source_status` test and a malformed-port guard were added.
  No Sync, Archive, commit or push was performed.

## BUILD 2 - GeoRef and coverage

- Live GeoRef probes: `/direcciones` needs a province/departamento scope and often rejects the
  `Av.` prefix; `/ubicacion` returns departamento/municipio but no localidad; CABA returns
  `Comuna N`; `localidad_censal` may differ from the ENRE localidad.
- Implemented `app/georef.py` (forward/reverse, Buenos Aires/CABA scope, candidate selection,
  partido degradation, body-only inputs, per-client 429) and `app/coverage.py` with the versioned
  catalog `app/data/edesur_coverage.2026-11-10.json`.
- Mapping rule: normalized exact match for partido/localidad, explicit CABA→`CAPITAL` alias, and
  localidad only when the catalog or the current ENRE snapshot uses it; otherwise partido-level.
- Coverage seed: partial observation-based entries from real ENRE Edesur payloads (provenance and
  retrieval date in the file). Absence stays `coverage_unverified`; no `out_of_coverage` entry is
  asserted. The definitive Edesur enumeration is not machine-readable, so task 0.4 remains a
  documented limitation and `no_reports` only applies to explicitly seeded localidades.
- API: `/outages` and `/outages/areas` now use three-valued coverage; `/outages/resolve` and
  `/outages/resolve-location` return a resolved zone or candidates, with 422 for geographic
  errors and 429 for throttling.
- PASS: 51/51 CU01 tests (live ENRE and live GeoRef included), Ruff/mypy (38 files),
  `openspec validate --strict`, full suite 368 tests with only pre-existing CU05 photo/OCR
  environmental failures.

## BUILD 3 - Public frontend and E2E

- `frontend/src/features/outages/`: typed API client with strict payload guards, state/format
  helpers, and a public panel with partido→optional-localidad selection from `/outages/areas`, a
  normalized "Buscar zona" filter, GeoRef address search with candidate selection, consented
  browser geolocation, granularity messaging, category table, Edesur-scope totals and provenance.
- Shell: a "Cortes"/"Mi cuenta" switch without a router; the account view remains the default so
  the existing CU09 login flow is unchanged. The nav label avoids duplicating the login button.
- `lib/http.ts`: a narrow allowlist for the two public resolve POSTs (no CSRF) while private
  writes keep the session CSRF; `DiaryError.retryAfter` exposes `429 Retry-After`; `statusMessage`
  covers 429.
- PASS: 106/106 frontend Node tests, Oxlint 0 warnings/0 errors, TypeScript and production build;
  CU01 Chromium 9/9 mocked flows (visitor query, ambiguous address, simulated/denied GPS, degraded,
  stale/unverified/unavailable, 429, 422 geographic, authenticated shell), 1/1 real-backend CU01
  smoke and the real CU09 E2E 1/1 against an isolated PostgreSQL/backend.
- No direct browser request to ENRE or GeoRef; addresses/coordinates remain body-only and
  unpersisted.
- Review correction: the initial payload guards required nested nullable keys, while FastAPI's
  `exclude_none` omits them. The client now accepts omitted nullable fields, with a contract test
  and a real-backend Chromium smoke (partido-only, a low-voltage row with omitted fields and a
  covered no-reports area). A degraded source no longer displays "Información actualizada".

## Verify and close

- Final gates were re-run on the final images. Backend: Ruff/mypy, `alembic upgrade head`,
  51/51 CU01 tests on a fresh PostgreSQL 18.6 with live ENRE/GeoRef, and the full suite
  (368 tests; only the 2 known CU05 OCR failures). Frontend: pinned verification image build
  (TypeScript, production build, 106/106 tests, Oxlint 0/0), 9/9 mocked CU01 Chromium flows, 1/1
  real-backend CU01 smoke and the real CU09 E2E 1/1. `openspec validate --strict` PASS.
- Accepted exception **0.1** (U20): no populated `cortesServicioMedia`/`cortesPreventivos` capture
  was observed. The parser ignores unknown collections and extra keys, fails closed on invalid
  rows and keeps the last valid snapshot; only synthetic fixtures exercise those paths. No claim
  is made that populated categories were verified in production.
- Accepted exception **0.4** (U20): the versioned nine-localidad catalog with provenance is
  approved; unverified zones remain `coverage_unverified` and no coverage or negative result is
  invented. The catalog is not expanded without evidence.
- Closure preparation only: no Sync, Archive, commit, push or deployment was performed.

## Checks and results

| Check | Result | Evidence |
| --- | --- | --- |
| `openspec validate --strict` | PASS | Change valid, 4/4 artifacts |
| Ruff (`ruff check app tests`) | PASS | Verification image, 0 findings |
| mypy (`mypy app`, strict) | PASS | 38 source files |
| CU01 unit/API/DB/live tests | PASS 51/51 | Fresh PostgreSQL 18.6; `TEST_ENRE_LIVE=1` and `TEST_GEOREF_LIVE=1` |
| `alembic upgrade head` (`0005_cu01`) | PASS | Fresh database; additive tables/indexes |
| Live ENRE → API | PASS | Outcome `ok`; EDESUR snapshot; `Last-Modified`, totals 7198/2819686; 3 low-voltage rows |
| Full backend suite | PASS with pre-existing CU05 failures | 368 tests; only CU05 photo/OCR tests fail under the ad-hoc image (fresh DB+volume baseline: 2 OCR failures); no CU01/core failures |
| Frontend unit/contract tests | PASS 106/106 | `npm test` in the pinned frontend verification image |
| Frontend lint/typecheck/build | PASS | Oxlint 0 warnings/0 errors (75 files); `npm run build` typecheck + Vite build |
| CU01 Chromium E2E | PASS 9/9 mocked + 1/1 real backend | Mocked states/flows plus a real partido-only, low-voltage and no-reports smoke |
| Real CU09 E2E | PASS 1/1 | Isolated PostgreSQL/backend, synthetic accounts, new shell |
| Independent implementation review | PASS with corrections | BUILD 1–2 reviews closed; BUILD 3 review recorded separately |

## Redacted evidence

Live payload observed on 2026-11-10: `HTTP 200`, `application/x-javascript`, UTF-8, `Last-Modified`
present and advancing, `ultimaActualizacion` in ART, totals 7198 / 2,819,686, low-voltage rows 3,
medium/preventive 0 (still unobserved). No personal data, credentials or real addresses are stored
in this record or in fixtures.

## Limitations and next steps

- `cortesServicioMedia` and `cortesPreventivos` populated shapes remain unobserved; this is the
  accepted 0.1 exception (U20). The parser fails closed on invalid rows, on a missing known
  collection and on a null/non-list known collection, and preserves the last valid snapshot;
  synthetic fixtures only.
- GeoRef address matching is sparse and needs a province/departamento scope; reverse geocoding
  returns no localidad, so most address/position results degrade to partido. `no_reports` is
  reachable only for localidades explicitly present in the approved nine-localidad coverage seed;
  `out_of_coverage` remains unimplemented (accepted 0.4 limitation).
- The public frontend presents the 422 geographic message, candidates, partido degradation,
  staleness, unverified coverage and the unavailable source; the `geographic_error` state enum
  branch is reserved and not synthesized by the panel. No pre-close gates remain: 0.1/0.4 are
  accepted exceptions (U20).
- Legacy TLS at security level 1 is a documented trade-off; ENRE schema drift is fail-closed.
- CU01 is verified; formal closure (Sync/Archive) awaits explicit authorization. No Sync, Archive,
  commit or push was performed.

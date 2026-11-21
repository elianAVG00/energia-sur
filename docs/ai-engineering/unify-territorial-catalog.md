# Shared CU01/CU02 territorial catalog

## Goal and specification

- Active change: [proposal](../../openspec/changes/unify-territorial-catalog/proposal.md),
  [design](../../openspec/changes/unify-territorial-catalog/design.md), and
  [task checklist](../../openspec/changes/unify-territorial-catalog/tasks.md).
- Use one persistent GeoRef-backed catalog for CU01/CU02 selectors while preserving ENRE
  snapshots, original source labels, and uncertainty about locality-level service coverage.
- Approved source scope: twelve Buenos Aires partidos; GeoRef v2.1 `/localidades`, retrieved
  2026-11-15. The fixture contains 99 source records and 93 party-scoped locality names; the
  reviewed reserve entry remains in provenance but is not selectable, leaving 92 options.

## Decisions and implementation

- PostgreSQL is the shared persistent selector source. Additive revisions
  `0009_territorial_catalog` and `0010_territorial_alias_party_fk` seed metadata, parties,
  locality identities, source records, aliases, and enforce party-scoped alias targets.
- Seed writes are deterministic conflict-safe upserts. This capture is versioned and treated as
  immutable: source corrections/removals require a reviewed follow-up migration; reseeding does
  not silently delete catalog records.
- Existing report/work comparison keys are re-keyed from original labels using accent-folding,
  case-folding, and whitespace normalization. Original labels, rows, and snapshots are retained.
- CABA/CAPITAL is excluded from selector data and constraints. Existing GeoRef CABA resolution
  behavior is retained for compatibility: accepted requirements exclude CABA from selectors,
  while the design requires preserving existing geographic-resolution behavior and identifies
  adding CABA to the catalog as a non-goal. This remains separate from selector membership.
- `Santa Anita` and `Zona Rural` remain unresolved observations. Their own raw normalized labels
  may be queried only within the selected party; no substitute locality is inferred.

## Work and review

- Implementation was performed in the primary OpenCode session using repository tools and
  documented OpenSpec contracts. No subagent edited files.
- An independent read-only reviewer initially raised questions about party-scoping unresolved
  exact-name queries, CABA resolution versus selector scope, migration fixture breadth, and seed
  reconciliation policy.
- Follow-up static review found no current actionable findings. It confirmed that the fallback
  unresolved query key is constrained by the selected party predicate; CABA resolution does not
  conflict with selector-only exclusion; migration tests cover the two new revisions and include
  null, accent-folded, and unresolved labels; and reseeding is documented as an immutable capture
  with reviewed follow-up migrations. The reviewer did not run runtime checks and marked
  independent migration/data verification blocked pending them; this is not an independent
  runtime migration sign-off.
- A prior live GeoRef address probe with an inconsistent party hint was rejected; a coherent
  Lomas de Zamora hint resolved. No address or coordinate payloads are stored in this record.

## Verification evidence

- PostgreSQL revision reached `0010_territorial_alias_party_fk`; observed catalog counts:
  12 parties, 93 locality names, 92 selectable localities, 99 source records, 14 aliases and
  2 unresolved aliases. No duplicate party/name keys or CABA party were present.
- Existing application data at migration observation: 188 outage rows, 57 scheduled-work rows,
  and 3 accounts. These report/work counts can change as ENRE refreshes; the migration test
  independently checks retained synthetic rows and original labels.
- Live API checks: both area endpoints returned identical 12-party/92-locality hierarchies with
  no `reported` selector field or CABA/CAPITAL; verified party and locality aliases returned
  equivalent outcomes; `Santa Anita` remained `coverage_unverified`; GeoRef address and reverse
  location resolution succeeded for coherent test inputs.
- `tests.test_territorial_catalog_migration_postgres`: PASS in a temporary PostgreSQL schema,
  including repeatable seed, CABA rejection, duplicate rejection, alias-party mismatch rejection,
  accent-folded re-keying, null locality preservation, unresolved ENRE labels, and downgrade
  restoration from preserved labels. This test invokes the two new revisions directly rather
  than replaying the full historical Alembic chain.
- Backend Docker verification: Ruff PASS; mypy PASS. The complete backend suite previously passed
  485 tests with 247 prerequisite skips, including the latest migration fixture additions; focused
  CU01/CU02 tests report 83 tests, 30 passed and 53 skipped because isolated PostgreSQL and
  external/live prerequisites are absent.
- Pinned frontend Docker verification passed typecheck, production build, 117 unit tests, and
  lint. Local Windows Node/npm verification was unavailable due to missing local dependencies and
  versions differing from the pinned image.
- Focused CU01/CU02 unit tests: 83 tests, 30 passed and 53 skipped because isolated PostgreSQL
  and external/live prerequisites are absent. CU01/CU02 Playwright: PASS, 30/30, run against
  `http://127.0.0.1:5173` inside the frontend container's network namespace so geolocation is
  available in a secure browser context. New fixture asserts both selector options equal the
  twelve approved parties and omit CABA/CAPITAL; the shared mock carries the approved hierarchy.
- Initial Playwright attempts using the Compose hostname got Vite 403 (`server.allowedHosts`);
  using the container IP fixed HTTP loading but was not a secure geolocation context. The
  namespace-local loopback run passed. A Vite restart was needed to clear a stale transformed
  module during fixture validation. No application host-policy change was made.
- Static independent review: PASS, no actionable findings. Independent runtime migration/data
  sign-off remains pending. PostgreSQL CU01/CU02 API integration suites remain blocked until an
  isolated migrated `TEST_DATABASE_URL` is available. No commit, push, deployment, or archive.

## Remaining work

1. Obtain independent reviewer disposition of the migration/runtime evidence; the configured
   read-only reviewer cannot execute shell commands, so independent runtime execution may remain
   blocked even after static review.
2. Keep the change unarchived until the mandatory independent review gate passes.

## Closure verification follow-up (2026-11-16)

- The primary agent corrected tests only; no production endpoint, migration, business rule,
  dependency, or security behavior changed. The old assertions expected uppercase selector labels,
  snapshot-derived coverage, or a `current_snapshot` mock on an endpoint that now reads the
  PostgreSQL catalog. Updated assertions target the accepted canonical labels and catalog contract;
  none were removed or relaxed.
- The two catalog area endpoints were exercised over ASGI against a fresh, fully migrated,
  isolated PostgreSQL database. With no CU01/CU02 snapshot rows, they returned identical 12-party
  and 92-locality hierarchies. CU01's selector response was also compared before and after deleting
  only synthetic snapshot rows in that isolated test database.
- A separate CU01/CU02 test run passed 83 tests with 6 live-source prerequisite skips. It covers
  endpoint behavior, party/locality filters, canonical labels, coverage uncertainty, stale and
  degraded states, GeoRef adapter v2.1 locality precedence, address privacy, and rate limits.
- `tests.test_territorial_catalog_migration_postgres` passed 1/1 against the isolated test server:
  migration seed counts, repeatable seed, row/label preservation, normalized-key upgrade/downgrade,
  CABA and duplicate rejection, and alias party integrity. Full Alembic `upgrade head` also passed
  on a newly initialized isolated test database.
- One full backend run passed: 491 tests, 484 passed, 7 skipped for explicit ENRE/GeoRef or
  reconciliation prerequisites. Ruff passed; mypy passed (54 source files); strict OpenSpec
  validation passed. Existing frontend type/lint/build/unit and CU01/CU02 Playwright evidence was
  not repeated because this follow-up changed no frontend files.
- PostgreSQL test containers used private Docker networks and ephemeral tmpfs data directories.
  Neither connected to nor changed/restarted the original Compose database or its volumes.
- Independent static/runtime evidence review was requested from the configured reviewer. That
  agent is read-only and has no shell permission; its response and any independent runtime
  execution limitation will be recorded before closure. No sync/archive/commit/push/deploy occurred.

## Final regression correction (2026-11-16)

- The two alias regressions now query the canonical locality `Presidente Perón` against synthetic
  ENRE rows whose preserved source label is `PTE PERON`; this exercises a reviewed, non-mechanical
  alias rather than accent/case normalization alone. A separate parity test uses distinct CU01/CU02
  snapshots, and both endpoints continue to return the same catalog hierarchy.
- Final focused CU01/CU02 and migration tests: 86 run, 80 passed, 6 external/live-source skips.
  The single complete backend suite after those test changes passed 493 tests: 486 passed, 7 skipped,
  0 failed, using isolated PostgreSQL on a private network with tmpfs storage.
- Final-tree Ruff, mypy, strict OpenSpec validation (19/19), and `git diff --check` all passed.
  The independent reviewer remains static-only; runtime migration/data sign-off is BLOCKED and
  task 5.3 remains unchecked. No sync, archive, commit, push, or deploy occurred.

## Party-scope review follow-up (2026-11-16)

- This follow-up supersedes the earlier focused-test count of 86 in the preceding closure snapshot.
- Independent static review found a Low coverage gap: the alias tests did not explicitly exclude a
  competing party. The first CU02 fixture-insertion attempt targeted an abbreviated substation
  label and silently made no insertion; the reviewer identified this before closure.
- Both tests now assert that the constructed, parsed ENRE feed contains the expected `PTE PERON`
  alias row and a competing `CAÑUELAS` row for the same locality before querying canonical
  `Presidente Perón`. CU02 insertion now matches the full fixture substation label. The API
  assertions require exactly one result and preserve the original `PTE PERON`/`GUERNICA` labels.
- Rebuilt the verification image after the final test edits. Focused CU01/CU02 modules passed:
  57 tests, 55 passed and 2 live-source skips. One subsequent complete suite passed 493 tests
  (486 passed, 7 skipped) in 138.351 seconds against fresh isolated PostgreSQL on a private
  network with tmpfs. A previous complete-suite attempt ended at the 120-second shell timeout
  before a test summary; it is not counted as a test failure or pass.
- Follow-up static review confirmed both competing rows are actually present in the parsed feeds,
  the API assertions exclude the competing party, and original source labels are preserved. No
  remaining test-assertion concern was reported. The reviewer cannot execute tests or independently
  inspect the production diff; the primary diff contains test/documentation changes only, with no
  `backend/app`, migrations, frontend, or dependency changes. Independent runtime migration/data
  sign-off remains BLOCKED.
- Rebuilt-image runtime evidence: focused tests 57 run (55 passed, 2 skipped); final complete suite
  493 total (486 passed, 7 skipped) in 138.351 seconds. Final-tree Ruff, mypy, strict OpenSpec
  validation (19/19), and `git diff --check` passed. No sync, archive, commit, push, or deploy.

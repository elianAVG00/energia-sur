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

1. Obtain independent runtime migration/data sign-off.
2. Run PostgreSQL API integration suites with an isolated migrated test database if available;
   otherwise keep that acceptance criterion explicitly blocked.
3. Keep the change unarchived until mandatory verification and review requirements pass.

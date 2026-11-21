# Tasks

## 1. Confirm the territorial data set and persistence contract

- [x] 1.1 Review and capture the official ENRE audit citation and the GeoRef v2.1 `/localidades` responses for the twelve approved Buenos Aires departments; verify response totals, department IDs, locality IDs, categories, duplicate-name groups, source URL and retrieval date in a redacted/reproducible fixture. Evidence: `backend/app/data/territorial_catalog_georef_v2_1.json` records the 99 live API rows, IDs/categories, twelve department IDs, source URLs and retrieval timestamp; checks confirmed 99 source records and 93 unique party-scoped names.
- [x] 1.2 Review each exceptional selector candidate, including `Área Reserva Cinturón Ecológico`; retain it by default and exclude only a specifically reviewed non-useful record with a recorded reason; verify the finalized selector names against the captured response. Evidence: the reserve's source row/category remains in the capture but has `selectable: false` with an individual reason; remaining selectors contain 92 names.
- [x] 1.3 Compare all redacted ENRE fixtures and the existing seed against GeoRef names; record confirmed equivalents such as `SAN JOSE`/`San José` and `PTE PERON`/`Presidente Perón`, retain `Santa Anita` and `Zona Rural` as unresolved, and verify no unsubstantiated equivalence is added. Evidence: inspected all redacted ENRE fixtures and the versioned seed; confirmed accent/case variants and party alias candidates, with `Santa Anita` and `Zona Rural` absent from the GeoRef department response and left unmapped.

## 2. Add the persistent PostgreSQL catalog and seed

- [x] 2.1 Add SQLAlchemy models and additive Alembic revisions `0009_territorial_catalog` and `0010_territorial_alias_party_fk` after `0008_cu10`; enforce party-scoped locality uniqueness, approved party IDs, source-ID preservation, and alias target-party integrity.
- [x] 2.2 Add a deterministic conflict-safe seed for the approved 12 parties, reviewed GeoRef records and verified/unresolved ENRE equivalences with provenance; PostgreSQL verification confirmed 12 parties, 93 locality names, 99 source rows, 14 aliases and 2 unresolved observations; the isolated migration test runs the seed twice.
- [x] 2.3 Re-key existing outage and scheduled-work comparison keys from preserved source labels using accent/case/whitespace normalization; downgrade restores the former key format from original labels. The isolated PostgreSQL test confirms labels/rows remain intact and exercises both directions.
- [x] 2.4 Add isolated-PostgreSQL migration tests for upgrade, repeatable seed, duplicate and mismatched-party rejection, retained snapshot re-keying, rollback restoration and CABA exclusion. Test: `tests.test_territorial_catalog_migration_postgres` passed in a temporary schema.

## 3. Unify backend catalog reads and matching

- [x] 3.1 Implement one typed PostgreSQL catalog reader for both selectors; area construction reads no ENRE snapshots and emits no snapshot-derived `reported` flag. PASS: isolated migrated PostgreSQL endpoint tests confirmed the catalog response is unchanged with and without CU01 snapshots; CU01/CU02 expose the same hierarchy.
- [x] 3.2 Route both area endpoints through that reader with matching 12-party/92-locality hierarchies and provenance; live endpoint acceptance confirmed equal hierarchies and no CABA/CAPITAL.
- [x] 3.3 Apply shared accent/case/whitespace normalization and verified alias matching to queries and ENRE ingestion keys; live CU01/CU02 checks confirmed party/locality aliases return equivalent results and `Santa Anita` remains unverified. Original report/work labels remain unchanged.
- [x] 3.4 Resolve GeoRef v2.1 address and reverse-location results against the persistent catalog; mocked adapter regression tests and live address/GPS checks passed with party fallback and privacy/rate-limit behavior retained.
- [x] 3.5 Add regression coverage for catalog-only selectors, aliases, unresolved names, v2.1 locality precedence and query behavior; verify both suites against isolated migrated PostgreSQL. PASS: final focused CU01/CU02 modules ran 57 tests (55 passed, 2 external/live skips); the full suite passed the territorial migration test as well. Canonical filters, unresolved coverage, selector parity, GeoRef adapter precedence, non-mechanical canonical alias mapping (`Presidente Perón` against source label `PTE PERON`), competing-party exclusion and source-label preservation were exercised. The final full suite had 7 external/live prerequisite skips, not failures.

## 4. Keep frontend selectors and empty-result explanations compatible

- [x] 4.1 Update CU01/CU02 area-result TypeScript types and runtime validators for the shared catalog contract without the snapshot-derived `reported` field; frontend API tests cover the catalog response.
- [x] 4.2 Update empty-result explanations to describe no matching report in the latest available update without guaranteeing power or no interruptions; state tests cover normative result states and freshness/unavailability presentation.
- [x] 4.3 Preserve party/locality selection, address candidate selection and device-location controls in both panels; frontend unit tests and CU01/CU02 Playwright flows pass against catalog mocks. Playwright verifies both selectors expose the same twelve approved parties and no CABA/CAPITAL option; final result: 30/30 passed.

## 5. Integrated verification and review

- [x] 5.1 Run relevant backend migration, CU01/CU02 API and parser tests plus frontend tests, type checks, lint and builds using documented repository commands; record PASS/FAIL/BLOCKED evidence and do not run the migration against any non-isolated database. PASS: focused CU01/CU02 modules 57 tests (55 passed, 2 external/live skips); final full backend suite 493 total (486 passed, 7 skipped); final-tree Ruff, mypy, strict OpenSpec validation (19/19) and `git diff --check` passed. Existing frontend unit/type/lint/build and CU01/CU02 Playwright evidence remains applicable; no frontend files changed.
- [x] 5.2 Run migrated-database acceptance checks for both actual area endpoints with empty and different snapshots, exercise query-by-party/locality and GeoRef address/GPS flows, and verify freshness/coverage uncertainty remains intact; record reproducible evidence for every CU acceptance criterion. PASS: both real ASGI endpoints returned identical 12-party/92-locality hierarchies without snapshot rows; CU01 returned the same hierarchy after removing snapshot rows; party/locality filters, coverage uncertainty, no-report/degraded states, privacy and GeoRef adapter behavior passed. Historical live GeoRef address/reverse-location probes remain documented separately and were not repeated.
- [ ] 5.3 Obtain independent review of schema/data migration, key re-normalization, alias integrity, CABA exclusion and API/UI regressions; resolve findings and rerun affected checks before closure. Static follow-up review found no actionable findings; independent runtime migration/data sign-off remains pending, and the PostgreSQL API suite limitation is recorded.
- [x] 5.4 Update README, `docs/STATE.md`, and the engineering record with source provenance, review decisions, migration details, test evidence and remaining limitations; verify referenced paths and keep `docs/STATE.md` under 60 lines.

## Workflow follow-up

- Present this plan for explicit human approval before implementation.
- Do not execute database migrations, deploy, commit, or push as part of implementation without the applicable explicit authorization.
- Archive only after acceptance checks and independent migration/data review have passed.

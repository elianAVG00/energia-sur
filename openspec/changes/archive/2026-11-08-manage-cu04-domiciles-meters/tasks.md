# Tasks

## 1. Review and authorization gates

- [x] 1.1 Record U12 approved ASCII normalization, alias validation, API and coded 409 contract; verify traceability and strict OpenSpec validation.
- [x] 1.2 Complete independent read-only review with no blockers and record all REVIEW results; U12 authorizes Apply only if all applicable gates pass, not from structural validation alone.

## 2. Additive persistence and backend

- [x] 2.1 Load the `fastapi-endpoint` skill and implement the additive 0001-descendant migration and models; prove with a real PostgreSQL upgrade test that existing domicile IDs, cuts and meter-free API remain intact and composite FKs reject inconsistent ownership.
- [x] 2.2 Implement validated owner-scoped domicile and meter routes, retaining old API shapes; verify positive, invalid, foreign/missing, Origin and CSRF cases in backend tests.
- [x] 2.3 Implement ASCII normalization, database-enforced per-account uniqueness and atomic optimistic versions; verify concurrent creates/edits, non-ASCII rejection, Spanish alias, coded constraint-specific 409 and rollback with real PostgreSQL tests.
- [x] 2.5 For each domicile and meter PATCH use an owner- and version-qualified database write that advances version once even on no-op; verify on real PostgreSQL with independent connections current changed/no-op writes, stale no-op, concurrent same-version writes, changed-versus-old-value race, foreign/missing 404 and failure atomicity.
- [x] 2.4 Document accepted endpoints and exact normalization/error semantics in the relevant README/engineering record and verify examples match API tests.

## 3. Frontend feature and local checks

- [x] 3.1 Add `features/domiciles/` forms, typed adapter and feature-local meter state using existing stack; verify schema and adapter tests cover invalid payloads, response identities, warnings and both conflict types.
- [x] 3.2 Compose into existing Workspace using its single domicile list and selected-ID store; verify selection changes, session changes, cancellation, stale responses and preservation of diary drafts with focused frontend tests.
- [x] 3.3 Scope 409 feedback correctly without weakening diary recovery; verify existing diary and new duplicate/version conflict tests, and update frontend documentation if integration guidance changes.

## 4. Integration, acceptance and independent review

- [x] 4.1 Load `quality-gate`; record PASS/FAIL/BLOCKED/NOT APPLICABLE with commands, evidence and justified exclusions for backend tests, Ruff/mypy, frontend tests, lint/build/type checks and strict OpenSpec structural validation.
- [x] 4.2 Run permitted real PostgreSQL and browser/backend acceptance using synthetic data: two-account isolation, migration/restart persistence, meter-free domicile, create/correct meter, conflicts, stale requests and accessible UI; record evidence.
- [x] 4.3 Run CU09 end-to-end regression including owned/foreign operations, summary and actual PDF after address correction; prove stable cut/domicile IDs and unchanged calculations and record evidence.
- [x] 4.4 Obtain independent read-only security/data-isolation review and resolve confirmed findings; record reviewer, scope and evidence. If unavailable mark BLOCKED, not complete.
- [x] 4.5 Update engineering record, README index and `docs/STATE.md` with actual results and pending items; verify evidence is redacted and no tests or approvals are fabricated.

## Workflow follow-up

- Sync/archive only after applicable gates pass and explicit authorization is obtained; never alter the CU09 archive.

# Tasks

All tasks are intentionally unchecked. Artifact existence is not design acceptance
or implementation progress; **Apply is blocked until group 1 is satisfied**.

## 1. Human design and implementation gates

- [ ] 1.1 Obtain acceptance/revision of D0 minimum CU04 input and D4 temporal/correction/concurrency contract; verify dated user decision evidence and updated contracts without invented approvals.
- [ ] 1.2 Approve D1 auth/provisioning/session/cookie/CSRF/error design and exact dependencies; verify a written two-account access matrix covering all five CU09 operations.
- [ ] 1.3 Approve D2 driver/ORM/migration/connection choices and exact versions; verify reviewed additive schema and data-preserving migration/credential plan.
- [ ] 1.4 Approve D3 PDF library/version, fonts, pagination and delivery; verify a documented choice against alternatives and supported Windows/Docker setup.
- [ ] 1.5 Approve D5 API payloads/errors, UI/test approach and required lint/backend-type tools; verify no mandatory check remains undefined or silently waived.
- [ ] 1.6 Obtain a separate explicit Apply request after proposal/design review; verify authorization evidence before any code, dependency, schema or account-provisioning action.

## 2. Approved foundations and account boundary

- [ ] 2.1 Add only approved dependencies/configuration and regenerate locks consistently; verify locked builds and backend-only secret handling, documenting actual setup commands.
- [ ] 2.2 Implement reviewed additive account/session/domicile/interruption migrations and connection lifecycle; verify persistence and data-preserving migration tests on approved synthetic storage, with migration documentation.
- [ ] 2.3 Implement approved credentialed login/logout/session/provisioning and CSRF boundary; verify two-account positive/negative auth tests and document synthetic-only provisioning without an account-switch bypass.

## 3. Minimal domicile prerequisite

- [ ] 3.1 Implement accepted register/list/select own-domicile API and UI input contract; verify AD-S01/AD-S02, including no meter requirement and no other account's domiciles in results.
- [ ] 3.2 Add CU09 domicile selection/save precondition and direct-ID ownership enforcement; verify CU09-S03 and document the bounded CU04 scope, not full meter/address management.

## 4. Cut lifecycle and date validation

- [ ] 4.1 Implement typed CU09 save/view storage and Buenos Aires minute validation using the accepted contract; verify CU09-S01/S02/S10 with fixed clocks and no mutation on invalid dates, documenting API fields/errors.
- [ ] 4.2 Implement owner correction for open/closed records and explicit closure; verify CU09-S11/S12, including future/equal/earlier end rejection and accepted atomic-update/conflict behavior.
- [ ] 4.3 Enforce all five action permissions on direct record/domicile IDs; verify CU09-S09 with two accounts for view/list/summary/mutation/export routes and document authorization semantics.

## 5. Shared report calculations

- [ ] 5.1 Implement positive period intersections and ongoing effective end with one trusted captured clock; verify CU09-S05/S07/S08/S13 and document report boundaries without implicit stored closure.
- [ ] 5.2 Implement retained-overlap union and integer-minute totals; verify CU09-S04/S14 plus disjoint/nested/touching synthetic intervals, documenting hours/minutes output for UI and PDF reuse.

## 6. Diary user interface

- [ ] 6.1 Integrate real account/domicile diary create/view/correct/close paths and error states; verify approved frontend tests and rendered form validation, with reproducible usage documentation.
- [ ] 6.2 Integrate period summary/download UI against backend outputs only; verify type/build/UI tests including empty and excluded-cut results, documenting that no authoritative date/union logic is duplicated.

## 7. PDF implementation

- [ ] 7.1 Implement approved authenticated PDF response using shared authorized report data; verify CU09-S06/S07/S15 content/order/“En curso”/totals and negative export access tests.
- [ ] 7.2 Handle optional text/Unicode/fonts/multiple pages and generation failures; verify actual PDF inspection with synthetic long-text fixtures and document generation/runtime requirements.

## 8. Integrated verification and review

- [ ] 8.1 Exercise real browser -> FastAPI -> PostgreSQL persistence and downloaded/opened PDF using two synthetic accounts; verify all CU09 scenarios plus AD-S01/AD-S02 with retained acceptance evidence, not health-only or mock-only claims.
- [ ] 8.2 Run approved backend/frontend tests, lint, types, build, locked-install and relevant scaffold regressions; record commands/results as PASS/FAIL/BLOCKED/NOT APPLICABLE without weakening inherited requirements.
- [ ] 8.3 Obtain independent auth/data-isolation/security review and correct/recheck findings; verify a separate review artifact covering every owner-bound operation and no remaining mandatory failure/blocker.
- [ ] 8.4 Run strict OpenSpec and documentary validation, reconcile tasks, update STATE/README/engineering evidence; verify acceptance links and distinguish implemented CU09 from excluded CU04 scope.

## Workflow follow-up

- Proposal stops at human review now; no task is performed merely because listed.
- Sync/Archive, commit and push require their own applicable authorization and gates;
  stage 05 documentary closure did not authorize or perform any of them.

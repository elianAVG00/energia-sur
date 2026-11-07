# Tasks

U07 approves the proposal and recommended D0-D5 options and explicitly authorizes
Apply, with QA and independent review. Group 1 retains any unfulfilled detail gates;
per the user, independent approved work may advance while affected tasks are blocked.
Artifact existence is not implementation evidence; partial tasks remain unchecked.

## 1. Human design and implementation gates

- [x] 1.1 Obtain acceptance/revision of D0 minimum CU04 input and D4 temporal/correction/concurrency contract; verify dated user decision evidence and updated contracts without invented approvals.
- [x] 1.2 Approve D1 auth/provisioning/session/cookie/CSRF/error design and exact dependencies; verify a written two-account access matrix covering all five CU09 operations.
- [x] 1.3 Approve D2 driver/ORM/migration/connection choices and exact versions; verify reviewed additive schema and data-preserving migration/credential plan.
- [x] 1.4 Approve D3 PDF library/version, fonts, pagination and delivery; verify a documented choice against alternatives and supported Windows/Docker setup.
- [x] 1.5 Approve D5 API payloads/errors, UI/test approach and required lint/backend-type tools; verify no mandatory check remains undefined or silently waived.
- [x] 1.6 Obtain a separate explicit Apply request after proposal/design review; verify authorization evidence before any code, dependency, schema or account-provisioning action.

## 2. Approved foundations and account boundary

- [x] 2.1 Add only approved dependencies/configuration and regenerate locks consistently; verify locked builds and backend-only secret handling, documenting actual setup commands.
- [x] 2.2 Implement reviewed additive account/session/domicile/interruption migrations and connection lifecycle; verify persistence and data-preserving migration tests on approved synthetic storage, with migration documentation.
- [x] 2.3 Implement approved credentialed login/logout/session/provisioning and CSRF boundary; verify two-account positive/negative auth tests and document synthetic-only provisioning without an account-switch bypass.

## 3. Minimal domicile prerequisite

- [x] 3.1 Implement accepted register/list/select own-domicile API and UI input contract; verify AD-S01/AD-S02, including no meter requirement and no other account's domiciles in results.
- [x] 3.2 Add CU09 domicile selection/save precondition and direct-ID ownership enforcement; verify CU09-S03 and document the bounded CU04 scope, not full meter/address management.

## 4. Cut lifecycle and date validation

- [x] 4.1 Implement typed CU09 save/view storage and Buenos Aires minute validation using the accepted contract; verify CU09-S01/S02/S10 with fixed clocks and no mutation on invalid dates, documenting API fields/errors.
- [x] 4.2 Implement owner correction for open/closed records and explicit closure; verify CU09-S11/S12, including future/equal/earlier end rejection and accepted atomic-update/conflict behavior.
- [x] 4.3 Enforce all five action permissions on direct record/domicile IDs; verify CU09-S09 with two accounts for view/list/summary/mutation/export routes and document authorization semantics.

## 5. Shared report calculations

- [x] 5.1 Implement positive period intersections and ongoing effective end with one trusted captured clock; verify CU09-S05/S07/S08/S13 and document report boundaries without implicit stored closure.
- [x] 5.2 Implement retained-overlap union and integer-minute totals; verify CU09-S04/S14 plus disjoint/nested/touching synthetic intervals, documenting hours/minutes output for UI and PDF reuse.

## 6. Diary user interface

- [x] 6.1 Integrate real account/domicile diary create/view/correct/close paths and error states; verify approved frontend tests and rendered form validation, with reproducible usage documentation.
- [x] 6.2 Integrate period summary/download UI against backend outputs only; verify type/build/UI tests including empty and excluded-cut results, documenting that no authoritative date/union logic is duplicated.

## 7. PDF implementation

- [x] 7.1 Implement approved authenticated PDF response using shared authorized report data; verify CU09-S06/S07/S15 content/order/“En curso”/totals and negative export access tests.
- [x] 7.2 Handle optional text/Unicode/fonts/multiple pages and generation failures; verify actual PDF inspection with synthetic long-text fixtures and document generation/runtime requirements.

## 8. Integrated verification and review

- [x] 8.1 Exercise real browser -> FastAPI -> PostgreSQL persistence and downloaded/opened PDF using two synthetic accounts; verify all CU09 scenarios plus AD-S01/AD-S02 with retained acceptance evidence, not health-only or mock-only claims.
- [x] 8.2 Run approved backend/frontend tests, lint, types, build, locked-install and relevant scaffold regressions; record commands/results as PASS/FAIL/BLOCKED/NOT APPLICABLE without weakening inherited requirements.
- [ ] 8.3 Obtain independent auth/data-isolation/security review and correct/recheck findings; verify a separate review artifact covering every owner-bound operation and no remaining mandatory failure/blocker.
- [x] 8.4 Run strict OpenSpec and documentary validation, reconcile tasks, update STATE/README/engineering evidence; verify acceptance links and distinguish implemented CU09 from excluded CU04 scope.

## Workflow follow-up

Evidence: [Apply engineering record](../../../docs/ai-engineering/record-cu09-interruption-diary.md).
U07/U07-T/U08 approve the package, inclusive 1970 floor and Oxlint. U09 explicitly
resolves M1: trusted-Origin login without pre-auth CSRF, Origin plus valid CSRF for
authenticated writes. Contract, route table and delta spec are aligned. Latest
acceptance passes 66 backend tests (14 PostgreSQL), exactly one quick Chromium pass
and PDFs. Full independent source audit `ses_e4a277d40ffeKFk0IOVunZlbV5` plus focused
U09 recheck `ses_e48c2222cffebM8WOEV9Jfbiux` found no remaining M1 issue.
Task 8.3 remains open solely for final human review/disposition of recorded low
residuals, not date/lint/M1 approval. No final closure/Archive is claimed. Foundation
adoption is separately planned under `establish-frontend-foundation` and is not
claimed by the existing CU09 verification evidence.

- U07 authorizes Apply now; only complete/evidenced tasks may be checked, and no implementation closure is implied by approval.
- Sync/Archive, commit and push require their own applicable authorization and gates;
  stage 05 documentary closure did not authorize or perform any of them.

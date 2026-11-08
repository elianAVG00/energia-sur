# CU04 domicile and meter management - engineering record

## Goal and sources

Implement [CU04](../use-cases/cu04.md) on top of the existing CU09 domicile slice. [Proposal](../../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/proposal.md), [design](../../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/design.md), [delta specs](../../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/specs/), [tasks](../../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/tasks.md).

## Authorization and decisions

The initial PROPOSE authorization and CU04-scoped Q03/Q08/Q09 are recorded in [U11](../use-cases/decisions.md#u11---cu04-scoped-decisions-and-proposal-authorization). [U12](../use-cases/decisions.md#u12---cu04-contract-refinements-and-conditional-apply) approves ASCII number normalization, alias, API and 409 codes and conditionally authorizes Apply only after successful documentary gates and independent review. No sync, archive, commit or push is authorized.

## Work and evidence

- Primary agent used local read-only inspection, OpenSpec propose guidance, CLI context/list/new/status/instructions and documentation patches. No subagents were used.
- PASS: OpenSpec status reports 4/4 planning artifacts present; this is file status only, not structural validation or functional acceptance.
- NOT RUN: tests, builds, application, migrations and strict structural validation in this documentation-only stage. No runtime or security verification is claimed.
- BLOCKED: Apply until the U12 REVIEW gates pass; closure requires future functional checks, including independent data-isolation review.
- Risks: database/app ASCII equivalence, duplicate versus stale-write feedback, preserving existing domicile/cut associations, and future PDFs displaying corrected addresses. See design and tasks.
- No code, archived CU09, CU03 mount, data, commit, push, sync or archive changed in this proposal.

## U12 REVIEW evidence - stopped before Apply

- PASS: `openspec validate --all --strict --no-interactive`: 7 passed, 0 failed. Targeted `openspec validate manage-cu04-domiciles-meters --type change --strict --json --no-interactive`: 1 passed, 0 issues. Structural success is not functional approval.
- PASS: `git diff --check` and `git diff --cached --check` exited 0; Git warned that tracked documentation LF will become CRLF. These commands do not cover untracked files.
- Initial spec-analyst review found outdated Unicode/alias/409 rules; artifacts were updated. A follow-up (`ses_e46b917f5ffekwJAZA0M2xqOh6`) found the CU04 fiche stale; it was updated after that review and has not yet been independently rechecked.
- FAIL: independent read-only reviewer `ses_e46b6bc69ffeJp2DZBHSumUNCy` identified a HIGH concurrency gap in `design.md`: mapper version checks alone can skip an UPDATE for an unchanged payload, so a concurrent version change may not produce `VERSION_CONFLICT`. Required correction: an atomic version-qualified operation for every correction, including no-ops, with real PostgreSQL interleaving tests and independent re-review.
- BLOCKED: REVIEW acceptance, Apply/BUILD and all runtime gates. The user explicitly required stopping without implementation if REVIEW fails. No migration, app code, tests, builds, sync, archive, commit or push were executed in U12 REVIEW.

## Concurrency correction for renewed REVIEW

The user explicitly directed correcting the HIGH finding without reopening U11/U12. The design now requires every owner-scoped PATCH, including identical data, to execute an atomic version-qualified PostgreSQL UPDATE, increment exactly once and return the new version; failed writes roll back. Both deltas and task 2.5 specify stale/no-op, simultaneous edits, isolation and failure cases.

- PASS: `openspec validate --all --strict --no-interactive` returned 7 passed, 0 failed after the design/spec correction.
- PASS: `git diff --check` and `git diff --cached --check` returned 0; LF/CRLF warnings only. A PowerShell check of all seven untracked CU04 files found no trailing whitespace.
- PASS: read-only spec analyst `ses_e46b2b913ffe5IYUBbNd1dibxg` verified both resources' seven scenario classes and U11/U12 traceability.
- PASS: independent read-only reviewer `ses_e46b2b90effdcU6La50gERU6xb` found no remaining material blocker, accepted the previous HIGH correction statically and reviewed the reported change inventory and checks. Runtime behavior remains unverified.
- Conditional Apply was expressly authorized by the user after these gates; no additional functional-policy decision was identified. This does not authorize sync, archive, commit or push. Real PostgreSQL interleavings, browser acceptance and final independent security review remain mandatory.

## Apply and verification evidence

- Backend agent `ses_e46b093d5ffeV62WZgD07JUbVR` implemented the additive revision, owner-scoped APIs, atomic updates and tests; frontend agent `ses_e46b093d3ffe6wZjEPT6GqYdLi` implemented the CU04 feature, typed transport and browser scenarios. The primary integrated and verified. No new dependency pins or CU03/archived CU09 edits.
- Corrections observed: first frontend image build failed TS1294 due to a parameter property; corrected. Second failed an existing CU09 adapter conflict-guidance assertion; restored adapter behavior without weakening the test. First backend Ruff run identified two import-order errors; corrected and reran successfully. These are distinct failures, not passing initial runs.
- PASS: backend verification image build, `ruff check --no-cache app tests migrations`, and `mypy --cache-dir /tmp/mypy-cache app` (11 modules).
- PASS: frontend verification image build including strict TypeScript, production build, 56 Node tests and Oxlint (39 files, zero warnings/errors). Build reports upstream Radix module-directive warnings.
- PASS: primary-run isolated synthetic network/PostgreSQL acceptance via `%LOCALAPPDATA%/Temp/opencode/cu04-acceptance.ps1`, verification images `energia-sur-backend-checks:cu04` and `energia-sur-frontend-checks:cu04`: populated `0001_cu09` upgraded additively preserving domicile/cut IDs; 91 backend tests, zero skips, including opt-in populated migration, independent-connection races and two sanitized failure/rollback tests. No existing app database or containers were restarted or used for fixtures.
- PASS: same isolated run, CU04 Chromium 3/3 and CU09 Chromium 1/1; corrected-address PDF, existing CU09 closed and ongoing PDFs were downloaded and inspected via pypdf. Stable cut IDs and totals were checked across address correction; repeated migration and synthetic backend restart preserved IDs. The delayed-response test allows that the browser cancels a held response on unmount, so it does not prove delivery after cancellation.
- Retained synthetic resources: `cu04-qa-db-c7d6e6a6b763`, `cu04-qa-backend-c7d6e6a6b763`, `cu04-qa-frontend-c7d6e6a6b763`, browser containers `cu04-qa-browser-c7d6e6a6b763` and `cu09-qa-browser-c7d6e6a6b763`, network `cu04-qa-c7d6e6a6b763`; earlier isolated synthetic DB/network pairs `4bd9201dad8f`, `46c8be8a50d0`, and `c2c3dc60fc69` remain. No cleanup authorized. Synthetic PDFs are in the corresponding local OpenCode temp evidence directory.
- BLOCKED: final independent cross-stack security review and its recheck. Prior reviewer `ses_e46a6a7c6ffelt5m9wauNMKsJw` found two evidence gaps; extra backend failure tests and corrected-address browser/PDF evidence were added and passed. No closure, sync, archive, commit or push.
- FAIL: the same reviewer found a cross-form draft-loss regression: the shared revision key remounts and resets an unrelated address or meter form after a successful save. Fix and rendered tests in both directions, followed by independent recheck and affected gates, remain required.
- Correction: separate address/meter revisions and target-specific conflict reload preserve unrelated drafts. The frontend agent began this correction but its session ended with a subscription-sharing quota error; the primary inspected the partial changes and verified them without discarding work. A new rendered scenario covers both directions with successful saves, synthetic 503 failures and 409 recovery.
- PASS after correction: verification image rebuild (strict type/build, 56 Node tests and Oxlint), plus isolated PostgreSQL 91/91, CU04 Chromium 4/4, CU09 Chromium 1/1, both original and corrected-address downloaded PDFs and restart persistence. Latest retained synthetic resource suffix `8006325f633b`; same naming pattern as above. Static independent recheck of the fix is pending, and no completion is claimed yet.
- PASS: independent reviewer `ses_e46a6a7c6ffelt5m9wauNMKsJw` rechecked the corrected `DomicileManagement.tsx` and rendered scenarios: the shared-revision draft-loss finding is resolved, no new blocker in the reviewed scope. The reviewer was read-only; runtime evidence was generated by the primary agent. The earlier review covered backend authorization, migration and concurrency; its two test gaps were filled and exercised. A synthetic 409 on meter creation in the new form-preservation test supplements, rather than substitutes for, the separate real stale-edit scenario.
- CU04 is implemented and verified against the recorded checks. Pending separately authorized actions: OpenSpec Sync/Archive and any commit/push. Main specs have not been synchronized and CU09 archives remain untouched. Synthetic resources from the earlier full run with suffix `46c8be8a50d0` also include backend, frontend and browser containers, not just its database/network; all are retained without cleanup.

## Authorized sync and archive

- On 2026-11-08 the user explicitly authorized CU04 sync and archive, prohibited Git commands and application changes, and retained Git management personally. U11/U12 and the recorded verification evidence above remain the basis for closure.
- Pre-flight PASS, limited: inspected additive `0002_cu04.py`, reviewed CU04 ownership paths and scanned 20 implementation/test files for selected credential patterns without displaying values; no matches. This scan is not exhaustive. No Git commands were run, so the current complete worktree inventory and `0001_cu09.py` against its committed version were not independently rechecked in this closure session; the earlier verification evidence remains applicable.
- PASS: merged the four added domicile requirements while retaining the existing CU09 requirements, and created the `account-meters` main spec. `openspec validate --specs --strict --no-interactive` reported 5 passed, 0 failed. Existing `account-domiciles` purpose was intentionally preserved by the sync workflow even though it describes the original CU09-only slice.
- PASS: official `openspec archive manage-cu04-domiciles-meters --yes --skip-specs --json` moved the already-synchronized change to `openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/`; `specsUpdated: false` indicates the CLI did not repeat the earlier sync.
- No tests, builds, migrations, Git commands, functional code changes or CU09 archive edits were performed during closure. Retained synthetic resources were not removed.

# Public account registration

## Goal and authority

Implement transversal public username/password registration without adding a use
case or changing the existing opaque-session, CSRF, role, or account-isolation
architecture. User authorization and supersession evidence: U36 in
[`decisions.md`](../use-cases/decisions.md#u36---public-account-registration-authorization).

OpenSpec artifacts:
- [Proposal](../../openspec/changes/add-public-account-registration/proposal.md)
- [Design](../../openspec/changes/add-public-account-registration/design.md)
- [Tasks](../../openspec/changes/add-public-account-registration/tasks.md)
- [Registration contract](../../openspec/changes/add-public-account-registration/specs/account-registration/spec.md)
- [CU09 auth delta](../../openspec/changes/add-public-account-registration/specs/interruption-diary/spec.md)
- [Frontend transport delta](../../openspec/changes/add-public-account-registration/specs/frontend-session-transport/spec.md)

The prior CU09 prohibition on public registration is replaced narrowly; CLI
provisioning remains, and administrator promotion remains CLI-only.

## Work and decisions

- User-requested Build; synthetic data only. No migration or dependency change is
  planned. Registration creates a `user`, returns confirmation without a session,
  and requires subsequent login.
- `spec-analyst` reviewed the prior manual-provisioning policy, U09 boundary,
  account roles, and frontend transport. It confirmed the narrow conflict and
  reported no conflict with Origin/CSRF or role policies.
- Backend and frontend implementation agents were assigned disjoint code areas.
  Independent QA and security review are required before closing.
- Process-local abuse limiting is intentionally not distributed; the approved
  design documents multi-instance and proxy-address limitations.

## Verification evidence

- `pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1 -BackendTestPattern test_registration.py -E2ETestPattern e2e/public-registration.spec.ts -ArtifactDirectory <unique user-local temp path>` — PASS. Six backend PostgreSQL/ASGI registration tests passed; both Chromium tests passed, including Origin/no-CSRF, no automatic session, credential-free browser storage, username retained at login, Mi cuenta access, and logout. Existing DB container ID remained unchanged. Synthetic database/QA/artifact resources are retained; no database or volume was deleted.
- Runner prerequisite correction: local pgvector was available but the non-superuser synthetic role could not create it. The script now installs `vector` using the local database administrator only in the two newly created synthetic databases. It explicitly disables the outage/scheduled-work schedulers and guide ingestion, restores process environment variables in `finally`, and optionally selects test patterns; its default remains the broad suite.
- A first target run used stale verification images and exposed an invalid rate-limit fixture username (over 32 characters). The fixture was shortened; rebuilt verification images then passed the targeted suite.
- The initial browser assertion used `Request.headers()` to inspect Origin; Playwright omits security-related headers there. It now uses `Request.allHeaders()`. Browser execution then exposed a username-retention defect across form switching; the login field now receives the retained username as controlled form state. The final real browser run passed.
- `docker run --rm energia-sur-backend-checks:cu09 ruff check --no-cache app tests migrations` — PASS; `mypy --cache-dir /tmp/mypy-cache app` — PASS.
- `docker run --rm energia-sur-frontend-checks:cu09 npm test` — PASS (120/120); `npm run typecheck` — PASS; `npm run lint` — PASS (108 files, zero warnings/errors); `npm run build` — PASS (336 modules). Build emitted existing chunk-size and Radix `"use client"` bundler warnings.
- `openspec validate add-public-account-registration --strict --json --no-interactive` — PASS (1/1 change).
- `git diff --check` — PASS before the final documentation updates; rerun after review/doc edits.
- Fresh default diagnostic run: `pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1 -ArtifactDirectory <unique user-local temp path>` executed all 491 tests against a newly migrated synthetic PostgreSQL test DB and attempted the broad browser stages. Backend reported 14 failures and 7 skips; the browser stage exposed missing CU07/CU08 state fixtures and did not produce the CU09 PDF/persistence artifacts. Raw output and full backend traces are retained outside the repository under `%LOCALAPPDATA%\Temp\opencode\cu09-diagnostic-20261116-021040.log`; only redacted summaries are recorded here.
- Isolated configuration group rerun: bill PostgreSQL module PASS (17/17), photo PostgreSQL module PASS (30/30). Root cause for three bill failures was no synthetic `CU06_CONFIRMATION_SECRET` in the verification test process, causing storage requests to return 503. Three photo/OCR failures were due to missing cgroup memory/swap/core-dump preconditions and missing private CU06 bill directory: OCR abstained before validating/recognizing payloads, and a second bill-reconciliation warning invalidated the one-warning assertion. The runner now supplies a generated synthetic secret through environment-name forwarding, 2 GiB memory with swap equal to memory, core limit zero, and separate private tmpfs photo/bill directories. No functional CU05/CU06 code or policy changed.
- One complete post-correction backend confirmation run: 491 total; 476 PASS, 8 FAIL, 7 SKIP. The eight residual failures are unrelated to registration and were reproduced by module:
  - `test_cu01_outages.ApiTests.test_areas_list_from_snapshot`: legacy uppercase party-label assertion versus current catalog canonical title case.
  - `test_cu01_outages.ApiTests.test_database_unavailable_returns_503`: test mocks `current_snapshot` but requests `/outages/areas`, which calls `load_catalog` and never invokes that mock.
  - `test_cu01_outages.ApiTests.test_no_snapshot_and_unverified_area`: old coverage-state expectation conflicts with the active shared coverage catalog’s classification.
  - `test_cu01_territory.ResolveApiTests.test_resolve_address_with_hint_and_privacy` and `test_resolve_location_and_out_of_scope`: legacy uppercase expected labels versus canonical title-case catalog labels.
  - `test_cu02_scheduled_works.ApiTests.test_areas_list_is_catalog_only`: legacy uppercase key expectation versus canonical catalog label.
  - `test_cu02_scheduled_works.ApiTests.test_degraded_source_never_reports_no_works` and `test_no_works_only_with_fresh_covered_snapshot`: old `unavailable`/`no_works` expectations conflict with the active catalog’s `coverage_unverified` classification.
  The seven skips are pre-existing live ENRE/GeoRef and reconciliation prerequisites. No CU01/CU02 business behavior or test assertions were changed. These residuals do not exercise registration, but the broad backend gate remains FAIL and must be disclosed.
- Integrated real-browser run used `-BackendTestPattern test_registration.py -E2ETestPattern 'e2e/cu04.spec.ts;e2e/cu09.spec.ts;e2e/public-registration.spec.ts' -RunPostBrowserChecks`: backend 6/6 and Chromium 7/7 PASS. It verified a newly registered account, subsequent login, own domicile create/list, absence of its domicile under a second CLI-provisioned account, authenticated POST rejected without CSRF, logout/session invalidation, and the legacy CLI login flow.
- Actual generated CU09 closed/ongoing PDFs passed Unicode, fields, row-order, status, and total assertions. After migration and backend restart, the runner logged back into the new registered account and a CLI-provisioned account and verified account/domicile/diary identities and values. The existing DB container ID was unchanged; no volume/data was deleted. Synthetic report/artifacts are retained under `%LOCALAPPDATA%\Temp\opencode\cu09-integration-confirm-20261116-023903`.
- The default all-E2E run exposed missing unrelated `/state/cu07-state.json` and `/state/cu08-state.json` fixtures. The scoped real CU04/CU09/public-registration browser run passed; this does not claim all-CU Playwright acceptance.
- QA review identified that the account labeled CLI-style had initially been inserted directly by the fixture. The test now actually invokes `python -m app.provision --password-stdin` against the isolated test database and verifies subsequent login; the rebuilt focused PostgreSQL/ASGI suite passed 6/6 and selected browser run passed 2/2 again.
- Independent static security review found no confirmed implementation defect. Its low-severity documentation finding that README omitted `/register` from the narrow CSRF-exempt public unsafe endpoints has been corrected; authenticated mutations are explicitly documented as retaining Origin and session-bound CSRF. The review also found stale verification/task records, now reconciled in this log, `docs/STATE.md`, and `tasks.md`. Reviewer follow-up confirmed both findings resolved and identified no remaining issue; review was static-only and did not independently run checks or inspect exact diff attribution.
- Independent QA completed its read-only acceptance review. It confirmed the focused reported checks, identified the CLI compatibility-test gap, and that gap was fixed by invoking the actual provisioner; backend (6/6), browser (2/2), Ruff, mypy, strict OpenSpec validation, and `git diff --check` were rerun/passed afterward. QA did not independently execute checks. The broad backend suite remains FAIL as described above.
- During an earlier PowerShell quoting attempt, one environment value was emitted to local shell output. The owner classified it as synthetic/non-sensitive; it was not re-read or reproduced, and no value is recorded here. No credential rotation is indicated by that classification.
- Final independent QA read-only review confirmed the registration acceptance scenarios and correctly retained the broad backend result as FAIL. It noted two stale README claims that integral acceptance was pending; those statements were corrected. The independent security/regression reviewer found no confirmed defect in the reviewed source/runner/E2E contracts. That review was static, did not execute checks, and could not confirm exact diff attribution; runtime evidence remains the separately recorded test output. Neither review calls the full backend suite green.
- At the verification checkpoint, no Archive, sync, commit, push, or deploy had occurred. Registration-specific acceptance and both final reviews are complete; the broad backend suite remains a failed required regression gate. Under the project quality-gate rules, do not Archive until the unrelated residual failures are resolved or explicitly dispositioned under project policy.

## Follow-up status (2026-11-16)

- `openspec validate add-public-account-registration --strict --json --no-interactive` and `git diff --check` — PASS after documentation/task updates (Git reports LF/CRLF conversion warnings only).
- PowerShell syntax parse for `scripts/Test-Cu09Acceptance.ps1` — PASS. Frontend verification image build — PASS (TypeScript/build 336 modules, 120/120 unit tests, Oxlint). Ruff and mypy — PASS.
- The owner classified the previously exposed local shell-output value as synthetic/non-sensitive; it was not re-read or copied into this record. No rotation was performed.
- Full backend suite: FAIL (476/8/7); six CU06/OCR environment failures resolved; eight unrelated CU01/CU02 tests remain. Scoped account-registration/CU04/CU09 integration, PDFs, persistence, and existing CLI compatibility PASS.
- OpenSpec tasks 4.1 and 4.2 are complete as performed (fresh diagnostic/classification, one full confirmation run, scoped synthetic integration, PDFs/persistence, and final QA/static review). The change is still **BLOCKED for Archive** by the 8 unrelated failures in the required broad backend gate; the reviewer and QA explicitly did not call that gate green. See [tasks](../../openspec/changes/add-public-account-registration/tasks.md).

## Closure constraints

Do not archive, sync, commit, push, deploy, delete databases, or remove volumes.
Preserve unrelated pre-existing changes in the territorial catalog and outage/
scheduled-work specifications.

## Backend regression closure follow-up (2026-11-16)

- The eight CU01/CU02 failures that had blocked the registration broad-regression gate were
  reproduced against isolated PostgreSQL and corrected in tests only. Assertions now match the
  accepted title-case catalog labels, PostgreSQL-backed area endpoints, and locality-level
  `coverage_unverified` semantics. The unavailable-database test now mocks the catalog reader
  actually used by `/outages/areas`. No registration behavior, authorization rule, or assertion
  strength was weakened.
- Focused CU01/CU02 and territorial migration tests passed before the final broad run. The
  complete backend suite then passed once on a fresh, fully migrated, network-isolated PostgreSQL
  container: 491 tests total, 484 passed, 7 skipped for external/live or explicit reconciliation
  prerequisites.
- Ruff, mypy, and strict OpenSpec validation passed. Existing registration-specific PostgreSQL,
  Chromium, PDF, and restart-persistence evidence remains as recorded above; the current full
  backend run additionally passed registration/session/CSRF/ownership coverage.
- No production registration/session code, frontend files, dependencies, migrations, or
  authentication policy changed. The original Compose services and database volume were not used.
  No sync, archive, commit, push, or deploy occurred.
- Final result superseding the earlier 491-test snapshot above: the final complete backend suite
  passed 493 tests (486 passed, 7 external/live prerequisite skips, 0 failures) after the CU01/CU02
  test-only corrections. It ran against a newly created PostgreSQL container on a private network
  with tmpfs storage; the original Compose services and volumes were not used. Registration-specific
  backend/browser/PDF/restart acceptance remains PASS. This clears the broad backend regression
  blocker; it does not waive the separate territorial catalog runtime-review gate.

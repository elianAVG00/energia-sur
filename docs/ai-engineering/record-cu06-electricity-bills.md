# CU06 proposal engineering record

## Goal and authority

Implement private bill recording for an owned meter, preserving CU07 date boundaries. The user's CU06 PLAN instruction approved the functional rules; PROPOSE authorized planning, Review approved the design and Apply implemented it. See [Q12](../use-cases/decisions.md#q12), [archived proposal](../../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/proposal.md), [design](../../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/design.md), [delta](../../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/specs/electricity-bills/spec.md), [tasks](../../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/tasks.md) and the [main specification](../../openspec/specs/electricity-bills/spec.md). The change was archived on 2026-11-09. No original proposal PDF was available; `docs/stage-05-context.md` was consulted instead.

## Work and review

The subsequent user instruction explicitly approved Review and authorized CU06 Apply/BUILD. It selected `pypdf` for structural, page, encryption and detectable-active-content checks in an isolated time- and memory-bounded process. This authorizes that runtime dependency direction, not Sync, Archive, commit, push or CU07. Exact enforcement and hostile-file evidence remain required.

OpenCode inspected CU04/CU05 contracts and relevant source, created the OpenSpec change using CLI 1.16.1 and updated the CU06 fiche/register. `spec-analyst` (`ses_e3f50baf2ffejE6O6dtql80w2U`) reviewed traceability; independent `reviewer` (`ses_e3f50baeaffeQATP7aQE2QzIWB`) performed one scoped static review. Findings corrected: Q09's stale CU06 status; same-key idempotency versus distinct-key duplicate scenario; overlap token binding to the full validated payload; and file acceptance conditional on a reviewed safety policy. The reviewer did not inspect every CU05 storage dependency and no re-review is claimed. The primary agent inspected `backend/app/photo_store.py`, `photo_files.py` and `photo_reconciliation.py`; this is not a substitute for independent implementation review.

## Checks and limitations

- **PASS:** `openspec validate record-cu06-electricity-bills --type change --strict --no-interactive` (repository root, OpenSpec 1.16.1): change valid. This checks structure, not human approval or implementation.
- **PASS:** `git diff --check` for tracked edits, with only Git LF/CRLF notices; new untracked change files are outside that command's coverage.
- **BLOCKED:** human technical Review; approved bounded PDF validation approach, exact resource limits and any production dependency; separate Apply authorization. PDF runtime safety cannot be established from this draft.
- **NOT APPLICABLE:** functional application tests/build, migration, deployment, Sync and Archive in this proposal-only phase. No runtime isolation, recovery or end-to-end result is claimed.

## Apply checkpoint

- **PASS (limited):** `python -m unittest tests.test_bills` from `backend/`, two tests on host Python 3.15.2. The project supports Python 3.13, so this does not replace the required container-runtime gate. The standalone `app/bills.py` is not connected to routes or persistence.
- **PASS:** `openspec validate record-cu06-electricity-bills --type change --strict --no-interactive` after Apply began.
- **BLOCKED / incomplete:** the PDF implementation and hostile-file evidence, migrations, private storage, endpoints, frontend, isolation/concurrency/recovery verification, E2E and final independent implementation review have not been completed. No production dependency or lockfile was changed. OpenSpec progress: 2/16, only human Review and Apply authorization recorded.

## Subsequent Apply work

- Added standalone `app/bill_pdf.py` with a spawn worker, 512 MiB address-space limit, 10 s CPU/wall limits, no core dumps, strict pypdf parsing, bounded reachable-object walk, page checks and rejection of selected active keys. This is not integrated into an endpoint, nor a malware scanner or proof of absence of all active content; detached/unreachable objects and parser limitations require further analysis. Runtime `pypdf` dependency and lockfile have not yet been changed.
- Added draft `0004_cu06` migration and corresponding bill/idempotency models. No migration was run and no PostgreSQL constraint or concurrent-write verification was performed.
- **FAIL then PASS:** with the existing Python 3.13 verification image and a read-only backend bind mount, `python -m unittest tests.test_bills tests.test_bill_pdf` first failed because pypdf 7 removed `add_js`; the synthetic fixture was corrected to set an OpenAction. The rerun passed 4 tests in 2.758 s. This does not prove timeout, memory enforcement or all malicious-content cases.
- **PASS:** same image and mount: Ruff on the new/changed Python files and mypy on `app/bill_pdf.py app/bills.py app/models.py`. `openspec validate record-cu06-electricity-bills --type change --strict --no-interactive` passed.
- **INCOMPLETE:** PDF safety evidence and dependency update, DB migration tests, storage and routes, UI, security, concurrency, recovery, integration, browser acceptance and final independent review remain open. No cleanup, Sync, Archive, commit or push performed. No task has been marked complete without its tests.

## Continuation

- The user reaffirmed Apply, explicitly accepted pypdf's documented limitations and requested a single final independent implementation review. The locked `pypdf==7.0.0` dependency was moved from the dev group to runtime, with the lock regenerated using uv 0.13.7; `uv lock --check` passed. No version upgrade was introduced.
- The design now spells out CU06 JSON field names and overlap conflict shape for frontend/backend consistency. The earlier proposal-stage language about missing PDF approval is superseded by the user's Apply and limitation-acceptance instructions.
- Backend subagent produced unintegrated overlap HMAC primitives; the primary agent added isolated-directory immutable-file primitives. Neither provides routes, account authorization, reference-checked cleanup or database transaction coordination. Their use requires further implementation.
- **PASS:** seven synthetic focused tests under the Python 3.13 verification image (`python -m unittest tests.test_bills tests.test_bill_pdf tests.test_bill_confirmation tests.test_bill_files`); Ruff and mypy passed for the added primitives. The confirmation test's initial Ruff import-order failure was corrected and rerun successfully. `uv lock --check` and strict OpenSpec validation passed. No end-to-end or independent final implementation review is claimed.
- Frontend subagent implemented the bill UI and adapter; backend subagent added unconnected transactional primitives. **FAIL then PASS:** frontend Node tests and TypeScript initially failed on unsupported parameter-property syntax; replacing it with an erasable field declaration fixed both. Reruns: 80 frontend tests passed, lint passed and build passed with Vite bundle/directive warnings. Backend `tests.test_bill_store` passed (one fingerprint test) with Ruff and mypy; no DB integration is implied.
- **BLOCKED:** connecting the overlap HMAC requires a shared server-only key across instances. The prior suggestion to use `WebSession.token_hash` is unsafe: a session owner who knows their cookie can derive it and forge confirmations. The approved design does not specify server-key generation, persistence, sharing or rotation. No such key has been installed or used. The user needs to approve a backend-only shared secret configuration or another reviewed key design. Routes, crash-safe storage coordination, migration integration tests, browser E2E and final independent review remain incomplete; UI is not evidence of a working CU06.

## Current continuation

- The user approved a random backend-only environment key of at least 32 bytes, generated for local Docker, with restart invalidating pending confirmations accepted and no rotation infrastructure. The prior key-provisioning decision blocker is resolved; implementation evidence is pending.
- Added `frontend/e2e/cu06-real.spec.ts` for a synthetic real-service bill flow. With the current E2E tree mounted, frontend lint passed. Typecheck initially failed at an existing optional synthetic PNG encoding in `cu05-real.spec.ts`; a fail-fast null guard corrected it and typecheck then passed without changing application behavior.

## Implemented slice and final checks

Backend: `app/bill_api.py` (owner-scoped routes, strict JSON, private delivery), `app/bill_store.py` (meter lock, replay, version, duplicate, overlap snapshot/staging), `app/bill_confirmation.py` (HMAC token bound to payload and snapshot), `app/bill_files.py` (private immutable objects), `app/bill_pdf.py` (bounded pypdf worker), `app/start.py` (process-local key), `migrations/versions/0004_cu06.py`, models and `main.py` router registration. Compose mounts the private `cu06_bills` volume, and the backend image creates `/var/lib/energia-sur/bills`. The overlap secret is a backend-only environment variable; local Compose start generates one and restart invalidates pending confirmations as the user accepted.

Frontend: `features/bills/{api,BillHistory}` plus small transport additions for structured bill conflicts and idempotency. The UI supports list/detail, create, correction with optional replacement, private download, overlap review/confirmation, safe retries and account/meter reset.

Review corrections (single independent review, `ses_e3ebea2b4ffeNHKXaAU4N6FBjo`): reused request connection before the guard (pool exhaustion); accepted and surfaced an empty current overlap snapshot; moved expensive file validation under the serialized guard (aggregate admission); invalidated in-flight list requests on mutation.

Evidence in this run (PowerShell, repository root, isolated network `cu06-qa-20261109`):

- **PASS:** `docker run ... energia-sur-backend-checks:cu05-ocr python -m unittest discover -s tests` against fresh migrated `cu06_fresh3` with tmpfs bill/photo dirs: 238 tests, 1 skipped (populated CU04 migration opt-in), 116.245 s. Passed on a second fresh database after earlier runs exposed cross-test filesystem residue, which was isolated by the tmpfs.
- **PASS:** Ruff on `app tests migrations`; mypy strict on 27 modules; `uv lock --check`; runtime image build with `pypdf==7.0.0` installed.
- **PASS:** frontend Node tests 80/80, Oxlint zero warnings, TypeScript and Vite production build (chunk-size and Radix directive warnings only).
- **PASS:** OpenSpec `validate --all --strict --no-interactive`: 9/9 items.
- **PASS:** real Chromium against isolated backend/frontend, DB `cu06_e2e` and volume `cu06-e2e-bills`: register bill, duplicate-free create, overlap warning plus confirmation, correction with file replacement, private PNG download, second account gets 404 for list and file (2 tests). After a backend restart, the bill list and private file remained available (1 test). No real bill or personal data used.
- **LIMITATION:** PDF checks reject synthetic encrypted, OpenAction, malformed, empty and oversized files, but cannot prove absence of malware; the wall-clock timeout branch is configured, not exercised.
- **LIMITATION:** PDF checks reject synthetic encrypted, OpenAction, malformed, empty and oversized files, but cannot prove absence of malware; the wall-clock timeout branch is configured, not exercised.

## Recovery and matched backup/restore (tasks 3.2-3.3)

`app/bill_reconcile.py` adds a startup pass that shares the writer advisory key and CU06 filesystem lock, reads all committed `file_key` values, and deletes only unreferenced `cu06-` objects and `.cu06-*.tmp` names. It ignores CU05-named objects, never follows links, and deletes nothing when a reference is invalid or missing.

- **PASS:** four synthetic planning tests (`tests.test_bill_reconcile`): referenced files protected, orphan and temporary candidates identified, CU05 objects ignored, missing references and symlinks block the plan, no deletion occurs during planning.
- **PASS:** opt-in `tests.test_bill_reconcile_postgres` against dedicated migrated `cu06_reconcile`: a live bill file survived reconciliation; an orphan modelling a rolled-back/unknown commit and a crashed temporary were removed; a CU05 object was untouched; 20 concurrent reads during reconciliation returned identical bytes; after deleting the referenced file, reconciliation removed nothing and retained a new candidate (fail closed).
- **FAIL then PASS:** the first integration attempt reused a shared database containing bills whose files lived in earlier temporary directories; reconciliation correctly failed closed and kept everything. The test was moved to a dedicated database and rerun successfully.
- **PASS:** full backend suite against fresh `cu06_fresh4`: 243 tests, 2 opt-in skips, 116.503 s; Ruff and mypy strict on 28 modules; OpenSpec strict 9/9.
- **FAIL then PASS:** the first drill attempt stopped after provisioning because the script assigned the read-only PowerShell automatic variable `$HOME`. No backup had been taken. A continuation script renamed it, reused the already migrated synthetic database and completed the drill.
- **PASS:** isolated matched backup/restore drill on network `cu06-drill-net-20261109` with PostgreSQL container `cu06-drill-pg-20261109`, backend `cu06-drill-backend-20261109`, volumes `cu06-drill-pgdata-20261109` and `cu06-drill-bills-20261109`. One synthetic bill (`cu06_drill`, PNG, 42.5 kWh, ARS 1234.56) was created through the real API. The backend was stopped, `pg_dump -Fc` and a volume tar were taken, then restored into `cu06-drill-pg-restore-20261109` and `cu06-drill-bills-restore-20261109`. After restart the bill ID, period, kWh, amount and file SHA-256 (`C414CD0E...D7CE77`) matched. The original drill database container was not recreated.
- **PASS:** with the new backend image, a clean two-account browser flow passed on DB `cu06_e2e2` and volume `cu06-e2e-bills2`, and a restart with startup reconciliation reported no recovery failure and retained the bills and private file.
- Synthetic resources retained: databases `cu06_synthetic`, `cu06_fresh2`, `cu06_e2e`, `cu06_fresh3`, `cu06_fresh4`, `cu06_reconcile`, `cu06_e2e2`; containers `cu06-qa-postgres-20261109`, `cu06-qa-frontend-20261109`, stopped `cu06-qa-backend-20261109`, `cu06-e2e-backend`, `cu06-e2e-frontend`, and the `cu06-drill-*` drill containers; volumes `cu06-qa-bills-20261109`, `cu06-e2e-bills`, `cu06-e2e-bills2` and the `cu06-drill-*` volumes; artifacts under the user-local OpenCode temp directory. The drill script lives only in that temp directory. No cleanup, Sync, Archive, commit, push or CU07 work performed.

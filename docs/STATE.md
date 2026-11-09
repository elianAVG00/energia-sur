# Operational state - energia-sur

Updated: 2026-11-09 (CU05 authenticated DEV tests passed; red-fraction contract decision open).

## Active CU05 proposal
- [Proposal](../openspec/changes/record-cu05-meter-readings/proposal.md), [design and review gates](../openspec/changes/record-cu05-meter-readings/design.md), [delta](../openspec/changes/record-cu05-meter-readings/specs/meter-readings/spec.md), [tasks](../openspec/changes/record-cu05-meter-readings/tasks.md); [U13](use-cases/decisions.md#u13---cu05-functional-decisions-and-propose-authorization) and [M1](use-cases/decisions.md#cu05-m1---ocr-may-abstain-closure-decision) record approved rules.
- OCR endpoint now runs Tesseract + OpenCV in a bounded child, using a shared-volume inherited flock and Linux parent-death signal; frontend keeps suggestions editable and requires explicit confirmation. All backend instances must share the same private volume and lock inode.
- PASS fresh isolated DB: 207 backend tests; Ruff and mypy (20 files); frontend 75 tests and lint. Chromium regression now reads the formerly misrecognized synthetic canvas correctly, keeps it editable and does not save; the real photo abstains, which the user accepts. No representative accuracy is claimed.
- PASS isolated container tests: shared-lock saturation, first-container kill, recovery and restart; measured 256 MiB engine and 512 MiB worker limits, timeout and no swap/core on configured runtime. OCR now abstains before buffering if privacy controls cannot be verified.
- One focused independent review found three issues: image validation before admission, wrong invalid-crop status, and a conflict between absolute red-fraction requirements and heuristic detection. The first two were fixed; worker and API checks passed, including API death during decoding.
- PASS: two authenticated Chromium DEV flows, including confirmed synthetic reading/photo, history, OCR suggestion and abstention; both were repeated after fixes (2/2). Synthetic DEV accounts and data are retained. No real photo was transferred or committed.
- BLOCKED for Sync/Archive: the spec's unconditional exclusion of fractional digits conflicts with the heuristic, which cannot prove all red fractions are detected. A user decision on that contract is required; no new independent review has been requested. The real-photo abstention remains accepted.
- The real photo stays Git-ignored and was tested locally; preprocessing abstained, with no value returned. The user supplied only a provisional visual reference, not a confirmed ground truth. See [evidence](ai-engineering/record-cu05-meter-readings.md).
- PASS isolated synthetic backup drill: fresh migrated PostgreSQL and photo volume were backed up with writers stopped and restored as a matched pair. After database and backend restarts, the restored reading and synthetic PNG were retrieved through the authenticated API. Resources are retained under `cu05-restore-*-20261109` and `cu05-drill-*-20261109`; this is not a production deployment.
- Isolated synthetic resources retained: container `cu05-isolated-pg-20261108`, network `cu05-isolated-qa-20261108`, volumes `cu05-photo-test-20261108` and `cu05-pw-artifacts-20261108`, databases `cu05_tmpfs_20261108`, `cu05_final_20261108`, `cu05_final2_20261108`, `cu09_app_71a13f97d035`, `cu09_test_71a13f97d035`, `cu09_app_78cb3dbbb73a`, `cu09_test_78cb3dbbb73a`, and QA containers `energia-sur-cu09-qa-71a13f97d035` and `energia-sur-cu09-qa-78cb3dbbb73a`; no published PostgreSQL port. Do not use for real data or remove without authorization.

## Latest checkpoint - CU09 and frontend foundation archived
- **CU04 IMPLEMENTED / VERIFIED / ARCHIVED:** [proposal](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/proposal.md), [design](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/design.md), [tasks](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/tasks.md); U11/U12 and REVIEW authorized Apply. Synthetic backend 91 tests, frontend 56 tests, browser CU04 4/4 and CU09 1/1, PDF and restart checks passed. Independent reviewer rechecked the draft-loss fix; see [evidence](ai-engineering/manage-cu04-domiciles-meters.md). User authorized sync and archive; main specs synchronized.
- Apply entry checkout: clean `main`, ahead 1 of `origin/main`, HEAD `f76bc0f06b24666ff7852010142baf218dc8eed4` (`docs: close stage 05`). Existing human commit preserved; no commit/push authorized here.
- **Stage 05 CLOSED documentarily:** user explicitly accepts [catalog](use-cases/README.md), [shared rules](use-cases/shared-rules.md), [register](use-cases/decisions.md) and [workflow](openspec-workflow.md), including their remaining TBDs. See [U06](use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization) and [closure record](ai-engineering/stage-05-sdd.md#accepted-baseline-checkpoint---u06).
- **Q00 APPROVED:** user confirms the teacher approved all ten Energía Sur CUs. No teacher approval date/channel recorded. This satisfies the academic prerequisite, not design/Apply authorization.
- **CU09 SELECTED first for stage 06:** [proposal](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/proposal.md), [design](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/design.md), [delta specs](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/specs/interruption-diary/spec.md), [tasks](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/tasks.md), [engineering evidence](ai-engineering/record-cu09-interruption-diary.md).
- U07/U07-T approve the [technical package](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/contract.md); U09 clarifies trusted-Origin login and CSRF on authenticated writes. User approved closure and archive on 2026-11-08.
- U10 authorized foundation Apply; both changes are archived after sync: [CU09 archive](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/), [foundation archive](../openspec/changes/archive/2026-11-08-establish-frontend-foundation/), [evidence](ai-engineering/establish-frontend-foundation.md), [reuse guide](frontend-foundation.md). No commit/push/deployment.

## Approved stack and existing implementation
- React/TS/Vite/npm pins preserved; Python/FastAPI/Uvicorn/uv/PostgreSQL retained. CU09 adds approved SQLAlchemy/psycopg/Alembic, ReportLab, Playwright/pypdf and Ruff/mypy with locked versions.
- PostgreSQL `db:5432` is internal; `pgdata` at `/var/lib/postgresql`. Loopback frontend/backend mappings are 5173/8000. Images use verified linux/amd64 digests; services run non-root.
- `/api/health` proxies to `GET /health`, HTTP liveness only, with no database/provider readiness claim. Backend LangChain + OpenAI is confirmed later direction, not installed here.
- Implemented: private login/logout, owned domicile register/list/select/correct, owned meter create/list/correct, and CU09 cuts, summaries and Unicode PDFs. CU04 archived; no chatbot.
- Previous CU09/foundation acceptance PASS: 66 backend tests (14 real PostgreSQL/ASGI, zero skips, 10.397s), including U09 Origin/CSRF regressions. Frontend 50 Node tests, Oxlint (33 files, zero warnings/errors), strict TS/production build, locked builds and uv/npm drift rejection PASS; backend Ruff/mypy (10 modules) PASS.
- Exactly one quick Chromium workflow PASS (7.7s), now exercising foundation-adapted CU09: actual PDFs/text, two accounts, 409/draft resets, narrow/desktop layout, one deferred chat mount/no chat requests and migration/restart persistence. Strict OpenSpec4/4 PASS; foundation18/18 tasks verified; no repeated browser suite.
- Existing synthetic database credentials/data are technical-only; changing `.env` does not rotate persisted credentials. Preserve `energia-sur_pgdata` and do not read secrets for context.
- Foundation includes Tailwind/local MIT-licensed shadcn primitives, memory-only Zustand, RHF/Zod on all CU09 forms, shared Axios and a single unavailable CU03 mount. Separate reviewer `ses_e48b00a1dffevhekFKL5Dug2tR` found no remaining confirmed defects after timeout fix/recheck; review static, runtime checks primary-run.

## Existing technical changes and evidence
- Docker remains OPEN: [18/22 tasks](../openspec/changes/docker-development-environment/tasks.md), [design](../openspec/changes/docker-development-environment/design.md), [delta spec](../openspec/changes/docker-development-environment/specs/development-environment/spec.md), [runtime/review evidence](ai-engineering/docker-development-environment.md).
- Docker tasks 1.4/2.4/7.1/7.2 remain unchecked pending their own reconciliation; CU09 Ruff/mypy/Oxlint pass. Do not silently close inherited gates.
- Development MCP setup remains 8/8 checked and unarchived: [tasks](../openspec/changes/configure-readonly-development-mcp/tasks.md), [real-call evidence](ai-engineering/configure-readonly-development-mcp.md). No fresh token/isolation assurance claimed.
- Installed CLI 1.16.1, schema `spec-driven`, custom profile with explore/propose/apply/update/sync/archive. Review and Verify are team steps; installed generated skills/configuration preserved.

## Blockers and unresolved decisions
- U08 resolved prior blockers: inclusive 1970-01-01 00:00 Buenos Aires input floor and Oxlint 1.92.0, preserving TypeScript 7.0.2. Implemented and verified; no rounding or forced dependency install.
- M1 resolved by U09 and focused independent recheck `ses_e48c2222cffebM8WOEV9Jfbiux`; earlier full source audit covered every owner-bound route. CU09 24/24 tasks and foundation 18/18, archived; 4 main specs synchronized.
- Low CU09 residuals: out-of-band pre-1970 DB rows can fail reads; NUL text may yield 503. Registry-config limitation resolved by primary security inspection: frontend/.npmrc has no credential-related entries (no values logged). Review is static; runtime evidence is primary-run.
- Latest app uses synthetic acceptance DB; retained databases/containers/artifacts are listed in engineering evidence. Original db container/volume preserved; cluster has additive synthetic databases. No cleanup authorized.
- Unrelated catalog TBDs, hosting and persistent chatbot memory remain unresolved. No other CU claimed complete.

## Next actions
1. Resolve the red-fraction contract conflict with the user before Sync/Archive; do not invent a guarantee.
2. Keep the synthetic DEV accounts and data until their deletion is explicitly authorized.
3. Preserve retained synthetic resources and unrelated work; test-only repository artifacts were removed.
4. Reuse the foundation for future accepted CUs; CU03 chat runtime is separate.
5. Track CU09's low out-of-band-row and NUL-input risks for future triage.

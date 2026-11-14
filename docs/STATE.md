# Operational state - energia-sur

Updated: 2026-11-13 (CU05 red-fraction contract resolved by human decision; `record-cu05-meter-readings` and `isolate-cu05-reading-history-by-meter` synced and archived; `meter-readings` 21 requirements / 44 scenarios; QA-INT-CU04-08 deferred).

## CU03 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/proposal.md), [assistant spec](../openspec/specs/assistant/spec.md) (17 requirements), [engineering record](ai-engineering/implement-integrated-assistant-cu03.md); [U23](use-cases/decisions.md#u23---cu03-integrated-assistant-decisions-and-propose-authorization).
- BUILD 1 backend: guide ingestion (`guide_parser`/`guide_store`), pgvector 0.8.7 on PostgreSQL 18.6, LangChain + OpenAI (`gpt-4o-mini`, `text-embedding-3-small`), `POST /assistant/chat` SSE, Origin/rate-limit, static fallback. Migration `0007_cu03` (4 additive tables). Docker includes `knowledge/` in both stages.
- BUILD 2: read-only CU01/CU02 LangChain tools and deterministic RAG/current/scheduled routing in `assistant_tools`; frontend `features/assistant` (fetch/ReadableStream SSE, temporary Zustand history, cancel, safe HTTPS sources) inside the single `ChatMount`; `optional_actor` and concurrency slots.
- BUILD 3: owner-scoped persistent conversations (`assistant_memory`), bounded history injected into LangChain, `GET /assistant/conversations`, `GET .../{id}/messages` and CSRF-protected `DELETE .../{id}`; visitor TTL in Zustand; reset on session generation change; retention documented (30 days proposed, messages kept until owner delete, auto-delete pending approval); visible OpenAI/privacy notice.
- PASS: Ruff, mypy (50 files), 54 CU03 backend tests (offline + PostgreSQL/pgvector + tools/routing + memory/isolation/CSRF), 134 frontend tests, 81 CU01/CU02 regressions (6 skipped live), 7 health/security, 3/3 mocked Playwright flows + 1 real-backend flow, migration upgrade/downgrade, `openspec validate --strict`, PostgreSQL 18.6 + pgvector 0.8.7.
- Real OpenAI PASS (2026-11-11): 53 articles indexed with `text-embedding-3-small` (53 active chunks, 1536 dims, no duplicates); question about a vencida bill retrieved **PA-02** and returned an SSE answer with official `edesur.com.ar` sources and `done ok:true`.
- Infrastructure: Compose `energia-sur` (`compose.yaml` + `compose.cu09.yaml`), db `energia-sur-db-1`, volume `energia-sur_pgdata`; app connection reused the existing `energia_sur` database/role. `alembic upgrade head` → `0007_cu03 (head)`, vector 0.8.7, 19 `es_*` tables; backend rebuilt and healthy; guide SHA-256 unchanged. Task 2.1 PASS (marker survived db recreation; volume preserved).
- Accepted limitations (not implemented features): authenticated history is API-only, without a listing/restoration UI; the 30-day retention policy is proposed, with no approved automatic deletion; answers render as plain text, with official HTTPS sources shown separately.
- Sync/Archive (2026-11-11): 17 requirements added to `openspec/specs/assistant/spec.md`; 2 modified (`frontend-session-transport`, `frontend-shell`); `openspec validate --all --strict` 14/14 PASS. Archived with 31/31 tasks.
- Closing commit `feat(cu03): implement RAG-powered assistant with OpenAI and pgvector`; no push.

## CU01 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/proposal.md), [main spec](../openspec/specs/current-outages/spec.md) (18 requirements); U16/U20. Public ENRE snapshot (5-min advisory lock), GeoRef/coverage and public panel. PASS: 51 CU01 backend tests, 106 frontend tests, real-backend/E2E, `openspec validate --strict`. Exceptions 0.1/0.4 accepted (unverified zones stay `coverage_unverified`). No push.

## CU02 - COMPLETED / ARCHIVED (U22 definitive scope)
- [Archived change](../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/proposal.md), [main spec](../openspec/specs/scheduled-works/spec.md) (13 requirements); U21/U22. ENRE `cortesProgramados` only; dates/reason/distance out of scope. PASS: 30 tests, additive `0006_cu02`, `openspec validate --strict`. No push.

## CU10 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/proposal.md), [main spec](../openspec/specs/source-refresh-administration/spec.md) (12 requirements), [engineering record](ai-engineering/supervise-source-refresh-cu10.md); [U24/25](use-cases/decisions.md#u24---cu10-source-supervision-decisions-and-propose-authorization). Admin-only supervision of the two existing ENRE sources, reusing the CU01/CU02 schedulers, advisory locks (`0x43553031`/`0x43553032`), fetch runs and snapshots.
- Backend: additive `0008_cu10` (`es_accounts.role` default `user`; `es_source_config` seeded 300/300); `app/source_config.py`; `app/admin_api.py`; `app/promote.py`; `refresh_now()` → 409 `SOURCE_BUSY`; atomic versioning → 409 `VERSION_CONFLICT`; per-cycle `next_interval`/`run_cycle` with safe `300` fallback.
- Frontend: `features/admin/{api,state,AdminPanel}`; conditional "Administración" nav; two cards; 25 s timeout only for the retry; 401/403/409/422/timeout handling; interval persistence; additive `role` in the session contract.
- PASS: backend Ruff/mypy, 30/30 CU10 tests, 190-test regression set (6 skipped); frontend typecheck, 142/142 tests, lint, build; mocked CU10 Playwright 9/9; real-backend admin flow 1/1 (synthetic QA admin/user); mocked CU01/CU02/CU03 regressions; `openspec validate --all --strict` 15/15.
- Sync/Archive: 12 requirements added (`source-refresh-administration`), 2 modified (`current-outages`/`scheduled-works` cadence only); archived with 32/32 tasks. No commit/push. Pre-existing, not CU10: 6 CU05/CU06 backend environment failures and 1 CU05 history E2E failure reproduced on the pre-CU10 image; CU04/CU09 real specs need external QA state.

## CU05 - CLOSED / ARCHIVED (red-fraction contract resolved 2026-11-13)
- [Archived base change](../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/proposal.md), [archived isolation change](../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/proposal.md), [main spec](../openspec/specs/meter-readings/spec.md) (21 requirements / 44 scenarios), [engineering records](ai-engineering/record-cu05-meter-readings.md) and [isolation record](ai-engineering/isolate-cu05-reading-history-by-meter.md); [resolution](use-cases/decisions.md#cu05-red-fraction-contract-resolution-2026-11-13).
- Contract resolution (documentation-only): OCR may mask clearly separable red fractional digits and suggest only the integer when the boundary is unambiguous, abstains with the exact fallback when it is uncertain, never saves without explicit owner confirmation, and claims no absolute detection guarantee, superseding the absolute prohibition and always-abstain clarification; behavior, limits and tests unchanged. Sync: the base delta created the canonical spec (18/38), the isolation delta appended 3/6 (21/44), and `openspec validate --all --strict` PASS after each step with no requirement, contract or security control dropped.
- Isolation fix (already verified): distinct React keys for `ReadingHistory`/`BillHistory`/`ConsumptionPanel`; `cu05-history.spec.ts` 9/9, red proof 5 failed / 4 passed with keys reverted, typecheck/142 node tests/lint/build PASS. No backend/API/numeric-contract change. Independent 2026-11-13 reviews: `spec-analyst` 1 MAJOR wording finding (corrected) and `reviewer` APPROVED with MINOR/NIT documentation items (corrected); `openspec validate --all --strict` 15/15 PASS after corrections.
- Deferred QA: **QA-INT-CU04-08** — seeded CU04/CU06/CU07/CU08 real Chromium specs not executed; deferred to integral regression. Not PASS.

## CU05/CU06 backend test runtime stabilization - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-13-stabilize-cu05-cu06-backend-test-runtime/proposal.md), [engineering record](ai-engineering/stabilize-cu05-cu06-backend-test-runtime.md). Added `scripts/Test-Cu05Cu06BackendRuntime.ps1`: isolated PostgreSQL role/database, per-run tmpfs CU5/CU6 storage, synthetic CU6 confirmation secret, OCR privacy precondition checks, per-test logs.
- Six historical failures reproduced and classified as environmental: 3x `test_bill_postgres` (missing `CU06_BILL_DIR`/`CU06_CONFIRMATION_SECRET`), 2x OCR (`private_ocr_runtime` fail-closed without cgroup swap=0), 1x reconciliation log count (second warning from `reconcile_bills()` when CU6 config missing). All six now **PASS** with the runner.
- Regression: 32/32 CU06 backend tests OK (1 skipped dedicated reconcile URL), 45/45 CU05 backend tests OK, Ruff/mypy OK, `openspec validate --all --strict` 16/16 PASS.
- Sync/Archive (2026-11-13): archived with 10/10 tasks; no spec deltas. No commit/push.

## Other CUs
- CU08, CU07, CU06, CU04, CU09 and CU05 are implemented, verified and archived.

## Approved stack and existing implementation
- React/TS/Vite/npm and Python/FastAPI/uv/PostgreSQL 18.6 with SQLAlchemy/psycopg/Alembic; pinned images and dependencies. Implemented: CU09 auth/diary, CU04, CU05, CU06, CU07, CU08, CU09, CU01, CU02 and CU03.
- Foundation: Tailwind/local shadcn, memory-only Zustand, RHF/Zod, shared Axios and one functional root assistant mount.

## Blockers and unresolved decisions
- CU03: automated retention deletion remains pending approval (policy documented at 30 days); closure is complete.
- Guide delivered (v1.0.0, 2026-11-10); time-sensitive data still requires periodic revalidation.
- CU05: no contract blocker remains. OCR accuracy on real photos is not claimed; the supplied real photograph abstains and that limitation is accepted.
- **QA-INT-CU04-08** pending: CU04/CU06/CU07/CU08 seeded real Chromium specs deferred by the user to integral regression; not executed and not PASS; risk is the meter-scoped remount of bill/comparison/estimate panels.
- Hosting remains unresolved; Q21/Q22 are resolved for the CU10 scope by U24, while other catalog TBDs remain.

## Next actions
1. Run **QA-INT-CU04-08** seeded CU04/CU06/CU07/CU08 regression when QA state is provisioned; it is the only open CU05-related item.
2. Run the integral CU01–CU10 regression before academic delivery.
3. Await approval before implementing the 30-day automatic retention deletion.
4. Resolve hosting before any deployment.

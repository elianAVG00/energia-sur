# Operational state - energia-sur

Updated: 2026-11-11 (CU03 CLOSED / ARCHIVED; CU01/CU02 archived; CU05 red-fraction block open).

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

## Other CUs
- CU08, CU07, CU06, CU04 and CU09 are implemented, verified and archived; CU05 is implemented with the red-fraction Sync/Archive block.

## Approved stack and existing implementation
- React/TS/Vite/npm and Python/FastAPI/uv/PostgreSQL 18.6 with SQLAlchemy/psycopg/Alembic; pinned images and dependencies. Implemented: CU09 auth/diary, CU04, CU05, CU06, CU07, CU08, CU09, CU01, CU02 and CU03.
- Foundation: Tailwind/local shadcn, memory-only Zustand, RHF/Zod, shared Axios and one functional root assistant mount.

## Blockers and unresolved decisions
- CU03: automated retention deletion remains pending approval (policy documented at 30 days); closure is complete.
- Guide delivered (v1.0.0, 2026-11-10); time-sensitive data still requires periodic revalidation.
- CU05 red-fraction contract conflict still blocks its Sync/Archive.
- Hosting remains unresolved; unrelated catalog TBDs (Q21/Q22 and others) remain.

## Next actions
1. Resolve the CU05 red-fraction conflict before its Sync/Archive.
2. Keep synthetic DEV data and retained artifacts until deletion is explicitly authorized.
3. Await approval before implementing the 30-day automatic retention deletion.

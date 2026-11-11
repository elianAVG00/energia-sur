# CU03 integrated assistant - implementation record

## Goal and specification links

- Change: [implement-integrated-assistant-cu03 (archived)](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/proposal.md)
- [Proposal](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/proposal.md),
  [design](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/design.md),
  [delta: assistant](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/specs/assistant/spec.md),
  [delta: frontend-shell](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/specs/frontend-shell/spec.md),
  [delta: frontend-session-transport](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/specs/frontend-session-transport/spec.md),
  [tasks](../../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/tasks.md),
  [main assistant spec](../../openspec/specs/assistant/spec.md).
- Decisions: [U23](../use-cases/decisions.md#u23---cu03-integrated-assistant-decisions-and-propose-authorization),
  Q06 (PARTIAL), Q07 (CU03 static fallback).
- Operational state: [STATE](../STATE.md).

## Decisions and approvals

- The user approved for CU03: RAG over the delivered Edesur Markdown guide (article-level
  ingestion),
  PostgreSQL 18.6 + pgvector, read-only CU01/CU02 tools, temporary public plus persistent
  authenticated memory, SSE streaming, organism/link citations, static fallback and
  resource limits.
- The user approved `POST /assistant/chat` as public and CSRF-exempt only for that
  endpoint, with server-side Origin validation, and the deferral of an external MCP server
  to CU10.
- At the proposal stage, scope was documentation and OpenSpec artifacts only; apply, code,
  dependency installation, migrations, Docker changes, Sync, Archive, commit and push were
  not authorized then. The BUILD 1-3 sections below record the later, separately authorized
  implementation and its checks.

## Agents, tools and prompts

- Primary: OpenCode (DeepSeek V4.1 Flash) acting as architect in Plan mode, then a
  documentation-only Build.
- Read-only inspection: `AGENTS.md`, `docs/STATE.md`, CU03 fiche, the decision register,
  CU01/CU02 specs, backend modules (`api`, `outages_api`, `scheduled_api`, `models`,
  `security`, `db`), `frontend/src/lib/http.ts`, `ChatMount.tsx`, `AppLayout.tsx`,
  `compose.yaml` and the migration chain.
- Reference: the `Gonzacerbelli/donata-ia` README (fetched read-only) for tool-calling,
  no-write assistant behavior and RAG patterns.
- Subagents: `spec-analyst` (traceability and completeness) and `reviewer` (architecture,
  security and regressions), both read-only, in two rounds.
- OpenSpec CLI: `new change`, `status`, `instructions`, `validate --strict`.

## Problems and correction attempts

- Round 1 (pre-write): the draft requirements missed uncertainty/freshness preservation
  and out-of-scope refusal, risked turning Q06 into a requirement, and left the CSRF/Origin
  and cross-account conversation concerns open. Fixed by adding the requirements, making
  "guide absent" normative, and documenting the Origin policy and account scoping.
- Round 2 (post-write): reviewers found a spec/design contradiction about persisting
  message content, the `frontend-shell` transitional clause, and a missing requirement for
  listing conversations. Fixed by rewording the privacy requirement, adding the
  `frontend-shell` MODIFIED delta, documenting the `frontend-session-transport`
  classification, and adding the owner-listing scenario.
- Scenario-name validation error in the `frontend-shell` MODIFIED block was fixed by
  preserving the existing scenario name.

## Checks and results

- PASS: `openspec validate implement-integrated-assistant-cu03 --strict`.
- PASS: `openspec validate --changes --strict` (4/4).
- PASS: `openspec validate --specs --strict` (10/10).
- PASS: `openspec status --change implement-integrated-assistant-cu03` (4/4 artifacts).
- Proposal stage: BLOCKED / NOT RUN — no code, tests, migrations, Docker or runtime checks
  were executed then; they were not authorized at that stage. Superseded by the BUILD 1-3
  sections below.

## Limitations and pending decisions

- The Edesur guide is delivered (v1.0.0, 2026-11-10); its content is not modified.
- The `pgvector/pgvector` image digest, PostgreSQL minor parity and application-role
  privilege are Apply-time verification items.
- The embedding model/dimension (proposed `text-embedding-3-small`, 1536) needs
  confirmation before the migration is fixed.
- The exact Spanish fallback/refusal wording is a review presentation detail.
- An external MCP server is deferred to CU10; CU03 exposes internal read tools only.
- The approved `MODIFIED` `frontend-session-transport` delta is included in this change
  (public chat is an Origin-validated streaming exception; authenticated operations keep
  CSRF).

## Guide delivery and Docker inspection (2026-11-10)

- The user supplied `backend/knowledge/guia-oficial-edesur.md` (frontmatter
  `document_id: energia-sur-kb-edesur-001`, `version: 1.0.0`,
  `last_verified_at: 2026-11-10`): 9 content sections and 53 `### <ID> —` article units
  (CA/PA/CO/TS/EL/EE/CR/TR/LI) plus a source index. The guide content was not modified.
- Ingestion design: parse frontmatter, split at article IDs, one complete chunk per
  article, metadata `document_id`, `version`, `last_verified_at`, `section`, `article_id`,
  `source_name`, `source_urls`; exclude frontmatter, intro and section 10; idempotent
  upsert by `(document_id, article_id, version)` with `content_sha256` and active-version
  replacement.
- Static Docker inspection (not executed): `backend/.dockerignore` starts with `**` and whitelists only
  `app/`, `tests/`, `alembic.ini`, `migrations/`, `pyproject.toml`, `uv.lock` and
  `.python-version`; `backend/Dockerfile` copies neither `knowledge/` nor any Markdown.
  The guide is therefore absent from the `verification` and `runtime` images. Required at
  Apply: add `!knowledge/` plus `!knowledge/*.md` to `.dockerignore` and
  `COPY knowledge ./knowledge` in both stages. This is a BUILD 1 prerequisite until applied.
- No code, Docker or migration changes were made in this PROPOSE stage.

## Review round 3 - guide ingestion verification

- `spec-analyst` and `reviewer` confirmed the mixed provenance, incomplete/volatile signal,
  monotonic version guard, four guide/memory tables, LI-01 exemption, anti-mixing rule and
  Docker omission are addressed.
- Remaining documentation gaps were fixed: a deterministic volatility keyword map with a
  fail-safe `revalidate` default; hash scope plus revalidation semantics; per-chunk
  `last_verified_at`; `parser_version` and embedding columns; a static citation allowlist
  including ENRE; a plain-text rendering requirement; LI-01 moved from Open Questions to a
  requirement; and a single `.dockerignore` form (`!knowledge/` + `!knowledge/*.md`).
- BUILD 1 documentation is ready for authorization; remaining items are Apply-time
  decisions (staleness threshold, embedding model/dimension, pgvector extension role,
  force-flag governance, retention/transparency) rather than design blockers.

## BUILD 1 implementation (2026-11-10)

- Delivered backend scope: guide parser (53 article units, metadata, fail-closed), pgvector
  ingestion (`guide_parser`, `guide_store`, `ingest_guide` CLI), LangChain/OpenAI RAG
  (`assistant`), public SSE endpoint (`assistant_api`), limits/config
  (`assistant_limits`), migration `0007_cu03`, Docker `knowledge/` inclusion and
  `compose.yaml` pgvector image.
- Model selection: `gpt-4o-mini` (economical, available and LangChain-compatible) as the
  default `OPENAI_MODEL`; embeddings `text-embedding-3-small` with 1536 dimensions.
  Both are server-side environment settings; no key is stored in the repository.
- pgvector: `pgvector/pgvector:pg18` pinned by digest
  (`sha256:c29f30688a9ad961691bdf0ec1650717cc132a5814619d80f80463d6e4c42e47`), PostgreSQL
  18.6, extension 0.8.7. Migration `0007_cu03` was upgraded and downgraded on an isolated
  test database; four additive tables were created.
- Files added: `app/guide_parser.py`, `app/guide_store.py`, `app/assistant.py`,
  `app/assistant_limits.py`, `app/assistant_api.py`, `app/ingest_guide.py`,
  `migrations/versions/0007_cu03.py`, `tests/test_cu03_*.py`. Modified: `app/models.py`,
  `app/main.py`, `pyproject.toml`, `uv.lock`, `Dockerfile`, `.dockerignore`, `compose.yaml`.
- Checks (PASS): Ruff; mypy (47 files); 29 CU03 tests (offline with fake embeddings/LLM
  plus a real PostgreSQL/pgvector integration); 81 CU01/CU02 regression tests (6 skipped
  live); 7 health/security tests; migration upgrade/downgrade; `docker compose config
  --quiet`; both Docker stages contain `/app/knowledge/guia-oficial-edesur.md`;
  `openspec validate --strict`.
- Pending: the single real OpenAI query was not run because `OPENAI_API_KEY` is not
  configured; the CU01/CU02 read tools, frontend runtime and conversation memory remain
  BUILD 2/3. No commit, push, Sync or Archive was performed; the guide content was not
  modified.
- Correction during BUILD 1: the chunk insert initially violated the document FK because
  the document was created after the chunks; the upsert now creates/flushes the document
  first. The parser also rejected a fabricated `ZZ-01` prefix and the plural "sujetos a
  cambio" volatility wording was corrected.

## BUILD 1 independent review and corrections (2026-11-10)

- `reviewer` audited the implementation read-only and found: no relevance threshold
  (out-of-scope refusal unreachable), missing host-boundary citation allowlist, hash not
  covering version/metadata/parser/embedding model, incomplete body/timeout limits,
  sources reported for all retrieved articles, destructive downgrade, missing Compose
  forwarding, and test-evidence gaps.
- Corrections applied: `ASSISTANT_MAX_DISTANCE` filtering (off-topic queries return the
  refusal); exact-or-dot-boundary `ALLOWED_HOSTS` used at parse and before emitting
  sources; metadata/parser-aware content hash plus embedding-model change detection and
  older-date no-op; body-size middleware plus a total stream timeout; top-1 source
  citation; downgrade guard that refuses to drop assistant conversations with data;
  Compose forwarding of `OPENAI_*`/`ASSISTANT_*` with empty/default values; and tests for
  body limit, timeout, allowlist, off-topic refusal, SSE headers, `ok:false`, metadata
  correction and non-official source filtering.
- Residuals: anti-mixing is enforced by the system prompt (no per-token deterministic
  guard); a concurrency semaphore is deferred to BUILD 2; `Test-DatabasePersistence.ps1`
  remains unrun (no `.env`/Compose password); the real OpenAI query is pending (no key).
- Re-checked after corrections: Ruff, mypy, 29 CU03 tests, 81 CU01/CU02 regressions,
  compose config and OpenSpec strict all pass.

## BUILD 2 implementation (2026-11-10)

- Backend: extracted pure freshness/state/limitation helpers into `app/public_reads.py`
  and delegated the CU01/CU02 routers to them (byte-compatible; 81 regressions pass).
  Added `app/assistant_tools.py` with read-only `lookup_current_outages` /
  `lookup_scheduled_works`, LangChain `@tool` wrappers, a deterministic zone resolver
  and a RAG/current/scheduled planner. `assistant.py` now renders a `CONTEXTO DINÁMICO`
  block with provenance/freshness/coverage and the U22 limitations. `assistant_api.py`
  adds `optional_actor`, a concurrency slot, `tool` events and merged official sources;
  the body cap is a pure ASGI middleware so `/health` keeps its exact two-message contract.
- Frontend: `features/assistant/api.ts` (fetch + ReadableStream SSE parser for
  `conversation`/`delta`/`tool`/`sources`/`error`/`done`, partial frames, HTTPS-only
  sources, no retry), `state.ts` (memory-only Zustand conversation with a
  `getRandomValues` fallback) and `AssistantPanel.tsx` (progressive render, loading,
  cancel, safe source links, accessible log). `ChatMount.tsx` keeps the single root mount.
- Tests: 40 backend CU03 tests (parser, assistant, API, PostgreSQL/pgvector, tools and
  routing), 128 frontend tests, 81 CU01/CU02 + 7 health/security regressions (6 skipped
  live), Ruff/mypy, frontend typecheck/build/lint, and one Playwright `e2e/cu03.spec.ts`
  pass with a mocked SSE response. The E2E verified the answer text and the official
  source link; no image element was rendered inside the panel.
- Incident/correction: the Vite dev server rejected the container hostname, so the E2E
  used the container IP; `crypto.randomUUID` is unavailable on insecure non-localhost
  origins, so identifier generation now falls back to `crypto.getRandomValues`.
- Pending: BUILD 3 (persistent authenticated memory), the real OpenAI query (no key) and
  `Test-DatabasePersistence.ps1` (2.1). No Sync, Archive, commit or push.

## BUILD 2 independent review and corrections (2026-11-10)

- `reviewer` audited BUILD 2 read-only. Blockers/majors found: `Content-Length`-only body
  cap (chunked bypass), citations for all retrieved articles instead of the used one,
  missing first-byte timeout, duplicated Origin policy, dynamic-dynamic mixed routing, and
  smaller client/test/doc gaps.
- Corrections: the ASGI body cap now buffers the body up to the limit and replays it, so a
  chunked request without `Content-Length` still gets a controlled 413; the context and
  `sources` use only the best retrieved article; `ASSISTANT_FIRST_BYTE_TIMEOUT` wraps the
  first token; `origin` lives in `security.py` and is shared by `api.py`/`assistant_api.py`;
  the planner sets both dynamic flags for mixed outage/works questions; the client checks
  the official host allowlist, finishes a truncated stream and no longer duplicates the
  fallback; ingest/retrieval pin `GUIDE_DOCUMENT_ID`; tests restore their monkeypatches and
  cover chunked bodies, best-article citations, mixed routing and the host allowlist.
- Re-checked after corrections: 40 CU03 backend tests, 88 CU01/CU02/health/security
  regressions, 128 frontend tests, Ruff/mypy, frontend typecheck/build/lint, the Playwright
  chatbot flow and `openspec validate --strict` all pass.
- Residuals: `Test-DatabasePersistence.ps1` (2.1), the real OpenAI query (no key), and
  BUILD 3 persistent memory. Anti-mixing remains prompt-level; the relevance threshold is
  validated with a deterministic test embedder, not real embeddings.

## BUILD 3 implementation (2026-11-10)

- Persistence: `app/assistant_memory.py` stores owner-scoped conversations/messages in the
  existing `es_assistant_conversations`/`es_assistant_messages` tables. `resolve_conversation`
  never attaches a foreign id (it creates a new owned conversation); `append_message`,
  `load_history`, `list_conversations`, `get_messages` and `delete_conversation` all filter
  by `account_id`. Chat turns are persisted for authenticated users only; visitors remain
  temporary and are never written to PostgreSQL.
- API: `GET /assistant/conversations`, `GET /assistant/conversations/{id}/messages` and
  `DELETE /assistant/conversations/{id}` (the last one uses `Writer`, i.e. Origin + CSRF).
  The public chat keeps its Origin/rate-limit/body/timeout/concurrency controls and returns
  `scope: persistent` plus the owned conversation id for authenticated users.
- Context: bounded history (`ASSISTANT_HISTORY_MAX_MESSAGES` 10, `ASSISTANT_HISTORY_MAX_CHARS`
  4000) is injected into the LangChain prompt as context only; the system prompt forbids
  using it as evidence of a current outage. The history query is owner- and
  conversation-scoped.
- Frontend: `conversationId`/`scope` in the Zustand store, a configurable visitor TTL
  (`VITE_ASSISTANT_TTL_MINUTES`, default 30), reset on session-generation change, abort of
  in-flight streams on logout/account change, a visible OpenAI privacy notice and a
  `Limpiar` action that deletes the persistent conversation through the shared CSRF client.
- Privacy/retention: `ASSISTANT_RETENTION_DAYS` documents a proposed 30-day policy; messages
  remain until the owner deletes them and automatic deletion is not executed because it
  needs explicit approval. No keys, tokens, prompts or full conversations are logged (only
  error class names).
- Tests: 54 CU03 backend tests (parser, assistant, API, PostgreSQL/pgvector, tools/routing,
  memory/isolation/CSRF/context), 134 frontend tests, 81 CU01/CU02 + 7 health/security
  regressions, and 3 Playwright flows (visitor, authenticated/logout and failed-delete). Ruff/mypy,
  frontend typecheck/build/lint, migration upgrade/downgrade, PostgreSQL 18.6/pgvector 0.8.7
  and `openspec validate --strict` pass.
- Pending: any automated retention deletion (approval pending). No Sync, Archive, commit
  or push.

## BUILD 3 independent review and corrections (2026-11-10)

- The first BUILD 3 review found: the `frontend-session-transport` delta missing (H1),
  visitor temporary memory relying only on the client (M1), blocking DB I/O in the async
  SSE generator (M2), evidence gaps (M3), retention/notice wording (L4), cancellation
  presentation (L5), late `conversation` events (L6), empty conversations (L7), missing
  config docs (L8) and stale README/foundation/tasks text (L2/L3).
- Corrections: added the approved `MODIFIED` `frontend-session-transport` delta and
  reconciled the proposal/design/tasks; the frontend now sends bounded Zustand history for
  anonymous turns (backend uses DB history only for authenticated turns and ignores client
  history on resolution failure); all memory calls run in `run_in_threadpool`; the visitor
  cap keeps the newest turns; tests cover anonymous no-persistence, two-turn continuity,
  history forwarding, slot release and authenticated logout; the notice mentions
  authenticated storage and retention is worded as a proposal; cancellation shows
  "Respuesta interrumpida"; the event callback drops late generations; empty conversations
  are hidden; compose/design document the new variables; README and the foundation guide
  reflect BUILD 3.
- Second review confirmed the fixes and flagged only medium/low residuals: a failed DELETE
  now keeps the panel and shows an error instead of silently claiming deletion; the BUILD 3
  authorization is the recorded human approval for the `MODIFIED`
  `frontend-session-transport` delta (no additional approval pending);
  `VITE_ASSISTANT_TTL_MINUTES` is a build-time setting; no test covers the generation guard
  directly (the E2E logout covers the reset).
- Final review found H-1: a cancelled turn or an HTTP failure left an empty assistant
  message and a long answer exceeded 2000 characters, so the next client history payload
  could fail Pydantic validation with 422. Fixed with `priorHistory` (drops empty turns and
  truncates to 2000 characters), a server-side empty-entry skip, and regression tests; a
  failed-DELETE E2E and an empty-conversation test were added.
- Accepted limitation: conversation listing/restoration is API-only; BUILD 3 has no UI list
  (the API provides owner-scoped list/messages, so no approved UI requirement is
  contradicted).
- Pending: automated retention deletion (approval pending). No Sync, Archive, commit or
  push.

## H-1 correction verification (2026-11-10)

- The final review's H-1 was fixed in the client (`priorHistory` drops empty turns and
  enforces a 4000-character total budget, matching `ASSISTANT_HISTORY_MAX_CHARS`) and in
  the server (`HistoryMessage.content` accepts empty strings; `_client_history` skips
  them). A follow-up review then found that 10 x 2000 characters could still exceed the
  16384-byte request cap and yield a 413; the 4000-character budget closes that path.
- New regression tests: `priorHistory` budget plus a serialized-body assertion under the
  body cap, an empty history turn, empty conversations hidden, and a failed-DELETE E2E.
- Re-run after the change (PASS): frontend typecheck; **134** frontend tests; Oxlint
  0 warnings/0 errors; `npm run build`; 3/3 Playwright flows; backend **54** CU03 tests;
  Ruff; mypy (50 files); `openspec validate implement-integrated-assistant-cu03 --strict`.
- Remaining low residuals accepted: no component-level test of the `AssistantPanel`
  payload wiring; no automated test for the DELETE 404 reset branch; a configured
  `ASSISTANT_HISTORY_MAX_MESSAGES` above 10 does not extend the anonymous client bound;
  the client budget counts UTF-16 units, not encoded bytes, so `ASSISTANT_MAX_BODY_BYTES`
  must stay above ~12 KB (the default 16384 does).
- Follow-up review confirmed the correction and found no remaining code, security,
  isolation or contract blocker; code/specs are READY FOR ARCHIVE. The real OpenAI query
  was completed on 2026-11-11 (see below).

## Environment recovery and task 2.1 (2026-11-10)

- Recovered the existing PostgreSQL configuration instead of creating a database: Compose
  project `energia-sur` with `compose.yaml` + `compose.cu09.yaml`, container
  `energia-sur-db-1`, volume `energia-sur_pgdata`, network `energia-sur_default`, driver
  `pgvector/pgvector:pg18` pinned by digest. `POSTGRES_PASSWORD` was read from the running
  db container into the process environment and never printed; `DATABASE_URL` came from
  the running backend container.
- Finding: the backend container was still pointing at `cu08_app_602f0b6f01d6`, a synthetic
  CU08 acceptance database, and the `energia_sur` database only had the persistence marker
  table. The app connection was repointed to the existing `energia_sur` database/role
  (superuser provisioned by Compose) via `CU09_DATABASE_URL`; no database or role was
  created and no data was deleted.
- `docker compose -f compose.yaml -f compose.cu09.yaml config --quiet` PASS with the
  recovered variable. The backend image was rebuilt from the current CU03 source (the
  running container predated CU03 and lacked `pgvector` and `/app/knowledge`).
- Task 2.1 PASS: `pwsh -NoProfile -File scripts/Test-DatabasePersistence.ps1` recreated the
  db container, marker `35fc388e-7897-4c7a-8b57-896cedc226c5` survived, container id
  changed from `c0e90b6b19fe...` to `70642360494d...`, and volume `energia-sur_pgdata` was
  preserved. No volume removal or seed rerun.
- PostgreSQL 18.6, pgvector 0.8.7 installed by `0007_cu03`; `alembic upgrade head` PASS
  (`0007_cu03 (head)`), 19 `es_*` tables present. The backend container can read
  `/app/knowledge/guia-oficial-edesur.md`; SHA-256 still
  `DDDD22CAECD4B8BC29EF5E69E0EAEAAC1B6CB78166AC5A5995D0455B24A4E8AF`.
- Smoke check without a key (explicitly a fallback, not an OpenAI answer): the public
  endpoint returned `text/event-stream` through both `127.0.0.1:8000` and the Vite proxy,
  emitting `provider_unavailable`, the static fallback, empty sources and `done ok:false`;
  a request without `Origin` returned 403.
- `.env.example` now documents `OPENAI_API_KEY`, `OPENAI_MODEL`,
  `OPENAI_EMBEDDING_MODEL` and a commented `CU09_DATABASE_URL` placeholder. No key was
  written; `.env` remains absent and Git-ignored.
- Completed on 2026-11-11: the user placed `OPENAI_API_KEY` in the root ignored `.env`;
  ingestion, retrieval and generation then passed (next section).

## Real OpenAI verification (2026-11-11)

- Configuration: `.env` exists at the repository root and is Git-ignored
  (`.gitignore:18`); it contains `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`,
  `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL` and `CU09_DATABASE_URL`
  (names only checked; no values printed). `docker compose config --quiet` PASS; only the
  backend was recreated to load the variables. It connects to `energia_sur` (not a
  synthetic database) as role `energia_sur`.
- PostgreSQL 18.6, pgvector 0.8.7 and Alembic `0007_cu03` re-verified after the restart.
  `/app/knowledge/guia-oficial-edesur.md` is readable in the container; SHA-256 unchanged
  (`DDDD22CA…E8AF`).
- Ingestion: `python -m app.ingest_guide` printed
  `indexed: energia-sur-kb-edesur-001 1.0.0 (53 articles)`. Database checks: 1 document,
  **53 chunks**, **53 active**, **53 distinct article IDs**, all with non-null embeddings,
  `min(vector_dims) = max(vector_dims) = 1536`, model `text-embedding-3-small`, parser
  `cu03-guide-parser-1`, metadata and per-article official URLs present. The uniqueness
  constraints and the partial unique active-article index remain in place, so the 53 rows
  are not duplicated.
- Retrieval: the real question "¿Cómo puedo pagar una factura vencida de Edesur?" returned
  **PA-02** ("¿Puedo pagar una factura vencida o una deuda anterior?") as the top article,
  followed by PA-01, PA-07 and PA-06. PA-02's official sources are
  `https://www.edesur.com.ar/servicios-al-cliente/opciones-de-pago/` and
  `https://www.edesur.com.ar/hogares/conoce-tu-factura/`.
- SSE generation: HTTP 200 `text/event-stream` with `conversation`, incremental `delta`
  tokens, a `sources` event carrying those two HTTPS `edesur.com.ar` URLs and
  `done {"ok": true}`. The answer described paying through the Oficina Virtual and the
  second-vencimiento/plan-de-pagos options; it was a generated answer, not the static
  fallback (`provider_unavailable` did not appear).
- Frontend: a temporary real-backend Playwright flow (no API mocks) opened the panel,
  submitted the question, received the generated answer and found the official link. The
  frontend container IP origin was added to `APP_ORIGINS` only for that run and reverted;
  the temporary spec was deleted. The existing 3 mocked flows are unchanged.
- Cost: one ingestion batch (53 articles) plus a few short embedding/generation calls,
  well within the USD 0.05 cap. No automatic retries were made.
- Gates re-run: Ruff PASS; mypy PASS (50 files); 54 CU03 backend tests PASS; 88
  CU01/CU02/health/security regressions PASS (6 skipped live); 134 frontend tests PASS;
  typecheck, Oxlint 0/0 and build PASS; `openspec validate --strict` PASS; 31/31 tasks.
- Secrets: no `sk-...`-like value in tracked files or backend logs; `.env` is not tracked.
  The guide Markdown was not modified.

## Sync and Archive (2026-11-11)

- The user authorized formal closure after the real OpenAI verification. Sync and archive
  ran with the installed OpenSpec CLI (`openspec archive implement-integrated-assistant-cu03
  --yes --json`), after a backup of `openspec/`.
- Specs synced: created `openspec/specs/assistant/spec.md` from the delta Purpose and all
  **17** ADDED requirements; modified the existing `frontend-session-transport` "Central
  cookie and CSRF request policy" (public-chat exception plus its scenario) and
  `frontend-shell` "Single deferred floating-chat mount" (functional mount plus the updated
  unavailable/fallback scenario). CLI totals: 17 added, 2 modified, 0 removed, 0 renamed.
- `openspec validate --strict` initially failed on the modified session-transport
  description exceeding 500 characters. The main-spec description was tightened without
  changing behavior or any scenario; final `openspec validate --all --strict` passed
  **14/14** (10 main specs + 3 active changes).
- Archived as `openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03`;
  the active change directory is gone and its 31/31 tasks remain in the archive. No
  contracts of other use cases were modified.
- Accepted limitations recorded without presenting them as implemented: authenticated
  history is API-only (no listing/restoration UI); the 30-day retention policy is proposed
  and automatic deletion is not approved; the answer body renders as plain text and
  official HTTPS sources are shown separately.
- Closing commit: `feat(cu03): implement RAG-powered assistant with OpenAI and pgvector`;
  no push.

## Redacted evidence

- No secrets, provider keys, real bills, photos or personal addresses were read or stored.
- The reference repository was inspected read-only; no code or content was copied.

# Tasks

Status: BUILD 1, BUILD 2 and BUILD 3 implemented and verified; all 31 tasks are complete.
Task 2.1 passed against the existing `energia-sur` Compose database, and the single real
OpenAI query passed on 2026-11-11 (53 articles indexed, PA-02 retrieved, official sources).
Checked tasks have recorded evidence in the engineering record.
No Sync, Archive, commit or push has been performed.

## 1. Approval and preconditions (gates)

- [x] 1.1 Obtain explicit human REVIEW approval to APPLY this plan and record the approval evidence in `docs/ai-engineering/implement-integrated-assistant-cu03.md`. Verify: the record cites the approval and the change remains unapplied before it.
- [x] 1.2 Confirm the delivered guide `backend/knowledge/guia-oficial-edesur.md` (document_id `energia-sur-kb-edesur-001`, version `1.0.0`, last_verified_at `2026-11-10`) is the approved source and that its content is not modified; verify the design references the delivered metadata and proposes no content change.
- [x] 1.3 Confirm the server-side OpenAI key plan (env only, no default) and that its absence degrades to the static fallback without failing startup. Verify: documented in design, no key value stored in repository files.

## 2. Infrastructure and persistence

- [x] 2.1 Replace the `db` image with a digest-pinned `pgvector/pgvector:<version>-pg18` and verify `docker compose config --quiet` plus `pwsh -File scripts/Test-DatabasePersistence.ps1` still pass with `pgdata` preserved.
- [x] 2.2 Add pinned `langchain`, `langchain-core`, `langchain-openai` and `pgvector` dependencies (no `langchain-postgres`) and update `uv.lock`; verify the locked container install succeeds and `uv sync --locked` rejects drift.
- [x] 2.3 Add additive migration `0007_cu03` (`CREATE EXTENSION IF NOT EXISTS vector` then `es_guide_documents`, `es_guide_chunks`, `es_assistant_conversations`, `es_assistant_messages`) with the `conversation_id` index, the partial unique active-article index and an `embedding` index/scan decision; verify `alembic upgrade head` on an isolated `TEST_DATABASE_URL`, the `vector` extension is present, and existing data is preserved.
- [x] 2.4 Add configuration handling for `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL` and `ASSISTANT_*` limits; verify a missing key yields the unavailable/fallback path and no crash, with a unit test.
- [x] 2.5 Verify the single `DATABASE_URL` role owns the database or has `CREATE`, create the extension once via Alembic, and record the resolved image digest and pgvector version; verify `SELECT extname FROM pg_extension WHERE extname='vector'` and that no superuser is required. A separate migration role is not in scope.
- [x] 2.6 Whitelist `knowledge/` in `backend/.dockerignore` and add `COPY knowledge ./knowledge` to the `verification` and `runtime` stages; verify both images contain `/app/knowledge/guia-oficial-edesur.md` and the runtime user can read it.

## 3. Backend read tools and shared reads

- [x] 3.1 Extract the pure freshness/state/limitation helpers into a shared read module used by the existing CU01/CU02 routers and the tools; verify the existing CU01/CU02 regression tests pass byte-compatibly.
- [x] 3.2 Implement `assistant_tools.py` read-only tools over `outage_store`/`scheduled_store` snapshots with `load_catalog`, `normalized_key` and `latest_source_status`, with no router import and no ENRE/GeoRef call; verify parity tests for states, coverage and limitations.
- [x] 3.3 Implement the guide parser (frontmatter parsed only up to the second `---`, `## N.` sections and `### <ID> —` articles) producing LangChain Documents with `document_id`, `version`, `last_verified_at`, `section`, `article_id`, `title`, `content`, `content_sha256`, `chunk_index`, `source_name`, per-URL `source_urls`, `limitations`, `information_type`, `volatility` (documented keyword map, fail-safe `revalidate`), `source_type` and the paraphrase disclaimer; fail closed on missing metadata, article count ≠ 53, missing sections 1–9, or duplicate/malformed IDs; verify no frontmatter or section-10 chunks.
- [x] 3.4 Implement idempotent upsert and controlled version replacement in `guide_store.py` (`es_guide_documents`/`es_guide_chunks`; hash of content + version + `last_verified_at` + `parser_version` + canonical metadata; equal hash accepts a newer `last_verified_at` in place; different hash requires a strictly newer numeric version; operator-only logged force; hash-skip before deactivation; distinct `pg_advisory_xact_lock` key; `is_active`; partial unique active-article index); verify re-ingest produces no duplicates, v1.0.1 supersedes v1.0.0, re-ingesting v1.0.0 after v1.0.1 is a no-op with exit 0, and a failing startup ingest keeps the last good index without aborting startup.
- [x] 3.5 Implement retrieval filtered to the active current version, returning `article_id` with per-URL `source_name`/`source_urls` and `https`-only citations from the static official allowlist (including ENRE); verify one representative retrieval test per section (CA/PA/CO/TS/EL/EE/CR/TR/LI) asserting the expected article ID and official URL, plus a mixed-organism article (TS-01 or CR-08), the LI-01 empty-source exemption, an ambiguity test that two articles are not blended, and a prompt-structure test that section 10 is absent and chunk content is delimited.
- [x] 3.6 Implement staleness, volatility and incomplete-article disclosure plus RAG-versus-dynamic routing, including `Importante`/`Aclaración` markers and the `source_type` paraphrase disclaimer; verify current-state questions use CU01/CU02, procedure questions use the guide, mixed questions label both, and PA-07/TR-03/TR-04/CO-01 report the limitation without invention; verify no URL is fetched during ingestion.

## 4. Assistant chain, guardrails and fallback

- [x] 4.1 Implement the LangChain + OpenAI chain, system prompt and guardrails that use only read tools and RAG, route current-state versus procedure questions, treat guide/tool results as untrusted data, and never invent facts; verify with a deterministic fake LLM plus a prompt-structure test that adversarial chunk text is not promoted to system instructions.
- [x] 4.2 Implement the identifiable static fallback and out-of-scope refusal paths; verify tests for provider error, tool error, rate limit, empty index and unsupported question.
- [x] 4.3 Implement limits in `assistant_limits.py` (per-client rate limit with pruning, first-byte and total timeouts, message length, token/context/output caps); verify 429 + `Retry-After`, overlong rejection before provider call, and timeout behavior.

## 5. SSE transport, memory and auth policy

- [x] 5.1 Implement `optional_actor` (missing/invalid/expired cookie → anonymous) and `POST /assistant/chat` as `text/event-stream` with Origin validation before the limiter/provider, a request-body cap, bounded concurrency, `Cache-Control: no-store` and terminal `error` events; verify SSE contract tests.
- [x] 5.2 Implement temporary in-memory memory (bounded, TTL) and persistent account-scoped memory plus owner-scoped `GET`/`DELETE /assistant/conversations`, with server-generated IDs and unknown/foreign IDs yielding a fresh conversation or 404 without loading other-account data; verify account isolation and that anonymous conversations are not durably persisted.
- [x] 5.3 Implement the CSRF-exempt public chat endpoint with Origin check and abuse protection, and record the approved `MODIFIED` `frontend-session-transport` delta for the public-chat exception; verify authenticated unsafe operations still require CSRF and trusted Origin.

## 6. Frontend runtime

- [x] 6.1 Implement the streaming client (`fetch` + `ReadableStream`) reusing `apiPath` and the session store, with credentials, generation guard, cancellation, no auto-retry and `https`-only citation handling; verify parser/guard tests.
- [x] 6.2 Implement the assistant panel inside `ChatMount.tsx` (incremental render, answer body as plain text with no Markdown/HTML, source citations rendered as text/links with an official-host allowlist and never raw HTML, fallback/refusal, accessible labels/`aria-live`); verify component tests and exactly one root mount.
- [x] 6.3 Verify `npm run typecheck`, `npm run build`, `npm test` and `npm run lint` pass and existing frontend tests are unaffected.

## 7. Integration verification and independent review

- [x] 7.1 Run the backend gates (unit tests, per-section retrieval suite, mixed-organism provenance, version-resurrection no-op, incomplete/volatile disclosure, anti-mixing and prompt-injection structure, migration/pgvector tests, `ruff check`, `mypy`) including a test that logs and terminal `error` events contain no message content or keys, and record PASS/FAIL/BLOCKED with commands and evidence.
- [x] 7.2 Run the frontend gates (tests, typecheck, build, lint) and record results.
- [x] 7.3 Run a Playwright flow against a mocked SSE stream and record the result; the real-model run was executed on 2026-11-11 with an approved key (PA-02 retrieved, official sources, SSE `done ok:true`).
- [x] 7.4 Run `openspec validate --strict` and `openspec status --change implement-integrated-assistant-cu03` and record the output.
- [x] 7.5 Obtain an independent reviewer audit of architecture, isolation and security; record findings, severities and resolution (no fixes by the reviewer).
- [x] 7.6 Update `docs/ai-engineering/implement-integrated-assistant-cu03.md` and `docs/STATE.md` with actual results, limitations and next actions; verify the links resolve.
- [x] 7.7 Update `README.md` and `docs/frontend-foundation.md` for the assistant runtime, the CSRF-free public chat POST and the streaming client; verify the documented commands still hold.

## Workflow follow-up

- Sync the delta spec to `openspec/specs/assistant/spec.md` and archive the change only after human approval and all applicable gates pass (not authorized at proposal stage).
- Commit and push only with explicit authorization; none is granted by this proposal.

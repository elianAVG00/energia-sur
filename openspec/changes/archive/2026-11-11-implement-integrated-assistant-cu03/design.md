# Design

## Context

See `proposal.md` for motivation. Current constraints that shape the approach:

- CU01/CU02 already expose public, snapshot-based reads with provenance, freshness and
  three-valued coverage (`outage_store.current_snapshot`, `scheduled_store.current_snapshot`,
  `load_catalog`, `normalized_key`, `latest_source_status`). Their routers hold the pure
  freshness/state/limitation logic but call no external provider at query time.
- The backend uses lazy PostgreSQL engines (`db.py`), SQLAlchemy models and an additive
  Alembic chain `0001_cu09`…`0006_cu02`; no ORM table is auto-created.
- Sessions/CSRF/Origin live in `api.py` (`current`, `origin`, `mutation`); the frontend
  transport (`http.ts`) centralizes same-origin validation, the public-POST allowlist,
  CSRF attachment, cancellation and the 401/generation guard.
- `ChatMount.tsx` is the single root-layout mount; `frontend-shell` requires exactly one,
  and `frontend-session-transport` requires cancellation and stale-401 protection.
- Compose runs PostgreSQL 18.6 pinned by digest with the `pgdata` volume mounted at
  `/var/lib/postgresql`. Development MCP servers are distinct from runtime chat tools.
- The approved Edesur guide is now delivered at `backend/knowledge/guia-oficial-edesur.md`
  (frontmatter `document_id: energia-sur-kb-edesur-001`, `version: 1.0.0`,
  `last_verified_at: 2026-11-10`): 9 content sections and 53 `### <ID> — question` article
  units (CA/PA/CO/TS/EL/EE/CR/TR/LI) plus a source index. The backend image currently
  excludes `knowledge/` (`.dockerignore` ignores everything and the Dockerfile does not
  copy it), so image inclusion is a BUILD 1 prerequisite.

No assistant runtime exists yet.

## Goals / Non-Goals

**Goals:**

- A public, grounded assistant over official sources with read-only CU01/CU02 tools and
  RAG over the delivered Edesur guide at article granularity.
- Streaming SSE, separated temporary/persistent memory, static fallback/refusal, and
  bounded resource use.
- Additive persistence and infrastructure; no behavioral change to CU01/CU02/CU09.
- Keep exactly one chat mount and preserve the existing session/CSRF policy for
  authenticated operations.

**Non-Goals:**

- Writes, complaint submission, private CU04-CU09 access, account administration.
- Runtime MCP tools or exposure of development MCP servers.
- Editing the Edesur guide content, sources or links; only ingest it as delivered.
- Planning CU02 dates/reasons/distances (U22) or CU01 per-address supply status.
- Hosting decisions or multi-instance memory/rate-limit design.

## Decisions

### D1 — Module boundaries

- `assistant_api.py`: SSE transport, optional auth, Origin check, rate limit.
- `assistant.py`: chain assembly, system prompt, guardrails, fallback/refusal copy.
- `assistant_tools.py`: read-only tools over CU01/CU02.
- `guide_store.py`: pgvector ingest and retrieval.
- `assistant_memory.py`: persistent owner-scoped conversations and bounded history.
- `assistant_limits.py`: limit constants and env resolution.

Rationale: mirrors the existing focused-module style (`outages_api`, `scheduled_api`,
`bill_store`) and keeps transport, business rules and external I/O separate.
Alternative: a single `assistant.py` — rejected (mixes transport, policy and I/O).

### D2 — Read tools over stores, never HTTP or GeoRef

Tools call `outage_store`/`scheduled_store` snapshot reads plus `load_catalog`,
`normalized_key` and `latest_source_status`. They never import the FastAPI routers and
never call ENRE or GeoRef. To avoid duplicating state rules, the pure
freshness/state/limitation helpers are extracted into a shared read module used by both
the existing routers and the tools; existing responses must stay byte-compatible
(regression tests). Alternative: internal HTTP to the public endpoints — rejected
(SSRF/coupling, session overhead). Alternative: copy the logic — rejected (divergence).

### D3 — Additive data model (`0007_cu03`)

- `CREATE EXTENSION IF NOT EXISTS vector` first.
- `es_guide_documents`: `document_id` (text PK), `current_version` (text),
  `last_verified_at` (date), `indexed_at` (timestamptz), `source_name` (text, document
  label such as "Edesur / Argentina.gob.ar"), `source_type` (text), `embedding_model`
  (text), `embedding_dimension` (int), `parser_version` (text).
- `es_guide_chunks`: `id` (String(36), matching the codebase), `document_id` FK,
  `version` (text), `last_verified_at` (date, denormalized for the staleness check),
  `section` (text), `article_id` (text, validated against
  `^(CA|PA|CO|TS|EL|EE|CR|TR|LI)-\d{2}$`), `title` (text), `content` (text),
  `content_sha256` (text), `source_name` (text, primary label), `source_urls`
  (JSON array of `{source_name, url}` so each link keeps its organism), `limitations`
  (JSON array), `information_type` (text), `volatility` (text: `stable|variable|revalidate`),
  `source_type` (text), `chunk_index` (int), `embedding vector(N)`, `is_active` (bool),
  `created_at` (timestamptz); unique `(document_id, article_id, version)` and a partial
  unique index `(document_id, article_id) WHERE is_active`.
- `es_assistant_conversations`: `id` (UUID), `account_id` FK `es_accounts.id` (indexed,
  NOT NULL), `created_at`, `updated_at`.
- `es_assistant_messages`: `id`, `conversation_id` FK cascade, `role`, `content`,
  `sources` JSON, `created_at`.

Anonymous conversations are not persisted (they live only in the browser Zustand store
with a TTL), so no nullable account path is added. Conversation IDs are server-generated; a persistent ID is never
accepted as a client-supplied primary key. Add an index on
`es_assistant_messages.conversation_id`, indexes on `(es_guide_chunks.document_id,
is_active)` and `es_guide_chunks.article_id`, and an HNSW index on
`es_guide_chunks.embedding` (or an explicitly documented sequential scan for a small
guide). The vector dimension `N` is fixed at migration time to the chosen embedding model
(proposed 1536); changing it requires a new migration. Alternative: store embeddings as
`float8[]`/JSON — rejected (no index, poor recall).

### D4 — pgvector image

Replace `postgres:18.6-bookworm` with `pgvector/pgvector:<version>-pg18@sha256:<digest>`,
pinned by immutable digest. The image is `FROM postgres:18` and keeps the `pgdata` mount
and `PGDATA` layout. The deployment currently supplies one `DATABASE_URL` for both Alembic
and the app; a separate migration role is not in scope. Verify at Apply that this role can
create `vector` (database owner or `CREATE` on the database); if not, provisioning the
privilege is an explicit, approved deployment change. Record the resolved digest and
pgvector version, and confirm the `-pg18` tag's PostgreSQL minor matches the intended 18.6
(or document the difference). Verify at Apply:
`Test-DatabasePersistence.ps1`, an extension check after `alembic upgrade head`, and an
index/scan decision for `es_guide_chunks.embedding`. Alternative: a custom Dockerfile that
installs pgvector — rejected (extra maintenance and drift).

### D5 — Guide ingestion at article granularity

The approved guide is `backend/knowledge/guia-oficial-edesur.md` (frontmatter
`document_id: energia-sur-kb-edesur-001`, `version: 1.0.0`,
`last_verified_at: 2026-11-10`). Ingestion is deterministic and local (no URL fetch):

- Parse the YAML frontmatter for `document_id`, `version`, `last_verified_at`, `title` and
  `source_organizations`.
- Split on `### <ID> — <question>` under each `## N. <section>`; each article
  (`CA-01`, `PA-01`, `CO-01`, `TS-01`, `EL-01`, `EE-01`, `CR-01`, `TR-01`, `LI-01`) is one
  complete chunk. Do not split within an article and do not mix procedures.
- Per-chunk metadata: `document_id`, `version`, `last_verified_at`, `section`, `article_id`,
  `title` (the question), `content` (the full article text including equivalent queries,
  answer and caveats), `content_sha256`, `source_name` (primary label), `source_urls`
  (array of `{source_name, url}` for every principal/complementary/context/informative
  link, `https` only), `limitations` (array), `information_type`, `volatility` and
  `chunk_index`.
- Derive `volatility` deterministically from `**Tipo de información:**` with a documented
  keyword map: `variable` for "variables", "sujeto a cambio", "comerciales" or "puede
  variar"; `revalidate` for "revalidación", "sensible a regulación", "sujeto a
  evaluación", "prioridad", "no contiene disponibilidad actual" and for any unrecognized
  text (fail-safe default); `stable` only for explicitly static items. Never infer `stable`
  from silence. `information_type` stores the raw line; `limitations` includes every
  caveat marker (`Información no publicada`, `Límite`, `Limitación`, `No asumir`,
  `Advertencia`, `Advertencia esencial`, `Importante`, `Aclaración`, `Aclaración para
  Energía Sur`, `Importante para Energía Sur`) plus the prose-incomplete `TR-03` and
  `TR-04` (PA-07 already carries the `Información no publicada` marker). Ingest
  `source_type` and the paraphrase disclaimer from the frontmatter/intro so guide-sourced
  answers can state that the guide is a synthesis, not an Edesur-issued document. `LI-01`
  is a capability statement with no external source: `source_urls` may be empty there and
  the answer cites `document_id` + `article_id` + title instead.
- Exclude the frontmatter, the document intro and section 10 (source index/maintenance)
  from retrieval; use section 10 to validate source names and URLs.
- Parse the YAML frontmatter only up to the second `---` (the body contains horizontal
  rules); fail closed if required metadata is missing, the article count is not 53, the
  numbered content sections 1–9 (excluding section 10) are not all present, or an
  `article_id` is duplicated or malformed.
- Build LangChain `Document` objects (page content = article text, metadata = the fields)
  and embed with `OpenAIEmbeddings`; persist with the `pgvector` SQLAlchemy type and a raw
  SQL upsert.
- Idempotency and version replacement: upsert by `(document_id, article_id, version)`.
  The hash covers content, `version`, `last_verified_at`, `parser_version` and the
  canonical stored metadata, so a metadata-only correction is not skipped. If the content
  hash is equal, accept a newer `last_verified_at` in place; if it differs, require a
  strictly newer version (numeric dotted compare, not string compare). Skip unchanged
  hashes before any deactivation. In one transaction, under a dedicated
  `pg_advisory_xact_lock` with a key namespace distinct from CU01's `0x43553031`, mark the
  prior version's chunks `is_active = false`, insert/activate the new version, and update
  `current_version`. An operator-only, logged force flag may override the monotonic guard;
  a non-forced older version is a no-op with exit 0, not an error. The partial unique index
  keeps at most one active row per article. Retrieval filters `is_active = true` and the
  current version.
- Trigger: a one-off command (for example `python -m app.ingest_guide`) or a startup flag
  `ASSISTANT_GUIDE_INGEST=true`, fail-closed; an empty index or missing key yields the
  static fallback. A failing startup ingest logs only the failure class, keeps the last
  good index and falls back statically; it does not abort startup or the CU01/CU02/CU09
  schedulers.

Retrieval is SQL cosine similarity (`<=>`) over the active chunks, top-k with a relevance
threshold. Alternative: `langchain-postgres` PGVector — rejected (opaque internal tables
conflict with the metadata schema). Alternative: a generic character splitter — rejected
(it breaks article boundaries and mixes procedures).

### D6 — Memory and optional auth

- Temporary: the visitor conversation lives in the frontend Zustand store with a
  configurable TTL and is sent to the backend as bounded history for each anonymous turn
  (10 messages/4000 characters); the Zustand array itself is TTL-bound. There is no
  server-side temporary store and nothing is persisted.
- Persistent: DB rows scoped to `account_id`. The POST resolves `conversation_id` with
  `WHERE id = :id AND account_id = :account_id`; the `DELETE` uses strict `Auth` + `Writer`
  and returns 404 on non-ownership.
- New `optional_actor` dependency treats missing/invalid/expired cookies as anonymous
  (`None`), not 401, so a stale cookie cannot block public chat. `DELETE` keeps strict auth.
- Message content is persisted only inside the owning account's conversation; anonymous
  content is never durably persisted. Logs, telemetry and terminal `error` events never
  contain message content, prompts or provider keys. Users are not required to supply
  personal data; the only content sent to the provider is the chat text the user chooses.
  Logs, telemetry and error events are verified by tests.
Alternative: persist anonymous conversations — rejected (privacy/at-rest).

### D7 — SSE contract

`POST /assistant/chat` returns `StreamingResponse` (`text/event-stream`) with events:
`conversation` (id, scope), `delta` (text), `tool` (name, sources), `sources`, `error`,
`done`. `Cache-Control: no-store`. Mid-stream failures emit a terminal `error` event
instead of relying on global exception handlers. Alternative: EventSource GET — rejected
(message length/encoding limits).

### D8 — CSRF/Origin for the public chat endpoint

`POST /assistant/chat` is CSRF-exempt (approved) but enforces `origin(request)` server-side
and abuse protection, and performs no provider call on a disallowed Origin. Authenticated
unsafe operations keep the existing Origin + session-bound CSRF requirement unchanged.
The `frontend-session-transport` adaptation is documented for review but not applied now:
a raw-fetch streaming client reuses `apiPath`, sends credentials, never forges
`Origin`/`Authorization`, attaches CSRF only where required (not for chat), applies the
`generation` guard on 401 and never auto-retries the same message. For this contract the
chat endpoint is a public endpoint with session-aware persistence, not an "authenticated
unsafe operation" in the sense of the existing requirement; login/logout and authenticated
mutations are unchanged. The `MODIFIED` `frontend-session-transport` delta is included in
this change; the BUILD 3 authorization approved the public-chat exception. The `origin`
helper is shared from `security.py` to avoid coupling the assistant transport to the CU09
router.

### D9 — Fallback and refusal

Static, identifiable constants for provider/tool/rate-limit/empty-index failure and for
unsupported questions; they direct users to official channels and never invent data. The
exact Spanish wording is a review-level presentation detail (Q07/CU03).

### D10 — Limits

A per-client rate limiter mirroring `outages_api._allow` (with pruning) returns 429 +
`Retry-After` before the stream starts; first-byte and total timeouts; a message and
request-body size cap enforced before JSON parsing; and token/context/output limits. The
Origin check runs before the limiter and any provider call, concurrent streams are bounded,
and the limiter keys on peer plus available session identity where possible. The client
renders the static fallback copy on 429/503. The single-instance in-process assumption is
documented, consistent with the existing public resolve limiter and the shared peer bucket
behind the Vite proxy.

### D11 — Dependencies and configuration

Add pinned `langchain`, `langchain-core`, `langchain-openai`, `pgvector` and an explicit
YAML parser (`pyyaml`) for the frontmatter (exact pins and `uv.lock` at Apply;
`langchain-postgres` excluded; IDs stay `String(36)` for codebase consistency).
Configuration is server-side only:
`OPENAI_API_KEY` (no default), `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`, and
`ASSISTANT_*` limits. Without a key the assistant reports unavailable and uses the static
fallback; embeddings are disabled and startup does not fail.

### D12 — MCP deferral

CU03 exposes internal LangChain read tools, not MCP. The academic requirement of at least
one external MCP server is deferred to CU10 as a proposal (not implemented or verified
here). Development MCP servers remain separate and are never exposed to the runtime.

### D13 — Guide source packaging (Docker)

The guide must be present in the backend image at
`/app/knowledge/guia-oficial-edesur.md`. Today `backend/.dockerignore` starts with `**`
and whitelists only `app/`, `tests/`, `alembic.ini`, `migrations/`, `pyproject.toml`,
`uv.lock` and `.python-version`, and `backend/Dockerfile` does not copy `knowledge/`.
The guide is therefore absent from both the `verification` and `runtime` stages. Required
at Apply: add `!knowledge/` plus `!knowledge/*.md` (mirroring the existing `!app/` +
`!app/*.py` shape), keeping the secret patterns after the negations, and add
`COPY knowledge ./knowledge` in both stages. The copied file is
root-owned 644 and readable by UID 10001. Compose mounts only `app/`, so guide edits
require a rebuild (or an explicit read-only dev mount); document this. Verify with an image
listing that `/app/knowledge` contains only the guide. Alternative: a Compose bind mount —
rejected because the requirement is image inclusion and the image must run without a host
mount.

### D14 — Staleness and incomplete information

`last_verified_at` is stored per chunk. A configurable `ASSISTANT_GUIDE_MAX_AGE_DAYS`
(proposed default 90; confirm at Apply) triggers a staleness disclosure when exceeded.
Regardless of age, an article whose `volatility` is `variable` or `revalidate` (derived
from `Tipo de información`) SHALL carry a "subject to change; confirm at the official link"
notice. Articles marked `Información no publicada`, `Límite`, `Limitación`, `No asumir`,
`Advertencia` or `Advertencia esencial`, and the prose-incomplete `PA-07`, `TR-03` and
`TR-04`, SHALL surface the limitation and never be filled in. The guide's "Control de
vigencia" list (phones, hours, WhatsApp scope, payment methods, subsidies, amounts,
requirements, form routes) is the revalidation checklist.

### D15 — RAG versus dynamic data

The guide answers "where/how to consult" and procedural questions; live outage and
scheduled-work status comes only from CU01/CU02 tools. `CR-01`, `CR-03` and `LI-02`
explicitly say the guide does not contain current availability. Routing: current-state
questions go to the CU01/CU02 tools with freshness and coverage; procedure, channel and
benefit questions go to RAG; mixed questions combine both but label sources and never let
a guide article override dynamic state. If dynamic data is unavailable, the assistant says
so and does not substitute a static guess. Top-k retrieval SHALL cite only the articles
actually used, and a procedure answer SHALL draw from one procedure article at a time (no
mixing of different procedures); genuine ambiguity is resolved by asking the user or
choosing the single best article.

## Contracts

**HTTP**

| Method | Path | Auth | Notes |
| --- | --- | --- | --- |
| POST | `/assistant/chat` | public (optional session) | SSE; CSRF-exempt + Origin check; rate-limited |
| GET | `/assistant/conversations` | session | owner-scoped list |
| GET | `/assistant/conversations/{id}/messages` | session | owner-scoped messages, 404 on mismatch |
| DELETE | `/assistant/conversations/{id}` | session + Origin + CSRF | owner-scoped, 404 on mismatch |

**SSE events:** `conversation` `{conversation_id, scope}`, `delta` `{text}`,
`tool` `{name, status, sources: [{source_name, url}]}`, `sources`
`{sources: [{source_name, url}]}`, `error` `{code, message}`, `done` `{}`;
`Cache-Control: no-store`.

**Config:** `OPENAI_API_KEY`, `OPENAI_MODEL`, `OPENAI_EMBEDDING_MODEL`,
`ASSISTANT_GUIDE_INGEST`, `ASSISTANT_GUIDE_MAX_AGE_DAYS`, `ASSISTANT_RATE_LIMIT`,
`ASSISTANT_RATE_WINDOW_SECONDS`, `ASSISTANT_MESSAGE_MAX_CHARS`, `ASSISTANT_TIMEOUT_SECONDS`,
`ASSISTANT_FIRST_BYTE_TIMEOUT`, `ASSISTANT_MAX_CONCURRENCY`, `ASSISTANT_MAX_OUTPUT_TOKENS`,
`ASSISTANT_TOP_K`, `ASSISTANT_MAX_DISTANCE`, `ASSISTANT_MAX_BODY_BYTES`,
`ASSISTANT_HISTORY_MAX_MESSAGES`, `ASSISTANT_HISTORY_MAX_CHARS`,
`ASSISTANT_RETENTION_DAYS`.

## Security

- Read-only public-data tools only; no CU04-CU09 access, no keys, no development tools.
- Prompt injection: guide chunks and tool results are delimited, untrusted data; the
  system prompt forbids following embedded instructions and inventing facts.
- No SSRF: the guide is a local file; the only external egress is the fixed ENRE client
  and OpenAI. Citations are built server-side from retrieved guide rows and tool metadata,
  restricted to `https` URLs whose host matches a static, code-owned allowlist
  (`edesur.com.ar`, `ov.edesur.com.ar`, `argentina.gob.ar`, `www.enre.gov.ar`) using
  exact-or-dot-boundary matching, and rendered as text/links with `rel="noopener
  noreferrer"`, never raw HTML; guide URLs are cross-checked against section 10 at ingest
  and a non-matching guide URL is dropped while its `source_name` text is kept. The model
  cannot introduce a citation URL, and scheme/host/length are validated server-side and
  client-side. The model-authored answer body renders as plain text (no Markdown/HTML); if
  linkification is kept, only allowlisted `https` hosts become links.
- Origin validation and rate limiting on the public endpoint; owner-scoped persistence and
  404-on-mismatch; no logging of keys, prompts, message content or PII, including terminal
  `error` events (verified by tests); `Cache-Control: no-store`.

## Testing

- Backend unit: guide parser (53 article units across 9 sections; no frontmatter or
  section-10 chunks), retrieval per section (one representative question per
  CA/PA/CO/TS/EL/EE/CR/TR/LI section asserting `article_id` and expected `source_urls`),
  idempotent re-ingest (no duplicates) and version replacement (v1.0.1 supersedes v1.0.0,
  old inactive), staleness and incomplete-article disclosure, RAG-versus-dynamic routing,
  tool parity with CU01/CU02, memory, limits, SSE with a fake LLM, fallback/refusal,
  `optional_actor`, ownership isolation.
- Migration/pgvector against an isolated `TEST_DATABASE_URL`; no real OpenAI calls.
- Image check: the `verification` and `runtime` images contain
  `/app/knowledge/guia-oficial-edesur.md`.
- Frontend: streaming parser/guards, state reducer, panel/source rendering, accessibility.
- E2E: Playwright with a mocked SSE stream; real-model run is manual/optional.

## Risks / Trade-offs

- Guide delivered (v1.0.0): time-sensitive data and incomplete procedures → disclose the
  verification date and limitations, and revalidate; never fill gaps.
- Docker image omits `knowledge/` until `.dockerignore`/`Dockerfile` include it → BUILD 1
  blocker; verify the file is present in both the `verification` and `runtime` stages.
- pgvector image swap → verify persistence/extension/role before Apply.
- CSRF-exempt public POST → Origin check + rate limit + documented exception.
- Prompt injection → delimiters + anti-invention prompt; residual model risk.
- Streaming duplicates transport security → reuse `apiPath`/session store and test parity.
- Single-instance rate limiter/concurrency slots; visitor history is client-side with TTL.
- Cost/latency → limits; hallucination → grounding + citation + fallback.

## Migration Plan

Additive `0007_cu03`: create the extension, then the four tables (`es_guide_documents`,
`es_guide_chunks`, `es_assistant_conversations`, `es_assistant_messages`); no existing
table is altered and `pgdata` is preserved. Deploy steps (at Apply): add `knowledge/` to
`.dockerignore`/`Dockerfile`, pin and pull the pgvector image, run `alembic upgrade head`
against the isolated database, ingest guide v1.0.0 from the image at
`/app/knowledge/guia-oficial-edesur.md`, then start backend/frontend. Downgrade SHALL NOT
delete user data; the exact
downgrade behavior is an Apply-time decision to verify (existing `0005`/`0006` drop their
own new tables, so this must not be assumed). Proposed: downgrade drops only the guide
tables and refuses to drop `es_assistant_conversations`/`es_assistant_messages` (user
data), or refuses downgrade entirely; this destructive-migration choice needs explicit
approval at Apply, and rollback leaves the new tables unused.

## Open Questions

- Exact Spanish fallback/refusal wording (presentation detail for review).
- Final embedding model/dimension (proposed `text-embedding-3-small`, 1536; confirm at Apply).
- Staleness threshold default (`ASSISTANT_GUIDE_MAX_AGE_DAYS`, proposed 90; confirm at Apply).
- Authenticated-message retention and a one-line third-party-processing notice for the
  OpenAI provider — privacy/presentation decision.
- pgvector extension owner/role when only one `DATABASE_URL` is supplied — Apply-time
  verification; a separate migration role is not in scope.
- External MCP server scope in CU10 (separate proposal).

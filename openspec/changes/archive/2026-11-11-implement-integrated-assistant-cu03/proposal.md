# Proposal

## Why

CU03 ("Get guidance from the integrated assistant") is the remaining planned public
use case. CU01 and CU02 already expose public, read-only outage and scheduled-work data
with provenance, and U09/U10 reserved exactly one floating chat mount in the shared
layout but deliberately left it unavailable. This change turns that placeholder into an
integrated, grounded assistant so a visitor or account holder can ask about outages,
scheduled works and consultation/complaint procedures without inventing live status or
fabricating guidance.

The accepted baseline (`docs/use-cases/cu03.md`, SR01/SR03/SR06) fixes the actor,
public access, provenance and the no-invention constraint but leaves Q06 (guide and
retrieval/citation granularity), Q07 (CU03 fallback UX) and persistent assistant memory
open. The eight decisions recorded as U23 resolve the mechanism, and the Edesur guide is
now delivered at `backend/knowledge/guia-oficial-edesur.md` (version 1.0.0, verified
2026-11-10); it is ingested at article granularity and its content is not modified.

## What Changes

- Add a new **public assistant capability**: conversational guidance about current
  outages, scheduled works and consultation/complaint procedures, grounded on official
  sources and cited with organism, title and URL.
- Add a backend LangChain + OpenAI runtime with **read-only tools** over the CU01/CU02
  cached snapshots (no query-time ENRE/GeoRef calls, no writes) and **RAG** over the
  delivered Edesur guide at article granularity (`CA-01`, `PA-01`, ...), carrying
  `document_id`, `version`, `last_verified_at`, `section`, `article_id`, `source_name` and
  `source_urls` metadata.
- **Ingest the guide idempotently** with controlled version replacement (stable article
  IDs, content hash, active-version filter), and disclose stale or incomplete information
  instead of filling gaps.
- Add **streaming SSE** (`text/event-stream`) for the chat endpoint, plus temporary
  in-memory memory for visitors and persistent, account-scoped memory for authenticated
  users.
- Add a **static, identifiable fallback** for provider/tool/rate-limit/no-source cases
  and an explicit refusal for unsupported questions; preserve source freshness,
  coverage and normative states.
- Add **limits**: per-client rate limit (429 + `Retry-After`), first-byte and total
  timeouts, message-length caps and token/context/output limits.
- Replace the unavailable `ChatMount` placeholder with the runtime, keeping exactly one
  floating mount per root layout.
- Documentation: record U23; move Q06 to PARTIAL, resolve the CU03 part of Q07, and
  supersede the prior "persistent chatbot memory TBD" entry. Document the CSRF-exempt
  public `POST /assistant/chat` with server-side Origin validation, the approved
  `frontend-session-transport` MODIFIED delta for the public-chat exception, and the
  deferral of any external MCP server to CU10.

### Scope

- Public guidance and read-only data questions (outages, scheduled works, procedures).
- Visitor and authenticated use of the same public endpoint.
- Authenticated persistent conversation history (owner-scoped, clearable).

### Exclusions

- No complaint submission, no account administration.
- No access to private CU04-CU09 records from the assistant.
- No write tools, no privileged/development tools, no MCP exposure in the runtime.
- No expansion of CU02 beyond the U22 definitive scope: no planned start/end, reason,
  distance, future agenda or date filters.
- No individual-address or meter supply status (CU01 zone granularity only).
- No fabricated Edesur guide content, sources or links.
- No change to CU01, CU02 or CU09 behavior.

## Capabilities

### New Capabilities

- `assistant`: public grounded conversational guidance about outages, scheduled works
  and consultation/complaint procedures, with source citation, temporary/persistent
  memory, SSE streaming, a static fallback/refusal and bounded resource usage.

### Modified Capabilities

- `frontend-shell`: the single floating-chat mount changes from a deferred, unavailable
  placeholder to a functional assistant mount when the runtime/provider is available,
  with an explicit unavailable/static-fallback state otherwise.
- `frontend-session-transport`: the public assistant chat is an Origin-validated,
  CSRF-exempt streaming exception; all other authenticated unsafe operations keep the
  session-bound CSRF token.

## Confirmed decisions (U23)

1. RAG over the delivered Edesur Markdown guide, ingested at article granularity; its
   content is not modified and stale or incomplete items are disclosed.
2. PostgreSQL 18.6 with pgvector.
3. Read-only tools for CU01/CU02 (snapshot reads only).
4. Temporary public memory and persistent memory for authenticated users.
5. Streaming SSE.
6. Official sources identified by organism and link.
7. Identified static fallback on errors.
8. Rate limit, timeout, message-length and token limits.
   Also approved for this proposal: `POST /assistant/chat` is CSRF-exempt but requires a
   server-side Origin check; any external MCP server is deferred to CU10.

## Dependencies and approval gates

- **Delivered dependency:** the Edesur guide is delivered at
  `backend/knowledge/guia-oficial-edesur.md` (v1.0.0); ingestion is local and idempotent.
  Time-sensitive data and procedures the guide marks incomplete require disclosure and
  periodic revalidation.
- **BUILD 1 prerequisite:** the backend image must include `knowledge/`; today
  `.dockerignore` ignores it and the Dockerfile does not copy it, so the guide is absent
  from the image until the whitelist/`COPY` change is applied.
- **Apply-time verification:** pin the `pgvector/pgvector` image by immutable digest,
  confirm the application role can create the `vector` extension, and re-run the
  migration/persistence checks.
- **Runtime dependency:** a server-side OpenAI key; without it the assistant reports an
  unavailable state and uses the static fallback, without crashing startup.
- This proposal authorizes documentation and OpenSpec artifacts for review only.
  Apply requires a subsequent explicit implementation request; Sync, Archive, commit,
  push, deployments, dependency installation and migrations are not authorized here.

## Impact

- **Backend:** new assistant modules (`assistant_api`, `assistant`, `assistant_tools`,
  `guide_store`, `assistant_memory`, `assistant_limits`), an optional-auth dependency,
  migration `0007_cu03`, new pinned dependencies (LangChain/OpenAI/pgvector) and a
  `db` image change to pgvector that preserves `pgdata`. The guide ingestion reads
  `backend/knowledge/guia-oficial-edesur.md` at article granularity, so the backend image
  must whitelist and copy `knowledge/`. The read tools extract the existing pure
  freshness/state helpers into a shared module, so CU01/CU02 responses must stay
  byte-compatible (regression tests); this is a refactor with no behavior change.
- **Frontend:** `ChatMount` runtime, a dedicated streaming client (fetch/ReadableStream)
  and a new `features/assistant/` module; one root mount preserved.
- **Docs:** `docs/use-cases/decisions.md` (U23, Q06, Q07, memory status), the CU03 fiche
  status references, `docs/STATE.md`, and at Apply `README.md` plus
  `docs/frontend-foundation.md`.
- **Unchanged:** CU01/CU02/CU09 behavior, existing authenticated session/CSRF policies for
  non-chat operations, and development MCP configuration.

# Shared frontend foundation

CU09 is the first adopter. Reuse the existing React/TypeScript/Vite application;
this foundation is not a second app, backend framework, router or query cache.

## Boundaries and modules

| Concern | Location | Ownership |
| --- | --- | --- |
| Root shell and chat mount | `frontend/src/layouts/` and `src/components/` | One layout and one functional assistant mount, independent of account/domicile feature keys. |
| CU03 assistant | `frontend/src/features/assistant/` | SSE client, temporary Zustand conversation with TTL, owner-scoped authenticated persistence, safe sources and fallback states. |
| Local shadcn/ui primitives | `frontend/src/components/ui/` | Repository-owned accessible presentation, Tailwind tokens and upstream license/provenance. |
| Memory session and selection | `frontend/src/stores/session.ts` | Validated account/session CSRF, selected domicile, generation and lifecycle actions only. |
| HTTP policy | `frontend/src/lib/http.ts`, `httpError.ts` | Fixed same-origin `/api`, cookie credentials, interceptors, cancellation and safe typed errors. |
| CU09 DTO adapter | `frontend/src/diaryApi.ts` | Payload/status/MIME validation and response identity checks; authoritative data comes from backend. |
| CU09 presentation/forms | `frontend/src/features/diary/` | Feature-local rows, summaries, drafts and React Hook Form/Zod schemas. |
| Cancellation/calendar presentation | `frontend/src/diaryState.ts`, `useRequestScope.ts` | Existing request lanes and Buenos Aires display helpers; not authoritative duration calculations. |

All paths in the table are repository-relative; abbreviated `src/` paths are under
`frontend/`. See the archived [design](../openspec/changes/archive/2026-11-08-establish-frontend-foundation/design.md)
and [tasks](../openspec/changes/archive/2026-11-08-establish-frontend-foundation/tasks.md) for scope and evidence.

## Adding another CU

1. Resolve its accepted OpenSpec contract before adding routes or business rules.
   Add a feature directory under `frontend/src/features/`, not another Vite app.
2. Reuse local UI primitives and root layout. Keep labels, explicit button types,
   visible focus and field errors linked with `aria-describedby`/`aria-invalid`.
3. Define presentation schemas with Zod and use `zodResolver` with React Hook Form.
   Use `z.input`/`z.output` when transforms change payload types. Validate required
   text/shape/length for feedback, while backend validation remains authoritative.
   Never move tariff, ownership, timezone/DST, future-date, or overlap calculations
   into the shared form layer. Preserve external payload field names.
4. Write a typed adapter over the shared `http.request` function. Treat response
   data as `unknown` and validate status, content type, fields and resource identity.
   Do not create an Axios instance inside a component or log raw Axios errors.
   Streaming endpoints are the documented exception: use the feature's
   `fetch` + `ReadableStream` client with `apiPath`, credentials, cancellation and no
   auto-retry, as `features/assistant/api.ts` does.
5. Select only required session/selection values with `useSessionStore`. Keep
   drafts, server rows and pending/error states in the feature, not a global cache.
   Use request lanes and session generation checks so old responses cannot update
   a new account/domicile. Reset forms on account/domicile/editor/revision identity.
6. Add Node schema/store/adapter regressions and meaningful rendered acceptance.
   Unit adapter tests are not browser/backend acceptance. Preserve the existing
   login, diary conflict/reset and PDF regression checks when adopting a CU.
   Backend health is not a UI contract (U26): verify it through `GET /health` and
   the `/api/health` proxy, not through a screen or a layout request.

Example adapter shape (illustrative until a new CU contract is accepted):

```typescript
import { http } from '../../lib/http.ts';

// Use the accepted feature path and a real response validator, not an unchecked cast.
const response = await http.request('/domiciles', signal);
const body: unknown = response.data;
// Validate body/status/content type here, as DiaryClient does.
```

## Authentication and CSRF

- Session cookie is HttpOnly; JavaScript neither reads it nor creates a bearer token.
  Axios sends cookie credentials to the fixed same-origin `/api` path only.
- Login uses browser-supplied Origin and no pre-auth CSRF token. The backend rejects
  missing/null/malformed/foreign Origin; frontend code must never forge that header.
- Authenticated unsafe requests obtain the current CSRF token from the memory store.
  It comes from validated login/session JSON, not from a readable XSRF cookie.
  Axios cookie-derived XSRF behavior is disabled deliberately.
- Existing diary mutation arguments retain their CSRF parameter for compatibility,
  but ordinary writes use the store's current token, not a stale caller snapshot.
  Logout alone can use the token captured immediately before local state is cleared.
  This allows immediate UI isolation while sending the server revocation request.
  An unsuccessful logout reports that server revocation was not confirmed.
- A generation increments on session replacement/reset. Interceptors reject stale
  successes and stale 401 responses instead of installing old data or clearing a
  newer login. Account/domicile transitions also invalidate feature request scopes.
- No persistence or devtools middleware, localStorage/sessionStorage, password store,
  token logging, unsafe automatic retry or automatic credential refresh is added.

## Transport and PDFs

`createHttpClient` accepts a store, an optional Axios adapter, an optional per-client
timeout (default 10 seconds) and a test-only deadline-signal factory for isolated
deterministic tests. Production stays at 10 seconds except for the CU10 admin retry,
which uses a documented 25-second client timeout because the synchronous ENRE retry can
outlast the normal deadline; that exception is scoped to the single retry request.
Feature requests cannot override auth, headers, base URL, adapter or credentials.
External/protocol-relative URLs, traversal and unsafe normalized destinations are
rejected before network dispatch. `baseURL` alone is not a security boundary.

Pass an AbortSignal on every request. Default timeout is 10 seconds (25 seconds only for
the CU10 retry). Typed errors preserve
401/403/404/409/422/503 and distinguish cancellation, timeout, network and malformed
responses. Do not catch and expose raw request configs/cookies/passwords/CSRF.
409 requires explicit user recovery, never an automatic write retry.

For downloads, use blob response handling through the feature adapter. Validate
200, PDF content type and nonempty content before creating a download URL, and
revoke it after use. Error JSON can arrive as a blob; only bounded expected JSON
error data is decoded for safe feedback. Never download an error as a successful PDF.

## Styling and local component maintenance

Tailwind is integrated with the existing Vite configuration and stylesheet.
`frontend/components.json` describes local shadcn/ui paths and theme settings;
`@/` is configured consistently in TypeScript and Vite. Node-testable modules use
relative `.ts` imports. Do not overwrite existing files through an unreviewed CLI
initializer or add a whole registry. Retain upstream license/provenance when
adapting local component source. No shadcn runtime library is required.

Preserve the approved React/TS/Vite/Node/npm pins and strict TypeScript settings.
Add only approved exact dependencies and regenerate `package-lock.json`; never
force incompatible peers. Configuration files needed in the image must be in both
the Docker copy list and `.dockerignore` allowlist. No service exposure changes.

## Chat ownership

The layout owns exactly one functional floating-assistant mount across login, logout and
domicile transitions. It streams through the dedicated `features/assistant` client,
renders official HTTPS sources and keeps the visitor conversation in Zustand with a
configurable TTL. Authenticated users get owner-scoped persisted conversations (the chat
sends the conversation id and the server keeps bounded history); logout/account changes
abort in-flight streams and reset the panel. It never exposes provider credentials, never
persists anonymous conversations and never mounts a second chat. A visible notice explains
OpenAI processing and authenticated storage.

## Verification (PowerShell, repository root)

```powershell
docker build --target verification -t energia-sur-frontend-checks:cu03 frontend
docker run --rm energia-sur-frontend-checks:cu03 npm test
docker run --rm energia-sur-frontend-checks:cu03 npm run lint
docker run --rm energia-sur-frontend-checks:cu03 npm run build
# With a dev server reachable from the Playwright container:
npx playwright test e2e/cu03.spec.ts e2e/cu03-auth.spec.ts
openspec validate --all --strict --no-interactive
```

The verification image includes Chromium; one approved quick real CU09/PDF pass
can be run through `scripts/Test-Cu09Acceptance.ps1` after the documented backend
verification build. That script creates and retains additive synthetic databases,
restarts only frontend/backend and checks migration/restart persistence. It does
not delete existing data/volumes or deploy the application. See
[README](../README.md#cu09-setup-and-checks-powershell-repository-root) and the
[engineering record](ai-engineering/establish-frontend-foundation.md) for actual
run outcomes and limitations, not just runnable instructions.

# Design

## Context

See [proposal](proposal.md) for motivation and [shell](specs/frontend-shell/spec.md)
and [transport](specs/frontend-session-transport/spec.md) for required behavior.
U09 approves this technology direction; U10 subsequently authorizes Apply after
artifact presentation. The observations below describe the pre-Apply baseline;
the engineering record documents implementation, installed pins and actual checks.

Observed files, not hypothetical greenfield structure:

- `frontend/src/main.tsx` already mounts one StrictMode App and imports styles.
- `App.tsx` owns session and every CU09 form with React state. The keyed editor
  includes domicile, cut identity/version and reset revision to fix past draft leaks.
- `diaryApi.ts` wraps fetch, validates DTOs and ownership, enforces status/MIME
  checks, forwards cookies/CSRF and returns PDF blobs. `diaryState.ts` and
  `useRequestScope.ts` already protect against stale account/domicile responses.
- `styles.css` uses broad element rules; Vite retains the `/api` backend proxy.
  Strict TypeScript includes source/tests/E2E/config; Node tests use `.ts` imports.
- Docker copies an explicit allowlist and runs build, Node tests and Oxlint.
- CU09 U09 security clarification is independently rechecked. Its contract remains
  authoritative; no endpoint or auth-policy change is needed for this foundation.

## Goals / Non-Goals

**Goals:** reusable layout/primitives/forms/transport, one in-memory session source,
and actual CU09 adoption without losing its difficult error/reset/ownership cases.

**Non-Goals:** new app, router/query framework, backend rewrite or calculations,
database/auth migrations, remembered credentials, public signup, other-CU feature
implementation, chatbot answers, LangChain/streaming, persistent memory, deployment.

## Decisions

### F1 - Incremental layers in the existing application

Keep `main.tsx` and use `src/layouts/AppLayout.tsx` for the single shell/chat slot.
Place shared primitives in `src/components/ui/`, memory state in `src/stores/`,
and transport/utilities in `src/lib/`. Move CU09 presentation/forms to
`src/features/diary/`; retain the public typed diary adapter surface until callers
and tests migrate together. Keep HealthPanel working inside the layout.

Alternative: a new scaffold or generic feature/plugin architecture. Rejected as
scope growth and unnecessary risk to the working CU09 slice. No router is needed
for the one current feature. Only truly shared identity/selection belongs in the
store; cut rows, summaries, form drafts and pending state stay feature-local.

### F2 - Tailwind Vite integration and local shadcn/ui source

Use the Tailwind Vite plugin and CSS import/theme tokens in the current stylesheet;
preserve the existing proxy/port contract. Add `components.json` and a shared `cn`
utility. Start with reviewed local button, input, textarea, label, card, alert and
table primitives. Use native select for the small domicile selector rather than
adding an advanced combobox. Avoid unnecessary icon/animation dependencies.

Use official shadcn/ui component source (record provenance/license and version);
inspect CLI help/diffs before using the pinned CLI, never blindly run a registry
initializer that overwrites existing files. Copy only needed local source, with
strict typing and accessible labels/focus/error associations. Add a `@/` alias
consistently in Vite/TypeScript if required by local source; Node-test modules
retain resolvable relative `.ts` imports. Review Docker copy/allowlists for new
configuration. Tailwind preflight/global-rule changes must not break HealthPanel
or the diary table. Replace conflicting element styles incrementally.

Alternative: whole registry import or an opaque remote UI dependency. Rejected:
the user specifically requested local components and a minimal reusable base.

### F3 - Memory-only Zustand session and selection

Create typed vanilla store factories for isolated Node tests and React selectors.
State: validated session/account/CSRF, selected domicile ID and a generation marker.
Never store passwords, raw cookie tokens, PDF blobs, rows or summaries globally.
Do not use persistence/devtools middleware or browser storage.

Logout/401 expiry clears session/selection, advances the generation and invalidates
request scopes. A response from an older generation cannot overwrite or clear a
new session. Clear workspace/form data on account change; domicile switches reset
the selected feature's editor/closure/summary and invalidate its request lanes.
Keep the existing keyed reset revision including same-version 409 discard behavior.

Alternative: persist/rehydrate private state or replace request scopes with a new
cache library. Rejected because neither is approved/necessary and both increase
cross-account stale-data risk.

### F4 - React Hook Form and Zod at presentation boundaries

Adopt login, new domicile, create/correct cut, close cut and report-period forms.
Use `zodResolver` with explicit typed input/output schemas, accessible field errors,
and empty-string-to-null mapping compatible with the existing payload names. Keep
HTML constraints for user feedback, including the approved 1970 local floor.
Reset/unmount schemas and values on session/domicile/editor/revision changes.
Passwords exist only in the login form and clear after completion/unmount.

Mirror required/text-length/shape constraints only. Do not implement authoritative
future-date, timezone/DST, interval union, ownership or server clock calculations
in Zod. Backend 422 still appears usefully; 409 keeps the draft until explicit
discard/reload; do not auto-reset failed submissions. DTO validation may reuse
existing guards or explicit Zod parsing, but may not become unchecked casts.

Alternative: keep every form handwritten or move backend rules client-side.
Rejected by the requested reusable form stack and authority boundary respectively.

### F5 - One Axios boundary, preserving the diary contract

Create one testable instance/factory in `src/lib/http.ts`, with a fixed same-origin
`/api` prefix, `withCredentials`, 10-second timeout and per-request AbortSignal.
Disable Axios cookie-derived XSRF defaults: the backend exposes a session JSON token,
not a readable CSRF cookie. A request interceptor attaches `X-CSRF-Token` from the
current in-memory session on unsafe authenticated requests, but never on login or
GETs; do not attempt to set browser Origin or read the HttpOnly cookie.

Validate the fully resolved destination before dispatch: same origin AND API path
prefix. Reject absolute/protocol-relative external paths, traversal or overrides
that escape the prefix; `baseURL` alone is not an isolation boundary. No API caller
may override credentials/auth/baseURL/adapter arbitrarily. Test unsafe encoded and
normalized paths before token attachment. No global `axios.defaults`, bearer token,
automatic credential refresh, unsafe retry, or redirect-based login logic.

Response interception normalizes safe typed errors, invalidates only the matching
session generation on 401, and preserves status/409 recovery semantics. Avoid raw
AxiosError/config logging because configs can contain passwords/CSRF. Keep expected
status and content-type checks, unknown-payload validation and identity consistency
in the typed diary adapter. Preserve cancellation vs timeout/network distinctions.

PDF uses `responseType: 'blob'`; errors may also arrive as JSON blobs, so decode
only bounded expected JSON errors safely, never trigger a download for JSON/error,
and validate nonempty PDF MIME data before creating/revoking the object URL. No
retry of canceled requests. Adapter-injected tests avoid real-network unit tests.

Alternative: default Axios XSRF cookie behavior or keep two transports in parallel.
Rejected as incompatible with the approved JSON-token contract and duplicated policy.
Use a small DI factory, not a new dependency framework.

### F6 - Chat reserved once, runtime explicitly deferred

Mount one `ChatMount` in the root layout, outside login/CU09 conditional rendering
and domicile-keyed workspaces. Show an accessible disabled launcher or unavailable
status naming CU03. No message form, fake replies, network call, portal duplication,
conversation persistence, provider package or API key. This establishes an
integration seam only; CU03 later implements connection, streaming and behavior.

Alternative: mock an assistant or embed a chat per feature. Rejected because it
would misrepresent academic completion and create duplicated state/runtime mounts.

### F7 - Proposed exact additions and compatibility gate

Public npm registry metadata was checked on 2026-11-07 with the existing Node image;
these are proposed exact versions, not installed or a proven compatible lock:

| Addition | Proposed pin | Role |
| --- | --- | --- |
| tailwindcss / @tailwindcss/vite | 4.3.5 / 4.3.5 | CSS and Vite development integration |
| shadcn | 4.23.0 | Pinned source-generation CLI only, not runtime library |
| zustand | 5.1.0 | In-memory shared state |
| react-hook-form / @hookform/resolvers | 7.91.0 / 7.0.3 | Typed forms and Zod resolver |
| zod | 4.6.7 | Presentation/transport validation |
| axios | 1.21.0 | Centralized HTTP client |
| class-variance-authority / clsx / tailwind-merge | 0.7.1 / 2.1.1 / 3.7.0 | Minimal local component utilities |
| radix-ui | 1.8.1 | Only if copied component source needs its accessible primitives |

Preserve React 19.3.1, React DOM 19.3.1, TS 7.0.2, Vite 8.3.6, Node 24.22.2,
npm 11.19.1, Playwright 1.65.0 and Oxlint 1.92.0. React/Zod/Vite peer ranges in
the metadata support the proposed direction; verify optional peer metadata and
strict installation in Apply. Do not install every optional resolver/Zustand peer
or force peer compatibility. Inspect actual generated imports, install only needed
approved helpers, regenerate package-lock with npm, and rerun locked Docker builds.
If a new core dependency or major pin change is needed, stop and request approval.

### Verification and traceability

U09 is the source for both new capabilities. Preserve all CU09-S01–S15/AD-S01–S02
oracles from the active diary change; reference them rather than duplicating domain
requirements. Mandatory future checks: Node store/schema/adapter tests, Oxlint,
strict TS/build, locked install/drift, backend security regressions and independent
security review of interceptor/state handling. Exactly one quick real Chromium
workflow, including PDF download/text validation, is the requested browser scope;
do not claim a multi-browser/full visual audit. If it fails, report the failure
before expanding browser reruns beyond the requested one pass.

Reuse guide must explain where the next CU adds schemas, its typed API adapter and
feature components, how it uses session selectors/cancellation and shared primitives,
what stays in the backend, and why it must not create another chat/store/HTTP client.

## Risks / Trade-offs

- [Late response rehydrates old account or clears new login] -> generation-aware
  interceptors, invalidation/unmount reset and delayed-response regression tests.
- [RHF defaults retain old domicile/version draft] -> preserve keyed revision reset
  and test switch, cancel, 409 and same-version discard cases.
- [Axios PDF errors become downloads or leak request config] -> MIME/size validation,
  bounded safe error decoding, no raw logging and injected-adapter negative tests.
- [Tailwind preflight or local components break labels/layout] -> preserve accessible
  names, real CU09 browser pass, keyboard/focus and narrow-layout checks.
- [Current versions differ from library documentation examples] -> registry pins,
  inspect installed help/source/type definitions and run strict locked checks.
- [Scope expands into CU03 or other CUs] -> reserved mount only; no chat runtime or
  provider dependencies, no new business endpoints, no persistent state.

## Migration Plan

After review and subsequent Apply: lock dependencies first, introduce primitives
and shell, add/test store and Axios policies, then migrate CU09 forms/adapter without
changing backend payloads. Keep feature boundaries and tests passing per stage;
serialize shared contracts. Review all generated diffs. Run final gates and the one
browser pass. No DB migration or deployment is needed. If implementation fails,
stop and repair within this scope; do not use git reset/revert to discard existing
uncommitted human work. No rollback of unrelated CU09 files is authorized.

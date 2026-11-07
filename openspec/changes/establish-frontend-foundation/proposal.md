# Proposal

## Why

CU09 currently combines layout, session state, forms and transport in a small
React implementation. Before adopting the other CUs, the user requests a reusable
frontend foundation so those concerns are shared without duplicating security,
backend business calculations or the future chat integration.

## What Changes

- Reuse the existing Vite/React/TypeScript application and preserved toolchain pins;
  do not scaffold a second application or replace the backend.
- Introduce Tailwind CSS and a small set of local, accessible shadcn/ui components.
- Use memory-only Zustand for shared session and domicile selection; use React Hook
  Form with Zod for CU09 forms, while backend validation remains authoritative.
- Centralize Axios requests/interceptors with HttpOnly cookie authentication,
  in-memory CSRF on authenticated writes, typed safe errors, cancellation and PDFs.
  Preserve U09 Origin-only login and do not synthesize the browser Origin header.
- Adapt CU09 first without changing its route payloads, ownership rules, timestamps,
  overlap calculations, conflict recovery or PDF behavior.
- Provide exactly one root-layout floating-chat mount, explicitly unavailable until
  CU03. No simulated assistant, LangChain connection, streaming or persistent memory.
- Document reuse and verify static/unit/security checks plus a single quick real
  browser pass through CU09 including downloaded PDF.

User authority: U09 in [decision register](../../../docs/use-cases/decisions.md).
The technology direction was approved before planning. U10 subsequently requested
Apply after artifact presentation. The implementation and actual verification are
recorded in the engineering record; this proposal itself is not execution evidence.

## Capabilities

### New Capabilities

- `frontend-shell`: shared accessible layout/components/form feedback, CU09 adoption,
  and a single visibly deferred chat integration point.
- `frontend-session-transport`: memory-only shared session state, account-scoped
  reset/cancellation, and centralized cookie/CSRF-safe Axios transport.

### Modified Capabilities

None. The main-spec inventory is empty. The active CU09 change supplies preserved
contracts and scenario oracles, not a main spec to modify or duplicate here.

## Impact

Planned affected files: `frontend/src/`, Vite/TypeScript configuration, a local
`components.json`, dependency manifests/lock, Docker allowlist/copy steps, tests,
README and frontend reuse documentation. No backend API/schema/storage migration,
auth-policy change, public exposure, new router framework, query cache, full CU04,
other-CU implementation, or chatbot runtime is included. No Archive/commit/push.

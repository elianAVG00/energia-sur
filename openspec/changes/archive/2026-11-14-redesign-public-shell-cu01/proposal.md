# Proposal

## Why

The shared shell is a bare `main` with one heading: navigation floats inside the
page body, "Cerrar sesión" sits inside the account view, and there is no page or
section hierarchy, footer or visual identity. CU01 mixes search and results in one
undifferentiated block. U26 D5 approved modernizing incrementally, shell plus CU01
first, using the approved light palette and the existing local shadcn/ui primitives
without new dependencies.

## What Changes

- Adopt the approved light visual system through semantic Tailwind tokens: primary
  `#0D6177`, background `#F8FAFC`, surface `#FFFFFF`, foreground `#0F172A`, system
  typography, visible focus and a centred container of about 1200 px.
- Introduce one shared shell: an identity header with horizontal, keyboard-operable
  navigation (Cortes, Trabajos, Mi cuenta and conditional Administración), a visible
  and accessible active section, a skip link, a titled `main` and a simple
  informational footer.
- Move the single "Cerrar sesión" control to the header, reusing the existing logout
  handler; remove the duplicated control from the account view while preserving the
  `Cuenta: {username}` text that tests rely on. Authentication, cookies, CSRF and
  session state are unchanged.
- Set the HTML document title to "Energía Sur".
- Stage B (implemented under U28) redesigns CU01's search form, results, states and
  provenance presentation as pure presentation, preserving every id, accessible name,
  control, service call and behavior.
- Leave the initial landing, CU02, CU04–CU10, the floating chat and all backend,
  HTTP, store and business logic untouched. The shared shell changes appearance
  everywhere but not functional content.

No **BREAKING** API, dependency or contract change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `frontend-shell`: the shared accessible application layout now requires header,
  main and footer landmarks, a 1200 px container and a skip link; three requirements
  are added for header navigation and logout placement, the citizen-facing visual
  system, and the informational footer. The no-technical-status rule is preserved.

## Impact

- Frontend: `frontend/src/styles.css` tokens; new
  `frontend/src/components/layout/SiteHeader.tsx` and `SiteFooter.tsx`;
  `frontend/src/layouts/AppLayout.tsx` shell; `frontend/src/App.tsx` navigation,
  logout placement, page titles and descriptions; minimal radius/spacing alignment
  in `frontend/src/components/ui/{button,card,input,table}.tsx` without interface or
  behavior changes; `frontend/index.html` title.
- Stage B (implemented under U28): `frontend/src/features/outages/OutagesPanel.tsx`
  and a presentational `OutagesResultCard.tsx`; no `api.ts`, `state.ts`,
  geolocation, validation or HTTP change.
- Tests and evidence: new `frontend/e2e/redesign-shell.spec.ts` and
  `frontend/e2e/visual-capture.spec.ts`; before/after screenshots under
  `docs/ai-engineering/evidence/redesign-public-shell-cu01/`.
- Documentation: `README.md`, `docs/frontend-foundation.md`, `docs/STATE.md`,
  decision U27 and `docs/ai-engineering/redesign-public-shell-cu01.md`.
- Unchanged: backend, endpoints, HTTP services, Zustand stores, auth transport,
  CU01–CU10 business behavior, the single `ChatMount`, active OpenSpec changes and
  all dependencies/manifests.

## Out of scope

CU02, CU04–CU10, the floating chat redesign, the initial landing, backend/auth,
and any archive, commit or push. Stage B (CU01) is no longer out of scope: it was
authorized by U28 and implemented.

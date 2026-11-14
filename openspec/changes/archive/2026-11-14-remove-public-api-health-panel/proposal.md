# Proposal

## Why

The shared root layout currently renders a technical "Conexión con la API" panel on
every Energía Sur view: public outage and works screens, the account/login screen and
the administrative screen. The panel exposes an internal health check, a raw JSON
response, a manual re-check button and development-only wording to citizens and
administrators, and it issues an unnecessary `/api/health` request on every layout
mount. Technical backend status is an infrastructure concern and must not be part of
the user-facing product.

## What Changes

- Remove the visible API health panel from the component tree. It is not hidden with
  CSS: the component stops being mounted by the shared layout.
- Delete the health panel component, its dedicated fetch/state modules and its
  exclusive unit tests, after confirming that no other module consumes them.
- Stop the automatic `/api/health` request that only existed to feed the panel. The
  `GET /health` backend endpoint, the Vite `/api` proxy and the technical PowerShell
  verification scripts remain available and unchanged in behavior for HTTP, Docker and
  diagnostic use; only the obsolete closing message of `Test-HealthProxy.ps1` no longer
  points to a removed browser step.
- Reconcile the accepted frontend shell requirement so it no longer demands a visible
  health panel, and correct the `Real frontend health display and failure state`
  requirement inside the still-active `docker-development-environment` change so its
  acceptance is expressed as HTTP verification of the retained endpoint.
- Record the product decision (U26) that technical backend status is not shown in
  public, authenticated or administrative views.

Out of scope: the visual redesign (header, navigation, chat launcher, CU01 layout),
backend behavior, API contracts, authentication/CSRF/cookies, Zustand state, Zod
schemas, assistant functionality and CU01–CU10 business behavior.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `frontend-shell`: the shared accessible application layout no longer requires nor
  renders a technical API health panel, while keeping its accessible controls, visible
  focus, loading/error states and narrow-viewport usability.

## Impact

- Frontend: `frontend/src/layouts/AppLayout.tsx` stops mounting the panel;
  `frontend/src/HealthPanel.tsx`, `frontend/src/health.ts` and
  `frontend/src/healthState.ts` are removed together with
  `frontend/tests/health.test.ts` and `frontend/tests/healthState.test.ts`;
  `frontend/src/styles.css` loses the panel-only style block.
- Specifications: `frontend-shell` main spec delta in this change; the
  `development-environment` requirement inside the active
  `docker-development-environment` change is adjusted without archiving it or
  completing its open tasks.
- Unchanged: backend `/health`, Vite proxy, Compose services, the health checks in
  `scripts/*.ps1`, session/auth transport, Zustand stores, Zod schemas, the
  assistant runtime and all CU01–CU10 HTTP contracts. `Test-HealthProxy.ps1` keeps its
  success/failure/restore checks; only its final message, which referenced the removed
  browser step, is corrected.

# Proposal

## Why

The approved visual system and the CU01 redesign modernized the public shell and the
outages screen, but CU02 (scheduled works) and CU10 (source administration) still use
the previous dense presentation: mixed forms, plain definition lists, undifferentiated
states and destructive styling for informational limitations. The result is visually
inconsistent with the rest of the citizen portal and harder to scan, especially on
narrow viewports.

## What Changes

- Redesign the public CU02 "Trabajos" view as presentation only, reusing the approved
  palette, local shadcn/ui primitives and the CU01 visual patterns.
- Split the CU02 search into a primary "Consultar trabajos" card and a secondary
  "Buscar por dirección" card; add an initial-state panel and a presentational result
  card with state chips, a zone/scope panel, the existing works table and a provenance
  panel.
- Show planned start/end as "No publicado" when the source does not publish them, and
  keep the existing "No publicado por la fuente" reason text. Do not add date inputs or
  temporal filters.
- Redesign the CU10 administrative view as presentation only: one card per ENRE source,
  clearer status hierarchy, explicit error and lock-contention presentation, and grouped
  configuration and retry controls.
- Preserve every id, label, accessible name, message, handler, validation, HTTP request,
  geolocation call, Zustand behavior and API contract.
- Keep M2 (duplicate aria-live announcements), M3 (shared table region label), the
  floating-assistant overlay and the stale/unavailable totals presentation out of scope.

No **BREAKING** API, dependency or contract change.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `scheduled-works`: the public view requirement now specifies the redesigned
  search/address/result hierarchy, explicit unpublished dates and reasons, distinct
  states and responsive/accessible presentation, while keeping the no-date-filter rule.
- `source-refresh-administration`: the minimal admin-only view requirement now specifies
  per-source status hierarchy, explicit error and lock-contention presentation, grouped
  controls and the existing retry/interval behavior.

## Impact

- Frontend CU02: `frontend/src/features/scheduled-works/ScheduledWorksPanel.tsx` and a
  new presentational `ScheduledWorksResultCard.tsx`.
- Frontend CU10 (Stage B, implemented under U30):
  `frontend/src/features/admin/AdminPanel.tsx` and a presentational `SourceCard.tsx`.
- Tests: `frontend/e2e/cu02.spec.ts`, `frontend/e2e/cu10.spec.ts`,
  `frontend/e2e/redesign-works-admin.spec.ts` and a gated
  `frontend/e2e/visual-capture-works-admin.spec.ts`.
- Documentation: `README.md`, `docs/STATE.md`, `docs/use-cases/decisions.md` and
  `docs/ai-engineering/redesign-public-works-admin.md`.
- Unchanged: backend, `features/*/api.ts`, `features/*/state.ts`, `lib/http*`, Zustand
  stores, authentication/CSRF, the shared shell and layout, CU01, CU03, CU04-CU09, the
  landing view, the floating assistant, dependencies and active OpenSpec changes.

## Approval and execution boundary

U29 records the approved interpretation A: presentation-only redesign, no date filters
and no invented dates. U29 authorized Stage 0 (preparation) and Stage A (CU02); U30
authorized Stage B (CU10). Both stages are implemented as presentation only. No commit,
push or archive is authorized.

# Tasks

## 1. Preparation and evidence

- [x] 1.1 Confirm `main` is clean at `33786cf`, the two active changes (`docker-development-environment`, `configure-readonly-development-mcp`) are untouched, and record the verified `git status`/`git log` output in the engineering record.
- [x] 1.2 Add `frontend/e2e/visual-capture.spec.ts`, gated by `VISUAL_CAPTURE=1` and `VISUAL_DIR`, with synthetic mocks for login, Cortes (initial and reported result) and Trabajos at 1440×900, 820×1180 and 390×844; verify it runs only with the flag and writes the expected files.
- [x] 1.3 Capture the "before" screenshots from the unmodified tree into `docs/ai-engineering/evidence/redesign-public-shell-cu01/before/`; verify no real credentials or personal data appear.
- [x] 1.4 Record decision U27 in `docs/use-cases/decisions.md` (Stage A/Stage B split, tokens, header logout, unchanged landing) and note the `dashboard-01` adaptation in the engineering record.

## 2. Visual system (Stage A)

- [x] 2.1 Replace the `@theme` palette in `frontend/src/styles.css` with the approved tokens and keep `system-ui` typography, light mode and visible focus; verify with `npm run build` and a DOM token check.
- [x] 2.2 Align radius, spacing and header treatment in `frontend/src/components/ui/{button,card,input,table}.tsx` only where needed, without changing props, exports or behavior; verify their existing consumers still typecheck and unit tests pass.
- [x] 2.3 Compute contrast ratios for primary/background/surface/foreground and record them in `docs/ai-engineering/redesign-public-shell-cu01.md`; verify every recorded ratio meets WCAG AA for its usage.

## 3. Shared shell (Stage A)

- [x] 3.1 Implement `frontend/src/components/layout/SiteHeader.tsx` (identity, horizontal nav slot, active `aria-current`, conditional Administración, one logout button) and verify keyboard order, visible focus and wrapping at 390 px.
- [x] 3.2 Implement `frontend/src/components/layout/SiteFooter.tsx` with static identity and public source note, no technical/environment/session detail; verify the footer text in the rendered page.
- [x] 3.3 Rewrite `frontend/src/layouts/AppLayout.tsx` with skip link, header slot, `main#contenido` at about 1200 px, `PageHeader` (single `h1` + optional description), footer and the single unchanged `ChatMount`; verify one `h1` per view and no chat overlap.
- [x] 3.4 Update `frontend/src/App.tsx` to render navigation and the existing logout handler in the header, remove the duplicate logout from the account view, keep `Cuenta: {username}`, and supply view titles/descriptions; verify login, anonymous navigation and admin-only visibility.
- [x] 3.5 Set the document title in `frontend/index.html` to "Energía Sur"; verify the browser tab and `npm run build`.

## 4. Shell verification (Stage A)

- [x] 4.1 Add `frontend/e2e/redesign-shell.spec.ts` covering landmarks, active section, admin-only Administración, exactly one logout and its effect, skip link, no `/api/health` request, single chat mount and no horizontal overflow at 390/820/1440 px; verify the suite passes.
- [x] 4.2 Run typecheck, lint, unit tests and build in the pinned verification image; record PASS/FAIL evidence and investigate any failure for regression versus pre-existing cause.
- [x] 4.3 Run focused mocked Playwright regressions for navigation, account and shell (`cu01`, `cu02`, `cu03`, `cu03-auth`, `cu05-history`, `cu10`, `redesign-shell`) and record results.
- [x] 4.4 Run `openspec validate --all --strict`; verify every artifact and merged spec passes, including requirement lengths under 500 characters.
- [x] 4.5 Perform a manual keyboard/focus/contrast pass on desktop, tablet and mobile widths and record the observations.
- [x] 4.6 Capture the "after" screenshots with the same spec, viewports and data; verify they correspond to the "before" set and add the side-by-side comparison table to the engineering record.

## 5. Documentation and closure (Stage A)

- [x] 5.1 Update `README.md`, `docs/frontend-foundation.md` and `docs/ai-engineering/redesign-public-shell-cu01.md` with the shell, token and verification changes; verify links and commands are accurate.
- [x] 5.2 Update `docs/STATE.md` (≤60 lines) with the last verified result, active change link, blockers and next actions; verify the line count.
- [x] 5.3 Request an independent read-only review from `reviewer` over accessibility, security and regressions; record findings and corrections, and leave any mandatory review blocking issue open. Two rounds: all prior findings resolved; the final LOW items (stale error on view change, 43/43 vs 44/44 count) were corrected and re-checked.

## 6. CU01 redesign (Stage B)

- [x] 6.1 Restructure the CU01 search card in `frontend/src/features/outages/OutagesPanel.tsx` while preserving ids, labels, accessible names, status/error messages and handlers; verify `cu01.spec.ts` passes. Two cards were introduced: "Consultar cortes" (zone filter, partido, localidad, `Consultar cortes`, `Usar mi ubicación`) and "Buscar por dirección" (address, `Buscar dirección`, privacy note, candidates). Ids `outage-filter`, `outage-partido`, `outage-localidad` and `outage-address` are unchanged, as are labels, accessible names, all state/handlers and every message. `cu01.spec.ts` 14/14 (three later cases add state, loading and address-feedback coverage).
- [x] 6.2 Add presentational `frontend/src/features/outages/OutagesResultCard.tsx` (state chips, stat tiles, provenance panel, table) reusing `state.ts`; verify headings, provenance and table labels stay test-compatible. The component receives the validated `OutagesResult`, reuses `stateHeading`/`stateDetail`/`coverageLabel`/`freshnessLabel`/`categoryLabel`/`formatInstant`/`formatReportedTime`, keeps `aria-live="polite"`, all alert texts and the Edesur-wide totals caveat, and adds `scope="col"` without new data or indicators. `cu01.spec.ts` headings/provenance assertions pass unchanged.
- [x] 6.3 Verify the result and feedback states at desktop/tablet/mobile widths and confirm no horizontal overflow; record results. Regular `cu01.spec.ts` cases exercise reported, coverage-unverified and unavailable states at 390/820/1440 px (zero document overflow), plus no-reports, loading and address-error feedback at 390 px; the table scroll region is focused and confirmed to scroll internally at 390 px, and the address error is asserted in-card and in view. Gated `frontend/e2e/visual-capture-cu01-states.spec.ts` (desactualizado, cobertura no verificada, fuente no disponible, candidatas) writes 12 state captures to `docs/ai-engineering/evidence/redesign-public-shell-cu01/stage-b/`.
- [x] 6.4 Audit `frontend/src/features/outages/{api,state}.ts`, geolocation, validation, `lib/http*` and stores for zero changes, and record the diff evidence. `git status`/`git diff` show no changes in those paths, `frontend/src/stores/`, `backend/`, manifests, CU02–CU10 features or the assistant. Independent-review correction: two presentation-only scope flags (`errorScope`, `messageScope`) in the panel route the existing texts next to the form that produced them; no handler result, message string or request changed.

## 7. Stage B verification and review

- [x] 7.1 Run typecheck, lint, unit tests, build, the focused Playwright set (including the new no-reports, loading and address-feedback cases), the gated evidence captures and strict OpenSpec validation in the pinned verification image; record PASS/FAIL evidence. Results: 117/117 unit, 47/47 Playwright, 6/6 capture runs, 16/16 strict.
- [x] 7.2 Request an independent read-only review from `reviewer` over regressions, accessibility, visual consistency, responsiveness, presentation/logic separation and scope; correct the findings related to this implementation and re-verify the affected gates. Findings M1, M4, M5, M6 and L1–L4 were corrected and re-verified; pre-existing M2, M3 and the remaining LOW items are recorded as deferred.

## Workflow follow-up

- Stage B was authorized by the user's 2026-11-14 Stage B instruction (recorded as U28) and is implemented; tasks 6.1–6.4 and 7.1–7.2 are complete.
- Commit, push and archive remain unauthorized; archive only after the human review of this delivery.

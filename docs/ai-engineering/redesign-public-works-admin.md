# Redesign public works and admin views

## Goal and scope

Implement the approved `redesign-public-works-admin` change. This execution covers
Stage 0 (preparation), Stage A (CU02 scheduled works) and Stage B (CU10 source
administration).

- Archived change: `openspec/changes/archive/2026-11-14-redesign-public-works-admin/`
  (proposal, design, deltas for `scheduled-works` and
  `source-refresh-administration`, tasks).
- Decisions: [U29](../use-cases/decisions.md#u29---cu02-visual-redesign-stage-a-and-stage-b-proposal-authorization)
  for Stage A and [U30](../use-cases/decisions.md#u30---cu10-visual-redesign-stage-b-authorization)
  for Stage B.
- Evidence: [`evidence/redesign-public-works-admin/`](evidence/redesign-public-works-admin/).

## Approval and instructions

The user approved interpretation A: presentation-only redesign. No date filters, no
invented planned dates or reasons. Preserve ids, labels, accessible names, messages,
handlers, geolocation, requests and API contracts. Do not touch backend, `api.ts`,
`state.ts`, `lib/http*`, stores, auth/CSRF, CU01-CU09, shell/layout or dependencies.
U30 authorizes the CU10 presentation layer only: no new administrative capability,
endpoint, role, enablement, backoff, polling or data-entry tool. Run an independent
read-only review for each stage and stop before commit, push or archive.

## Repository state

`main` at `223a61c351a64cc63fca5c8659fa6415752b7bbb`, clean working tree before this
change. The two active changes (`docker-development-environment`,
`configure-readonly-development-mcp`) are untouched. A read-only
`git ls-remote origin refs/heads/main` returned the same commit and
`origin/main == HEAD`, so the commit is already on the remote even though the prior
STATE note said "nothing pushed". This record corrects the fact and performs no push
or history change.

## Work performed

| Area | Result |
| --- | --- |
| OpenSpec | New change with proposal, design, two capability deltas and tasks; strict validation passes 16/16. |
| Capture harness | New `frontend/e2e/visual-capture-works-admin.spec.ts`, gated by `VISUAL_CAPTURE=1` and `VISUAL_DIR`, with synthetic CU02/CU10 mocks; skips 6/6 without the flag. |
| Baseline | `before/` captures at 1440×900, 820×1180 and 390×844: six CU02 scenes and two CU10 scenes (24 PNGs). |
| Search cards | `ScheduledWorksPanel.tsx` now renders "Consultar trabajos" (zone filter, partido/localidad, primary query, device location, loading/error/zone feedback) and "Buscar por dirección" (address, button, unchanged privacy note, feedback and candidate zones). |
| Result card | New `ScheduledWorksResultCard.tsx`: state heading, granularity/coverage/freshness chips, existing alerts, zone/scope panel with unpublished planned dates, five-column works table, scroll hint and provenance. |
| Presentation routing | `errorScope` and `messageScope` route the existing `error`/`searchMessage` strings to the card that produced them. No handler, request or message string changed. |
| Accessibility | Labels, `aria-describedby` for filter/address help, `aria-labelledby` for candidate zones, `scope="col"`, focusable table region, visible focus and one `h1`. No new live region. |
| Tests (Stage A) | `cu02.spec.ts` keeps its five original cases and adds nine (scope/dates/provenance, stale+degraded, unverified coverage, loading/query error, address error, no-works/unverified date omission, denied geolocation, resolved-address feedback, 390 px table). New `redesign-works-admin.spec.ts` adds five cross-cutting CU02 cases. |
| Admin cards (Stage B) | `AdminPanel.tsx` keeps state/handlers and delegates presentation to a new `SourceCard.tsx` with "Estado", "Configuración" and "Acciones" sections, status chips and compact status fields. |
| Admin feedback routing | Feedback keeps its exact strings and gains a presentation-only `action` flag: interval results render under "Configuración" and retry results under "Acciones". |
| Admin states | Chips distinguish automatic scheduling enabled/disabled and last attempt successful/failed/none. A failed attempt shows its error and keeps the previous `last_success_at`; lock contention remains visible. |
| Admin contracts | `interval-outages`/`interval-scheduled_works`, accessible names, five intervals, optimistic version, 25-second retry, 401/403/409/422/timeout, reloads and no polling are unchanged. |
| Tests (Stage B) | `cu10.spec.ts` keeps its nine original cases and adds six (card hierarchy/only-existing-controls/no-polling, failed retry after a prior success, no attempts plus lock contention, conflict-feedback routing, invalid interval, mobile/tablet/desktop layout). `redesign-works-admin.spec.ts` adds the CU10 shell/palette/overflow case. |

No backend, `features/*/api.ts`, `features/*/state.ts`, `lib/http*`, store, auth,
shell/layout or manifest file changed. Stage B changed only `AdminPanel.tsx` and the new
presentational `SourceCard.tsx` under `features/admin/`.

## Before / after

| Scene | Before | After |
| --- | --- | --- |
| CU02 initial, desktop | [`before/cu02-inicial-desktop.png`](evidence/redesign-public-works-admin/before/cu02-inicial-desktop.png) | [`etapa-a/cu02-inicial-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-inicial-desktop.png) |
| CU02 reported, desktop | [`before/cu02-resultado-desktop.png`](evidence/redesign-public-works-admin/before/cu02-resultado-desktop.png) | [`etapa-a/cu02-resultado-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-resultado-desktop.png) |
| CU02 reported, mobile | [`before/cu02-resultado-mobile.png`](evidence/redesign-public-works-admin/before/cu02-resultado-mobile.png) | [`etapa-a/cu02-resultado-mobile.png`](evidence/redesign-public-works-admin/etapa-a/cu02-resultado-mobile.png) |
| CU02 stale/degraded, desktop | [`before/cu02-desactualizado-desktop.png`](evidence/redesign-public-works-admin/before/cu02-desactualizado-desktop.png) | [`etapa-a/cu02-desactualizado-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-desactualizado-desktop.png) |
| CU02 no works | [`before/cu02-sin-trabajos-desktop.png`](evidence/redesign-public-works-admin/before/cu02-sin-trabajos-desktop.png) | [`etapa-a/cu02-sin-trabajos-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-sin-trabajos-desktop.png) |
| CU02 unverified coverage | [`before/cu02-cobertura-no-verificada-desktop.png`](evidence/redesign-public-works-admin/before/cu02-cobertura-no-verificada-desktop.png) | [`etapa-a/cu02-cobertura-no-verificada-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-cobertura-no-verificada-desktop.png) |
| CU02 query error | [`before/cu02-error-consulta-desktop.png`](evidence/redesign-public-works-admin/before/cu02-error-consulta-desktop.png) | [`etapa-a/cu02-error-consulta-desktop.png`](evidence/redesign-public-works-admin/etapa-a/cu02-error-consulta-desktop.png) |

The `before/` set also keeps the CU10 normal and failed-attempt captures. `etapa-a/`
contains only the 18 CU02 captures; `etapa-b/` contains the six CU10 captures. The
pre-change no-works baseline was captured with the earlier evidence fixture that omitted
the limitation array; the Stage A no-works capture uses the contract-valid fixture, so
only the latter reflects the mandatory limitation alerts.

| CU10 scene | Before | After |
| --- | --- | --- |
| Normal, desktop | [`before/cu10-normal-desktop.png`](evidence/redesign-public-works-admin/before/cu10-normal-desktop.png) | [`etapa-b/cu10-normal-desktop.png`](evidence/redesign-public-works-admin/etapa-b/cu10-normal-desktop.png) |
| Normal, mobile | [`before/cu10-normal-mobile.png`](evidence/redesign-public-works-admin/before/cu10-normal-mobile.png) | [`etapa-b/cu10-normal-mobile.png`](evidence/redesign-public-works-admin/etapa-b/cu10-normal-mobile.png) |
| Failed attempt + prior success + lock contention, desktop | [`before/cu10-error-desktop.png`](evidence/redesign-public-works-admin/before/cu10-error-desktop.png) | [`etapa-b/cu10-error-desktop.png`](evidence/redesign-public-works-admin/etapa-b/cu10-error-desktop.png) |
| Failed attempt + prior success + lock contention, mobile | [`before/cu10-error-mobile.png`](evidence/redesign-public-works-admin/before/cu10-error-mobile.png) | [`etapa-b/cu10-error-mobile.png`](evidence/redesign-public-works-admin/etapa-b/cu10-error-mobile.png) |

| Aspect | Before | After |
| --- | --- | --- |
| Card hierarchy | Title, plain meta line and one `<dl>` | Title, status chips, "Estado", "Configuración" and "Acciones" |
| Status | Plain rows | Compact tiles plus automatic/attempt chips |
| Failure | Destructive alert mixed with all fields | Error panel and failed chip, with the prior success still shown separately |
| Controls | Inline select/save and retry at the bottom | Grouped configuration and action sections, full-width on mobile |
| Feedback | One block at the end of the card | Save feedback under "Configuración", retry feedback under "Acciones" |
| Mobile | Single dense card | Cards stack; controls and buttons full width; no document overflow |

| Aspect | Before | After |
| --- | --- | --- |
| Form hierarchy | One card mixing zone, actions and address | Primary "Consultar trabajos" plus secondary "Buscar por dirección" |
| Controls | Inline, compressed on mobile | Two-column grid at ≥640 px; stacked full-width inputs/buttons on mobile |
| Result | Plain meta line, plain list, plain table | State chips, scope panel, treated table and provenance panel |
| Dates | Not identified | "Inicio/Fin planificado: No publicado" with an explicit source-limitation note |
| States | Same texts, undifferentiated weight | Neutral/attention/critical chips; no green success or local claim |
| Mobile table | Cells wrapped | Internal horizontal scroll with focusable region and hint |
| Feedback | At the bottom of the only card | Query feedback with the search card, address feedback with its card |

## Problems and corrections

1. **Stale Vite module graph (repeated).** The first post-change test run still served
   the old panel: the new result card and chips were absent. `docker restart
   energia-sur-frontend-1` was required; a DOM probe then showed the new classes and
   width. No test was changed to accommodate the stale build.
2. **Strict-locator collision.** The first result card used
   "Detalle de trabajos informados" as an `h3`, which made the existing
   `getByRole('heading', { name: 'Trabajos informados' })` resolve to two elements.
   Renamed to "Listado de trabajos"; existing tests were not edited.
3. **Mock error detail.** The new error test initially returned `detail: "unavailable"`,
   which the HTTP client displays instead of the status fallback. The mock now returns a
   realistic source-error detail and the test asserts that text.
4. **Pre-existing duplicate stale copy.** The stale state description and the freshness
   alert both contain "La última actualización tiene más de 15 minutos". The new test uses
   `.first()` and the duplication remains documented as a deferred accessibility item.
5. **Duplicate evidence.** The gated capture run also wrote unchanged CU10 images to
   `etapa-a/`; they were removed. CU10 stays in `before/` until Stage B.
6. **Degraded-source label.** The old meta text "Sincronización con errores" is presented
   as the CU01-consistent chip "Fuente degradada". The condition, the degraded alert and
   the rest of the result are unchanged; this is a presentational label harmonization,
   recorded here as requested by the reviewer.

## Repository scope

`git status --porcelain=v1 -uall` shows only:
- modified `README.md`, `docs/STATE.md`, `docs/use-cases/decisions.md`,
  `frontend/e2e/cu02.spec.ts`, `frontend/e2e/cu10.spec.ts`,
  `frontend/src/features/scheduled-works/ScheduledWorksPanel.tsx` and
  `frontend/src/features/admin/AdminPanel.tsx`;
- new `ScheduledWorksResultCard.tsx`, `SourceCard.tsx`,
  `redesign-works-admin.spec.ts`, `visual-capture-works-admin.spec.ts`, this record;
- the OpenSpec change and the evidence PNGs.

`git diff` is empty for `backend/`, `features/scheduled-works/api.ts`,
`features/scheduled-works/state.ts`, `features/admin/api.ts`, `features/admin/state.ts`,
`features/outages/`, `components/ui/`, `layouts/`, `App.tsx`, `package.json`,
`package-lock.json`, the shell and the two active changes.

## Checks and results

Environment: verification image `energia-sur-frontend-checks:works-admin-b`
(`sha256:fbb70ea1883e576f7004cf36889641991deb5a224e6523e65e7a79c1c0bcc68f`),
pinned Node `v24.22.2` / npm `11.19.1`, Playwright Chromium, frontend service healthy
at `127.0.0.1:5173`, 2026-11-14.

```powershell
docker restart energia-sur-frontend-1
docker exec energia-sur-frontend-1 npm run typecheck
docker exec energia-sur-frontend-1 npm run lint
docker exec energia-sur-frontend-1 npm test
docker exec energia-sur-frontend-1 npm run build
docker run --rm --network host -e E2E_BASE_URL=http://127.0.0.1:5173 `
  energia-sur-frontend-checks:works-admin-b `
  npx playwright test e2e/cu01.spec.ts e2e/cu02.spec.ts e2e/cu03.spec.ts `
  e2e/cu03-auth.spec.ts e2e/cu05-history.spec.ts e2e/cu10.spec.ts `
  e2e/redesign-shell.spec.ts e2e/redesign-works-admin.spec.ts
openspec validate --all --strict --no-interactive
```

| Check | Result | Evidence |
| --- | --- | --- |
| Typecheck | PASS | `npm run typecheck`, no diagnostics |
| Lint | PASS | 0 warnings, 0 errors, 101 files |
| Unit tests | PASS | 117/117 |
| Build | PASS | Vite build completed (333 modules); only the Radix `use client` notice |
| CU02 Playwright | PASS | 14/14 (5 original + 9 new) |
| CU10 Playwright | PASS | 15/15 (9 original + 6 new) |
| Focused regressions | PASS | 68/68: CU01 14, CU02 14, CU03 1, CU03-auth 2, CU05-history 9, CU10 15, shell 7, works/admin 6 |
| OpenSpec strict | PASS | 16/16 items, including the new change |
| Capture spec | PASS | 6/6 viewport runs; 24 before, 18 Stage A and 6 Stage B PNGs |
| Responsive | PASS | Zero document overflow at 390/820/1440 for CU02 and CU10; CU02 table scrolls internally; CU10 cards stack on mobile and use two columns at 1440 |
| Stage A independent review | CHANGES REQUESTED, corrected | Static read-only review found no BLOCKER/HIGH; F1/F2/F5/F9/F10 were corrected and re-verified, F3 was resolved by design wording, F4/F6/F8 were recorded, and F7 was already fixed before the review. See the findings table below. |
| Stage B independent review | CHANGES REQUESTED, corrected | Static read-only review found no BLOCKER/HIGH; the no-polling coverage, neutral configuration chip and documentation coherence items were corrected/re-verified. See the Stage B findings below. |
| Real CU02 source / CU10 real / QA-INT-CU04-08 | NOT APPLICABLE in this stage | Mocked UI acceptance only; QA-INT-CU04-08 remains deferred |

### Independent review findings

The reviewer worked statically without shell/git/runtime access, so parts of its report
described the pre-correction tree. Each finding was checked against the current files:

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| F1 | MEDIUM | `etapa-a` no-works/unverified captures were said not to match the card. | The current card omits planned fields when there are no works; the captures now match that conditional rendering. A new automated case asserts the absence in both states. |
| F2 | MEDIUM | The capture fixture used `limitations: []` for no-works. | The fixture now carries the contract-valid `dates_not_published`, `reason_not_published` and `proximity_not_available`; `etapa-a` was recaptured. |
| F3 | LOW | Design said planned instants are never read, while the card reads them. | Design D3 now states that published values are shown and null values render as "No publicado"; no inventing. |
| F4 | LOW | The old "Sincronización con errores" label became "Fuente degradada". | Recorded as a presentational harmonization; the condition and degraded alert are unchanged. |
| F5 | LOW | Address-origin "Zona resuelta" feedback rendered in the query card. | `applyZone` now receives an origin; address resolution/candidates render in the address card, geolocation in the query card. A new case covers it. |
| F6 | LOW | The result card adds content inside the existing `aria-live`. | Documented as a slight worsening of deferred M2; not fixed in this change. |
| F7 | LOW | Tests entrenched the M3 "Cortes registrados" label. | Tests select `[data-slot="table-container"]`; no label is asserted. |
| F8 | LOW | At 390 px the added description moves "Usar mi ubicación" closer to the assistant overlay. | Documented as a pre-existing overlay issue for the separate accessibility change. |
| F9 | LOW | Some copied geolocation/area/429 branches had no CU02 tests. | Added denied-geolocation, resolved-address feedback and no-works/unverified date cases; the remaining branches are unchanged CU01-pattern code and are recorded as residual coverage. |
| F10 | LOW | Tasks, README, STATE and evidence coherence. | Tasks checked only for completed work, the record exists, README links it, STATE was rewritten and the CU10 evidence exemption is documented. |

### Stage B independent review findings

| ID | Severity | Finding | Resolution |
| --- | --- | --- | --- |
| B1 | MEDIUM | The checked no-polling task had no matching test. | The current hierarchy test records the initial status GET count, waits 300 ms and asserts it did not change; it passes in the focused suite. The reviewer had read the pre-correction tree. |
| B2 | LOW | The scheduler-enabled chip used the attention tone reserved for verified success. | The configuration chip is now always neutral; a new assertion checks `bg-muted` and rejects `bg-accent`, and the failure capture uses an enabled+failed source so the neutral/critical contrast is visible. |
| B3 | LOW | STATE, record, proposal, design and tasks still described Stage B as unauthorized or pending. | STATE, record, proposal, design, tasks and U30 were reconciled; no future-tense Stage B text remains. |
| B4 | LOW | Accessible names and save-disabled behavior might have changed. | Confirmed pre-existing from the `AdminPanel.tsx` diff: the same `aria-label` values and `disabled={busy.save || !changed}` were already present. No change was introduced. |
| B5 | LOW | 401 and 422 paths lacked Stage B tests. | The 422 save path is now covered in the configuration section. The 401 path is the pre-existing global session-expiry behavior (the store clears the session and the admin view unmounts), not a CU10-specific message contract; it remains covered by the existing session/auth checks. |

## Limitations

- The comparison is manual, not a pixel-diff baseline.
- No screen-reader session was run; semantics rely on landmarks, labels, roles and
  keyboard/overflow checks.
- Mocked API data only; no live ENRE query, no real admin session and no real backend
  acceptance in either stage.
- M2 (result announcement/duplicate stale copy), M3 (shared table region label),
  the floating-assistant overlay and totals on stale/unavailable snapshots are
  pre-existing and unchanged. The result card adds content inside the existing
  `aria-live` section, so the deferred M2 announcement is slightly longer. At 390 px the
  added query-card description moves "Usar mi ubicación" closer to the fixed assistant
  panel; the overlay itself remains out of scope for a separate accessibility change.
- Stage B (CU10) is implemented as presentation only. Commit, push and archive were not
  performed.

## Stage B — CU10 verification

U30 authorized the presentation-only CU10 redesign. The change was archived after the
gates below; the CU10 presentation is part of the archived delivery. `AdminPanel.tsx` now owns the
existing state/handlers and delegates presentation to `SourceCard.tsx`; `cu10.spec.ts`
keeps its nine original cases and adds six, and `redesign-works-admin.spec.ts` adds the
CU10 shell/palette/overflow case. The six synthetic `etapa-b/` captures cover normal,
failed-attempt (with previous success and lock contention) and the three viewports.

The Stage B independent reviewer returned no BLOCKER/HIGH. Its no-polling coverage,
configuration-chip tone and documentation-coherence findings were corrected and the
affected tests rerun; the 401 note and remaining coverage limits are recorded above.

## Closure

Archived on 2026-11-14 as `2026-11-14-redesign-public-works-admin`. The two deltas were
synchronized into `openspec/specs/scheduled-works/spec.md` and
`openspec/specs/source-refresh-administration/spec.md` (0 added, 2 modified, 0 removed);
strict validation passes 15/15 after archive. The CU02/CU10 implementation, tests,
evidence, documentation and archived change are included in one local commit. Nothing
was pushed or deployed. M2, M3, the assistant overlay, totals on stale/unavailable data,
QA-INT-CU04-08 and the real CU10 administrator E2E remain outside this closure.

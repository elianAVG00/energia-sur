# Redesign public shell and visual system (Stages A and B)

## Goal and scope

Implement the approved `redesign-public-shell-cu01` change. The first execution
covered Stage A only: the shared public shell, the visual tokens and the
navigation/logout placement. Stage B (CU01 search, results and states) was
authorized later (U28) and implemented in this second execution; it is recorded
in [Stage B](#stage-b--cu01-redesign-implemented) below. Stage A was preserved
unchanged.

- Change: `openspec/changes/archive/2026-11-14-redesign-public-shell-cu01/` (proposal,
  design, delta spec for `frontend-shell`, tasks; archived 2026-11-14).
- Decision: [U27](../use-cases/decisions.md#u27---public-shell-and-visual-system-stage-a-authorization),
  following U26 D1–D7.
- Evidence: [`evidence/redesign-public-shell-cu01/`](evidence/redesign-public-shell-cu01/).

## Approval and instructions

The user approved the plan and restricted this BUILD to Stage A: tokens, shared
layout, header/navigation/logout, footer, page titles/descriptions, before/after
captures, quality gates and documentation. The user required preserving
`Cuenta: {username}`, a single `ChatMount`, no backend/HTTP/store/business changes,
no new dependencies, no CU01 redesign, and no commit, push or archive.

## Work performed

| Area | Result |
| --- | --- |
| Tokens | `frontend/src/styles.css` now defines the approved light palette (`#0D6177`, `#F8FAFC`, `#FFFFFF`, `#0F172A`), system typography, visible focus and derived secondary/muted/accent/border/input tokens. |
| Header | New `frontend/src/components/layout/SiteHeader.tsx`: Energía Sur identity, horizontal nav slot, active `aria-current="page"`, conditional Administración and one `Cerrar sesión` button reusing the existing handler. |
| Footer | New `frontend/src/components/layout/SiteFooter.tsx`: portal identity plus "Cortes y trabajos: datos públicos del ENRE.", no API/environment/session detail. |
| Layout | `frontend/src/layouts/AppLayout.tsx`: skip link, sticky header, `main#contenido` at about 1200 px, single `h1` with description, footer, single unchanged `ChatMount`. |
| Navigation | `frontend/src/App.tsx`: nav moved into the header, logout removed from the account view, `Cuenta: {username}` preserved, per-view titles and descriptions added. |
| Primitives | Only `TableHead` gained a muted header background; no prop, export or behavior change. No shadcn reinstall. |
| Document title | `frontend/index.html` title changed to "Energía Sur". |

No backend, `features/*/api.ts`, `state.ts`, `lib/http*`, `diary*`, stores, auth,
geolocation or business logic changed.

## Before / after comparison

Repository state: `main` at `33786cf`, working tree clean before the change; the two
active OpenSpec changes were not touched. Synthetic mocks only; no real credentials,
addresses or bills.

| Viewport | Before | After |
| --- | --- | --- |
| Desktop 1440×900 | [`before/cortes-inicial-desktop.png`](evidence/redesign-public-shell-cu01/before/cortes-inicial-desktop.png) | [`after/cortes-inicial-desktop.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-desktop.png) |
| Tablet 820×1180 | [`before/cortes-inicial-tablet.png`](evidence/redesign-public-shell-cu01/before/cortes-inicial-tablet.png) | [`after/cortes-inicial-tablet.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-tablet.png) |
| Mobile 390×844 | [`before/cortes-inicial-mobile.png`](evidence/redesign-public-shell-cu01/before/cortes-inicial-mobile.png) | [`after/cortes-inicial-mobile.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-mobile.png) |

The evidence folder also contains login, reported-outages and reported-works
captures at all three viewports, before and after.

| Aspect | Before | After |
| --- | --- | --- |
| Identity | None; page starts with the view title | Brand block with icon and "Zona Sur · Edesur" |
| Navigation | Buttons inside the page body, no persistent header | Horizontal header navigation with active state |
| Hierarchy | `h1` followed directly by content | Header, titled page section, content, footer |
| Palette | Blue-gray `#075b73` on `#f5f7fa` | Approved `#0D6177` on `#F8FAFC` |
| Footer | None | Informational footer without technical detail |
| Mobile | Controls stacked inside the page | Brand, nav and (when signed in) logout remain reachable; no sidebar |
| Logout | Inside the account view | Single header control; account keeps `Cuenta: {username}` |

Contrast measured: white on primary 7.02:1, muted foreground on background 7.24:1,
foreground on white 17.85:1, primary on background 6.71:1, input border on white
4.76:1. All meet WCAG AA for their use.

## Problems and corrections

1. After editing `frontend/src`, the running Vite container kept serving the old
   module graph; the first focused Playwright run failed three shell assertions
   (no banner/footer/skip link). Investigation showed the source files were correct
   and the container stale. Correction: rebuild/recreate the `frontend` service
   (also applies the new `index.html` title). No test was changed.
2. Independent review returned CHANGES REQUESTED. Corrections:
   - **M1 logout feedback:** session errors now render above the current view, so a
     failed revocation stays visible from Cortes or Trabajos. Added a failed-logout
     test and a `POST /api/logout` assertion to the success path.
   - **m1 footer overlay:** the footer reserves `pb-28`, so the collapsed assistant no
     longer covers footer text; design and record wording were corrected.
   - **m2 brand:** the design claimed a link; the implementation is non-interactive
     identity text because there is no router. Design corrected.
   - **m3 coverage:** added exactly-one `aria-current`, one `h1` per view, banner
     identity, anonymous-no-logout, admin nav at 390 px, keyboard nav and footer
     no-button assertions.
   - **m4 active-state captures:** the first after set showed mid-transition colors.
     `visual-capture.spec.ts` now freezes CSS transitions and the set was re-captured;
     active nav state is dark primary in every view.
   - **m5 command context:** the full commands and image revision are recorded below.
   - **m6 spec gaps:** added scenarios for shared primitive consistency and footer
     session controls; requirement descriptions stay under 500 characters.
   - **n1:** removed `outline-none` from `main`, so the global focus-visible outline
     remains visible after the skip link activates.
   - **n4:** added `--color-card-foreground` to the design token table.
4. Second reviewer pass confirmed all nine prior findings resolved and raised two LOW
   items: a stale session error persisted after changing view, and STATE still said
   43/43. Corrections: `App.tsx` clears the session error on view change, the
   failed-logout test now checks that navigating to Trabajos removes the message,
   STATE reports 44/44, design D2/D7 wording matches the implementation, and the
   logout-request assertion uses `expect.poll`.
5. `npm` update notices appear in container output; they are informational and do not
   affect results.

## Repository scope

`git status --porcelain=v1 -uall` shows only this change: README, STATE,
frontend-foundation, U27, `index.html`, `App.tsx`, `AppLayout.tsx`, `styles.css`,
`table.tsx`, the two new layout components, the two new E2E specs, the change
artifacts, this record and the evidence PNGs. There are no diffs under `backend/`,
`frontend/src/features/*/{api,state}.ts`, `frontend/src/lib/http*`,
`frontend/src/stores/`, `package.json`/`package-lock.json`, or the active changes
`docker-development-environment` and `configure-readonly-development-mcp`.

## Checks and results

Revision: verification image `energia-sur-frontend-checks:redesign`
(`sha256:2c1362c01eac94ac36ee52533aa82085d16520f0375e5bc8393cff94b16ca8ca`),
`frontend` service healthy, 2026-11-14; the after captures were regenerated from this image.

```powershell
docker build --target verification -t energia-sur-frontend-checks:redesign frontend
docker run --rm energia-sur-frontend-checks:redesign npm run typecheck
docker run --rm energia-sur-frontend-checks:redesign npm run lint
docker run --rm energia-sur-frontend-checks:redesign npm test
docker run --rm energia-sur-frontend-checks:redesign npm run build
docker run --rm --network host -e E2E_BASE_URL=http://127.0.0.1:5173 `
  energia-sur-frontend-checks:redesign npx playwright test `
  e2e/cu01.spec.ts e2e/cu02.spec.ts e2e/cu03.spec.ts e2e/cu03-auth.spec.ts `
  e2e/cu05-history.spec.ts e2e/cu10.spec.ts e2e/redesign-shell.spec.ts
docker run --rm --network host -e E2E_BASE_URL=http://127.0.0.1:5173 `
  -e VISUAL_CAPTURE=1 -e VISUAL_DIR=/evidence `
  -v "<repo>/docs/ai-engineering/evidence/redesign-public-shell-cu01/after:/evidence" `
  energia-sur-frontend-checks:redesign npx playwright test e2e/visual-capture.spec.ts
openspec validate --all --strict
```

| Check | Result | Evidence |
| --- | --- | --- |
| Typecheck | PASS | `npm run typecheck` (no diagnostics) |
| Lint | PASS | 0 warnings, 0 errors, 95 files |
| Unit tests | PASS | 117/117 |
| Build | PASS | Vite build completed |
| Focused Playwright | PASS | 44/44: `cu01`, `cu02`, `cu03`, `cu03-auth`, `cu05-history`, `cu10`, `redesign-shell` |
| Shell spec | PASS | 7/7 (landmarks, palette tokens, active nav, admin-only + 390 px, single logout + revocation, failed-logout feedback, skip/keyboard nav, chat/health/overflow) |
| OpenSpec strict | PASS | 16/16 items, including this change and both active changes |
| Visual capture spec | PASS | 3/3 viewport runs, 12 before and 12 after PNGs |
| Keyboard/focus/contrast | PASS | Skip link focused and activates `#contenido`; nav operable by Tab/Enter and reachable at 390/820/1440 px; contrast ratios recorded above |
| CU01 real / CU09 / CU04 / CU06–CU08 real specs | NOT APPLICABLE | Not part of Stage A; existing deferral QA-INT-CU04-08 remains open |

## Stage B — CU01 redesign (implemented)

### Authorization and constraints

U28 records the user's Stage B instruction: redesign only CU01 inside this change,
keep Stage A intact, preserve every existing id, label, accessible name, message,
handler, validation, geolocation call and request shape, add no dependency, and do
not commit, push or archive. The panel keeps all query logic; its JSX moved and two
presentation-only flags decide where the existing feedback is rendered.

### Work performed

| Area | Result |
| --- | --- |
| Search card | `OutagesPanel.tsx` now renders "Consultar cortes" with the zone filter (`outage-filter`), a `sm:grid-cols-2` partido/localidad grid (`outage-partido`, `outage-localidad`), a primary `Consultar cortes` and a secondary `Usar mi ubicación` that is full width below 640 px. |
| Address card | Separate "Buscar por dirección" card with `outage-address`, `Buscar dirección`, the unchanged privacy note and the candidate zone buttons (wrapping labels, comfortable targets). |
| Result card | New `frontend/src/features/outages/OutagesResultCard.tsx`: state heading, granularity/coverage/freshness chips, normative description, the three existing alerts, Edesur-wide stat tiles, the outage table and the provenance panel. |
| States | Initial, loading, error, no reports, stale, unavailable, degraded, unverified coverage, out of coverage and geographic error keep their exact texts and distinctions; loading now sits under the search controls, and the shared error/status text is routed to the card that produced it by presentation-only scope flags. |
| Table | Same five columns and values, `scope="col"`, `min-w-[44rem]`, the existing accessible scroll region (`role="region"`, `tabIndex={0}`) and a small-screen scroll hint. |
| Responsive | Cards stack, controls stack below 640 px, buttons keep `min-h-11` and full width on mobile; no document-level horizontal overflow at 390/820/1440 px. |
| Evidence | Gated `frontend/e2e/visual-capture-cu01-states.spec.ts` writes the 12 state captures; the same run also regenerated the six shell captures, which duplicated the Stage A `after/` set (five byte-identical, the sixth differing only in the fixed-assistant frame), so `stage-b/` keeps the six CU01 viewport captures plus the twelve state captures. The Stage A `before/` and `after/` sets were not touched. |

### Presentational decisions

1. **Two cards, feedback next to its form.** Splitting the form makes the primary and
   secondary paths explicit. Address resolution and area queries share the `error` and
   `searchMessage` state, so two presentation-only flags (`errorScope`, `messageScope`)
   select where the same text renders: query feedback stays with the search card, and
   address feedback appears next to the address form and its candidates. Exactly one
   copy of each shared message renders, so the routing itself never duplicates an
   announcement; the separate duplication of state copy is documented under
   Limitations. The loading status moved under the search controls for the same
   reason.
2. **Presentational result component.** `OutagesResultCard` receives the validated
   `OutagesResult` and holds no state, no requests and no new calculations. The two
   pure helpers it needs (`optionalNumber`, `coverageNote`) moved with it, and the
   labels/formatting still come from `state.ts`.
3. **No success/green signal.** The palette has no success token by design. Chips
   use `attention` (accent) only for a verified dimension — coverage `covered`, or
   freshness `fresh` with an `ok` source — and stay neutral for unknown coverage or
   stale data; `out_of_coverage`, `unavailable` and `degraded` use the destructive
   border/text. The heading, the normative description and the existing alerts keep
   "no reports" distinct from "cannot confirm".
4. **Totals are distributor-wide.** The three compact tiles replace the plain list
   but keep the exact "Total Edesur (todos los partidos, no la zona consultada)"
   label and add one explicit sentence saying the totals are Edesur-wide and not
   necessarily the queried zone. No figure is computed, summed or inferred.
5. **Table readability.** The shared table primitive was not modified. The result
   table sets its own minimum width so columns stay legible and the existing
   focusable container scrolls; the hint is only visible below 640 px, where the
   scroll actually occurs.
6. **Initial state.** A neutral dashed panel invites a zone query and states that
   results describe the zone, not a dwelling. It hides while loading, after an
   error, when a result exists and while candidate zones are being chosen.
7. **Accessible names.** The visible "Zonas candidatas" text labels the list through
   `aria-labelledby` (removing a duplicated name), and the filter and address
   fields point to their helper/privacy text with `aria-describedby`.

### Before / after (baseline = the Stage A `after/` set)

| Viewport | CU01 initial | CU01 result |
| --- | --- | --- |
| Desktop 1440×900 | [`after/cortes-inicial-desktop.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-desktop.png) → [`stage-b/cortes-inicial-desktop.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-inicial-desktop.png) | [`after/cortes-resultado-desktop.png`](evidence/redesign-public-shell-cu01/after/cortes-resultado-desktop.png) → [`stage-b/cortes-resultado-desktop.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-resultado-desktop.png) |
| Tablet 820×1180 | [`after/cortes-inicial-tablet.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-tablet.png) → [`stage-b/cortes-inicial-tablet.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-inicial-tablet.png) | [`after/cortes-resultado-tablet.png`](evidence/redesign-public-shell-cu01/after/cortes-resultado-tablet.png) → [`stage-b/cortes-resultado-tablet.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-resultado-tablet.png) |
| Mobile 390×844 | [`after/cortes-inicial-mobile.png`](evidence/redesign-public-shell-cu01/after/cortes-inicial-mobile.png) → [`stage-b/cortes-inicial-mobile.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-inicial-mobile.png) | [`after/cortes-resultado-mobile.png`](evidence/redesign-public-shell-cu01/after/cortes-resultado-mobile.png) → [`stage-b/cortes-resultado-mobile.png`](evidence/redesign-public-shell-cu01/stage-b/cortes-resultado-mobile.png) |

State evidence at the same three viewports: `estado-desactualizado-*`,
`estado-cobertura-no-verificada-*`, `estado-fuente-no-disponible-*` and
`estado-candidatas-*` in the same `stage-b/` folder. The evidence tree is
organised as `before/` (pre-change baseline), `after/` (Stage A result) and
`stage-b/` (CU01 redesign and states); the Stage B shell captures were omitted
because they repeated `after/`.

| Aspect | Stage A baseline | Stage B |
| --- | --- | --- |
| Form hierarchy | One card mixing zone, address and privacy | Primary "Consultar cortes" card plus a secondary "Buscar por dirección" card |
| Control layout | Inline row with a compressed address field on mobile | Two-column grid at ≥640 px, stacked full-width controls and buttons on mobile |
| Results | Title plus a single meta line, plain provenance list, plain totals box | Chips for granularity/coverage/freshness, stat tiles, treated table and a provenance panel |
| Totals caveat | One label | Same label plus an explicit Edesur-wide sentence |
| States | Same texts, untyped visual weight | Neutral/attention/critical chips without green success or local claims |
| Mobile table | Cells wrapped until unreadable | Internal horizontal scroll with visible hint and focusable region |
| Error feedback | At the bottom of the only card | Address alert inside the "Buscar por dirección" card, query errors above the search card, exactly one alert at a time |

Contrast of the new surfaces (computed, WCAG AA for their usage): white on primary
7.02:1, primary on accent 6.14:1, foreground on muted 16.30:1, muted-foreground on
muted 6.92:1, muted-foreground on white 7.58:1, destructive on white 6.89:1.

### Problems and corrections

1. **Stale module graph (repeated from Stage A).** The first capture run rendered
   the pre-change single-card form even though the new files were correct. The
   `frontend` service was restarted, the served module was verified to contain the
   new component and the captures were regenerated. No test was changed.
2. **Sticky header in full-page captures.** After the address search scrolled the
   page, the sticky header was painted mid-page. The states spec now resets the
   scroll position before every screenshot.
3. **Squashed mobile table.** With `w-full` only, cells wrapped into narrow columns.
   The table now sets `min-w-[44rem]` so the existing scroll container handles small
   screens, and a hint appears below 640 px. Covered by the new automated check.
4. **Contradictory initial panel.** The first wording ("Todavía no consultaste…")
   appeared beside ambiguous address candidates. It is now an instruction and is
   hidden while candidates are shown.
5. **Duplicated accessible name.** The candidate list carried both visible text and
   the same `aria-label`; it now uses `aria-labelledby` on the visible heading.
6. **Independent review (two rounds).** The read-only review raised six MEDIUM and seven
   LOW items. Corrected here: M1 (address feedback rendered far from its card — now routed
   by presentation-only scope, with a 390 px in-viewport assertion), M4 (proposal and design
   still described Stage B as unimplemented — reconciled with U28), M5 (verification wording
   overstated the exercised states — corrected, and no-reports, loading and address feedback
   now have automated tests), M6 (this section), L1 (stale `/api/health` mention in README),
   L2 ("messages unchanged" wording), L3 (every partido-level fixture now uses
   `granularity: 'partido'`, and the state captures were regenerated), L4 (all duplicated
   state texts are documented below). A second read-only pass confirmed these corrections,
   found no new BLOCKER/HIGH/MEDIUM, and raised only precision nits (test counts, the width
   qualifier, "five" versus four corrected LOW items, the duplicate-announcement sentence,
   the handler wording, the stale-fixture granularity, the `design.md` id grouping and the
   completed next action), which were corrected before this record was closed. Deferred as
   pre-existing and outside the authorized
   Stage B scope: M2 (result announcement still relies on the pre-existing inserted
   `aria-live` card and `role="alert"` notes), M3 (the shared table region is named "Cortes
   registrados" for every consumer, including diary tables), L5 (the "Sin dato/Sin datos"
   placeholders are unchanged from the pre-Stage-B panel), L6 (the shared focus-ring pattern
   was not modified) and L7 (the new test targets the CU01 table region by its current name).
   The reviewer's session denied `git`, so the diff-scope statements below were verified by
   the primary agent with `git status --porcelain=v1 -uall` and targeted `git diff`.
7. **One transient Playwright failure under build load.** A focused run started while the
   verification image was being built failed the ambiguous-address case after a 120 s
   timeout (the suite took 2.9 min). The isolated rerun of `cu01` passed 14/14 in 8.2 s and
   the full focused suite passed 47/47 in 51.6 s. No test or product change was made; the
   failure was not reproduced and is attributed to host contention from the concurrent
   image build.

### Repository scope (Stage B)

Stage B adds `OutagesResultCard.tsx` and
`visual-capture-cu01-states.spec.ts`, edits `OutagesPanel.tsx` (JSX plus two
presentation-only scope flags) and adds three tests to `cu01.spec.ts`, plus
documentation and the `stage-b/` evidence. No Stage B diff exists under
`backend/`, `features/*/{api,state}.ts`, `features/scheduled-works/`,
`features/assistant/`, `lib/http*`, `stores/`, `package.json` or
`package-lock.json`. `layouts/`, `components/layout/`, `components/ui/` and
`styles.css` differ from `HEAD` only because of Stage A (recorded above), not
because of this Stage B work, and the two unrelated active changes are untouched.
`git status --porcelain=v1 -uall` shows exactly this change's files.

### Checks and results (Stage B)

Revision: verification image `energia-sur-frontend-checks:stage-b`
(`sha256:efba306659819cbd4fd7de050e5a3b77b9265bd7404acbc6576409b8639ced4b`),
`frontend` service healthy, 2026-11-14; captures regenerated from this image.

```powershell
docker build --target verification -t energia-sur-frontend-checks:stage-b frontend
docker run --rm energia-sur-frontend-checks:stage-b npm run typecheck
docker run --rm energia-sur-frontend-checks:stage-b npm run lint
docker run --rm energia-sur-frontend-checks:stage-b npm test
docker run --rm energia-sur-frontend-checks:stage-b npm run build
docker run --rm --network host -e E2E_BASE_URL=http://127.0.0.1:5173 `
  energia-sur-frontend-checks:stage-b npx playwright test `
  e2e/cu01.spec.ts e2e/cu02.spec.ts e2e/cu03.spec.ts e2e/cu03-auth.spec.ts `
  e2e/cu05-history.spec.ts e2e/cu10.spec.ts e2e/redesign-shell.spec.ts
docker run --rm --network host -e E2E_BASE_URL=http://127.0.0.1:5173 `
  -e VISUAL_CAPTURE=1 -e VISUAL_DIR=/evidence `
  -v "<repo>/docs/ai-engineering/evidence/redesign-public-shell-cu01/stage-b:/evidence" `
  energia-sur-frontend-checks:stage-b npx playwright test `
  e2e/visual-capture.spec.ts e2e/visual-capture-cu01-states.spec.ts
openspec validate --all --strict --no-interactive
```

| Check | Result | Evidence |
| --- | --- | --- |
| Typecheck | PASS | `npm run typecheck` (no diagnostics) |
| Lint | PASS | 0 warnings, 0 errors, 97 files |
| Unit tests | PASS | 117/117 |
| Build | PASS | 331 modules; Vite emitted its chunk-size advisory and dependency `use client` notices only |
| CU01 Playwright | PASS | 14/14 (`cu01.spec.ts`: reported result, ambiguous address with in-card feedback, consented/denied geolocation, stale, unverified coverage, unavailable, no-reports without a supply claim, loading announced and in view, retry-after in the address card, degraded source, geographic error in the address card at 390 px, authenticated shell, state/width/scroll case, no health panel) |
| Focused regressions | PASS | 47/47: `cu01` 14, `cu02` 5, `cu03` 1, `cu03-auth` 2, `cu05-history` 9, `cu10` 9, `redesign-shell` 7 |
| Responsive/overflow | PASS | Zero document overflow at 390/820/1440 px for the initial view (shell spec) and for reported/stale/unverified/unavailable and candidate states (CU01 spec and capture spec); the result table scrolls inside its own focusable container at 390 px |
| OpenSpec strict | PASS | 16/16 items |
| Visual capture specs | PASS | 6/6 viewport runs; retained evidence: 6 CU01 viewport captures and 12 state captures (the 6 shell captures repeated `after/`) |
| Independent review | CHANGES REQUESTED, corrected | Six MEDIUM and seven LOW findings in the first pass; M1, M4, M5, M6 and L1–L4 were corrected and re-verified, and M2, M3, L5–L7 are pre-existing and recorded as deferred. A second pass confirmed the corrections with no new BLOCKER/HIGH/MEDIUM, and its precision nits were fixed. |
| CU01 real, CU09, CU04, CU06–CU08 real specs | NOT APPLICABLE | Not part of Stage B; QA-INT-CU04-08 remains deferred |

### Deferred accessibility follow-ups (not part of this change)

These items were identified during the Stage B review and are intentionally left for a
future, separately authorized change:

1. **M2 — aria-live and duplicate announcements.** The result card is an inserted
   `aria-live="polite"` region while several notes use `role="alert"`; verify the real
   screen-reader output and choose a persistent status region and/or a focus move to the
   result heading.
2. **M3 — shared table region label.** `frontend/src/components/ui/table.tsx` names the
   scroll region "Cortes registrados" for every consumer, including the private diary
   tables. Parameterize the label with a neutral default and update CU01/CU02/CU05/CU09
   consumers.
3. **Floating assistant overlay.** The fixed assistant can cover status/content at 390 px
   while scrolling. A later chat review should confirm a non-overlapping placement without
   adding a second mount.
4. **Totals on stale or unavailable data.** Distributor-wide totals remain visible when the
   snapshot is stale or unavailable, as before this redesign. A later change should decide
   whether to keep, mark or hide them, with the accepted `current-outages` contract.

## Limitations

- The comparison is manual, not a pixel-diff baseline. Transitions are frozen for
  capture stability.- No screen-reader session was run; semantics rely on landmarks, labels, roles and
  the automated keyboard/scroll checks.
- The fixed assistant can still float over page content mid-scroll as before; the
  footer reserves space so its text is not covered, and the mount is single. It was
  not redesigned in either stage.
- `stale` and `unavailable` keep two existing messages with the same wording (state
  description and freshness alert), and `coverage_unverified` can show its description
  plus the coverage note; deduplicating them would change current messages, so it was
  left for a later, explicitly authorized change. One pre-existing assertion still uses
  `.first()` for that reason.
- The result card keeps the pre-existing announcement pattern: a newly inserted
  `aria-live="polite"` section plus `role="alert"` notes. A persistent status region or a
  focus move to the result heading would be more reliable but changes behavior, so it
  needs explicit authorization.
- The shared `Table` primitive still names its scroll region "Cortes registrados" for
  every consumer, including the private diary tables. Parameterizing that label is a
  cross-CU change outside Stage B.
- `stale` and `unavailable` results still show the distributor-wide totals supplied by the
  API snapshot, exactly as before Stage B; the label, the caveat sentence and the
  timestamps state their scope and age.
- CU02 keeps its previous form/results presentation; only the shared tokens, table
  header tint and shell apply to it.
- Commit, push and archive were not performed.

## Closure

Archived on 2026-11-14 as `2026-11-14-redesign-public-shell-cu01`. The delta merged into
`openspec/specs/frontend-shell/spec.md` with 3 requirements added, 1 modified and none
removed; the purpose and the other requirements were preserved, and strict validation
passes 15/15 after the archive. Both stages were delivered in a single local commit
(`feat(frontend): redesign shared layout and outages UI`). Nothing was pushed.

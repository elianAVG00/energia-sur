# Mi cuenta redesign - Stages 0, A, B, C, D and E

## Goal and scope

Record the authorized and implemented Stage 0 (preparation), Stages A-E of the
`redesign-account-workspace` change for
the authenticated area that hosts CU04-CU09. Stages A-E are implemented. The
human-approved accumulated review and final mock/local gates passed; exact
Stage E per-hunk attribution and seeded QA remain unavailable as documented
below.

- Archived OpenSpec change: `openspec/changes/archive/2026-11-15-redesign-account-workspace/`
  (proposal, design, deltas for `account-workspace` and `meter-readings`, tasks).
- Decisions: [U31](../use-cases/decisions.md#u31---mi-cuenta-visual-redesign-stage-0a-authorization), [U32](../use-cases/decisions.md#u32---mi-cuenta-visual-redesign-stage-b-authorization-and-result), [U33](../use-cases/decisions.md#u33---mi-cuenta-visual-redesign-stage-c-authorization-and-result), [U34](../use-cases/decisions.md#u34---mi-cuenta-visual-redesign-stage-d-authorization-and-result) and [U35](../use-cases/decisions.md#u35---mi-cuenta-stage-d-review-completion-and-stage-e-authorization).
- Evidence: [`evidence/redesign-account-workspace/`](evidence/redesign-account-workspace/).

Stages B-E are implemented and verified against the available mocked/local
gates. Real seeded acceptance remains blocked. An independent accumulated
review found one PDF-action regression, which was corrected and independently
rechecked. Exact Stage E hunk attribution was expressly waived by the human in
favor of reviewing the integrated change and original source; no E-only
attribution is claimed.

## Approval and instructions

U31 approved Stage 0/A, and U32 authorized Stage B, within one presentation-only
OpenSpec change with verifiable stages;
a single page with the "Índice de Mi cuenta" anchor navigation; tabs, accordions
and routes rejected; the account `h1` renamed to "Mi cuenta"; six labelled
sections; existing ids, labels, messages, handlers, drafts, isolation and API
contracts preserved. The instruction explicitly allowed changing only the four
title assertions in `cu01.spec.ts` and `redesign-shell.spec.ts`, and forbade
touching the backend, adapters, state helpers, Zod schemas, Zustand, HTTP, the
shared shell, CU01-CU03/CU10 and dependencies.

Stage A kept `readingMeter` inside `DomicileManagement`; U32 subsequently
authorized its minimal lift to `AccountWorkspace` for the "Contexto de trabajo"
panel. Stage B's final architecture and address extraction are documented in D14.

## Repository state

`main` at `a966867400febc5f34a3531b9b32c07ec790927b` (`feat(frontend): redesign
scheduled works and admin UI`), clean working tree and `origin/main` at
`223a61c351a64cc63fca5c8659fa6415752b7bbb`, so one local commit was ahead and
unpushed before this work. No reset, restore, clean, commit, push or archive was
run.

## Work performed

| Area | Result |
| --- | --- |
| OpenSpec | Change created with `openspec new change`; proposal, design, `account-workspace` (3 ADDED requirements, 10 scenarios) and `meter-readings` (1 MODIFIED requirement, 3 copied scenarios); strict validation passed before UI edits. |
| Decision | U31 recorded with the approved scope, title decision, Stage 0/A authorization and deferred Stage B-E. |
| Capture harness | New `frontend/e2e/visual-capture-account.spec.ts`, gated by `VISUAL_CAPTURE=1` and `VISUAL_DIR`, with synthetic authenticated mocks for eight scenes; skips without the flag. Waits use anchors that exist before and after Stage A. |
| Baseline | `before/` captured before any UI edit: eight scenes at 1440x900, 820x1180 and 390x844 (24 PNGs). |
| Title | `VIEWS.account.title` is "Mi cuenta" and the description lists the area content; `Cuenta: {username}` is unchanged. |
| Composition | New `features/account/AccountWorkspace.tsx` owns the domicile list, selection and creation logic moved verbatim from the deleted `features/diary/Workspace.tsx`; new `AccountSection.tsx` renders a semantic section with `h2`, `aria-labelledby`, optional description and no extra card layer. |
| Sections | Domicilios, Medidores, Lecturas, Facturas, Consumo y estimación, Cortes e interrupciones. The existing feature cards are siblings; the CU04 card no longer contains the CU05/CU06/CU08 cards. |
| Index | `nav aria-label="Índice de Mi cuenta"` with anchors to the rendered sections; it lists only Domicilios when no domicile exists. |
| No-meter state | Lecturas, Facturas and Consumo render a guidance paragraph and no table when no meter is selected; CU09 remains usable. |
| Diary | `features/diary/DiarySection.tsx` extracts the existing `DiaryWorkspace` with identical state, handlers, conflict recovery, table, summary and PDF. |
| Titles | Removed the duplicate "Domicilios" card title and the inner "Medidores" `h3`; `ConsumptionPanel`'s card title became "Consumo del medidor" so "Consumo y estimación" is a single section heading. |
| Tests | New `frontend/e2e/redesign-account.spec.ts` (10 cases, including mocked coverage for the address/meter draft after a 409, for domicile switching and for a failed meter load); only the four approved title assertions changed in `cu01.spec.ts` and `redesign-shell.spec.ts`, plus the review-driven CU08 locator correction. |

### Section order and deferred work

Stage A rendered Domicilios, Medidores, Lecturas, Facturas, Consumo y estimación,
Cortes e interrupciones, with the diary last while the meter state lived in
`DomicileManagement`. Stage B implements the final order (Domicilios, Medidores,
Cortes e interrupciones, Lecturas, Facturas, Consumo y estimación).
`ConsumptionPanel` still nests its internal cards until Stage D.

## Stage B - CU04, context and section order

U32 authorized Stage B. The implemented architecture, and its difference from the
Stage A design note, is recorded in the change's D14.

| Area | Result |
| --- | --- |
| Meter state | `AccountWorkspace` owns the selection and the meter list as scope-tagged state (`generation:domicile`). A domicile or account change resets both synchronously during render, with no effect, no stale frame, no Zustand change and no update loop. |
| Meter data ownership | `DomicileManagement` remains the only owner of `GET /domiciles/{id}/meters` and the create/correct mutations, and reports the list through a typed `onMetersChange`; the parent never fetches a second list. |
| Address ownership | New `DomicileAddress.tsx` owns the single `GET /domiciles/{id}/management` request, the address correction, duplicate warning, 409 conflict and discard/reload. It is rendered inside Domicilios. |
| Context panel | New "Contexto de trabajo" after the index with the only `selected-domicile` and `reading-meter` selectors, the active domicile address and the active meter number/alias. It shows a neutral state before a domicile or meter is available. |
| Section order | Domicilios (registration and address), Medidores (list and form), Cortes e interrupciones, Lecturas, Facturas, Consumo y estimación. The index points to the same order. |
| Meter-scoped sections | Rendered by `AccountWorkspace` with the existing `generation:domicile:meter` keys and `active()` guards. Without a meter they show neutral guidance, never an unverified "no meters" claim. |
| Drafts and conflicts | Address and meter state are independent: an address 409/discard preserves the meter draft; a meter 409/discard preserves the address draft and resets the meter editor. Button names and messages are unchanged. |
| Preserved | `selected-domicile`, `reading-meter` (one each), all labels, accessible names, messages, handlers, duplicate detection, conflict recovery, OCR/photo, bills, comparison, consumption, PDF and ownership isolation. |
| Tests | `redesign-account.spec.ts` grew to 14 cases: context and duplicate ids, section order, A/B/A meter switching, photo isolation, both conflict-recovery directions, domicile switching, no domicile/no meter/failed meter load, responsive and no nested cards. |

## Gates

| Check | Command | Result |
| --- | --- | --- |
| Typecheck | `npm run typecheck` inside the verification image | PASS |
| Unit tests | `npm test` | PASS 117/117 |
| Build | `npm run build` | PASS 336 modules |
| Lint | `npm run lint` | PASS 0 warnings, 0 errors (106 files) |
| OpenSpec strict | `openspec validate --all --strict --no-interactive` | PASS 16/16 (before archive, with the new change) |
| Focused Playwright | `npx playwright test` with `E2E_BASE_URL=http://127.0.0.1:5173` | PASS 82/82 (including 14 account cases and mandatory `cu05-history` 9/9) |
| Captures | gated `visual-capture-account.spec.ts` | PASS 10/10 scenes; `etapa-b/` has 30 PNGs (10 scenes x 3 widths) |

Focused suite: `cu01`, `cu02`, `cu03`, `cu03-auth`, `cu05-history` (mandatory),
`cu10`, `redesign-shell`, `redesign-works-admin` and `redesign-account`.

Real backend coverage (`cu04`, `cu05-real`, `cu06-real`, `cu07`, `cu08`, `cu09`,
`cu06-restart`) was not run in this stage because it needs seeded synthetic data
and a prepared environment. Those specs are **not** reported as passing;
QA-INT-CU04-08 remains deferred.

## Before / after

All images use synthetic fixtures. Viewports: desktop 1440x900, tablet 820x1180,
mobile 390x844.

| Scene | Before | Stage A |
| --- | --- | --- |
| No domicile | [`before/cuenta-sin-domicilio-desktop.png`](evidence/redesign-account-workspace/before/cuenta-sin-domicilio-desktop.png) | [`etapa-a/cuenta-sin-domicilio-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-sin-domicilio-desktop.png) |
| Domicile without meters | [`before/cuenta-sin-medidor-desktop.png`](evidence/redesign-account-workspace/before/cuenta-sin-medidor-desktop.png) | [`etapa-a/cuenta-sin-medidor-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-sin-medidor-desktop.png) |
| Two meters, none selected | [`before/cuenta-dos-medidores-desktop.png`](evidence/redesign-account-workspace/before/cuenta-dos-medidores-desktop.png) | [`etapa-a/cuenta-dos-medidores-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-dos-medidores-desktop.png) |
| Readings | [`before/cuenta-lecturas-desktop.png`](evidence/redesign-account-workspace/before/cuenta-lecturas-desktop.png) | [`etapa-a/cuenta-lecturas-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-lecturas-desktop.png) |
| Bills | [`before/cuenta-facturas-desktop.png`](evidence/redesign-account-workspace/before/cuenta-facturas-desktop.png) | [`etapa-a/cuenta-facturas-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-facturas-desktop.png) |
| Comparison | [`before/cuenta-comparacion-desktop.png`](evidence/redesign-account-workspace/before/cuenta-comparacion-desktop.png) | [`etapa-a/cuenta-comparacion-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-comparacion-desktop.png) |
| Consumption | [`before/cuenta-consumo-desktop.png`](evidence/redesign-account-workspace/before/cuenta-consumo-desktop.png) | [`etapa-a/cuenta-consumo-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-consumo-desktop.png) |
| Cuts and summary | [`before/cuenta-cortes-desktop.png`](evidence/redesign-account-workspace/before/cuenta-cortes-desktop.png) | [`etapa-a/cuenta-cortes-desktop.png`](evidence/redesign-account-workspace/etapa-a/cuenta-cortes-desktop.png) |

The `before/` and `etapa-a/` folders also contain the tablet and mobile captures
for every scene (24 PNGs each).

### Stage B evidence

The full gated capture set was rerun after Stage B into `etapa-b/` at the same
three widths (30 PNGs), including the requested context states and the unchanged
feature views for direct visual comparison:

| Scene | Stage B |
| --- | --- |
| No domicile | [`etapa-b/cuenta-sin-domicilio-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-sin-domicilio-desktop.png) |
| Domicile without meters | [`etapa-b/cuenta-sin-medidor-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-sin-medidor-desktop.png) |
| Two meters, one selected | [`etapa-b/cuenta-dos-medidores-seleccionado-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-dos-medidores-seleccionado-desktop.png) |
| Meter switched to the empty meter | [`etapa-b/cuenta-cambio-medidor-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-cambio-medidor-desktop.png) |
| Readings | [`etapa-b/cuenta-lecturas-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-lecturas-desktop.png) |
| Bills | [`etapa-b/cuenta-facturas-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-facturas-desktop.png) |
| Comparison | [`etapa-b/cuenta-comparacion-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-comparacion-desktop.png) |
| Consumption | [`etapa-b/cuenta-consumo-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-consumo-desktop.png) |
| Cuts without a meter | [`etapa-b/cuenta-cortes-desktop.png`](evidence/redesign-account-workspace/etapa-b/cuenta-cortes-desktop.png) |

The `etapa-b/` series shows the context panel with both selectors, the final
section order, the address block in Domicilios, the meter list/form in Medidores and
the meter sections as siblings. The assistant FAB still overlaps the top of the
page in full-page captures; that is pre-existing debt.

### Stage B independent review and follow-up

The independent read-only review found no BLOCKER or HIGH. Its Stage B MEDIUM
findings were: architecture notes and evidence counts had drifted, meter loading
and failure were conflated with an empty list, and the domicile-registration draft
was keyed to the selected domicile. Corrections: D14/U32 now document the address
extraction, parent mirror/callback, render-time scope reset and duplicated CU04
state-machine cost; the meter callback carries `loading | ready | failed`; context
and feature guidance distinguish those states; the unnecessary form key was
removed and a domicile-switch draft assertion added; the full 10-scene/30-image
capture set was generated. The orphan meter label was also removed by rendering it
only with its selector, and the E2E asserts exactly one management and meter-list
request per domicile.

Remaining LOW observations: the two separate CU04 sections can expose identical
retry/discard accessible names if both requests fail or conflict simultaneously;
those names are retained to preserve the established controls. The scope-derived
meter reset has mocked E2E coverage but no unit-level pure helper. Review was
static; seeded real CU04/CU05-real/CU06-real/CU07/CU08/CU09 and QA-INT-CU04-08
remain unrun and are not claimed as passing.

## Stage A independent review history

A read-only `reviewer` audit found no BLOCKER, one HIGH and four MEDIUM findings.
Its static analysis could not run Git or the gates, so the primary agent verified
the diff and the gates listed above.

| ID | Severity | Finding | Correction |
| --- | --- | --- | --- |
| H1 | HIGH | The index link and the section heading both contain "Consumo y estimación"; the non-exact `getByText` in `cu08.spec.ts` would match two elements and fail in strict mode. | Changed that locator to `getByRole('heading', { name: 'Consumo y estimación', exact: true })`; `redesign-account.spec.ts` now asserts the heading remains unique with a meter selected. |
| M1 | MEDIUM | The design claimed "one heading per section", but `CardTitle` renders `h2`, so sections contain several `h2`s and section/card headings looked identical. | Corrected the spec/design wording to one labelled section heading with card headings retained at their accepted level; section `h2` is now larger than `CardTitle`. Changing the shared primitive's level is recorded as deferred. |
| M2 | MEDIUM | The no-meter text asserted "Este domicilio no tiene medidores" while loading or after a failed load. | Guidance now distinguishes loading, failed load, empty list and no selection. |
| M3 | MEDIUM | The engineering record and STATE update were missing. | Both were created after the review snapshot; this record and `docs/STATE.md` now exist. |
| M4 | MEDIUM | The artifacts did not map the change-level spec to the stages. | Added the D12 stage-mapping table, the proposal's Stage A order note and the ConsumptionPanel title to the impact list. |
| L1 | LOW | The proposal impact list omitted `ConsumptionPanel.tsx`. | Added. |
| L2 | LOW | `AppLayout` keeps the dead default title "Diario de interrupciones". | Recorded as follow-up; the shared layout stays untouched. |
| L3 | LOW | Task boxes did not reflect completed work. | Updated for every verified Stage 0/A item; the review and pending stages stay open. |
| L4 | LOW | An unused option variant in the new spec. | Removed. |

A read-only Stage A re-audit of the corrections returned **no BLOCKER and no HIGH**. It
confirmed the CU08 locator fix, the four-state meter guidance, the heading wording
and the record/STATE coherence. Its only MEDIUM was a stale test count because it
read the tree before the final focused run was recorded; the final run is 78/78
with 10 new cases (verified after the last edit). Its LOW notes were documentation
leftovers (design D10 and a checked task now aligned), a mobile typography
observation (`h1` and section `h2` share 24 px below 640 px, recorded as a
follow-up for the deferred shell/typography work) and an observation that the
load-failure text names only meters although either request may fail; none changes
behavior. The reviewer did not observe runtime behavior (no browser, backend or
seeded accounts), so meter isolation, drafts, 409 recovery, OCR and PDF remain
supported by static review plus the focused mocked suites and the accepted real
suites, which were not re-run here.

## Limitations and pending work

- Stage B (meter context lift, "Contexto de trabajo", CU04 split and section
  reordering) is implemented; see U32.
- Stage C (CU05/CU06 presentation) is implemented; see U33 and the Stage C
  results below. Its independent diff review remains pending.
- Stage D (CU07/CU08 presentation) is implemented under U34. Stage E (Diario
  blocks) remains unauthorized and is not started.
- The assistant overlay still overlaps the page at 390 px (pre-existing debt).
- M2, M3, stale/unavailable totals, hosting, the CU03 retention policy and
  QA-INT-CU04-08 remain out of scope.
- No commit, push, archive or deployment was performed.

## Stage E - CU09 Cortes e interrupciones (U35)

U35 authorized a presentation-only redesign in the existing change. CU09 now
uses one principal card with visually grouped registration/correction, history,
closure, summary and PDF areas; existing forms and behavior remain in place.
Mocked account E2E coverage was extended for these workflows, isolation and
responsive history scrolling. The synthetic capture directory contains 24 PNGs
(eight scenarios at 1440, 820 and 390 px); these are not seeded QA evidence.

### Stage E verification status (2026-11-15)

| Check | Result |
| --- | --- |
| Synthetic capture inventory | PASS, 24 PNG files in `evidence/redesign-account-workspace/etapa-e/` |
| OpenSpec strict | PASS, `openspec validate --all --strict --no-interactive`, 16/16 |
| Diff whitespace | PASS, `git diff --check`; Git emitted line-ending conversion warnings |
| Typecheck | PASS: `docker exec -w /app energia-sur-etapa-e-verify-20261115 npm run typecheck` |
| Lint | PASS: same container, `npm run lint`; 106 files, 0 warnings/errors |
| Unit tests | PASS: same container, `npm test`; 117/117 |
| Build | PASS: same container, `npm run build`; 336 modules; known chunk-size and upstream `use client` warnings remain |
| Combined focused Playwright | PASS: same container, `npm run test:e2e -- e2e/redesign-account.spec.ts e2e/cu05-history.spec.ts e2e/redesign-shell.spec.ts`; 46/46 (30/9/7) |
| CU09-focused regressions | PASS: same container, `npm run test:e2e -- e2e/redesign-account.spec.ts --grep CU09`; 8/8, including change-of-user isolation |
| Responsive CU09 table | PASS: focused account test verifies internal horizontal overflow at 390/820 and no internal overflow at 1440, plus no document overflow at each width |
| OpenSpec strict / diff whitespace | PASS: 16/16; `git diff --check` and `git diff --cached --check` clean (Git emits line-ending conversion warnings) |
| Seeded CU09 / QA-INT-CU04-08 | BLOCKED: no confirmed isolated seeded QA setup; mock tests do not substitute for real acceptance |
| Independent accumulated review | PASS with one corrected HIGH finding; scope was the integrated change since base `a966867400febc5f34a3531b9b32c07ec790927b`, including new files and original deleted `Workspace.tsx`. Reviewer did not execute tests. Exact Stage E per-hunk attribution is unavailable and was expressly accepted; no E-only attribution is claimed. |

The independent reviewer audited the integrated change from base
`a966867400febc5f34a3531b9b32c07ec790927b`, including tracked changes, current
untracked source/tests and the original deleted `Workspace.tsx` recovered with
`git show`. The user expressly accepted this accumulated review in place of
unreliable E-only hunk attribution. No exact Stage E baseline snapshot exists,
so no per-hunk Stage E attribution is claimed.

The reviewer found a HIGH behavior regression: the PDF button was conditional
on `queriedPeriod`, whereas the original rendered it whenever a summary existed.
`DiarySection.tsx` now renders the action with every displayed summary, while
the query stores its period together with the summary and the download handler
retains its defensive guard. The existing mocked E2E asserts no button before a
summary, and a browser download after a successful summary. A separate
read-only reviewer follow-up confirmed the correction. The reviewer did not
execute gates; verification evidence below is from the implementer.

The previous native Windows failures were caused by incomplete local
`frontend/node_modules`, not a project dependency change. Reused
`energia-sur-frontend-checks:etapa-e`, verified Node 24.22.2/npm 11.19.1 and
installed locked dependencies, and confirmed the package/lock hashes match the
repository. Current `src`, `tests`, `e2e` and runner configs were copied into a
disposable container before execution. Container connectivity to the already
running Vite service was initially 403 via `host.docker.internal`; connecting
the runner to `energia-sur_default` and using the frontend container IP returned
200 and Playwright passed. No Windows install, manifest/lock edit, service
restart, backend restart or PostgreSQL restart was performed. Seeded acceptance
was not attempted because this run did not establish a prepared isolated QA
database/account; no secrets were read. Human review follows independent review;
no commit, push, archive or deployment was performed.

## Stage C - CU05 Lecturas and CU06 Facturas (U33)

U33 authorized only the existing change's Stage C. `ReadingHistory.tsx` now
separates the reading/correction area from a scannable, per-meter history;
`ReadingForm.tsx` labels the existing photo/OCR group and constrains the preview
within the available width/height. `BillHistory.tsx` organizes the existing
registration form into a responsive two-column field layout and presents bill
period, consumption, amount, version and file type in divided history rows.
CU07 comparison remains where it was, inside the invoice section; its component
and calculation logic were not modified. No shared component, dependency,
endpoint, state owner, adapter, schema, store or backend file changed.

The existing account selection and keyed children remain unchanged:
`generation:domicile:meter` still scopes each reading and bill history. No
presentation-only hiding was introduced. Photo URLs, file operations, draft
state, idempotency keys, attempts, versions and stale-response guards stay in
the original feature components. `Registrar factura` remains in its form.

### Stage C evidence and gates

| Check | Result |
| --- | --- |
| Local Windows typecheck/lint/unit | BLOCKED: frontend `node_modules` is absent; scripts reported missing `tsc`, `oxlint`, and imported packages. No dependency installation was run. |
| Docker frontend typecheck | PASS in existing frontend container |
| Docker frontend lint | PASS, 101 files, 0 warnings/errors |
| Docker frontend unit tests | PASS, 117/117 |
| Docker frontend build | PASS, 336 modules; existing chunk-size and upstream `use client` warnings remain |
| `cu05-history.spec.ts` | PASS, 9/9, Playwright runner in `energia-sur-frontend-checks:account-b4` against the current frontend container |
| `redesign-account.spec.ts` | PASS, 15/15, including presentation grouping and responsive/no-overflow checks at 390/820/1440 |
| `redesign-shell.spec.ts` | PASS, 7/7; together with `cu05-history`, 16/16 |
| Synthetic visual capture | PASS, 14 scenes, 42 PNGs at 1440/820/390 in `evidence/redesign-account-workspace/etapa-c/` |
| OpenSpec strict | PASS, 16/16, all active changes/specs |
| Real seeded CU04-CU08 E2E | BLOCKED: `QA_USERNAME_A`, `QA_USERNAME_B` and `QA_PASSWORD` are not present in the execution environment; no real seeded acceptance is claimed |
| Reviewer | BLOCKED for final approval: static snapshot found no confirmed defect but could not inspect/attribute the diff or run checks; coverage gap noted, and focused UI checks were added |

Representative synthetic captures (desktop; tablet/mobile variants are beside
each image):

- [Reading form and history](evidence/redesign-account-workspace/etapa-c/cuenta-lecturas-desktop.png)
- [Selected photo and OCR suggestion](evidence/redesign-account-workspace/etapa-c/cuenta-fotografia-ocr-desktop.png)
- [Lower-reading warning](evidence/redesign-account-workspace/etapa-c/cuenta-lectura-advertencia-desktop.png)
- [Bill registration and history](evidence/redesign-account-workspace/etapa-c/cuenta-facturas-desktop.png)
- [Bill overlap confirmation](evidence/redesign-account-workspace/etapa-c/cuenta-factura-superposicion-desktop.png)
- [Empty reading/bill histories](evidence/redesign-account-workspace/etapa-c/cuenta-sin-registros-desktop.png)

Playwright first used `http://frontend:5173`, which Vite rejected with HTTP 403
for an unapproved Host header. After switching to the container IP, the first
account suite found one presentation assertion absent from the already-running
Vite module graph. The mounted source itself contained the edit; restarting
only the frontend service loaded it, after which the account suite passed 15/15.
Final reruns passed `redesign-account` plus `cu05-history` 24/24. The real seeded
tests were not run. No commit, push, archive, deployment or Stage D/E work was
performed at Stage C closure; Stage D was authorized and performed afterward.

## Stage D - CU07 comparison and CU08 consumption (U34)

U34 authorized Stage D after the satisfactory Stage C diff review. The change is
limited to presenting the existing comparison in a labelled subpanel and
organizing consumption filters, interval consumption, daily averages and
estimation into semantic subpanels. The estimate displays its existing base
timestamps in Buenos Aires time. The existing simple bars are retained and
responsive; no chart or dependency was added. Existing requests, state ownership,
keys, calculations, validation, messages, units and meter isolation are preserved.
Stage E is authorized and implemented under U35; its verification and review
outcomes are recorded below.

### Stage D evidence and gates

| Check | Result |
| --- | --- |
| Frontend typecheck | PASS in the existing pinned Docker verification image |
| Frontend lint | PASS, 106 files, 0 warnings/errors |
| Frontend unit tests | PASS, 117/117 |
| Frontend build | PASS, 336 modules; existing chunk-size and upstream `use client` warnings remain |
| Focused Playwright (`redesign-account`, `cu05-history`, shell/navigation) | PASS, 37/37 before the added outcome test; account suite rerun PASS 22/22 |
| Synthetic visual capture | PASS, 22/22 scenarios; 66 PNGs at 1440/820/390 in `evidence/redesign-account-workspace/etapa-d/` |
| Responsive checks | PASS at 390/820/1440, including no-overflow with comparison and estimate open |
| OpenSpec strict | PASS, 16/16 |
| `git diff --check` | PASS after documentation edits |
| Real seeded CU04-CU08 E2E / QA-INT-CU04-08 | BLOCKED: QA credentials/seeded setup unavailable; no real seeded acceptance claimed |
| Native Windows typecheck/lint/unit | BLOCKED: frontend dependencies/tools absent (`tsc`, `oxlint`, imported packages); no installation performed |
| Independent Stage D diff review | BLOCKED for exact diff attribution: reviewer lacks Git/shell access; static review finding corrected below |

The initial focused Playwright run observed 33/37 against a stale Vite module
graph. Only the local frontend service was restarted; the rerun against current
source passed 37/37. Backend and database were not restarted.

### Stage D reviewer follow-up

The independent reviewer performed a static read of current files but reported
that exact diff attribution was BLOCKED because its tool permissions did not
include Git/shell. It identified one LOW test-adequacy gap: the CU07 tests did
not cover the decreasing-reading `no_comparison` result or the `billed_higher`
and `equal` messages. Added mocked cases for all three and reran
`redesign-account.spec.ts` in the pinned Playwright image: PASS 22/22. The
first full-suite rerun exposed a strict-locator ambiguity for billed kWh shown
in both the invoice summary and result; the test locator now uses exact matching
and the rerun passed. Lint also passed (106 files, 0 warnings/errors). The
reviewer reported no confirmed accessibility or responsive defect in static
markup inspection, but did not run checks or inspect a Git diff. Task 6.12
remains open; independent diff review and human review are still pending.

## Final accumulated review and closure verification (2026-11-15)

The human explicitly authorized closing task 6.17 through review of the
integrated change rather than fabricated Stage E hunk attribution. The
independent reviewer inspected the accumulated changes since
`a966867400febc5f34a3531b9b32c07ec790927b`, the current newly added source and
tests, and the deleted CU09 `Workspace.tsx` recovered from that base. This does
not claim that an E-only diff was verified. The static reviewer did not execute
tests.

The reviewer identified a HIGH regression: PDF download had become conditional
on client period state despite a displayed successful summary. The action now
renders with every summary, and the existing E2E covers both pre-query absence
and successful browser download. An independent source-only follow-up confirmed
the fix.

Final post-fix implementer gates in the pinned verification image:

| Check | Result |
| --- | --- |
| Typecheck | PASS: `docker compose exec -T frontend npm run typecheck` |
| Lint | PASS: same frontend container, 101 source/test/E2E files, zero warnings/errors |
| Unit tests | PASS: same frontend container, 117/117 |
| Production build | PASS: same frontend container, 336 modules; existing chunk-size and upstream `use client` warnings |
| Account E2E | PASS: disposable verification image built from current source, 30/30 |
| Combined account/CU05-history/shell E2E | PASS: same image, 46/46 |
| OpenSpec strict after specs sync and archive | PASS: `openspec validate --all --strict --no-interactive`, 16/16 |
| `git diff --check` after specs sync and archive | PASS; only expected LF-to-CRLF working-copy notices |
| Real seeded CU09 / QA-INT-CU04-08 | BLOCKED; no isolated seeded QA setup, not substituted by mock E2E |

The visual capture spec remains skipped unless `VISUAL_CAPTURE=1`; no capture
run occurred during final verification. The 210 retained PNGs (~63 MB) are
synthetic presentation evidence. No backend/API/auth/CSRF/business-rule,
dependency, routing, or state-architecture change was made. Seeded CU09 and
QA-INT-CU04-08 remain deferred integration work; the complete product is not
claimed as integration-validated.

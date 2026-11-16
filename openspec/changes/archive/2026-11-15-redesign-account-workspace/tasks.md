# Tasks

## 1. Preparation (Stage 0)

- [x] 1.1 Verify `main`, clean working tree, the last local commit and `origin/main`; record the commands and redacted output in the engineering record.
- [x] 1.2 Create `openspec/changes/redesign-account-workspace/` with proposal, design, deltas for `account-workspace` and `meter-readings`, and `.openspec.yaml`; verify `openspec validate redesign-account-workspace --strict --no-interactive` passes before frontend edits.
- [x] 1.3 Record decision U31 in `docs/use-cases/decisions.md` (approved scope, "Mi cuenta" title, Stage 0/A authorization and later stage gates); verify the section anchor and links.
- [x] 1.4 Add `frontend/e2e/visual-capture-account.spec.ts` gated by `VISUAL_CAPTURE=1` and `VISUAL_DIR`, with synthetic authenticated mocks; verify it skips without the flag.
- [x] 1.5 Capture the `before/` set at 1440, 820 and 390 px into `docs/ai-engineering/evidence/redesign-account-workspace/before/`; verify every expected file exists and contains no credentials or personal data.

## 2. Account frame (Stage A)

- [x] 2.1 Rename the account view title to "Mi cuenta" in `frontend/src/App.tsx` and update its description; keep "Cuenta: {username}" unchanged.
- [x] 2.2 Add `frontend/src/features/account/AccountSection.tsx` (semantic section, `h2`, `aria-labelledby`, optional description) and `frontend/src/features/account/AccountWorkspace.tsx` with the existing domicile list, selection and creation logic.
- [x] 2.3 Add the "Índice de Mi cuenta" navigation with anchors to the six sections; verify no collision with the header "Secciones" navigation.
- [x] 2.4 Render the six sections: Domicilios (form, selector, empty state), Medidores (existing management card without the duplicate heading), Lecturas, Facturas y Consumo (existing components, no-meter guidance) and Cortes e interrupciones (extracted `DiarySection`).
- [x] 2.5 Preserve ids `selected-domicile` and `reading-meter`, labels, accessible names, messages, handlers, request scopes, conflict recovery and drafts; verify no adapter, state, schema, store or HTTP file changes.
- [x] 2.6 Verify responsive and accessible behavior at 390/820/1440 px: no document overflow, one `h1`, one labelled section heading per section (existing card headings retained), keyboard reachable index, no new live region and no nested card in the reorganized sections.

## 3. Tests, gates and review (Stage A)

- [x] 3.1 Update only the four title assertions affected by the approved `h1` change in `frontend/e2e/cu01.spec.ts` and `frontend/e2e/redesign-shell.spec.ts`.
- [x] 3.2 Add `frontend/e2e/redesign-account.spec.ts` with section/index presence, no-meter diary access, meter-scoped rendering, no nested card, no fabricated data, responsive, palette, one chat mount and no health request.
- [x] 3.3 Run `npm run typecheck`, `npm run lint`, `npm test` and `npm run build` in the pinned verification image; record PASS/FAIL and any pre-existing failure separately.
- [x] 3.4 Run focused Playwright for `cu01`, `cu02`, `cu03`, `cu03-auth`, `cu05-history`, `cu09`-independent mocked account checks, `cu10`, `redesign-shell`, `redesign-works-admin` and `redesign-account`; record actual counts.
- [x] 3.5 Run `openspec validate --all --strict --no-interactive` and audit the diff for zero changes under `backend/`, `features/*/api.ts`, `features/*/state.ts`, `features/*/schemas.ts`, `lib/http*`, `stores/`, the shell, layout, chat and manifests.
- [x] 3.6 Request a read-only `reviewer` audit focused on state loss, meter isolation, conflicts, drafts, accessibility, responsive behavior and out-of-scope changes; correct findings and rerun affected checks.
- [x] 3.7 Capture the `etapa-a/` set with the same scenes and viewports as `before/`; record the comparison table and any intentional visual difference.

## 4. Documentation and Stage A closure

- [x] 4.1 Update `tasks.md` only for completed items, decision U31 results and `docs/ai-engineering/redesign-account-workspace.md` with actual commands, counts and evidence.
- [x] 4.2 Update `docs/STATE.md` (at most 60 lines), `docs/frontend-foundation.md` only if the module map requires the new account module, and `README.md` only where the account view and evidence require it.
- [x] 4.3 Final scope audit and delivery report; confirm no commit, push or archive and no Stage B-E behavior.

## 5. Stage B - CU04, meter context and section order (authorized by U32)

- [x] 5.1 Add "Contexto de trabajo" after the index with the only `selected-domicile` and `reading-meter` selectors and the active domicile/meter text.
- [x] 5.2 Lift the meter selection into `AccountWorkspace` as scope-tagged state (`generation:domicile`) that resets synchronously; keep `DomicileManagement` as the only meter list/request owner and report the list through a typed callback.
- [x] 5.3 Extract `DomicileAddress.tsx` (management fetch, address correction, duplicates, 409 recovery) into the Domicilios section; keep meters in the Medidores section without duplicating requests or selectors.
- [x] 5.4 Render Cortes after Medidores and the meter-scoped sections from the container with the existing keys; CU09 stays usable without a meter.
- [x] 5.5 Preserve ids, labels, messages, handlers, request scopes, drafts, conflict recovery, OCR, bills, comparison, consumption and PDF behavior; verify no adapter, state, schema, store or HTTP change.
- [x] 5.6 Extend `redesign-account.spec.ts` with the context panel, no duplicate ids, section order, A/B/A switching, photo isolation, both conflict-recovery directions and domicile switching; run `cu05-history` and the focused suite.
- [x] 5.7 Capture `etapa-b/` for no domicile, no meter, two meters with one selected, meter switch and cuts without a meter; request the independent review and correct findings.

## 6. Pending stages

- [x] 6.1 Stage C: redesign the CU05 reading form, photograph/OCR presentation and per-meter history; redesign the CU06 bill form, attachment presentation and history while leaving CU07 comparison behavior/results unchanged.
- [x] 6.2 Stage D: redesign Comparación and Consumo, removing the remaining nested cards.
- [x] 6.3 Stage E: redesign the Diary blocks and summary/PDF presentation.

### Stage C verification and evidence

- [x] 6.4 Preserve CU05/CU06 labels, controls, warnings, photo/file workflows, retry/version/conflict handling and active-meter ownership; keep CU07 nested in the bill section without changing its logic.
- [x] 6.5 Add focused mocked presentation coverage and expand synthetic captures for OCR suggestion, lower-reading warning, bill overlap, and empty histories at 1440/820/390 px.
- [x] 6.6 Run typecheck, lint, unit tests, build, `cu05-history.spec.ts`, `redesign-account.spec.ts`, shell/navigation E2E and strict OpenSpec validation; record real seeded CU04-CU08 tests as blocked when QA credentials are unavailable.
- [x] 6.7 Obtain independent read-only review of the Stage C diff and correct any introduced findings before human review. — PASS: independent reviewer inspected the supplied implementation diff against the current source and CU05/CU06/CU07 contracts; no Stage C-attributable findings. Static review only; runtime gates and real seeded acceptance were not run by the reviewer.

### Stage D verification and evidence

- [x] 6.8 Preserve CU07 selection, matching, calculations, exact messages, confirmation, errors, API calls and meter isolation; render the selected bill, comparison values, difference, outcome, warnings and states in a clearly identified panel without a nested Card.
- [x] 6.9 Reorganize CU08 filters, real interval consumption, daily averages and estimate into semantic subpanels; preserve interval selection, calculations, labels, units, warnings, errors, request keys and active-meter state. Do not add dependencies or a graph.
- [x] 6.10 Add mocked regression tests for comparison results, no candidates, approximate warnings, errors, meter switching, period filtering, averages, estimates, representativeness, errors and flat card hierarchy; add the requested synthetic visual scenes. Added explicit CU07 coverage for decreasing readings and all result outcomes after review identified the gap.
- [x] 6.11 Run typecheck, lint, unit tests, build, focused Playwright including `redesign-account.spec.ts`, `cu05-history.spec.ts`, shell/navigation and any runnable CU07/CU08 tests; verify 390/820/1440 and strict OpenSpec. Record real seeded CU04-CU08 acceptance BLOCKED if its prerequisites remain unavailable. — PASS in pinned Docker image: typecheck, lint (106 files), unit 117/117, build (336 modules), account Playwright 22/22 (including new outcome coverage), previous combined focused Playwright 37/37 before the added regression, visual captures 22/22 (66 images), responsive/no-overflow at 390/820/1440, strict OpenSpec 16/16. Seeded QA BLOCKED; native Windows dependency/tooling checks BLOCKED.
- [x] 6.12 Obtain independent read-only review of the actual Stage D diff; correct introduced findings and rerun affected gates before human review. — PASS static review: reviewer directly inspected the supplied real `BillComparison.tsx` and `ConsumptionPanel.tsx` diffs, base/current context, Stage-D-focused mocked tests, CU07/CU08 specs and D15; no blocker/high or confirmed Stage-D defect. LOW limitation: exact ±7-day edge/manual candidate selection and the display of positive values below the two-decimal threshold are not directly asserted in the named visual suite; presentation logic does not change these rules. Attribution confidence high for supplied Stage D scope; reviewer could not verify omitted whole-tree diff or run checks. Prior account regression after the earlier LOW outcome-coverage correction: 22/22; runtime gates and seeded QA were not run by reviewer.

### Stage E verification and evidence (authorized by U35)

- [x] 6.13 Redesign CU09 registration/correction, history, closure, period summary and PDF presentation with one principal card and no nested cards; preserve all forms, validation, requests, drafts, 409 recovery, results and contracts.
- [x] 6.14 Add mocked CU09 coverage for registration, history, correction, closure, 409 recovery, domicile/user isolation, no-meter use, accepted summary/overlap results, PDF availability/errors and responsive scroll; use backend-provided results rather than reimplementing calculations.
- [x] 6.15 Capture synthetic CU09 states in `docs/ai-engineering/evidence/redesign-account-workspace/etapa-e/` at 1440, 820 and 390 px; preserve prior evidence. - PASS: 24 synthetic PNGs, eight scenes x three viewports.
- [x] 6.16 Run typecheck, lint, unit tests, build, focused Playwright (`redesign-account`, `cu05-history`, shell/navigation and seeded `cu09` only if already prepared), responsive/accessibility checks, strict OpenSpec and `git diff --check`. Keep seeded QA BLOCKED if prerequisites are unavailable. - PASS in `energia-sur-frontend-checks:etapa-e` (Node 24.22.2/npm 11.19.1, locked dependency versions): typecheck; lint 106 files, 0 warnings/errors; unit 117/117; build 336 modules; combined account/CU05-history/shell Playwright 46/46; CU09-filtered regression 8/8, including account-switch isolation; CU09 responsive table and no-overflow assertions at 390/820/1440; OpenSpec strict 16/16; tracked/staged `git diff --check`. Seeded `cu09.spec.ts` BLOCKED/not run: no confirmed isolated seeded QA setup; no credentials read and no database/backend restarted.
- [x] 6.17 Obtain read-only independent review under the human-approved accumulated-change procedure; correct findings and rerun affected checks. - PASS: the independent reviewer audited the integrated change from base `a966867400febc5f34a3531b9b32c07ec790927b` (Stages 0/A/B/C/D/E), including the tracked diff, current untracked sources/tests and the original `Workspace.tsx` recovered from Git. Exact Stage E per-hunk attribution is unavailable: `DiarySection.tsx` is new and no Stage E baseline snapshot exists. This limitation was expressly accepted; no E-only diff attribution is claimed. The reviewer found a HIGH regression where the PDF action was hidden unless `queriedPeriod` existed while a summary was displayed. The action was restored for every displayed summary; a follow-up independent source review confirmed the correction. Typecheck, lint, unit tests, build and the affected Playwright suites were rerun successfully by the implementer; the reviewer did not execute tests.
- [x] 6.18 Record U35, Stage E evidence, review/gate outcomes and outstanding blockers in the decision register, engineering record and operational state.

## Workflow follow-up

- U31 records the approved Stage 0/A; U32 records the Stage B authorization and result.
- U33 records the explicit Stage C authorization and this stage's presentation-only scope and evidence.
- U34 records the explicit Stage D authorization after the satisfactory diff-attributed Stage C review.
- U35 records Stage D review completion and Stage E authorization. Human-approved accumulated review completed; exact Stage E per-hunk attribution remains unavailable and is not claimed.
- QA-INT-CU04-08 remains deferred; mocked coverage must not be reported as a real seeded pass.
- Seeded QA-INT-CU04-08 and real CU09 remain pending; mocked tests do not substitute for those acceptance checks.
- Archive and one local commit are authorized only after final validation; push and deployment are not authorized.

# Tasks

## 1. Preparation

- [x] 1.1 Verify `main` at `223a61c`, clean working tree, active changes untouched and `origin/main` state; record the commands and redacted output in the engineering record.
- [x] 1.2 Create `openspec/changes/redesign-public-works-admin/` with proposal, design, deltas for `scheduled-works` and `source-refresh-administration`, and `.openspec.yaml`; verify `openspec validate redesign-public-works-admin --strict --no-interactive` passes before frontend edits.
- [x] 1.3 Record decision U29 in `docs/use-cases/decisions.md` (interpretation A, Stage 0/A authorization, no date filters, later U30 gate); verify the section anchor and links.

## 2. Baseline evidence

- [x] 2.1 Add `frontend/e2e/visual-capture-works-admin.spec.ts` gated by `VISUAL_CAPTURE=1` and `VISUAL_DIR`, with synthetic mocks for CU02 initial/reported/no-works/stale-degraded/unverified/error and CU10 normal/failed-attempt; verify it skips without the flag.
- [x] 2.2 Capture the `before/` set at 1440, 820 and 390 px into `docs/ai-engineering/evidence/redesign-public-works-admin/before/`; verify every expected file exists and contains no credentials or personal data.

## 3. CU02 implementation (Stage A)

- [x] 3.1 Restructure `frontend/src/features/scheduled-works/ScheduledWorksPanel.tsx` into "Consultar trabajos" and "Buscar por dirección" cards plus an initial panel, preserving ids `scheduled-filter`, `scheduled-partido`, `scheduled-localidad`, `scheduled-address`, labels, accessible names, messages, handlers, geolocation and request behavior; verify `cu02.spec.ts` existing cases pass.
- [x] 3.2 Add presentational `frontend/src/features/scheduled-works/ScheduledWorksResultCard.tsx` with state heading, granularity/coverage/freshness chips, existing alerts, zone/scope panel, unpublished planned dates, reason, five-column table and provenance; verify headings, table cells and source fields stay test-compatible.
- [x] 3.3 Verify responsive and accessible behavior at 390/820/1440 px: no document overflow, focusable internal table scroll, stacked full-width controls, visible focus, one `h1` and no new live regions.

## 4. CU02 tests, gates and review

- [x] 4.1 Extend `frontend/e2e/cu02.spec.ts` with cases for loading/query error, unpublished dates and reason, stale/degraded, unverified coverage, address error, no date inputs and 390 px table behavior; verify the full CU02 file passes.
- [x] 4.2 Extend `frontend/e2e/redesign-works-admin.spec.ts` with CU02 palette, landmark, `h1`, chat mount, no health request and overflow checks at 390/820/1440 px; verify it passes.
- [x] 4.3 Run `npm run typecheck`, `npm run lint`, `npm test` and `npm run build` in the pinned verification image; record PASS/FAIL and any pre-existing failure separately.
- [x] 4.4 Run focused Playwright for `cu02`, `cu01`, `redesign-shell`, `cu03`, `cu03-auth`, `cu05-history`, `cu10` and `redesign-works-admin`; record actual counts.
- [x] 4.5 Run `openspec validate --all --strict --no-interactive` and audit the diff for zero changes under `backend/`, `features/*/api.ts`, `features/*/state.ts`, `lib/http*`, `stores/`, `App.tsx`, the shell and manifests.
- [x] 4.6 Request a read-only `reviewer` audit of regressions, contracts, accessibility, responsive behavior, CU01 consistency, invented data and scope; correct findings and rerun affected checks.
- [x] 4.7 Capture the `etapa-a/` set with the same CU02 scenes and viewports as `before/`; CU10 remains in `before/` because it is unchanged until Stage B, and the exemption is recorded with the comparison table.

## 5. Documentation and Stage A closure

- [x] 5.1 Update `tasks.md` only for completed items, `docs/use-cases/decisions.md` U29 results and `docs/ai-engineering/redesign-public-works-admin.md` with actual commands, counts and evidence.
- [x] 5.2 Update `docs/STATE.md` (≤60 lines) and `README.md` only where the new view and evidence require it; verify links and the corrected remote statement.
- [x] 5.3 Final scope audit and delivery report; confirm no commit, push or archive and no out-of-scope CU10 behavior.

## 6. CU10 implementation (Stage B — authorized by U30)

- [x] 6.1 Extract `frontend/src/features/admin/SourceCard.tsx` and restructure `AdminPanel.tsx` with per-source title, scheduling/attempt chips, status grid, error panel and lock-contention note; verify `cu10.spec.ts` existing cases pass.
- [x] 6.2 Group "Configuración" (interval select and save) and "Acciones" (retry) while preserving ids, accessible names, feedback strings, 403/409/422/timeout handling and the 25-second retry; verify all CU10 cases.
- [x] 6.3 Verify responsive and accessible behavior at 390/820/1440 px and confirm no new admin tool, polling or endpoint.

## 7. CU10 tests and verification (Stage B — authorized by U30)

- [x] 7.1 Extend `frontend/e2e/cu10.spec.ts` and `redesign-works-admin.spec.ts` with hierarchy, failure-versus-success, lock contention, only-existing-controls, no-polling and responsive cases; verify the suites pass.
- [x] 7.2 Run the full quality gates, strict validation and scope audit; request the independent reviewer and correct findings.
- [x] 7.3 Capture `etapa-b/`, update the engineering record, U30, STATE and README; verify the comparison and report.

## Workflow follow-up

- U30 authorized Stage B; its independent review remains the pre-closure check.
- Human review of the combined Stage A + Stage B delivery is required before any commit.
- Archive, commit and push remain unauthorized.

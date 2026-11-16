# Operational state - energia-sur

Updated: 2026-11-16 (registration backend diagnostic and synthetic browser/PDF/restart acceptance completed; 8 unrelated backend failures remain).

## Public account registration - IMPLEMENTATION ACTIVE
- [Active OpenSpec change](../openspec/changes/add-public-account-registration/proposal.md), [engineering record](ai-engineering/add-public-account-registration.md), U36 in [decisions](use-cases/decisions.md#u36---public-account-registration-authorization).
- Focused PostgreSQL/ASGI registration tests PASS (6/6); synthetic Chromium integration PASS (7/7) for registration/login/Mi cuenta, domicile creation/query, cross-account isolation, no-CSRF rejection, logout, plus legacy CLI account compatibility.
- Actual downloaded CU09 PDFs PASS content checks; synthetic registered-account/CLI-account domicile and diary records persisted after backend restart. Original DB container ID stayed unchanged; synthetic DBs/artifacts are retained.
- Ruff, mypy, frontend tests (120/120), TypeScript, Oxlint, production build, OpenSpec strict, PowerShell runner parse, and `git diff --check` PASS. Build emitted existing bundler warnings.
- Backend confirmation: 491 total, 476 PASS, 8 FAIL, 7 SKIP. The initial 14-failure diagnostic was reduced by fixing CU06/OCR test-container configuration; the remaining 8 are unrelated active CU01/CU02 catalog/test mismatches and are detailed in the engineering record.
- No schema migration/dependency changes. No Archive, sync, or deploy. The user has explicitly authorized committing and pushing the complete current worktree; deployment remains unauthorized.
- The owner classified the earlier locally emitted environment value as synthetic/non-sensitive. It was not re-read or reproduced; no credential rotation is indicated by that classification.

## Shared CU01/CU02 territorial catalog - IMPLEMENTATION ACTIVE
- [Active OpenSpec change](../openspec/changes/unify-territorial-catalog/proposal.md), [engineering record](ai-engineering/unify-territorial-catalog.md).
- PostgreSQL is at `0010_territorial_alias_party_fk`; 12 parties, 93 locality names, 92 selectable localities, 99 source records, 14 aliases (2 unresolved). Existing report/work/account rows were preserved at the migration check.
- Live API parity passed: 12 parties/92 localities on both selectors, no CABA/CAPITAL, verified aliases equivalent, `Santa Anita` remains unverified; GeoRef address and reverse-location requests resolved.
- Isolated-schema migration test, full backend suite (485 passed; 247 prerequisite skips), Ruff and mypy pass. Frontend Docker build, 117 unit tests, lint, typecheck and CU01/CU02 Playwright (30/30) pass; E2E fixtures assert identical approved-party options and exclude CABA/CAPITAL.
- Live endpoint parity and GeoRef address/reverse-location checks passed. Static independent review found no actionable issues; independent runtime migration/data sign-off remains pending. Full CU01/CU02 PostgreSQL API integration suites remain blocked until an isolated migrated `TEST_DATABASE_URL` is available. No commit, push or archive.

## Mi cuenta redesign - STAGES 0/A/B/C/D/E ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-15-redesign-account-workspace/proposal.md), [record](ai-engineering/redesign-account-workspace.md), [U31-U35](use-cases/decisions.md).
- Stage A: h1 "Mi cuenta", "Índice de Mi cuenta", six sections; the CU05-CU08 cards became siblings of CU04; CU09 works without a meter.
- Stage B: "Contexto de trabajo" after the index with the only `selected-domicile` and `reading-meter` selectors; `AccountWorkspace` owns the meter selection as scope-tagged state; `DomicileManagement` stays the meter request owner; new `DomicileAddress` owns address correction; final order Domicilios, Medidores, Cortes, Lecturas, Facturas, Consumo.
- Stage C: CU05 reading/photo/OCR/history layout and CU06 invoice form/history layout; CU07 remains unchanged in the invoice section. No API/state/schema/store/backend/dependency changes.
- Stage D: CU07 comparison and CU08 consumption are presentation-only subpanels; existing CU08 bars retained, no new chart. Stage E: CU09 presentation-only composition and 24 synthetic screenshots at 1440/820/390; mock tests added.
- Stage E remains presentation-only. Independent accumulated review found a PDF-action regression; it was fixed, and reviewer follow-up confirmed the correction. Review accepts that exact Stage E hunk attribution is unavailable; no E-only attribution is claimed.
- Final Docker gates PASS: typecheck; lint 101 files; unit 117/117; build 336 modules; account E2E 30/30 and combined Playwright 46/46; post-archive OpenSpec strict 16/16 and `git diff --check`.
- Evidence: `docs/ai-engineering/evidence/redesign-account-workspace/{before,etapa-a,etapa-b,etapa-c,etapa-d,etapa-e}/`.
- Real seeded CU09 and QA-INT-CU04-08 BLOCKED: no confirmed isolated seeded QA setup; not reported as PASS.
- No backend/API/auth/CSRF/business-rule/dependency changes. Capture spec skips unless `VISUAL_CAPTURE=1`; 210 synthetic PNGs (~63 MB) retained.
- Archived only this change; specs synchronized (`account-workspace` added, `meter-readings` history isolation updated). The two temporary review packet files were removed.

## Closed work
- `redesign-public-works-admin` archived and committed at `a966867` (CU02 + CU10); `redesign-public-shell-cu01` at `223a61c`.
- CU01-CU10 are implemented and archived; CU02 definitive scope U22; CU03 SSE assistant; CU10 admin supervision.

## Blockers and unresolved decisions
- Public registration’s requested integration scenarios and final QA/static security review pass. Archive/closure remains BLOCKED by the failed broad backend gate (8 unrelated CU01/CU02 tests); broad Playwright for other CUs also lacks CU07/CU08 state fixtures.
- **QA-INT-CU04-08** deferred: real seeded CU04/CU06/CU07/CU08 Chromium specs not run.
- Real CU10 administrator E2E (`cu10-real.spec.ts`) not run.
- CU03 automatic 30-day retention deletion pending approval.
- Edesur guide v1.0.0 delivered; time-sensitive data needs periodic revalidation.
- CU05 OCR accuracy on real photos is not claimed.
- Hosting unresolved; deployment needs separate approval. `main` currently matches `origin/main`; the current user has authorized this worktree's commit and push.
- Deferred accessibility: M2 duplicate announcements, M3 shared table label, assistant overlay at 390 px, totals on stale/unavailable snapshots.

## Next actions
1. Assign the 8 unrelated CU01/CU02 test/catalog mismatches to their active change; do not alter those business rules in this registration change.
2. Decide whether to update the stale CU01/CU02 assertions/mock target under their own accepted specs, then rerun the affected checks and broad backend suite.
3. Provide CU07/CU08 synthetic state fixtures if a broad all-CU Playwright run is required.
4. Keep Archive blocked until required broad regression gates are resolved or explicitly dispositioned under project policy.
5. Run seeded QA-INT-CU04-08 / CU10 E2E only when an isolated prepared QA environment is available.

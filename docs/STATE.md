# Operational state - energia-sur

Updated: 2026-11-16 (territorial catalog implementation active; CU01/CU02 Playwright passed; final review/isolated API checks pending).

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
- **QA-INT-CU04-08** deferred: real seeded CU04/CU06/CU07/CU08 Chromium specs not run.
- Real CU10 administrator E2E (`cu10-real.spec.ts`) not run.
- CU03 automatic 30-day retention deletion pending approval.
- Edesur guide v1.0.0 delivered; time-sensitive data needs periodic revalidation.
- CU05 OCR accuracy on real photos is not claimed.
- Hosting unresolved; push and deployment need approval; one local commit ahead of `origin/main`.
- Deferred accessibility: M2 duplicate announcements, M3 shared table label, assistant overlay at 390 px, totals on stale/unavailable snapshots.

## Next actions
1. Inspect staged files, create the single authorized local commit, then verify clean status and origin state.
2. Run seeded CU09 and QA-INT-CU04-08 when an isolated prepared QA environment is available.
3. Run the real CU10 administrator E2E when seeded QA is available.
4. Await CU03 retention and hosting decisions; do not push or deploy.

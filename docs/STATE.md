# Operational state - energia-sur

Updated: 2026-11-20. Previous full backend gate on 2026-11-16: 493 tests, 486 passed, 7 skipped.

- CU01 address lookup now guides visitors to enter street and number, followed by the partido. The adapter sends a known partido's GeoRef department ID before the result limit. Bounded correction under the [existing CU01 contract](../openspec/specs/current-outages/spec.md#requirement-resolve-an-address-to-a-zone-via-georef). PASS: public Lanús address through Chromium and live GeoRef at 805 and 390 px, 31 mocked browser tests, 120 frontend unit tests, and 80 isolated backend tests (6 live-gated skips). Ruff, mypy, lint, build and strict CU01 spec validation passed.
- CU02 now uses the party and locality selectors directly and shares CU01 address parsing. The [CU02 UI scenario](../openspec/specs/scheduled-works/spec.md#scenario-search-and-address-assistance-are-separate) reflects the requested presentation change and the existing GeoRef contract. PASS: real scheduled works lookup by partido and by a public Lanús address in Chromium at 805 and 390 px, 38 mocked browser tests, 120 frontend unit tests, lint, build and strict CU02 spec validation.

## Public account registration - IMPLEMENTATION VERIFIED; CLOSURE GATE PENDING
- [Active OpenSpec change](../openspec/changes/add-public-account-registration/proposal.md), [engineering record](ai-engineering/add-public-account-registration.md), U36 in [decisions](use-cases/decisions.md#u36---public-account-registration-authorization).
- Focused PostgreSQL/ASGI registration tests PASS (6/6); synthetic Chromium integration PASS (7/7) for registration/login/Mi cuenta, domicile creation/query, cross-account isolation, no-CSRF rejection, logout, plus legacy CLI account compatibility.
- Actual downloaded CU09 PDFs PASS content checks; synthetic registered-account/CLI-account domicile and diary records persisted after backend restart. Original DB container ID stayed unchanged; synthetic DBs/artifacts are retained.
- Ruff, mypy, frontend tests (120/120), TypeScript, Oxlint, production build, OpenSpec strict, PowerShell runner parse, and `git diff --check` PASS. Build emitted existing bundler warnings.
- Final backend confirmation after CU01/CU02 test-only corrections: 493 total, 486 PASS, 7 external/live prerequisite SKIP, 0 FAIL. The run used a new PostgreSQL container on a private network with tmpfs storage; original Compose services/volumes were not used.
- Registration-specific browser/PDF/restart-persistence acceptance and static security/QA reviews remain PASS. No registration/session/auth/CSRF production code changed in the follow-up.
- No Archive, sync, commit, push, or deploy. Deployment remains unauthorized.
- The owner classified the earlier locally emitted environment value as synthetic/non-sensitive. It was not re-read or reproduced; no credential rotation is indicated by that classification.

## Shared CU01/CU02 territorial catalog - IMPLEMENTATION VERIFIED; REVIEW BLOCKED
- [Active OpenSpec change](../openspec/changes/unify-territorial-catalog/proposal.md), [engineering record](ai-engineering/unify-territorial-catalog.md).
- PostgreSQL is at `0010_territorial_alias_party_fk`; 12 parties, 93 locality names, 92 selectable localities, 99 source records, 14 aliases (2 unresolved). Existing report/work/account rows were preserved at the migration check.
- Live API parity passed: 12 parties/92 localities on both selectors, no CABA/CAPITAL, verified aliases equivalent, `Santa Anita` remains unverified; GeoRef address and reverse-location requests resolved.
- Final focused CU01/CU02 modules: 57 run, 55 passed, 2 live-source skips. The full suite also passed the territorial migration test. Final backend confirmation: 493 total, 486 passed, 7 prerequisite skips. Ruff, mypy, strict OpenSpec (19/19), and `git diff --check` passed.
- Final static reviewer confirmed the alias party-scope assertion gap is closed; reviewer could not inspect the full production diff or execute tests. Independent runtime migration/data sign-off remains BLOCKED; task 5.3 remains open. No commit, push or archive.

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
- Registration-specific acceptance and static reviews are complete; the broad backend suite now passes. Territorial catalog closure remains BLOCKED by mandatory independent runtime migration/data review (reviewer has no shell runner).
- **QA-INT-CU04-08** deferred: real seeded CU04/CU06/CU07/CU08 Chromium specs not run.
- Real CU10 administrator E2E (`cu10-real.spec.ts`) not run.
- CU03 automatic 30-day retention deletion pending approval.
- Edesur guide v1.0.0 delivered; time-sensitive data needs periodic revalidation.
- CU05 OCR accuracy on real photos is not claimed.
- Hosting unresolved; deployment, commit, and push require separate approval. No commit or push occurred in this work.
- Deferred accessibility: M2 duplicate announcements, M3 shared table label, assistant overlay at 390 px, totals on stale/unavailable snapshots.

## Next actions
1. Obtain independent runtime review of territorial migration/data behavior; static review is not runtime sign-off.
2. Rerun Ruff, mypy, strict OpenSpec validation and `git diff --check` after final documentation edits.
3. Request reviewer follow-up on canonical alias tests; record runtime review as BLOCKED if no independent runner is available.
4. Keep the territorial catalog unarchived until mandatory review passes; registration broad backend gate is green.
5. Prepare isolated synthetic fixtures for end-to-end regression of CU04–CU08 and CU10 when required.

# Operational state - energia-sur

Updated: 2026-11-14 (redesign-public-works-admin archived; single local commit; nothing pushed).

## Public works/admin redesign - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-14-redesign-public-works-admin/proposal.md), [record](ai-engineering/redesign-public-works-admin.md), [U29](use-cases/decisions.md#u29---cu02-visual-redesign-stage-a-and-stage-b-proposal-authorization), [U30](use-cases/decisions.md#u30---cu10-visual-redesign-stage-b-authorization).
- Stage A: CU02 split into "Consultar trabajos" and "Buscar por dirección"; `ScheduledWorksResultCard.tsx` adds state chips, scope, unpublished dates, the existing five-column table and provenance. No date filters; query/address/location behavior unchanged.
- Stage B: `AdminPanel.tsx` + presentational `SourceCard.tsx` with "Estado", "Configuración" and "Acciones", status chips, preserved failure-versus-success and the existing retry/interval/CSRF/409 behavior.
- Evidence: `docs/ai-engineering/evidence/redesign-public-works-admin/` (24 `before/`, 18 CU02 `etapa-a/`, 6 CU10 `etapa-b/` synthetic PNGs).
- PASS: typecheck, lint (101 files), 117/117 unit, build (333 modules), CU02 14/14, CU10 15/15, focused Playwright 68/68, strict OpenSpec 15/15 after archive. Both independent reviews were corrected/re-verified; no BLOCKER/HIGH.
- Archived 2026-11-14; `scheduled-works` and `source-refresh-administration` synchronized (~2 modified, none added/removed). One local commit; no push.

## Public shell + CU01 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-14-redesign-public-shell-cu01/proposal.md), [record](ai-engineering/redesign-public-shell-cu01.md), U27/U28, [spec](../openspec/specs/frontend-shell/spec.md).
- Approved palette, identity header/nav/footer, 1200 px main, single `h1`, skip link, header logout. CU01 uses search/address cards and `OutagesResultCard.tsx`.
- Archived 2026-11-14; `frontend-shell` synchronized. Local commit `223a61c` is on `origin/main` according to the read-only remote check.

## CU10 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/proposal.md), [spec](../openspec/specs/source-refresh-administration/spec.md), [record](ai-engineering/supervise-source-refresh-cu10.md); U24/U25/U30.
- Admin-only supervision of both ENRE sources, intervals and synchronous retry. Visual Stage B is archived with the current redesign.

## Other closed work
- CU01, CU02, CU03, CU04, CU05, CU06, CU07, CU08 and CU09 are implemented, verified and archived.
- CU02 definitive scope (U22): ENRE `cortesProgramados`; no agenda, date filters, planned dates, reasons or distances.
- CU03: SSE assistant with CU01/CU02 read tools, one `ChatMount`, owner-scoped memory and CSRF delete.

## Blockers and unresolved decisions
- **QA-INT-CU04-08** remains deferred: real seeded CU04/CU06/CU07/CU08 Chromium specs not run.
- Real CU10 administrator E2E (`cu10-real.spec.ts`) was not run; current acceptance is mocked UI plus preserved backend contracts.
- CU03 automatic 30-day retention deletion remains pending approval.
- Edesur guide v1.0.0 delivered; time-sensitive data needs periodic revalidation.
- CU05 OCR accuracy on real photos is not claimed; the supplied real photograph abstains (accepted).
- Hosting remains unresolved; push and deployment need explicit approval.
- Deferred accessibility: M2 duplicate announcements, M3 shared table region label, assistant overlay at 390 px, totals on stale/unavailable snapshots.

## Next actions
1. Run **QA-INT-CU04-08** and the integral CU01-CU10 regression before delivery.
2. Run the real CU10 administrator E2E when the synthetic admin environment is available.
3. Await approval for the 30-day automatic retention deletion.
4. Resolve hosting before deployment; pushing the local commit remains unauthorized.
5. Start the next visual change only under a new authorized OpenSpec change.

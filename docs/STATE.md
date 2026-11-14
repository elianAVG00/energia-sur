# Operational state - energia-sur

Updated: 2026-11-14 (public shell and CU01 redesign archived; single local commit prepared; nothing pushed).

## Public shell + visual system - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-14-redesign-public-shell-cu01/proposal.md), [record](ai-engineering/redesign-public-shell-cu01.md), [U27](use-cases/decisions.md#u27---public-shell-and-visual-system-stage-a-authorization), [U28](use-cases/decisions.md#u28---cu01-visual-redesign-stage-b-authorization), [spec](../openspec/specs/frontend-shell/spec.md).
- Stage A: approved light tokens, identity header with horizontal nav and active `aria-current`, conditional Administración, single header `Cerrar sesión`, skip link, 1200 px main, single `h1` + description, informational footer, title "Energía Sur". `Cuenta: {username}` and the single `ChatMount` preserved.
- Stage B (tasks 6.1-6.4): CU01 split into "Consultar cortes" and "Buscar por dirección" cards; new presentational `features/outages/OutagesResultCard.tsx` with state chips, Edesur-wide stat tiles plus caveat, table and provenance; initial/loading/error/state panels; error and status texts routed to the card that produced them; no green success signal for unverified coverage. Existing ids `outage-filter`, `outage-partido`, `outage-localidad`, `outage-address`, labels, functional messages, handlers, validation, geolocation, requests and data are unchanged; only presentational guidance text is new.
- PASS: typecheck, lint (97 files), 117/117 unit tests, build (331 modules), 47/47 focused Playwright (`cu01` 14 including state/width/scroll-region, no-reports, loading and address-feedback cases, `cu02` 5, `cu03` 1, `cu03-auth` 2, `cu05-history` 9, `cu10` 9, `redesign-shell` 7), strict OpenSpec 16/16, 6 CU01 viewport captures + 12 state captures at 1440/820/390 px (Stage A `before/` and `after/` preserved).
- NOT APPLICABLE: CU04/CU06-CU08/CU09 real specs (QA-INT-CU04-08 remains deferred).
- Independent review: M1, M4, M5, M6 and L1-L4 were corrected and re-verified; pre-existing M2/M3 and the remaining LOW items are deferred and recorded in the engineering record.
- Archived 2026-11-14 as `2026-11-14-redesign-public-shell-cu01`; `frontend-shell` synchronized (+3 added, ~1 modified, 0 removed) and strict validation passes 15/15 afterwards. Single local commit; nothing pushed. Stage A `before/` and `after/` evidence preserved.

## Public API health panel - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-14-remove-public-api-health-panel/proposal.md), [record](ai-engineering/remove-public-api-health-panel.md), U26. Panel unmounted; `/health`, `/api/health`, Vite proxy and script checks unchanged. Not pushed.

## CU03 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/proposal.md), [assistant spec](../openspec/specs/assistant/spec.md), [record](ai-engineering/implement-integrated-assistant-cu03.md); U23. SSE assistant with CU01/CU02 tools, one `ChatMount`, owner-scoped memory, CSRF delete. Automatic 30-day deletion pending approval. No push.

## CU01 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/proposal.md), [spec](../openspec/specs/current-outages/spec.md); U16/U20. Public ENRE snapshot, GeoRef/coverage, public panel. No push.

## CU02 - COMPLETED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-10-implement-scheduled-works-cu02/proposal.md), [spec](../openspec/specs/scheduled-works/spec.md); U21/U22. ENRE `cortesProgramados` only. No push.

## CU10 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/proposal.md), [spec](../openspec/specs/source-refresh-administration/spec.md), [record](ai-engineering/supervise-source-refresh-cu10.md); U24/U25. Admin-only supervision of both ENRE sources, intervals and synchronous retry.

## CU05 - CLOSED / ARCHIVED
- [Archived base change](../openspec/changes/archive/2026-11-13-record-cu05-meter-readings/proposal.md), [isolation change](../openspec/changes/archive/2026-11-13-isolate-cu05-reading-history-by-meter/proposal.md), [spec](../openspec/specs/meter-readings/spec.md); paragraph-5 contract resolution recorded. `cu05-history` 9/9, typecheck/lint/build pass.
- Deferred: **QA-INT-CU04-08** seeded CU04/CU06/CU07/CU08 real Chromium specs not executed; not PASS.

## Other CUs
- CU08, CU07, CU06, CU04 and CU09 are implemented, verified and archived.

## Approved stack and existing implementation
- React/TS/Vite/npm and Python/FastAPI/uv/PostgreSQL 18.6 with SQLAlchemy/psycopg/Alembic; pinned images and dependencies.
- Implemented: CU09 auth/diary, CU04-CU08, CU01, CU02, CU03, CU10 and the Stage A/B shell.

## Blockers and unresolved decisions
- CU03 automatic retention deletion remains pending approval (30-day policy documented).
- Guide delivered (v1.0.0, 2026-11-10); time-sensitive data still needs periodic revalidation.
- CU05 OCR accuracy on real photos is not claimed; the supplied real photograph abstains (accepted).
- **QA-INT-CU04-08** pending: real seeded CU04/CU06/CU07/CU08 specs deferred to integral regression.
- Hosting remains unresolved; other catalog TBDs remain open.
- Accessibility follow-up (future authorized change): M2 aria-live/duplicate announcements, M3 shared table region label, floating-assistant overlay at 390 px, and totals presentation on stale/unavailable snapshots. All are pre-existing or explicitly deferred and recorded in the Stage B record.

## Next actions
1. Open a separately authorized accessibility change for the deferred items above (M2, M3, assistant overlay, totals on stale/unavailable).
2. Run **QA-INT-CU04-08** and the integral CU01-CU10 regression before delivery.
3. Await approval for the 30-day automatic retention deletion.
4. Resolve hosting before deployment; pushing the local commit awaits explicit authorization.
5. CU02 and the authenticated area keep their current presentation until a new redesign change is authorized.

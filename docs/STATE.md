# Operational state - energia-sur

Updated: 2026-11-10 (CU01 synced and archived; 0.1/0.4 accepted exceptions; CU02 is the next use case; CU08/CU07/CU06 archived; CU05 red-fraction decision open).

## CU01 - CLOSED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/proposal.md), [design](../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/design.md), [tasks](../openspec/changes/archive/2026-11-10-implement-current-outages-cu01/tasks.md) (34/34), [main spec](../openspec/specs/current-outages/spec.md) (18 requirements), [engineering record](ai-engineering/implement-current-outages-cu01.md); [U16](use-cases/decisions.md#u16---cu01-current-outages-decisions-and-traceability) records D1–D11/T1–T3, [U17](use-cases/decisions.md#u17---cu01-build-1-authorization)–[U19](use-cases/decisions.md#u19---cu01-build-3-authorization) the three build stages and [U20](use-cases/decisions.md#u20---cu01-final-verification-and-closure-preparation) the final verification and accepted exceptions.
- Backend: ENRE → FastAPI → PostgreSQL → public API plus GeoRef/coverage (`enre_client`, `enre_parser`, `outage_store`, `georef`, `coverage`, `outages_api`). Frontend: public `features/outages/` panel, catalog-driven partido/localidad, GeoRef candidates, consented GPS, all normative states, provenance/totals; "Cortes"/"Mi cuenta" shell without a router and a narrow public-POST allowlist.
- PASS: 51/51 backend CU01 tests (live ENRE/GeoRef), Ruff/mypy (38 files), 106/106 frontend tests, Oxlint/TypeScript/build, 9/9 mocked CU01 Chromium flows, 1/1 real-backend CU01 smoke, real CU09 E2E 1/1, `openspec validate --strict`; full backend suite 368 tests with only 2 pre-existing CU05 OCR failures.
- Accepted exceptions (U20): 0.1 unobserved media/preventivo shapes (fail-closed parser, last snapshot preserved, synthetic fixtures only) and 0.4 partial nine-localidad coverage catalog (provenance documented; unverified stays `coverage_unverified`). Archived on 2026-11-10; no push performed.

## CU08 - IMPLEMENTED / VERIFIED / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/proposal.md), [design](../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/design.md), [tasks](../openspec/changes/archive/2026-11-09-view-cu08-consumption-evolution-and-estimates/tasks.md) (16/16), [main spec](../openspec/specs/consumption-trends/spec.md), [engineering record](ai-engineering/view-cu08-consumption-evolution-and-estimates.md); [U15](use-cases/decisions.md#u15---cu08-consumption-evolution-and-estimate-propose-authorization) and [R01–R07](use-cases/decisions.md#cu08-r01-r07---approved-residual-decisions).
- Read-only evolution/estimate endpoints and `features/consumption/` (no tables, migrations or dependencies). PASS: domain/adapter/PostgreSQL tests, Ruff/mypy, frontend 93 tests, Oxlint, TypeScript, build, 4/4 Chromium, OpenSpec strict. Eight global-suite failures were diagnosed as CU05/CU06 environmental configuration, not CU08.
- Sync created `consumption-trends` on 2026-11-09; archived. No commit or push.

## CU07 - COMPLETE / ARCHIVED
- [Archived change](../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/proposal.md), [design](../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/design.md), [tasks](../openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/tasks.md) (13/13), [main spec](../openspec/specs/bill-comparisons/spec.md), [engineering record](ai-engineering/compare-cu07-consumption-with-bill.md), [U14](use-cases/decisions.md#u14---cu07-revised-matching-and-comparison-authorization).
- Read-only CU05/CU06 comparison with ±7-day candidates, exact/approximate confirmation, manual selection, exact kWh and cross-account isolation; no new tables or dependencies. PASS: 278 backend tests, Ruff/mypy, frontend 80 tests, Oxlint, TypeScript, build, 4/4 Chromium, OpenSpec strict.

## CU06 - CLOSED
- [Archived change](../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/proposal.md), [design](../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/design.md), [tasks](../openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/tasks.md) (16/16), [main spec](../openspec/specs/electricity-bills/spec.md), [engineering record](ai-engineering/record-cu06-electricity-bills.md), [Q12](use-cases/decisions.md#q12).
- Owner-only bill list/create/detail/edit and private attachments; duplicates, overlap confirmation, versions, idempotency, startup reconciliation and a separate `cu06_bills` volume. PASS: 243 backend tests, Ruff/mypy, frontend 80 tests, Oxlint, TypeScript, build, OpenSpec strict, two-account flow, backup/restore; independently reviewed.

## Active CU05 proposal
- [Proposal](../openspec/changes/record-cu05-meter-readings/proposal.md), [design](../openspec/changes/record-cu05-meter-readings/design.md), [delta](../openspec/changes/record-cu05-meter-readings/specs/meter-readings/spec.md), [tasks](../openspec/changes/record-cu05-meter-readings/tasks.md); [U13](use-cases/decisions.md#u13---cu05-functional-decisions-and-propose-authorization) and [M1](use-cases/decisions.md#cu05-m1---ocr-may-abstain-closure-decision).
- PASS isolated backend/frontend gates, container safety tests, backup/restore and two Chromium DEV flows; synthetic artifacts are listed in [evidence](ai-engineering/record-cu05-meter-readings.md) and must not hold real data. The red-fraction contract conflict remains BLOCKED for Sync/Archive.

## CU09, CU04 and stage 05 checkpoint
- **CU04 IMPLEMENTED / VERIFIED / ARCHIVED:** [proposal](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/proposal.md), [design](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/design.md), [tasks](../openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/tasks.md); U11/U12 and REVIEW authorized Apply. PASS: 91 backend tests, 56 frontend tests, browser CU04 4/4 and CU09 1/1, PDF and restart checks; [evidence](ai-engineering/manage-cu04-domiciles-meters.md).
- **Stage 05 CLOSED documentarily:** [catalog](use-cases/README.md), [shared rules](use-cases/shared-rules.md), [register](use-cases/decisions.md) and [workflow](openspec-workflow.md) accepted under [U06](use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization); **Q00 approved** on user confirmation. Apply entry checkout was clean `main`, ahead 1, HEAD `f76bc0f06b24666ff7852010142baf218dc8eed4`.
- **CU09 + foundation archived:** [CU09 archive](../openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/), [foundation archive](../openspec/changes/archive/2026-11-08-establish-frontend-foundation/), [evidence](ai-engineering/establish-frontend-foundation.md), [reuse guide](frontend-foundation.md); U07/U07-T/U09/U10 approved the technical package and foundation Apply. No commit/push/deployment.

## Approved stack and existing implementation
- React/TS/Vite/npm and Python/FastAPI/Uvicorn/uv/PostgreSQL pins preserved; CU09 added SQLAlchemy/psycopg/Alembic, ReportLab, Playwright/pypdf and Ruff/mypy. PostgreSQL `db:5432` is internal; loopback mappings 5173/8000; images use verified linux/amd64 digests and run non-root.
- `/api/health` proxies to `GET /health`, liveness only. Implemented: private login/logout, owned domiciles/meters, CU09 cuts/summaries/PDFs, CU05 readings/OCR, CU06 bills, CU07 comparisons and CU08 evolution. No chatbot runtime.
- Foundation includes Tailwind/local shadcn primitives, memory-only Zustand, RHF/Zod, shared Axios and one unavailable CU03 mount. Existing synthetic DB credentials/data are technical-only; do not read secrets for context.

## Existing technical changes
- Docker remains OPEN: [18/22 tasks](../openspec/changes/docker-development-environment/tasks.md), [design](../openspec/changes/docker-development-environment/design.md), [evidence](ai-engineering/docker-development-environment.md); tasks 1.4/2.4/7.1/7.2 stay unchecked.
- Development MCP remains 8/8 checked and unarchived: [tasks](../openspec/changes/configure-readonly-development-mcp/tasks.md), [evidence](ai-engineering/configure-readonly-development-mcp.md). Installed CLI 1.16.1, schema `spec-driven`.

## Blockers and unresolved decisions
- CU01 exceptions accepted by U20: unobserved media/preventivo shapes (0.1) and the partial nine-localidad coverage catalog (0.4); unverified zones stay `coverage_unverified` and no coverage or negative result is invented.
- Low CU09 residuals: out-of-band pre-1970 rows can fail reads; NUL text may yield 503. Retained synthetic databases/containers/volumes must not be deleted or reused with real data without authorization.
- Unrelated catalog TBDs, hosting and persistent chatbot memory remain unresolved; CU02, CU03 and CU10 remain planned, and no CU02 work has started.

## Next actions
1. CU01 is archived; start CU02 only on a new explicit request.
2. Resolve the CU05 red-fraction contract conflict before its Sync/Archive.
3. Keep synthetic DEV accounts/data and retained artifacts until deletion is explicitly authorized.
4. Reuse the foundation for future accepted CUs; CU03 chat runtime remains separate.

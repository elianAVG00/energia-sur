# Operational state - energia-sur

Updated: 2026-11-07T06:02:01-03:00.

## Latest checkpoint - stage 05 CLOSED; stage 06 proposal REVIEW
- Checkout: `main` tracking `origin/main`, HEAD `96192587c03bd0897637ba238a0285b5f1588581`; incoming two tracked edits and 17 untracked files preserved, no staging/history changes.
- **Stage 05 CLOSED documentarily:** user explicitly accepts [catalog](use-cases/README.md), [shared rules](use-cases/shared-rules.md), [register](use-cases/decisions.md) and [workflow](openspec-workflow.md), including their remaining TBDs. See [U06](use-cases/decisions.md#u06---baseline-acceptance-and-cu09-proposal-authorization) and [closure record](ai-engineering/stage-05-sdd.md#accepted-baseline-checkpoint---u06).
- **Q00 APPROVED:** user confirms the teacher approved all ten Energía Sur CUs. No teacher approval date/channel recorded. This satisfies the academic prerequisite, not design/Apply authorization.
- **CU09 SELECTED first for stage 06:** [proposal](../openspec/changes/record-cu09-interruption-diary/proposal.md), [design](../openspec/changes/record-cu09-interruption-diary/design.md), [delta specs](../openspec/changes/record-cu09-interruption-diary/specs/interruption-diary/spec.md), [tasks](../openspec/changes/record-cu09-interruption-diary/tasks.md), [engineering evidence](ai-engineering/record-cu09-interruption-diary.md).
- PASS: strict OpenSpec 3/3 changes, zero main specs; 10 fiches/44 traced catalog scenarios; 2 new deltas/10 requirements/17 scenarios; 260 links/160 anchors, scope/whitespace/preservation. Planning 4/4 artifacts, tasks 0/24. No Apply, implementation, Sync, Archive, installation, AGENTS edit, commit or push.

## Approved stack and existing implementation
- React + TypeScript/Vite/npm (Node 24.22.2, npm 11.19.1); Python 3.13.18/FastAPI/Uvicorn/uv; PostgreSQL 18.6 in Compose. Manifests/locks and source are unchanged in stage 05.
- PostgreSQL `db:5432` is internal; `pgdata` at `/var/lib/postgresql`. Loopback frontend/backend mappings are 5173/8000. Images use verified linux/amd64 digests; services run non-root.
- `/api/health` proxies to `GET /health`, HTTP liveness only, with no database/provider readiness claim. Backend LangChain + OpenAI is confirmed later direction, not installed here.
- Historical Docker evidence: healthy services, four backend tests, 25 frontend helper/state tests, strict TS/build, real proxy and SQL persistence PASS; human browser success/error/recovery confirmed. None rerun for documentation.
- Existing synthetic database credentials/data are technical-only; changing `.env` does not rotate persisted credentials. Preserve `energia-sur_pgdata` and do not read secrets for context.

## Existing technical changes and evidence
- Docker remains OPEN: [18/22 tasks](../openspec/changes/docker-development-environment/tasks.md), [design](../openspec/changes/docker-development-environment/design.md), [delta spec](../openspec/changes/docker-development-environment/specs/development-environment/spec.md), [runtime/review evidence](ai-engineering/docker-development-environment.md).
- Tasks 1.4, 2.4, 7.1 and 7.2 remain unchecked due to unresolved lint/backend static-type gates. Prior independent static Apply review is historical, not a stage 05 Codex review.
- Development MCP setup remains 8/8 checked and unarchived: [tasks](../openspec/changes/configure-readonly-development-mcp/tasks.md), [real-call evidence](ai-engineering/configure-readonly-development-mcp.md). No fresh token/isolation assurance claimed.
- Installed CLI 1.16.1, schema `spec-driven`, custom profile with explore/propose/apply/update/sync/archive. Review and Verify are team steps; installed generated skills/configuration preserved.

## Blockers and unresolved decisions
- CU09 Apply BLOCKED pending proposal/design acceptance of D0-D5 and a separate implementation request. Minimum CU04 slice is register/list/select own domicile, not meters/full CU04; input/provisioning needs design approval.
- CU09 business rules approved: Buenos Aires minute dates, future rejection/end-after-start, owner-only five operations, open/closed correction, positive clipped union total hours/minutes, descending PDF table/“En curso”. Auth technology, PostgreSQL integration and PDF generation remain unapproved design choices.
- Register: 6 approved, 6 partial, 12 open. Unrelated reading validity Q10, CU07 presentation Q14, CU08 formula/period Q15/Q16 and lifecycle exclusions remain; no auth/driver/ORM/migration/hosting/memory/test tooling choice inferred.
- Docker Verify closure remains BLOCKED until approved lint/backend-type tooling is configured and checks pass; browser/SQL success does not waive them.

## Next actions
1. Review CU09 proposal/delta contracts and accept or revise D0-D5, especially domicile input, sessions/provisioning, persistence/migrations and PDF dependency/delivery.
2. Confirm technical minute/clock/payload, correction-edge/concurrency and API/error contracts; do not reopen approved counting/owner policies.
3. Approve exact dependencies/test/lint/type tooling where needed, then explicitly request Apply in a later interaction; no code now.
4. Preserve database data and complete remaining Docker lint/backend-type gates independently; no silent waiver.
5. Require real CU09 end-to-end evidence and independent auth/isolation review before implementation closure; Sync/Archive/commit/push need separate authorization.

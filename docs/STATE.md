# Operational state - energia-sur

Updated: 2026-11-07T04:19:26-03:00.

## Latest checkpoint
- Stage 04: Docker environment design approved; planning artifacts prepared, no Apply, commit, push, sync, or archive.
- This run began on clean `main`, three commits ahead of `origin/main`; prior work and MCP artifacts preserved.
- Latest planning gate PASS: strict OpenSpec validation, tracked/staged/untracked whitespace, 24 local links, 46-line/five-action STATE, and 22 unchecked tasks; see [evidence](ai-engineering/docker-development-environment.md).

## Confirmed decisions and implementation state
- Frontend: React + TypeScript, Vite, Node 24.22.2, npm 11.19.1 approved by user on 2026-11-07.
- Backend: Python 3.13.18, FastAPI, Uvicorn, uv with `pyproject.toml` and `uv.lock` approved.
- Database engine DECIDED: PostgreSQL 18.6, service `db` included from first Compose startup; not an unresolved motor choice.
- Database persistence: named `pgdata` at `/var/lib/postgresql`; internal `db:5432`, no published host port.
- Frontend/backend host ports: `127.0.0.1:5173` and `127.0.0.1:8000`; `/api/health` proxies to backend `GET /health` (200 JSON `{"status":"ok"}`).
- LangChain + OpenAI API in backend is confirmed direction for a separate change; initial environment must start without `OPENAI_API_KEY`.
- `frontend/` and `backend/` still contain only `.gitkeep`; no application manifests, locks, entry points, Dockerfiles, Compose, tests or CI workflows exist.
- Approved versions are targets, not verified registry tags/digests or successful builds. Those checks, locks and real builds remain Apply tasks.
- Acceptance A: actual React/API success, then visible error clearing success when backend stops and another check is requested.
- Acceptance B: `psql` query and committed unique synthetic datum surviving `db` recreation with the same volume; no application/database connection required.

## OpenSpec and evidence
- Schema `spec-driven`, installed CLI 1.16.1; no main specs yet.
- New change: [docker-development-environment tasks](../openspec/changes/docker-development-environment/tasks.md); all implementation tasks intentionally unchecked.
- Approved decisions/rationale: [Docker design](../openspec/changes/docker-development-environment/design.md); behavior: [spec](../openspec/changes/docker-development-environment/specs/development-environment/spec.md).
- Process/check evidence: [Docker record](ai-engineering/docker-development-environment.md). Structural validation does not prove runtime acceptance.
- GitHub MCP + Context7 setup COMPLETED per [8/8 checklist](../openspec/changes/configure-readonly-development-mcp/tasks.md); no archive. Earlier positive live calls and independent policy review are prior evidence, not rerun here.
- Earlier MCP validation PASS on CLI 1.16.1; broader runtime permission/path/symlink and token-scope assurance remains unproven. See [MCP record](ai-engineering/configure-readonly-development-mcp.md).
- Existing five agent profiles and generated integrations preserved. Profiles restrict shell/external reads/delegation; static permission evidence does not establish runtime isolation.
- Custom Skills [fastapi-endpoint](../.agents/skills/fastapi-endpoint/SKILL.md) and [quality-gate](../.agents/skills/quality-gate/SKILL.md) exist; quality-gate and openspec-propose loaded for this planning run.

## Pending work and blockers
- No blocker to approved planning. Implementation and real acceptance remain unexecuted; a separate Apply request is required.
- Apply must verify image tags/digests/platforms, select exact uv/library releases, generate locks and build. Stop for user review if approved versions are unavailable.
- Test/lint frameworks and runnable application checks remain to be agreed where needed; new tooling must not silently fill a TBD.
- FastAPI/PostgreSQL integration, driver, ORM, migrations and business tables are excluded and require later changes/decisions.
- Application auth/authorization, hosting and persistent assistant memory remain unresolved; unrelated TBDs do not block a storage-free technical API.
- Teacher approval of topic and ten use cases is still undocumented; business implementation remains BLOCKED, authorized environment/spec preparation may proceed.
- No secrets or actual credentials were inspected. `.env` configuration is future local setup, not supplied or created here.

## Next actions
1. Review the Docker planning/doc diff and actual final gate results linked above.
2. Request Apply separately for the approved technical environment, keeping implementation scope bounded by its tasks/spec.
3. In Apply, verify images/tool versions and resolve required exact dependency and verification-tool choices before installation.
4. Complete and record both independent real acceptance tests before claiming environment implementation success.
5. Document teacher approval and plan later business/database/assistant changes; obtain separate authorization for commit, push, sync or archive.

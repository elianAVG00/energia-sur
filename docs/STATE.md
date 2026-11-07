# Operational state - energia-sur

Updated: 2026-11-07T04:55:27-03:00.

## Latest checkpoint
- Focused Verify: human browser success/error/recovery confirmed; change OPEN and closure BLOCKED by tooling/check decisions. No archive, commit, push or sync.
- This Verify began on `main`, ahead 4, preserving the existing Apply diff and technical files; only documentation/tasks updated.
- Prior runtime checks PASS reused after hash/code identity checks. Focused strict OpenSpec, tracked/staged/untracked whitespace, local links/scope and STATE/task consistency PASS; see [evidence](ai-engineering/docker-development-environment.md).
- Progress: 18/22 tasks evidenced; 1.4, 2.4, 7.1 and 7.2 remain unchecked because mandatory lint/backend static-type gates are unresolved.

## Approved stack and current implementation
- Frontend: React + TypeScript, Vite, Node 24.22.2, npm 11.19.1; backend: Python 3.13.18, FastAPI, Uvicorn, uv with real `pyproject.toml`/`uv.lock`.
- Database engine DECIDED: PostgreSQL 18.6 as `db` from first startup; named `pgdata` at `/var/lib/postgresql`, internal `db:5432`, no published host port.
- Official Python/Node/PostgreSQL image and upstream uv 0.13.7 tags/index digests were verified for linux/amd64 before pinning; no approved runtime substitution.
- Exact libraries: React/DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.6, FastAPI 0.162.0, Uvicorn 0.54.0; generated npm/uv locks and locked builds PASS.
- Both application services run non-root. Build contexts exclude host environments/secrets. Source-only development mounts preserve container-installed dependencies.
- Compose services frontend/backend/db healthy; only host mappings are `127.0.0.1:5173` and `127.0.0.1:8000`.
- `/api/health` proxies to `GET /health` (200 JSON `{"status":"ok"}`); backend liveness remains available with db stopped and makes no database/provider readiness claim.
- Startup verified with `OPENAI_API_KEY` unset. LangChain + OpenAI backend assistant remains confirmed direction for another change, not installed here.
- Synthetic acceptance credentials supplied only in the child process environment; no actual credentials or `.env` file read/created. Test volume contains synthetic technical data only.

## Evidence and OpenSpec
- [Active tasks](../openspec/changes/docker-development-environment/tasks.md), [design](../openspec/changes/docker-development-environment/design.md), [spec](../openspec/changes/docker-development-environment/specs/development-environment/spec.md), [AI Engineering record](ai-engineering/docker-development-environment.md).
- Backend: 4 standard-library ASGI/model/lifespan tests PASS; frontend: 25 built-in Node helper/state tests, strict TypeScript and production build PASS. These do not render React.
- Acceptance A PASS: human user confirmed real browser success -> backend-down error -> restored success, combined with reused actual HTTP/proxy evidence. No agent-run browser or screenshot/trace is claimed.
- Acceptance B PASS: SELECT 1 and marker `4811ca06-7c8a-403a-bf63-2f1cbf58d924` survived db container recreation with the same `energia-sur_pgdata`. Normal stop/start also retained it; volume never deleted.
- Rootless uv-cache failure resolved after second correction (writable runtime cache plus no build cache); corrected npm negative fixture after verifying availability. Detailed attempts retained in evidence.
- Independent Apply reviewer: no confirmed static defects, reused unchanged-code review. Verify docs self-reviewed; human browser evidence and primary Apply execution are attributed separately.
- Schema spec-driven, CLI 1.16.1. Initial and final strict validation PASS; no main specs synced or change archived.
- GitHub MCP + Context7 setup remains COMPLETED per [8/8 checklist](../openspec/changes/configure-readonly-development-mcp/tasks.md); broader permission/path/token assurance not rerun or proven.
- Skills/agent definitions and existing MCP artifacts preserved. Actual backend/frontend delegates edited assigned source only; primary ran commands and a separate reviewer audited statically.

## Blockers and separate decisions
- Both runtime acceptances satisfied; Verify cannot close until required lint/backend static-type tools are approved, configured and their checks pass.
- Additional test/lint frameworks and backend static typing require separate approval where needed. None installed to fill the TBD; lint/backend-type and compound final gates remain BLOCKED.
- FastAPI/PostgreSQL connection, driver, ORM, migrations and business tables remain excluded and require later changes. Application auth/hosting and persistent assistant memory are unresolved.
- Teacher approval of topic/ten use cases is undocumented and still gates business implementation, not the authorized technical environment.
- Existing PostgreSQL initialization password is synthetic: changing `.env` does not rotate persisted credentials. Provision intended credentials explicitly before real data/database integration.

## Next actions
1. Review the focused Verify evidence and 18/22 task accounting; keep the change open.
2. Decide exact versions/configuration of proposed Ruff, ESLint/typescript-eslint and mypy (or explicitly approved alternatives), without silently installing them.
3. Run the approved lint/backend-type checks and reconcile 1.4/2.4 and compound final gates 7.1/7.2 only when complete.
4. Preserve `energia-sur_pgdata`; use documented non-destructive stop/start and configure development credentials deliberately.
5. Document teacher approval and plan later database/business/assistant changes; obtain separate authorization before commit, push, sync or archive.

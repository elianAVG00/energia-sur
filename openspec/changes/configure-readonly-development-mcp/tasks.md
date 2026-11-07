# Tasks

## 1. Approved configuration and boundaries

- [x] 1.1 Add project opencode.jsonc with remote read-only GitHub, Context7 OAuth, secret reference, global denies, and build-only ask rules; verify JSON parsing and native OpenCode loading without printing credentials.
- [x] 1.2 Verify loaded primary, custom subagent, and built-in subagent permission rules; record static cases/evidence and preserve existing rules and edit boundaries.
- [x] 1.3 Document authentication/setup and approved test calls in README and an English engineering record; update STATE.md within 60 lines/five next actions.
- [x] 1.4 Obtain independent read-only security review and address confirmed in-scope findings; record the result and any limitations before claiming verification complete.

## 2. User authentication and live verification

- [x] 2.1 User supplies a fine-grained read-only PAT via ENERGIA_SUR_GITHUB_PAT to the service and signs into Context7 through /mcps; verify connected states without reading credential values.
- [x] 2.2 Discover GitHub get_file_contents and read elianAVG00/energia-sur README.md at refs/heads/main after approval; record redacted actual response metadata without remote writes.
- [x] 2.3 Discover Context7 resolve-library-id/query-docs, resolve FastAPI, and query validation/error documentation using the returned library ID; record redacted actual results.
- [x] 2.4 Rerun applicable structural/diff checks, reconcile evidence and state, and confirm all mandatory checks/review pass; keep blocked tasks open and do not archive prematurely.

## Workflow follow-up

- Live evidence: [engineering record](../../../docs/ai-engineering/configure-readonly-development-mcp.md#live-verification--2026-11-07). The user reported both servers Connected; actual calls succeeded. Credentials and token scope were not inspected or audited.
- Archive only after live verification, mandatory review, and all required checks succeed through the installed authorized workflow.
- Commits and pushes require separate explicit approval; none are included here.

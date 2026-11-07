# Operational state — energia-sur

Updated: 2026-11-07T03:41:51-03:00.
Initial snapshot: 2026-11-07T02:01:41-03:00.

## Verified facts
- Initial milestone: AGENTS.md installed and reading/comprehension acceptance check performed.
- Latest milestone: all three agreed live MCP calls and applicable final checks PASS; user reports both servers Connected in /mcps. Diff ready for review; no commit/archive.
- Live session began on main, two commits ahead of origin/main, with existing setup/doc changes and untracked artifacts. Existing profiles, Skills, instructions, and commits preserved.
- Frontend: `frontend/` contains only `.gitkeep`; React + TypeScript selected, no implementation or manifests.
- Backend: `backend/` contains only `.gitkeep`; Python + FastAPI selected, no implementation or manifests.
- No application entry points, lockfiles, test/lint/build configuration, or CI workflows found; no runnable application verification commands established.
- OpenSpec: `openspec/config.yaml` exists with the `spec-driven` schema.
- Active tooling-only change: [configure-readonly-development-mcp tasks](../openspec/changes/configure-readonly-development-mcp/tasks.md); approved choice recorded in [design](../openspec/changes/configure-readonly-development-mcp/design.md). skip_specs: no application behavior changed.
- `openspec validate configure-readonly-development-mcp --strict --json --no-interactive`: PASS (CLI 1.16.1); tasks 8/8 complete; no archive.
- OpenCode: six generated commands in `.opencode/commands/` and six Skills in `.opencode/skills/`.
- Codex: six generated Skills in `.agents/skills/`; `.openspec-target` identifies `codex`.
- Custom Skills: [fastapi-endpoint](../.agents/skills/fastapi-endpoint/SKILL.md) and [quality-gate](../.agents/skills/quality-gate/SKILL.md); OpenCode version at setup checkpoint: 2.2.6.
- Generated integrations have not been exercised through complete workflows.
- Profiles: [spec-analyst](../.opencode/agents/spec-analyst.md), [backend](../.opencode/agents/backend.md), [frontend](../.opencode/agents/frontend.md), [qa](../.opencode/agents/qa.md), [reviewer](../.opencode/agents/reviewer.md).
- Prior profile evidence, not rerun here: five loaded subagents without model overrides; 85 static permission cases and five read-only child invocations passed; independent review found no confirmed profile defects.
- Configured limits: default deny; local reads; backend/frontend edits only in their respective directories; shell, external directories, secrets by filename, and further delegation denied.
- Those subagent profiles disable glob, grep, Code Mode, web, MCP, and Skill execution; this does not describe the primary agent, whose native Skill calls succeeded here.
- Scope: project opencode.jsonc, OpenSpec tooling plan, README, English evidence record, and STATE.md; no application code, dependency installation, credential files, commits, or pushes.

## Verified evidence and MCP checkpoint
- Prior Skill test: both custom Skills passed file/frontmatter checks, native discovery, and named loading; direct PowerShell file inspection was recorded separately, not as client loading.
- quality-gate loaded natively for this setup. Application tests/build/type checks: NOT APPLICABLE to development-only configuration.
- [Redacted MCP evidence, exact calls, and observed results](ai-engineering/configure-readonly-development-mcp.md); GitHub is maintained by GitHub, Context7 by Upstash; both are external remote servers used by OpenCode, not the chatbot.
- opencode.jsonc parsed and loaded on 2.2.6: PASS. GitHub PAT stored only as ENERGIA_SUR_GITHUB_PAT reference; no secret value inspected or printed. Context7 uses OAuth.
- Final loaded-rule evaluation: PASS, 156 cases across 12 profiles; only build asks for get_file_contents and the two Context7 documentation tools. All seven loaded subagents deny both namespaces.
- Generic MCP resource list/read tools denied for wildcard/empty resources; client removed those tools from its catalog. This is not proof of complete runtime isolation.
- Independent reviewer: PASS for static policy after one resource-discovery refinement; no confirmed defects. CLI cases were primary-agent evidence, not independently rerun.
- Live rerun: strict OpenSpec validation and unchanged tracked agent/Skill/AGENTS files PASS; earlier JSON/static-policy checks remain prior evidence, not rerun here.
- Native tool discovery and calls PASS: github_get_file_contents returned remote README.md at requested refs/heads/main, file SHA e752e622269f2e6d7b1f7b6b3784597258f6f31a; Context7 resolved /websites/fastapi_tiangolo and returned request-body/error documentation. Earlier auth errors are historical.

## Pending work and blockers
- Runtime denial/path-normalization/symlink tests: pending; static matching and successful reads do not prove isolation or secret-free content.
- fastapi-endpoint applied read-only: readiness review completed, but implementation is BLOCKED; no endpoint code, server, or application tests executed. Native loading does not prove endpoint correctness or Codex discovery.
- First-endpoint blockers: no accepted endpoint contract or implementation change/design/tasks; method/path, request/response fields, validation/business rules, error statuses/envelopes, access/ownership rules, and acceptance scenarios need agreement.
- First-endpoint setup: no manifests, approved test runner, application entry point, or verification commands; choose approved dependency/test/lint/type tooling and document runnable checks before implementation.
- Resolve storage/auth/external-I/O decisions only where required by the chosen endpoint; unrelated TBDs do not automatically block a storage-free or public contract, but must not be silently decided.
- MCP authentication checkpoint resolved for the agreed calls; credentials, fine-grained token scope, and auth storage were not inspected. /mcps Connected is user-reported, corroborated by successful calls.
- Process record and MCP setup documentation now exist; application installation/startup/test instructions remain pending actual manifests and approved tooling.
- Teacher approval of the topic and ten use cases: pending documentation; no verifiable repository evidence found, not a claim of rejection or non-approval.
- Functional implementation: BLOCKED until that evidence is verified; environment/specification preparation remains pending.
- Technical decisions pending: database, ORM/migrations, application authentication/authorization, hosting, test frameworks, and persistent chatbot memory. GitHub + Context7 development MCP selection is approved.
- README is English; broader runtime denial/path/symlink and token-scope verification remain unproven. Final gate PASS: tracked/staged and explicit untracked whitespace, local links, 55-line/five-action STATE limits, and evidence self-review.

## Next actions
1. Review the uncommitted MCP setup/evidence diff; the agreed positive live tests and applicable final gate passed.
2. Obtain separate authorization before any commit, push, or OpenSpec archive.
3. Plan broader runtime permission/token-scope verification using explicitly approved non-sensitive probes; successful reads do not establish isolation.
4. Document teacher approval of the topic/ten use cases and accept the first endpoint contract and required OpenSpec artifacts.
5. Approve relevant application/tooling TBDs and establish manifest-backed setup, tests, lint, type checks, and build commands before functional implementation.

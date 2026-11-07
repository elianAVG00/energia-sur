# Operational state — energia-sur

Updated: 2026-11-07T02:11:23-03:00.
Initial snapshot: 2026-11-07T02:01:41-03:00.

## Verified facts
- Initial milestone: AGENTS.md installed and reading/comprehension acceptance check performed.
- Latest milestone: five English OpenCode V2 profiles configured, loaded, and invoked in read-only smoke tests.
- `AGENTS.md` exists and was reread; it remains untracked in Git.
- Frontend: `frontend/` contains only `.gitkeep`; React + TypeScript selected, no implementation or manifests.
- Backend: `backend/` contains only `.gitkeep`; Python + FastAPI selected, no implementation or manifests.
- OpenSpec: `openspec/config.yaml` exists with the `spec-driven` schema.
- `openspec list --json` and `openspec list --specs --json`: PASS; zero changes and zero specifications.
- Active changes: none; no OpenSpec tasks to link.
- OpenCode: six generated commands in `.opencode/commands/` and six Skills in `.opencode/skills/`.
- Codex: six generated Skills in `.agents/skills/`; `.openspec-target` identifies `codex`.
- Generated integrations have not been exercised through complete workflows.
- Profiles: [spec-analyst](../.opencode/agents/spec-analyst.md), [backend](../.opencode/agents/backend.md), [frontend](../.opencode/agents/frontend.md), [qa](../.opencode/agents/qa.md), [reviewer](../.opencode/agents/reviewer.md).
- `opencode --version`: 2.2.6; `opencode debug agents`: PASS, all five loaded with `mode: subagent` and no model override.
- Static evaluation of loaded ordered permissions: PASS, 85 representative rule cases; not runtime enforcement testing.
- All five child invocations: PASS, local reads and role reports returned; no edits or shell execution requested.
- Independent reviewer: no confirmed profile defects in static review; runtime isolation remains unverified.
- Configured limits: default deny; local reads; backend/frontend edits only in their respective directories; shell, external directories, secrets by filename, and further delegation denied.
- Glob, grep, Code Mode, web, MCP, and Skill execution are disabled; relevant local Skill files can be read directly.
- Scope: authorized development-agent setup and state translation only; no application behavior or OpenSpec artifacts changed.

## Pending work and blockers
- Runtime denial/path-normalization/symlink tests: pending; static matching and successful reads do not prove isolation or secret-free content.
- No new session was needed for loading or smoke invocations; broader execution/permission testing remains pending.
- Custom Skills missing: `.agents/skills/fastapi-endpoint/SKILL.md` and `.agents/skills/quality-gate/SKILL.md`; baseline AGENTS.md workflow used.
- MCP selection, configuration, and real use remain unverified; no operational evidence documented in the repository.
- Process documentation: `docs/ai-engineering/` is missing; README lacks installation, startup, and verification instructions.
- Teacher approval of the topic and ten use cases: pending documentation; no verifiable repository evidence found, not a claim of rejection or non-approval.
- Functional implementation: BLOCKED until that evidence is verified; environment/specification preparation remains pending.
- Technical decisions pending: database, ORM/migrations, authentication/authorization, hosting, test frameworks, MCP, and persistent chatbot memory.
- Documentation language: English required; existing README remains untranslated because it is outside this task's six-file scope.

## Next actions
1. Review the five profiles and verify runtime permission boundaries using approved, non-sensitive probes before relying on isolation.
2. Create the custom `fastapi-endpoint` and `quality-gate` Skills in English; review exact verification commands before enabling shell exceptions.
3. Document teacher approval of the topic and ten use cases, and prepare their OpenSpec scope in English.
4. Compare and seek approval for technical TBDs, including MCP selection; record approved decisions in OpenSpec design.
5. Prepare English process/setup/verification documentation and redacted integration evidence; translate README within an authorized follow-up.

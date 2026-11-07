# Proposal

## Why

energia-sur needs reproducible development access to its published repository
and current library documentation. The user explicitly approved remote GitHub
MCP in read-only mode and remote Context7 MCP with OAuth, with narrowly scoped
confirmation prompts only for the primary agent.

## What Changes

- Add project-local OpenCode V2 MCP configuration; preserve existing agent rules.
- Deny both MCP tool namespaces globally; permit only three named tools with
  `ask` for the existing `build` primary agent.
- Reference the GitHub PAT only through ENERGIA_SUR_GITHUB_PAT; use Context7 OAuth.
- Validate effective primary/subagent permissions, obtain independent security
  review, and record redacted evidence and pending authentication honestly.
- After the user provides credentials through the client, read the remote
  README and query FastAPI documentation using the approved MCP tools.

## Capabilities

### New Capabilities

None. Development tooling only; `skip_specs: true` records the deliberate opt-out.

### Modified Capabilities

None. No application behavior, API, business rule, or chatbot runtime changes.

## Impact

Project opencode.jsonc, setup documentation, operational state, and a redacted
engineering evidence record. GitHub and Upstash receive the approved read/query
requests; no local server package is required. No dependency installation,
credential-file creation, agent-profile edits, commits, pushes, or deployment.

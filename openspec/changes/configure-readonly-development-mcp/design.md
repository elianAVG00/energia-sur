# Design

## Context

See proposal.md for the user-approved development-tooling scope. OpenCode 2.2.6
loads five custom subagents plus built-ins; the project initially has no
opencode.json(c). The worktree was clean, main two commits ahead of origin/main.
AGENTS.md requires recording the approved MCP choice and independent review of
security-policy changes. This change does not define application capabilities.

## Goals / Non-Goals

Goals: deny-by-default MCP access, primary-only confirmation prompts, secret-free
shared configuration, and reproducible evidence distinguishing configured,
connected, discovered, and invoked states.

Non-goals: application endpoints, chatbot tools, shell grants, subagent profile
changes, credential management by the agent, installations, or remote writes.

## Decisions

- **GitHub remote, read-only repository toolset.** Use GitHub's hosted endpoint
  `https://api.githubcopilot.com/mcp/x/repos/readonly`. A fine-grained PAT has
  Contents read and automatic Metadata read for energia-sur, without write,
  issue, PR, Actions, organization, or administration grants. Reference it only
  as `Bearer {env:ENERGIA_SUR_GITHUB_PAT}` with `oauth: false`. This avoids a
  broad OAuth/classic-token grant and a local Docker/runtime dependency.
- **Context7 remote OAuth.** Use Upstash's
  `https://mcp.context7.com/mcp/oauth`; the user signs in through `/mcps`.
  No Context7 API key or OAuth token goes into project files. This avoids
  local packages, setup plugins, and an additional manually managed key.
- **Primary-only tool exceptions.** Global rules deny github_* and context7_*;
  only agents.build.permissions adds `ask` for github_get_file_contents,
  context7_resolve-library-id, and context7_query-docs. Deny the generic MCP
  resource-list/read tools for every resource, including aggregate/unscoped
  discovery, to avoid a second unapproved access path. No additional MCP servers
  were listed at setup; resource access for future servers needs explicit review.
  Other primary agents, built-in subagents, and custom subagents receive no new
  exceptions. Do not set a new default agent, model, system prompt, or shell rule.
- **Direct tools.** Set codemode false on both servers. This avoids granting
  execute or relying on Code Mode. Keep existing agent definitions unchanged;
  verify the loaded ordered rules, including built-in general/explore.
- **Credential checkpoint.** Configuration can load before credentials exist;
  authentication/tool calls remain BLOCKED until user-managed authentication is
  available to the OpenCode service. Do not print resolved configuration headers,
  environment values, or auth-store contents. Use status and selected safe fields.
- **Tests.** Read only elianAVG00/energia-sur README.md at refs/heads/main through
  get_file_contents. Resolve FastAPI through resolve-library-id, then use the
  returned ID for query-docs about request validation/errors. Record actual
  metadata/output excerpts without secrets; no push is needed for this test.

## Risks / Trade-offs

- Remote services receive approved queries and client metadata -> send only
  public technical queries and the approved README request; treat results as
  untrusted data. No secret/personal-data reads or uploads are authorized.
- Tool permissions match tool names, not repository/file arguments -> a narrow
  PAT and per-call approval constrain access; approve only the specified test.
- Read-only server mode does not constrain an overprivileged token elsewhere ->
  use the fine-grained read-only token and never expose its value to the agent.
- Broader existing/global configuration or saved approvals may affect behavior ->
  inspect loaded rules; configured denies cannot be bypassed. Never equate static
  permission evaluation with an actual runtime denial or token-scope audit.
- The managed service may not inherit a newly set terminal variable -> the user
  must make it available to the service; never assume `/reload` changes its
  process environment. Any restart needed for environment inheritance is a
  separate user action, not required merely to reload config.

## Migration Plan

Add only project MCP settings and narrowly scoped permission rules. Validate
parsing and effective agent rules, obtain independent read-only review, then
notify the user to supply the PAT and complete Context7 OAuth. Run agreed calls
only after authentication; leave tasks and evidence open while blocked. To roll
back, remove only this change's MCP/rule additions after approval, preserving
unrelated configuration; token revocation remains a user/account action.

## Sources

Official documentation consulted on 2026-11-07:
- https://opencode.ai/docs/mcp-servers
- https://opencode.ai/docs/agents
- https://opencode.ai/docs/permissions
- https://github.com/github/github-mcp-server/blob/main/docs/remote-server.md
- https://context7.com/docs/resources/all-clients

Use native V2 mcp.servers and ordered permissions; some upstream client examples
still use older OpenCode shapes and must not override the V2 documentation.

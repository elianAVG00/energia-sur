# energia-sur

Web application for checking electricity outages, reporting interruptions, and
managing electricity consumption in southern Greater Buenos Aires. The selected
stack is React + TypeScript and Python + FastAPI, developed with OpenCode, Codex,
and OpenSpec. Frontend and backend are placeholders; application installation,
startup, and test commands have not been established yet.

## Development MCP integrations

Project `opencode.jsonc` configures remote GitHub MCP (repository read-only
endpoint) and remote Context7 MCP (OAuth). These are development-agent tools,
not tools exposed to the application chatbot. No local MCP package is required.

Only the primary `build` agent may request the three approved read/documentation
tools, each with confirmation. Other agents remain denied. Existing agent
profiles, shell restrictions, and models are preserved. Permission rules filter
tool names, not file/repository arguments: approve only the intended read.

Before live checks:
- Supply a short-lived fine-grained GitHub PAT for energia-sur with Contents read
  and automatic Metadata read through `ENERGIA_SUR_GITHUB_PAT` in the OpenCode
  service environment. Never put the token in project files, logs, or chat.
- Complete Context7 OAuth through `/mcps` in OpenCode. Credentials stay outside
  project configuration. `/reload` applies config changes; it does not update a
  running service's inherited environment.
- Check `opencode mcp list`, discover the tools, and approve the agreed README
  read and FastAPI documentation queries. Configuration alone is not a successful
  MCP test. No remote writes, commits, or pushes are part of these checks.

## Engineering context and evidence

- [Operational state](docs/STATE.md)
- [Approved MCP design and tasks](openspec/changes/configure-readonly-development-mcp/design.md)
- [MCP setup, authentication checkpoint, and redacted checks](docs/ai-engineering/configure-readonly-development-mcp.md)

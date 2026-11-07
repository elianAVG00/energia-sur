# energia-sur

Web application for checking electricity outages, reporting interruptions, and
managing electricity consumption in southern Greater Buenos Aires. The selected
stack is React + TypeScript and Python + FastAPI, developed with OpenCode, Codex,
and OpenSpec. Frontend and backend are placeholders; application installation,
startup, and test commands have not been established yet.

## Approved local environment (planning only)

The Docker development plan uses React + TypeScript with Vite, Node 24.22.2 and
npm 11.19.1; Python 3.13.18 with FastAPI, Uvicorn and uv; and PostgreSQL 18.6 from
the first Compose startup. Frontend/backend use loopback ports 5173/8000 with an
`/api/health` proxy. PostgreSQL has no published host port and persists in `pgdata`.
Startup will not require an OpenAI key. Backend/database integration and the
LangChain/OpenAI assistant are later changes, not part of this scaffold.

Only planning artifacts exist: images, lockfiles, Dockerfiles, Compose and the
real build/acceptance tests remain pending Apply. See the
[design](openspec/changes/docker-development-environment/design.md) and
[implementation checklist](openspec/changes/docker-development-environment/tasks.md).

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
- [Docker environment decisions, planning checks, and pending implementation evidence](docs/ai-engineering/docker-development-environment.md)

# energia-sur

Web application for checking electricity outages, reporting interruptions, and
managing electricity consumption in southern Greater Buenos Aires. The selected
stack is React + TypeScript and Python + FastAPI, developed with OpenCode, Codex,
and OpenSpec. The current implementation is a technical development scaffold,
not an implementation of those business features.

## Local Docker environment

The Docker development environment uses React + TypeScript with Vite, Node 24.22.2 and
npm 11.19.1; Python 3.13.18 with FastAPI, Uvicorn and uv; and PostgreSQL 18.6 from
the first Compose startup. Frontend/backend use loopback ports 5173/8000 with an
`/api/health` proxy. PostgreSQL has no published host port and persists in `pgdata`.
Startup does not require an OpenAI key. Backend/database integration and the
LangChain/OpenAI assistant are later changes, not part of this scaffold.

The runtime images and uv are pinned by verified immutable digests for
`linux/amd64`. npm and uv use versioned lockfiles; the normal builds run `npm ci`
and `uv sync --locked`, never regenerate locks. See the
[design](openspec/changes/docker-development-environment/design.md) and
[implementation checklist](openspec/changes/docker-development-environment/tasks.md).

### Setup and startup (PowerShell, repository root)

Prerequisite: Docker Desktop running Linux containers with Docker Compose.
The verified client/engine is 29.1.3 with Compose v2.40.3-desktop.1. Host Node,
Python, npm and uv installations are not required for the container workflow.

1. Copy the secret-free example with `Copy-Item .env.example .env` only if you do
   not already have a local file. Edit ignored `.env` locally and set a non-empty,
   development-only `POSTGRES_PASSWORD`; never share or commit the completed file.
   Alternatively supply the three PostgreSQL values in your process environment.
2. Run:

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose up -d --wait --wait-timeout 90
docker compose ps
```

Open `http://127.0.0.1:5173`; direct API health is
`http://127.0.0.1:8000/health`, returning HTTP 200 and `{"status":"ok"}`.
The browser uses relative `/api/health` through Vite; `backend` and `db` are
container-network names, not host/browser DNS names. The database has no published
host port. Database/provider credentials are not passed to frontend or backend.
The health response describes HTTP liveness, not PostgreSQL or provider readiness.

Source-only bind mounts keep host dependency directories out of containers.
React source edits use Vite's development server; after Python edits run
`docker compose restart backend`. Manifest/config changes require rebuilds.
If file watching does not notice Windows filesystem changes, rebuild rather than
assuming hot reload was verified for your filesystem.

### Checks without installing additional test frameworks

With local configuration supplied and images built, run from the root:

```powershell
docker compose exec -T backend python -m unittest discover -s tests -v
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
pwsh -File scripts/Test-Lockfiles.ps1
pwsh -File scripts/Test-HealthProxy.ps1
pwsh -File scripts/Test-DatabasePersistence.ps1
```

Backend tests exercise the actual ASGI route/model/lifespan using Python's
standard library. Frontend tests use Node's built-in runner for the fetch helper
and state transitions, with injected synthetic responses. They do not render
React or prove browser acceptance. No third-party test or lint runner has been
selected: lint and backend static-type tooling remain separate approval decisions.

`Test-Lockfiles.ps1` changes only disposable container copies and asserts locked
installs reject drift. `Test-HealthProxy.ps1` checks real direct/proxied HTTP,
stops only backend and restores it in `finally`; it does not inspect the UI.
`Test-DatabasePersistence.ps1` performs `SELECT 1`, commits a unique marker in an
ordinary technical-only table, recreates only `db`, checks a different container
with the same named volume, and retrieves that exact marker without reinserting.
It retains the marker and volume and installs no database driver in FastAPI.

### Acceptance A - manual browser verification

1. Open `http://127.0.0.1:5173` with Developer Tools → Network. Click **Volver a
   comprobar** and confirm `/api/health` returns HTTP 200, `{"status":"ok"}`,
   and the screen shows **API disponible** with that JSON.
2. Run `docker compose stop backend`, then click **Volver a comprobar** in the
   same screen. Verify previous success disappears and a visible error appears
   within five seconds. Record the failed request and screen state.
3. Restore immediately with `docker compose up -d --no-deps --wait backend`;
   retry in the browser and verify recovery. Do not stop or remove `db` here.

A terminal-only proxy success/failure does not complete this browser acceptance.
Record human browser evidence in the AI Engineering record before checking the
two browser tasks complete. This session's exact evidence and remaining blockers
are in that record, not implied by the instructions above.

Current Apply evidence: both images build, all three services run healthy, four
backend tests and 25 frontend tests pass, and real proxy success/failure/recovery
and PostgreSQL persistence pass. The user subsequently confirmed the real manual
browser success/error/recovery acceptance during focused Verify. Lint/backend
static-type tooling and its checks remain pending; the change stays open.

### Database configuration and non-destructive shutdown

PostgreSQL 18 stores data in `pgdata` mounted at `/var/lib/postgresql`; Compose
prefixes the actual volume name with the project name. Initialization variables
apply only to an empty data directory. Editing `.env` does not rotate credentials
already stored in a volume. The Apply acceptance run uses synthetic credentials
only; do not put real data in that test database or assume a new `.env` password
changes its existing account. Future database integration must handle credentials
explicitly in its own change.

```powershell
docker compose stop
docker compose up -d --wait --wait-timeout 90
```

Normal stop/start retains `pgdata`. Do not remove volumes or prune resources as
part of setup, tests, or shutdown. Data deletion requires separate authorization.

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
- [Accepted stage 05 catalog and decision baseline](docs/use-cases/README.md)
- [CU09 first-development proposal and pending design review](openspec/changes/record-cu09-interruption-diary/proposal.md)
- [CU09 planning evidence and review gates](docs/ai-engineering/record-cu09-interruption-diary.md)
- [Approved MCP design and tasks](openspec/changes/configure-readonly-development-mcp/design.md)
- [MCP setup, authentication checkpoint, and redacted checks](docs/ai-engineering/configure-readonly-development-mcp.md)
- [Docker environment decisions, planning checks, and pending implementation evidence](docs/ai-engineering/docker-development-environment.md)

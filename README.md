# energia-sur

Web application for checking electricity outages, reporting interruptions, and
managing electricity consumption in southern Greater Buenos Aires. The selected
stack is React + TypeScript and Python + FastAPI, developed with OpenCode, Codex,
and OpenSpec. CU09 has a private interruption diary and the minimum CU04
domicile-registration slice. CU09 and the shared frontend foundation were verified
and archived on 2026-11-08. CU04 was subsequently implemented and verified;
other business CUs are not implemented.

CU04 domicile and meter management is implemented, verified and archived;
Git staging, commits and pushes are managed by the user:
[proposal](openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/proposal.md),
[engineering record](docs/ai-engineering/manage-cu04-domiciles-meters.md).

## CU09 - private interruption diary

Implemented paths: credentialed local login/logout, own-account domicile registration
and selection, cut creation/list/correction/closure, period-clipped overlap-safe
summaries, and authenticated Unicode PDF downloads. Buenos Aires times are recorded
to the minute; inputs before 1970-01-01 00:00 are rejected with 422. Ongoing rows say
**En curso**; reports never implicitly close a cut.
This implements only CU04's domicile prerequisite, not meters/full address management.

The accepted [contract](openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/contract.md)
documents fields, errors, version conflicts, cookies and CSRF. U09 clarifies that
login requires a trusted explicit Origin without pre-auth CSRF; authenticated
unsafe requests require both Origin and a valid session-bound CSRF token. Accounts are provisioned
locally, not through a public signup or an account-switch bypass. No credentials,
addresses or provider keys belong in the frontend bundle/browser storage.

### CU09 setup and checks (PowerShell, repository root)

PostgreSQL already runs on the internal Compose network. Supply a **backend-only**
application connection in your process environment as `CU09_DATABASE_URL`, using
the `postgresql+psycopg://` driver, a deliberately provisioned role/database and
intended credentials. Never paste its completed value into docs or chat. Then use:

```powershell
docker compose -f compose.yaml -f compose.cu09.yaml config --quiet
docker compose -f compose.yaml -f compose.cu09.yaml build
docker compose -f compose.yaml -f compose.cu09.yaml run --rm --no-deps backend alembic upgrade head
docker compose -f compose.yaml -f compose.cu09.yaml up -d --no-deps --wait backend frontend
docker compose -f compose.yaml -f compose.cu09.yaml exec backend python -m app.provision --username your-local-account
```

The provisioning command prompts privately for a password. The migration is additive;
destructive downgrade is intentionally refused. Never remove `pgdata` or assume
changing `.env` rotates an existing database password. Keep the overlay for CU09
recreation; the base-only scaffold has no application database configuration.
Development cookies are HttpOnly/SameSite=Lax on loopback HTTP; HTTPS requires the
Secure cookie setting. `CU09_APP_ORIGINS` is an explicit comma-separated allowlist,
not `*`. Hosting/external exposure is not authorized by these development instructions.

Reproduce synthetic-only acceptance without disclosing or overwriting local credentials:

```powershell
docker build --target verification -t energia-sur-backend-checks:cu09 backend
docker build --target verification -t energia-sur-frontend-checks:cu09 frontend
pwsh -NoProfile -File scripts/Test-Cu09Acceptance.ps1
docker run --rm energia-sur-backend-checks:cu09 ruff check --no-cache app tests migrations
docker run --rm energia-sur-backend-checks:cu09 mypy --cache-dir /tmp/mypy-cache app
docker run --rm energia-sur-frontend-checks:cu09 npm run lint
```

The acceptance script deliberately creates uniquely named **synthetic** databases,
a nonprivileged role and two accounts, migrates them, runs PostgreSQL/ASGI tests,
recreates only frontend/backend, drives real Chromium, downloads/reads PDFs, reruns
migration with data, and checks record identities/values after backend restart.
It retains synthetic databases, the stopped QA container and artifacts under the
user-local OpenCode temporary directory for inspection: no database/table/volume
cleanup is performed. Existing PostgreSQL container/data are not replaced; the
cluster does receive additive synthetic databases. The running app afterward uses
the synthetic acceptance database, not a configured real-data account.

Frontend build runs strict TypeScript (including E2E/config), Node tests and pinned
Oxlint 1.92.0. Stable typescript-eslint 8.72.1 still requires TypeScript <6.1,
whereas this repo pins 7.0.2; U08 approved Oxlint as the TS-version-independent
alternative instead of force-installing or downgrading. Detailed actual outcomes,
date-floor decision and independent review:
[CU09 engineering evidence](docs/ai-engineering/record-cu09-interruption-diary.md).

## Shared frontend foundation - implemented and archived

The user approved the direction in U09 and explicitly authorized Apply in U10. The separate
[establish-frontend-foundation proposal](openspec/changes/archive/2026-11-08-establish-frontend-foundation/proposal.md),
[design](openspec/changes/archive/2026-11-08-establish-frontend-foundation/design.md),
[specifications](openspec/changes/archive/2026-11-08-establish-frontend-foundation/specs/frontend-shell/spec.md)
and [tasks](openspec/changes/archive/2026-11-08-establish-frontend-foundation/tasks.md) are archived after verification.
Implemented: Tailwind/local shadcn/ui components, memory-only Zustand session and
domicile selection, React Hook Form/Zod forms and centralized Axios with cookie/CSRF
interceptors, cancellation and safe PDF handling. CU09 adopts these layers without
changing backend contracts. One root-layout chat mount is visibly unavailable;
LangChain, messaging and streaming remain CU03 work, not implemented chat behavior.
See the [reuse guide](docs/frontend-foundation.md) for module boundaries, adding the
next CU, reset/security rules and documented checks. Actual verification and the
independent source review are in the [engineering record](docs/ai-engineering/establish-frontend-foundation.md).
Both changes were archived with main specs synchronized; no closure commit, push or deployment performed.

## Local Docker environment

The Docker development environment uses React + TypeScript with Vite, Node 24.22.2 and
npm 11.19.1; Python 3.13.18 with FastAPI, Uvicorn and uv; and PostgreSQL 18.6 from
the first Compose startup. Frontend/backend use loopback ports 5173/8000 with an
`/api/health` proxy. PostgreSQL has no published host port and persists in `pgdata`.
Startup does not require an OpenAI key. Base-only Compose remains the health scaffold;
CU09's overlay adds the backend/database connection. LangChain/OpenAI is still later scope.

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
host port. Base-only Compose passes no database credentials to the application;
the CU09 overlay passes its connection only to backend, never frontend.
No provider key is required or passed by either configuration.
The health response describes HTTP liveness, not PostgreSQL or provider readiness.

Source-only bind mounts keep host dependency directories out of containers.
React source edits use Vite's development server; after Python edits run
`docker compose restart backend`. Manifest/config changes require rebuilds.
If file watching does not notice Windows filesystem changes, rebuild rather than
assuming hot reload was verified for your filesystem.

### Checks without installing additional test frameworks

With local configuration supplied and images built, run from the root:

```powershell
docker compose exec -T backend python -m unittest discover -s tests -p test_health.py -v
docker compose exec -T frontend npm run typecheck
docker compose exec -T frontend npm test
docker compose exec -T frontend npm run build
pwsh -File scripts/Test-Lockfiles.ps1
pwsh -File scripts/Test-HealthProxy.ps1
pwsh -File scripts/Test-DatabasePersistence.ps1
```

The original backend health tests exercise ASGI/model/lifespan with the standard
library. Full CU09 backend tests additionally require the verification image and
an isolated migrated `TEST_DATABASE_URL`, as supplied by its acceptance script;
without it, PostgreSQL tests explicitly skip and cannot be counted as acceptance.
Node helper tests are not rendered React acceptance; CU09's Playwright script supplies
the real browser path. Ruff/mypy, Oxlint and browser/PDF tooling are approved for CU09;
the frontend lint gate passes with Oxlint 1.92.0. The runtime backend image
intentionally excludes development-only test/PDF-inspection tools.

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
3. Restore the same container with `docker compose start backend` and wait for
   health, then retry in the browser. This preserves CU09's existing overlay
   environment; do not recreate a CU09 backend with base-only Compose. Do not
   stop or remove `db` here.

A terminal-only proxy success/failure does not complete this browser acceptance.
Record human browser evidence in the AI Engineering record before checking the
two browser tasks complete. This session's exact evidence and remaining blockers
are in that record, not implied by the instructions above.

Historical Docker-scaffold Apply evidence: both images build, all three services run healthy, four
backend tests and 25 frontend tests pass, and real proxy success/failure/recovery
and PostgreSQL persistence pass. The user subsequently confirmed the real manual
browser success/error/recovery acceptance during focused Verify. CU09 now supplies
passing backend Ruff/mypy checks, Oxlint, and expanded tests. The old Docker change
stays open pending its own remaining gates and reconciliation.

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
- [CU09 approved first-development proposal and Apply contract](openspec/changes/archive/2026-11-08-record-cu09-interruption-diary/proposal.md)
- [CU09 implementation, verification evidence and remaining gates](docs/ai-engineering/record-cu09-interruption-diary.md)
- [Approved MCP design and tasks](openspec/changes/configure-readonly-development-mcp/design.md)
- [MCP setup, authentication checkpoint, and redacted checks](docs/ai-engineering/configure-readonly-development-mcp.md)
- [Docker environment decisions, planning checks, and pending implementation evidence](docs/ai-engineering/docker-development-environment.md)

# Design

## Context

See [proposal](proposal.md) for motivation and
[development-environment spec](specs/development-environment/spec.md) for behavior.
At planning start, `main` was clean and three commits ahead of `origin/main`.
`frontend/` and `backend/` contain only `.gitkeep`; there are no application
manifests, lockfiles, entry points, Compose files, or CI workflows to reuse.
OpenSpec 1.16.1 uses the installed `spec-driven` schema.

The user explicitly approved the stack, runtime versions, ports, proxy, database
volume, two acceptance tests, and documentation-only planning on 2026-11-07.
Prior-session Docker evidence was client/engine 29.1.3, Docker Desktop 4.55.0,
Compose v2.40.3-desktop.1, Linux containers; those commands were not rerun for
this planning request. Teacher approval for the topic and ten use cases remains
undocumented: environment preparation is authorized, business implementation is not.

## Goals / Non-Goals

**Goals:**
- Bootstrap only the technical screen, liveness route, and local infrastructure.
- Keep HTTP liveness, database readiness, and future business health distinct.
- Make image/dependency resolution explicit and repeatable rather than relying
  on host Python/Node installations or mutable image tags.
- Verify real browser/API behavior and independent SQL persistence separately.

**Non-Goals:**
- No FastAPI/PostgreSQL connection, driver, ORM, migrations, or business tables.
- No application authentication, production hosting, deployment, or public access.
- No LangChain/OpenAI packages, model calls, assistant runtime, or persistent
  assistant memory. LangChain with OpenAI in the backend is confirmed direction
  for a separate change; startup here must not require `OPENAI_API_KEY`.
- No changes to existing MCP setup, agent permissions, Skills, or `AGENTS.md`.

## Decisions

### Approved stack and separate version verification

| Area | Approved choice | Rationale / alternative considered |
| --- | --- | --- |
| Frontend | React + TypeScript, Vite, Node 24.22.2, npm 11.19.1 | Typed minimal screen and dev proxy; no additional full-stack framework or alternate package manager needed. |
| Backend | Python 3.13.18, FastAPI, Uvicorn | Focused ASGI service; no alternate web framework or production process manager needed. |
| Python dependencies | uv, `pyproject.toml`, `uv.lock` | Explicit transitive resolution and locked sync; preferable here to manually maintained requirements or adding Poetry. |
| Database | PostgreSQL 18.6, service `db` on first startup | Explicit user decision; neither SQLite nor a deferred optional database is an alternative for this change. |
| Persistence | `pgdata:/var/lib/postgresql` | PostgreSQL 18 image layout; do not reuse the pre-18 `/var/lib/postgresql/data` mount without reassessing the chosen image. |

These are approved targets, not claims of verified image availability or a
successful build. Apply must inspect registry metadata for the exact runtime
tags, Debian variants, Linux/amd64 support, and immutable digests, and record
provenance. It must also verify Node's npm version; pin npm 11.19.1 explicitly if
the chosen image does not supply it. Pin uv to an exact release and digest, and
record compatible exact releases of React, TypeScript, Vite, FastAPI, and Uvicorn
before installing. No guessed digest or automatic fallback/downgrade is allowed;
unavailable approved versions require user review.

### Minimal scaffolds and future file scope

These are planned implementation paths, not files created by this request:

| Area | Planned files |
| --- | --- |
| Root | `compose.yaml`, `.env.example` |
| Backend | `backend/app/__init__.py`, `backend/app/main.py`, `backend/pyproject.toml`, `backend/uv.lock`, `backend/.python-version`, `backend/Dockerfile`, `backend/.dockerignore`, focused health tests |
| Frontend | `frontend/package.json`, `frontend/package-lock.json`, `frontend/.npmrc`, `frontend/index.html`, `frontend/tsconfig*.json`, `frontend/vite.config.ts`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/Dockerfile`, `frontend/.dockerignore` |
| Verification/docs | Narrow PowerShell acceptance scripts under `scripts/`, README, STATE, and this change's AI Engineering record |

Use `app.main:app` as the planned ASGI entry point. Keep `GET /health` focused on
transport: public within the local development boundary, no request body, no
business logic or external I/O, HTTP 200 with JSON `{"status":"ok"}`. Load the
FastAPI endpoint Skill before implementing it. It is liveness, not database
readiness. Do not introduce a database client or `DATABASE_URL` to satisfy it.

### Compose, routing, and local-only exposure

| Service | Container behavior | Host mapping / persistence |
| --- | --- | --- |
| `frontend` | Vite on `0.0.0.0:5173`, strict port selection | `127.0.0.1:5173:5173` |
| `backend` | Uvicorn on `0.0.0.0:8000` | `127.0.0.1:8000:8000` |
| `db` | PostgreSQL on port 5432, readiness healthcheck | No host port mapping; `pgdata` named volume |

Use Compose's default project-scoped bridge network and service DNS, without
host networking, fixed container names, or extra externally exposed services.
The browser calls relative `/api/health`; Vite proxies `/api` to
`http://backend:8000` and removes the `/api` prefix. Never send a browser to
`http://backend:8000` directly: service DNS only exists inside Compose. The proxy
avoids a blanket CORS exception. Backend liveness must not depend on database
readiness; all three services still belong to the default startup set.

Use source-only development bind mounts, if needed, rather than mounting host
`node_modules` or `.venv` over dependencies installed in images. Keep installed
dependencies outside the mounted source directories. File-watch polling is a
documented fallback only if observed Windows/Docker behavior requires it.

### Configuration and reproducible builds

- Put non-sensitive development names `POSTGRES_DB` and `POSTGRES_USER` plus a
  password placeholder in `.env.example`. The user supplies a non-empty local
  `POSTGRES_PASSWORD` through ignored `.env` or their environment. Compose must
  reject a missing password, not enable `trust` or supply a committed default.
- Pass only those database variables to `db`; do not pass the entire root `.env`
  to every service. The initial backend needs no database credentials.
- Keep the proxy target in server-side Vite configuration, not a public browser
  environment variable. No provider or development-MCP credential is forwarded.
- Pin runtime images and the uv binary image using version/variant plus verified
  SHA-256 digest. Prefer Debian-based variants to avoid unnecessary musl/native
  extension compatibility work. Exact variants/digests are Apply evidence.
- Pin direct dependencies and version the generated transitive locks. Use
  `npm ci` and `uv sync --locked` with both manifest and lock present. Do not run
  a dependency resolver to update locks inside the normal image build.
- Record Python 3.13.18 in the image and `.python-version`, the supported Python
  range in `pyproject.toml`, and Node/npm requirements in `package.json` with npm
  `packageManager` metadata and enforced version checks. Metadata alone is not
  proof that the running tool version is correct.
- Exclude `.env*` secrets, host dependency directories, Git data, and unrelated
  content via focused build contexts and `.dockerignore`; keep only secret-free
  examples where required. Do not run remote installer scripts without review.
- Generate lockfiles and actually rebuild during Apply. This plan promises
  repeatable inputs/resolution, not bit-for-bit identical image output.

### Acceptance A: real React/API success and backend-down error

Run this independently of SQL persistence. With `OPENAI_API_KEY` unset, start all
three services and open `http://127.0.0.1:5173`. The technical screen requests
health on load and offers an explicit retry/check action. It validates HTTP
success and the expected JSON shape before showing success. Use a bounded request
timeout (planned five seconds), no fake success response, and no cached health
fallback. A new check clears the previous result while loading.

Record the browser's real `/api/health` request, HTTP 200, body, and visible screen
state, corroborated by backend request evidence. Stop only `backend`, trigger
another check in the same screen, and record the visible error within the timeout
with previous success removed. A direct API request or mocked test alone cannot
pass this acceptance. Restart backend afterward and confirm recovery.

### Acceptance B: SQL availability and persistence after real recreation

Run this separately through `psql` supplied by the `db` image; no Python driver
or application connection is needed. Use fail-on-error behavior (`ON_ERROR_STOP`)
and check process exit codes and query results. Execute `SELECT 1`, create a
dedicated ordinary technical acceptance table (not TEMP and not a business table),
and commit a unique synthetic marker generated only for this test run. Read it
back before recreation. Readiness checks alone do not prove successful SQL.

Record the current container identity and actual project-prefixed `pgdata` volume
identity. Recreate only `db` using Compose's force-recreate behavior without any
volume deletion; wait for readiness, verify the container identity changed and
the volume identity did not, then query the exact marker again with `psql`.
Never reinsert the marker after recreation or seed it from startup scripts.
Retain synthetic evidence; cleanup or volume deletion is not a prerequisite and
requires separately scoped approval. No `down --volumes`, prune, or reset belongs
to either acceptance workflow.

## Risks / Trade-offs

- Approved tags may be missing or differ from prior web release metadata ->
  inspect registries in Apply and stop for review rather than substituting versions.
- Immutable pins age -> record provenance and use explicit reviewed updates.
- A startup healthcheck can pass without useful work -> require the browser
  path and real `psql` assertions as separate mandatory acceptances.
- PostgreSQL 18 mount layout differs from older examples -> verify chosen image
  layout and volume identity during persistence acceptance.
- Local `.env` is not a production secrets solution -> keep it untracked, do
  not print rendered secret values, and do not reuse this deployment externally.
- Startup credentials only initialize an empty PostgreSQL data directory ->
  document that editing `.env` does not rotate credentials in existing `pgdata`.
- This is additive local scaffolding, not a breaking architecture or security
  policy change -> primary self-review plus human plan acceptance is appropriate;
  apply the mandatory independent-review rules if later scope changes trigger them.

## Migration Plan

No existing application or database needs migrating. After a separate Apply
request, verify tooling/image metadata, establish manifests and locks, add the
scaffolds and container configuration, then run mandatory acceptance and gates.
Document PowerShell-compatible root commands only after inspecting actual scripts.
Normal shutdown preserves `pgdata`. Rollback stops the newly introduced services
and proposes a focused reversal of this change without deleting data or unrelated
work; deletion, commits, pushes, deployment, sync, and archive need authorization.

## Open Questions

- Exact uv and library patch releases, Debian image variants and digests remain
  to be selected/verified during Apply within the approved stack. Additional
  dependencies or major tool changes require approval before installation.
- Test/lint runner selection is not granted by this plan; use existing or
  explicitly approved tools and manual browser/SQL evidence as appropriate.
  Missing mandatory verification tooling must be resolved, not marked passing.
- Driver, ORM, migrations, application auth, hosting, and persistent assistant
  memory remain separate future decisions, not blockers to this storage-free API.

## Documentation Sources

### Apply resolution (2026-11-07)

Official image tags, Linux/amd64 manifests and immutable index digests were
verified and recorded in the [AI Engineering record](../../../docs/ai-engineering/docker-development-environment.md).
Selected initial exact package versions are React/React DOM 19.3.1, TypeScript
7.0.2, Vite 8.3.6, React types 19.3.0, Node types 24.19.2, FastAPI 0.162.0,
Uvicorn 0.54.0 and uv 0.13.7. The approved Python/Node/npm/PostgreSQL versions
were available and were not replaced. Real locked installation, builds and
standard-runtime tests passed; external test/lint tools remain unselected.
Python uses standard-library unittest/ASGI calls and frontend uses Node's built-in
test runner for focused helpers/state without adding a third-party test runner.
Browser acceptance was subsequently confirmed by the human user during focused
Verify; lint/backend static typing remain verification gaps. No new tool is
approved by that confirmation; see the current decision proposals in the record.

### Planning references

Context7 documentation reads on 2026-11-07, not image/build verification:
- `/astral-sh/uv`: https://github.com/astral-sh/uv/blob/main/docs/guides/integration/docker.md
  (locked sync and immutable uv image pinning).
- `/vitejs/vite`: https://github.com/vitejs/vite/blob/main/docs/config/server-options.md
  (container listen address, strict port, and proxy rewrite).
- PostgreSQL image-layout reference from the prior diagnosis:
  https://github.com/docker-library/docs/blob/master/postgres/README.md.

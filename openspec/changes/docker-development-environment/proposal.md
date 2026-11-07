# Proposal

## Why

Energía Sur has approved its local development stack, but frontend and backend
are still empty placeholders with no reproducible startup path. A minimal
three-service environment will establish technical connectivity and persistence
before business features or chatbot integration are implemented.

## What Changes

- Plan a minimal React + TypeScript scaffold served by Vite and a Python +
  FastAPI scaffold served by Uvicorn, with npm and uv dependency management.
- Define `compose.yaml` with `frontend`, `backend`, and PostgreSQL `db` from the
  first startup; publish only frontend/backend on host loopback.
- Define `GET /health` and the frontend `/api/health` proxy, including a visible
  error state when the real backend cannot be reached.
- Persist PostgreSQL data in a named volume and define a separate SQL query and
  container-recreation acceptance test using synthetic data.
- Require startup without OpenAI credentials and reproducible image/dependency
  pinning. Verify image tags/digests, generate lockfiles, and run builds in Apply,
  not during this planning request.
- Record the user's approved stack and the remaining implementation decisions.

## Capabilities

### New Capabilities

- `development-environment`: local three-service startup, technical frontend/API
  connectivity, database persistence, and reproducible environment configuration.

### Modified Capabilities

None. There are no existing main specifications.

## Impact

Future implementation affects `frontend/`, `backend/`, root `compose.yaml` and
`.env.example`, two Dockerfiles, manifests/lockfiles, and setup/verification docs.
Approved runtimes are Node 24.22.2 with npm 11.19.1, Python 3.13.18, and PostgreSQL
18.6. Exact library/uv releases and image digests remain Apply prerequisites.

This request writes planning artifacts and documentation only. FastAPI/database
integration, PostgreSQL driver, ORM, migrations, business tables/endpoints,
application auth, hosting, LangChain/OpenAI implementation, deployment, commits,
pushes, and archive are outside this change's implementation scope. The integrated
assistant remains an approved backend direction for a separate change. GitHub MCP
and Context7 setup are already complete and are not reopened here.

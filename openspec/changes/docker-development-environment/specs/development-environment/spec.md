# Spec Delta

## Purpose

Provide a reproducible local environment that demonstrates real frontend/API
communication and independently verifies database availability and persistence
before business features or assistant integrations are added.

## ADDED Requirements

### Requirement: Three-service startup without an assistant credential

The local environment SHALL start `frontend`, `backend`, and `db` together from
the repository root without requiring `OPENAI_API_KEY` or contacting an assistant
provider. The backend health endpoint SHALL not require a database connection.

#### Scenario: Initial startup without OpenAI
- **GIVEN** documented local database configuration and available approved images
- **WHEN** the developer starts the environment with `OPENAI_API_KEY` unset
- **THEN** all three services reach their documented running or healthy state
- **AND** the frontend and backend health endpoint are accessible
- **AND** startup makes no assistant-provider requests

#### Scenario: Database is not part of API liveness
- **GIVEN** the frontend and backend are running
- **WHEN** `db` becomes unavailable and the developer requests backend health
- **THEN** the backend still returns its healthy technical response
- **AND** that response does not claim that the database is ready

### Requirement: Local-only service access

The environment SHALL publish frontend at `127.0.0.1:5173` and backend at
`127.0.0.1:8000`. The database SHALL be reachable as `db:5432` on the Compose
network without a published host port. Database credentials SHALL not be delivered
to the frontend or stored in tracked configuration.

#### Scenario: Inspect service exposure
- **WHEN** the developer inspects the rendered configuration and running services
- **THEN** only the two approved loopback port mappings are published
- **AND** `db` has no host port mapping and shares the Compose service network
- **AND** frontend configuration contains no database or provider credentials

### Requirement: Technical health response

The backend SHALL expose unauthenticated `GET /health` with HTTP 200,
`application/json`, and the JSON body `{"status":"ok"}` while its HTTP service
is running. This endpoint SHALL expose no configuration, credentials, business
data, or assertions about external service availability.

#### Scenario: Request health directly
- **WHEN** the developer requests `http://127.0.0.1:8000/health`
- **THEN** the response is HTTP 200 with JSON body `{"status":"ok"}`
- **AND** the response contains no database or assistant-provider status

### Requirement: Real frontend health display and failure state

The health check SHALL be verified through real HTTP requests, not a user-facing
technical screen. Same-origin `/api/health` SHALL proxy to backend `GET /health`,
and success SHALL only be reported after validating the real response. Network,
timeout, non-success status or unexpected-response failures SHALL surface as
verification failures, never masked by a fixture or cached success. No application
view SHALL display health status (U26).

#### Scenario: Acceptance A - real proxy success followed by backend failure
- **GIVEN** the three-service environment is running without OpenAI credentials
- **WHEN** the developer requests same-origin `/api/health` with an HTTP client
- **THEN** the response is backend HTTP 200 with the expected JSON through the real proxy and backend
- **AND** the result comes from the real backend rather than a fixture
- **WHEN** the developer stops only `backend` and repeats the request
- **THEN** the request fails within its documented timeout or returns a non-success status
- **AND** no mock or cached response masks the failure
- **AND** no application screen is required to observe either result

#### Scenario: Technical health status stays out of every application view
- **GIVEN** the three-service environment is running
- **WHEN** the developer opens the frontend at any public, authenticated or administrative view
- **THEN** no health panel, health-check JSON or manual re-check control is rendered
- **AND** the layout does not request `/api/health` on its own

### Requirement: Database query and persistence across recreation

The database SHALL execute SQL queries and retain committed synthetic acceptance
data in named volume `pgdata` across recreation of the `db` container. Persistence
evidence SHALL not depend on application/database integration, temporary tables,
or startup scripts reinserting the test datum.

#### Scenario: Acceptance B - independent SQL persistence test
- **GIVEN** `db` is ready with `pgdata` attached and contains no acceptance marker for this run
- **WHEN** the developer uses `psql` with fail-on-SQL-error behavior to execute `SELECT 1` and commit a unique synthetic marker to an ordinary technical acceptance table
- **THEN** the query returns `1` and the marker can be read back
- **WHEN** the developer recreates only `db` without deleting its named volume
- **THEN** the container identity changes while the same named volume remains attached
- **AND** after readiness returns, `psql` retrieves the exact committed marker
- **AND** no business table, migration, or FastAPI database connection is involved

### Requirement: Reproducible build inputs

Environment builds SHALL use verified immutable image digests and versioned
dependency lockfiles with locked installation commands. A manifest/lockfile
mismatch SHALL fail rather than silently resolve different dependencies. Images
and dependency inputs SHALL exclude local secrets and host-installed environments.

#### Scenario: Build from recorded inputs
- **GIVEN** verified image references and matching committed manifests and lockfiles
- **WHEN** the developer builds from a fresh checkout using documented commands
- **THEN** installation uses the recorded image and dependency resolutions without updating lockfiles
- **AND** local credential files and host dependency directories are not copied into images

#### Scenario: Detect dependency drift
- **WHEN** a dependency manifest changes without the matching lockfile update
- **THEN** the documented locked dependency installation fails
- **AND** the build does not regenerate or silently accept a new dependency resolution

### Requirement: Non-destructive documented local workflow

The environment SHALL document PowerShell-compatible setup, startup, acceptance
checks, and shutdown from the repository root. Normal shutdown SHALL preserve
`pgdata`. Volume deletion SHALL require a separately authorized destructive action
and SHALL not be part of startup, recreation, or acceptance checks.

#### Scenario: Stop and resume without data loss
- **GIVEN** the SQL acceptance marker is committed
- **WHEN** the developer follows normal shutdown and startup instructions
- **THEN** the named volume is preserved and the marker remains queryable
- **AND** no volume-deletion command is executed

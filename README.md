# energia-sur

Web application for checking electricity outages, reporting interruptions, and
managing electricity consumption in southern Greater Buenos Aires. The selected
stack is React + TypeScript and Python + FastAPI, developed with OpenCode, Codex,
and OpenSpec. CU09 has a private interruption diary and the minimum CU04
domicile-registration slice. CU09 and the shared frontend foundation were verified
and archived on 2026-11-08; CU04, CU06, CU07 and CU08 are implemented and
archived. CU05 is implemented with a red-fraction Sync/Archive block, CU01 and CU02
are implemented, verified and archived (CU02 under its U22 definitive scope), and
CU03 is closed and archived (BUILD 1-3, real OpenAI query passed) and CU10 is implemented,
verified and archived.

CU04 domicile and meter management is implemented, verified and archived;
Git staging, commits and pushes are managed by the user:
[proposal](openspec/changes/archive/2026-11-08-manage-cu04-domiciles-meters/proposal.md),
[engineering record](docs/ai-engineering/manage-cu04-domiciles-meters.md).

CU06 electricity bills are implemented: owner-scoped list/create/detail/edit and
private attachment download under `/api/meters/{meter_id}/bills`. Bills store inclusive
period dates, nonnegative kWh (3 decimals), optional ARS (2 decimals) and a required
PDF/JPG/PNG file up to 5,000,000 bytes. Identical periods are rejected; overlaps require
an explicit, payload-bound confirmation. Corrections keep the bill ID, increment a
version and may replace the file; deletion and reassignment are not offered.
See the [archived change](openspec/changes/archive/2026-11-09-record-cu06-electricity-bills/proposal.md),
[main specification](openspec/specs/electricity-bills/spec.md) and
[engineering record](docs/ai-engineering/record-cu06-electricity-bills.md). PDF checks
use a time- and memory-bounded `pypdf` worker and detect basic active content; they are
not an antivirus. Local Compose keeps attachments in the private `cu06_bills` volume and
generates the confirmation key at backend start. Startup reconciliation removes only
unreferenced CU06 objects; a synthetic matched PostgreSQL + volume backup/restore drill
passed with the backend stopped.

CU07 comparison is implemented as a read-only endpoint and bill-workspace panel. It
matches CU05 readings within +/-7 days of each CU06 bill boundary using Buenos Aires
local dates, compares exact dates directly and requires backend-validated confirmation
for approximate periods. Multiple candidates require manual selection; missing or
decreasing readings yield no calculation; recorded, billed and the exact difference are
shown in kWh without a percentage. See the
[archived change](openspec/changes/archive/2026-11-09-compare-cu07-consumption-with-bill/proposal.md),
[main specification](openspec/specs/bill-comparisons/spec.md)
and [engineering record](docs/ai-engineering/compare-cu07-consumption-with-bill.md). No
table, migration or dependency was added; independent review and archive are complete.

CU05 meter readings have manual history, confirmation, private photo attachments and
photo/OCR endpoints. The OCR endpoint uses local Tesseract and OpenCV in bounded
workers, with editable suggestions or abstention. Recognition is not guaranteed:
the supplied real example abstained, and the user must verify suggestions. OCR
requires cgroup v2 swap disabled, core dumps disabled, and a shared private photo
volume across backend instances; Compose configures these safeguards. The
[proposal](openspec/changes/record-cu05-meter-readings/proposal.md) and
[engineering record](docs/ai-engineering/record-cu05-meter-readings.md) record the
remaining recognition and safety-verification gates.

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
docker compose -f compose.yaml -f compose.cu09.yaml exec backend python -m app.promote --username your-local-account
```

The provisioning command prompts privately for a password. Promote an existing account
to the CU10 `admin` role with `python -m app.promote --username ...`; this CLI never
accepts a role from an argument and there is no role-management UI or self-assignment. The migration is additive;
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

## CU05/CU06 focused backend runtime checks

Run the six historical CU05/CU06 backend tests against an isolated synthetic database
and private temporary storage without touching shared services or persistent volumes:

```powershell
pwsh -NoProfile -File scripts/Test-Cu05Cu06BackendRuntime.ps1
```

Prerequisites: a running `energia-sur-db-1` container and an available backend
verification image (`energia-sur-backend-checks:cu10` by default). Build the image with:

```powershell
docker build --target verification -t energia-sur-backend-checks:cu10 backend
```

The runner creates a unique role/database, migrates it, generates a synthetic 32-byte
`CU06_CONFIRMATION_SECRET`, mounts per-run tmpfs directories for CU05 photos and CU06
bills, verifies OCR privacy preconditions (`RLIMIT_CORE == 0` and cgroup v2
`memory.swap.max == 0`), and runs each test individually. Results and per-test logs are
written to `$env:LOCALAPPDATA\Temp\opencode\cu05-cu06-runtime`.

Pass `-Cleanup` to drop the synthetic role/database after the run; without it they are
retained for inspection. Use `-MemoryLimit 2g` (default) or adjust if your Docker host
needs more headroom for the bounded OCR/photo workers. Pass `-Rebuild` to rebuild the
backend verification image before running. The runner does not recreate, restart or prune
the shared `db`, `backend` or `frontend` services.

Expected result with a current verification image: all six targeted tests PASS;
CU06 regression (`test_bill_*.py`) 32/32 OK; CU05 regression (`test_photo_*.py`) 45/45 OK.
The separate CU05 history E2E failure is tracked independently and is not covered by this
runner.

## Shared frontend foundation - implemented and archived

The user approved the direction in U09 and explicitly authorized Apply in U10. The separate
[establish-frontend-foundation proposal](openspec/changes/archive/2026-11-08-establish-frontend-foundation/proposal.md),
[design](openspec/changes/archive/2026-11-08-establish-frontend-foundation/design.md),
[specifications](openspec/changes/archive/2026-11-08-establish-frontend-foundation/specs/frontend-shell/spec.md)
and [tasks](openspec/changes/archive/2026-11-08-establish-frontend-foundation/tasks.md) are archived after verification.
Implemented: Tailwind/local shadcn/ui components, memory-only Zustand session and
domicile selection, React Hook Form/Zod forms and centralized Axios with cookie/CSRF
interceptors, cancellation and safe PDF handling. CU09 adopts these layers without
changing backend contracts. One root-layout chat mount now runs the CU03 assistant with
SSE, temporary visitor memory and authenticated conversation persistence.
See the [reuse guide](docs/frontend-foundation.md) for module boundaries, adding the
next CU, reset/security rules and documented checks. Actual verification and the
independent source review are in the [engineering record](docs/ai-engineering/establish-frontend-foundation.md).
Both changes were archived with main specs synchronized; no closure commit, push or deployment performed.

## CU01 public outage queries and UI (BUILD 3)

The public, read-only outage API is backed by a cached ENRE snapshot:
`GET /api/outages?partido=<name>&localidad=<optional>`, `GET /api/outages/areas`,
`POST /api/outages/resolve` (address in the body) and `POST /api/outages/resolve-location`
(coordinates in the body). Backend paths are `/outages`, `/outages/areas`, `/outages/resolve`
and `/outages/resolve-location`; no session is required and responses use
`Cache-Control: no-store`. Addresses and coordinates are body-only, rate-limited and never logged.
The backend refreshes `data_EDS.js` at a persisted interval under a PostgreSQL advisory lock when
`OUTAGE_SCHEDULER_ENABLED=true` (Compose default). The interval (`300`/`600`/`900`/`1800`/`3600`
seconds) is stored in `es_source_config` and read each cycle, so CU10 changes apply without a
restart; the seeded default is `300`. `OUTAGE_REFRESH_SECONDS` is no longer read.
Migration `0005_cu01` adds `es_outage_snapshots`, `es_outage_reports` and `es_outage_fetch_runs`.

Coverage uses the versioned catalog `backend/app/data/edesur_coverage.2026-11-10.json` with
`covered`, `out_of_coverage` and `coverage_unverified`. The shipped catalog is a partial,
observation-based seed (provenance and retrieval date in the file; most entries were observed in
current-outage collections and three in the same feed's programmed/comunicado collections).
Absence is always `coverage_unverified` and no `out_of_coverage` entry is asserted without
explicit evidence. `no_reports` is reachable only for localidades explicitly listed in the seed.

Resolve requests are rate-limited in-process per socket peer (20/minute). Behind the Vite proxy
all browser traffic shares that peer; revisit the client-identity key before multi-user hosting.
CABA addresses/positions resolve to partido `CAPITAL` only, because GeoRef returns a comuna and
not an ENRE barrio; the catalog's CABA barrios are not address-resolvable.

The public UI lives at the "Cortes" section of the shell (the "Mi cuenta" account view remains the
default, so the existing login flow is unchanged). It offers a partido→optional-localidad selector
from `/outages/areas`, a normalized "Buscar zona" filter, GeoRef address search with candidate
selection, consented browser geolocation, granularity messaging, category rows, Edesur-scope totals
and the source provenance. Every normative availability/coverage state is presented, including
"coverage unverified" (never "out of coverage" or "no outages" without evidence). The public view
calls only `/api/outages/*` plus the shared `/api/session` and `/api/health` probes; the two public
resolve POSTs and the public assistant chat are the only CSRF-free unsafe endpoints besides
login, and 429 responses surface `Retry-After`.

Known BUILD 3 limits are accepted by U20: the partial nine-localidad coverage catalog (0.4) and the
unobserved media/preventivo feed shapes (0.1). GeoRef address matching is sparse and reverse
geocoding returns only a partido, so address/position results often degrade to partido.

Verification: `docker build --target verification -t energia-sur-backend-checks:cu01 backend`,
then run `python -m unittest discover -s tests -p "test_cu01_*.py"` against an isolated migrated
`TEST_DATABASE_URL`; set `TEST_ENRE_LIVE=1` and `TEST_GEOREF_LIVE=1` for the live tests. Frontend:
`docker build --target verification -t energia-sur-frontend-checks:cu01 frontend` (runs typecheck,
build, tests and lint), then run `npx playwright test e2e/cu01.spec.ts` with the dev server up.
The contract-mocked suite needs no backend; the real-backend smoke
(`e2e/cu01-real.spec.ts`) requires a migrated isolated database seeded from
`backend/tests/fixtures/enre_data_eds_redacted.js` via `app.outage_store._store_snapshot`, the
backend reachable as `backend:8000` from the frontend proxy, and `CU01_LIVE=1`.
CU09 remains covered by its existing E2E against a seeded backend.

## CU02 maintenance works consultation (definitive scope)

**Definitive scope (U22):** *CU02 — Consultar trabajos de mantenimiento eléctrico
informados por ENRE.* CU02 is completed and archived with this scope. The original
academic proposal (upcoming works filtered by dates, with start/end, reason and
proximity) is preserved in the use-case fiche, with the redefinition recorded in U22;
it is not the delivered scope. No teacher approval of the redefinition is claimed.

CU02 shows the ENRE-reported maintenance works (`cortesProgramados`) and never invents
dates, reasons, coordinates or a future agenda. `GET /api/scheduled-works?partido=<name>&localidad=<optional>`
and `GET /api/scheduled-works/areas` reuse the same public resolve endpoints for
address/GPS zone resolution. `cortesComunicados` is counted and flagged but not
displayed because no populated payload has been observed; the Edesur agenda is out of
scope. `planned_start_at`, `planned_end_at` and `reason_text` are returned as null and
the response lists `limitations`; `normalizacion` is the ENRE estimated-restoration
text, never a planned end.

The backend refreshes the feed at the persisted CU10 interval under its own advisory lock
when `SCHEDULED_WORKS_SCHEDULER_ENABLED=true` (Compose default). The interval is stored in
`es_source_config` and read each cycle; the seeded default is `300`.
`SCHEDULED_WORKS_REFRESH_SECONDS` is no longer read. Migration `0006_cu02` adds
`es_scheduled_snapshots`, `es_scheduled_works` and `es_scheduled_fetch_runs` and does
not alter CU01 tables. The public "Trabajos" shell view offers partido/localidad
selection, address search and consented geolocation, provenance, coverage and every
availability state, with no date inputs.

Verification: `docker build --target verification -t energia-sur-backend-checks:cu02 backend`,
then run `python -m unittest tests.test_cu02_scheduled_works` against an isolated
migrated `TEST_DATABASE_URL` (set `TEST_ENRE_LIVE=1` for the live test). Frontend:
`docker build --target verification -t energia-sur-frontend-checks:cu02 frontend`
(runs typecheck, build, tests and lint), then run
`npx playwright test e2e/cu02.spec.ts` with the dev server up (mocked API only).
CU01 and CU09 remain covered by their existing E2E suites. The implementation record,
decisions and original-scope traceability are in the
[CU02 engineering record](docs/ai-engineering/implement-scheduled-works-cu02.md).

## CU03 integrated assistant (closed / archived)

The backend assistant ingests the approved guide at `backend/knowledge/guia-oficial-edesur.md`
(`document_id` `energia-sur-kb-edesur-001`, version `1.0.0`, verified 2026-11-10) into
PostgreSQL/pgvector at article granularity (53 units, `CA-01`...). It uses OpenAI embeddings
(`text-embedding-3-small`, 1536) and `gpt-4o-mini` for generation (both configurable via
`OPENAI_*`). `POST /api/assistant/chat` streams SSE (`text/event-stream`) with
`conversation`, `delta`, `tool`, `sources`, `error` and `done` events, server-side Origin
validation, a per-client rate limit and a static fallback/refusal.

Set `CU09_DATABASE_URL` and a server-side `OPENAI_API_KEY` in the ignored root `.env`.
Ingest once with the CU09 overlay (which supplies `DATABASE_URL`), for example
`docker compose -f compose.yaml -f compose.cu09.yaml exec backend python -m app.ingest_guide`,
or set `ASSISTANT_GUIDE_INGEST=true`. The base Compose file forwards the assistant/OpenAI
variables with empty defaults; never commit a key. Ingestion is idempotent, monotonic by
version and refuses an older version unless `--force`.
Migration `0007_cu03` adds the guide and assistant tables. The React assistant lives in
`frontend/src/features/assistant/` with one root mount, temporary Zustand history and a
configurable TTL (`VITE_ASSISTANT_TTL_MINUTES`, default 30; set
`ASSISTANT_VISITOR_TTL_MINUTES` when rebuilding the frontend), cancellation and official
HTTPS sources. Authenticated users get owner-scoped persisted conversations through
`GET /api/assistant/conversations`, `GET /api/assistant/conversations/{id}/messages` and
`DELETE /api/assistant/conversations/{id}` (Origin + CSRF); visitors are never persisted.
`ASSISTANT_RETENTION_DAYS` documents a proposed 30-day policy; messages remain until the
owner deletes them and automatic deletion is pending approval. The panel shows a visible
OpenAI/private-data notice.

## CU10 source supervision (implemented and archived)

The CU10 admin view lives at `frontend/src/features/admin/` and is visible only to
accounts with the `admin` role. It shows one card per ENRE source (current outages and
scheduled works) with the last real attempt, outcome, last successful check, last error,
lock-contention time, the persisted interval and whether automatic scheduling is
configured. It allows a synchronous "Actualizar ahora" retry and a 5/10/15/30/60-minute
interval selector.

`GET /api/admin/sources`, `POST /api/admin/sources/{key}/refresh` and
`PATCH /api/admin/sources/{key}/interval` enforce the stored admin role on the server and
require Origin + CSRF for mutations. A retry returns 409 `SOURCE_BUSY` while the source
lock is held and 409 `VERSION_CONFLICT` on a stale interval version. The retry is the
only request with a 25-second client deadline; a client timeout is treated as an
unconfirmed result and followed by a real status read. Promote an existing account with
`python -m app.promote --username <account>`; the nav appears after the session is
reloaded. Roles are `user` and `admin`; no role-management UI or self-assignment exists.
Archived change:
[`2026-11-13-supervise-source-refresh-cu10`](openspec/changes/archive/2026-11-13-supervise-source-refresh-cu10/proposal.md).

## Local Docker environment

The Docker development environment uses React + TypeScript with Vite, Node 24.22.2 and
npm 11.19.1; Python 3.13.18 with FastAPI, Uvicorn and uv; and PostgreSQL 18.6 from
the first Compose startup. Frontend/backend use loopback ports 5173/8000 with an
`/api/health` proxy. PostgreSQL has no published host port and persists in `pgdata`.
Startup does not require an OpenAI key. Base-only Compose remains the health scaffold;
CU09's overlay adds the backend/database connection. LangChain/OpenAI is implemented for
CU03; a key is optional and absent by default, so the assistant degrades to its static
fallback.

Compose mounts the private `cu05_photos` volume at `/var/lib/energia-sur/photos`.
FastAPI publishes and reads confirmed CU05 photos there under PostgreSQL and
filesystem locks and reconciles proven-unreferenced objects at startup. A coordinated
backup/restore drill and a real production restart remain untested. Preserve this
volume and `pgdata`; do not remove either as a cleanup step.

Run the backend in its Linux Docker image. Photo locking and bounded decoding import
Linux-only `fcntl`/`resource` modules, so starting `app.main` natively on the Windows
host is not supported; use Compose or the verification image for backend commands.

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
   `.env.example` also lists `OPENAI_API_KEY` (CU03, server-side only) and a
   commented `CU09_DATABASE_URL`; fill them in the ignored `.env`, never in tracked files.
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
- [CU07 comparison implementation, verification evidence and archive](docs/ai-engineering/compare-cu07-consumption-with-bill.md)
- [Approved MCP design and tasks](openspec/changes/configure-readonly-development-mcp/design.md)
- [MCP setup, authentication checkpoint, and redacted checks](docs/ai-engineering/configure-readonly-development-mcp.md)
- [Docker environment decisions, planning checks, and pending implementation evidence](docs/ai-engineering/docker-development-environment.md)
- [CU03 integrated assistant proposal, decisions and review evidence](docs/ai-engineering/implement-integrated-assistant-cu03.md) — [archived change](openspec/changes/archive/2026-11-11-implement-integrated-assistant-cu03/proposal.md), [main spec](openspec/specs/assistant/spec.md)

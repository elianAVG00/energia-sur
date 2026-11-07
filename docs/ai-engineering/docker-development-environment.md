# AI Engineering Record - docker-development-environment

The planning and Apply entries below are historical. The final "Focused Verify"
section records the latest human browser confirmation and verification status.

## Goal and scope

Prepare the approved local development environment plan without implementing it.
The change defines three-service startup, real React/FastAPI technical health
communication including failure, and independent PostgreSQL persistence evidence.

- [Proposal](../../openspec/changes/docker-development-environment/proposal.md)
- [Design and decision record](../../openspec/changes/docker-development-environment/design.md)
- [Specification](../../openspec/changes/docker-development-environment/specs/development-environment/spec.md)
- [Implementation tasks](../../openspec/changes/docker-development-environment/tasks.md)

## User instructions and approvals - 2026-11-07

The user first requested read-only Docker diagnosis, then approved PostgreSQL
from first startup and the separate future LangChain/OpenAI backend direction.
While the client remained in Plan mode, repository writes were blocked; a prior
validation attempt reported `Unknown item` because the change did not yet exist.
That was historical missing-plan evidence, not a failed implementation test.

In the current Build request the user explicitly authorized planning artifacts
and documentation only, approving:
- React + TypeScript, Vite, Node 24.22.2, npm 11.19.1.
- Python 3.13.18, FastAPI, Uvicorn, uv, `pyproject.toml`, and `uv.lock`.
- PostgreSQL 18.6 as `db`, internal service-network access only, and named volume
  `pgdata` mounted at `/var/lib/postgresql`.
- Frontend `127.0.0.1:5173`, backend `127.0.0.1:8000`, and `/api/health` proxy to
  `GET /health`, with startup independent of `OPENAI_API_KEY`.
- Separate real browser success/error and `psql` persistence acceptances.
- Image tag/digest verification, lock generation, and real builds deferred to
  Apply; all implementation tasks must remain unchecked.

The HTTP 200 JSON `{"status":"ok"}` contract was part of the approved technical
design. There is no approval here for business features, database integration,
driver, ORM, migrations, assistant implementation, commits, pushes, or Apply.

## Actual agent and tools

Primary OpenCode build agent only; no subagents or independent reviewer invoked.
This additive planning/docs request was self-reviewed against the user's accepted
design and AGENTS.md, not represented as an independent implementation audit.
Native Skills loaded: `openspec-propose` and `quality-gate`.

Tools used: local read/glob, PowerShell Git/OpenSpec/clock/path inspection, patch,
and Context7 documentation resolve/query calls. No application dependencies were
installed and no container was built, started, recreated, or removed.

Context7 is the existing Upstash-maintained external remote development MCP used
by this client, not the application chatbot. Queries sent only public generic
technical topics: uv Docker locked installation and Vite container/proxy options.
Resolve selected `/astral-sh/uv` and `/vitejs/vite`; query responses confirmed
`uv sync --locked`, immutable image pinning, host/strictPort and proxy rewrite.
No keys, personal data, repository source, or proprietary content were sent.
GitHub MCP and Context7 setup remain completed according to the existing
[MCP checklist](../../openspec/changes/configure-readonly-development-mcp/tasks.md);
this documentation lookup does not reopen or re-audit that checkpoint.

## Work performed

1. Confirmed clean `main`, three commits ahead of `origin/main`; preserved all
   existing tracked files and previous MCP change artifacts.
2. Read instructions, STATE, README, config, existing change artifacts, scaffold,
   ignore rules, and relevant tool configuration. No nested AGENTS files found.
3. Confirmed OpenSpec root/schema and empty main-spec inventory with installed
   OpenSpec 1.16.1. Used `openspec new change docker-development-environment` to
   create CLI metadata rather than hand-scaffolding it.
4. Loaded per-artifact instructions and wrote proposal, spec, design and tasks
   in dependency order. Kept every implementation checkbox empty.
5. Updated operational decisions, this evidence record, and the README index;
   did not create application code, Dockerfiles, Compose, manifests, or locks.

## Verification matrix

All commands run from the repository root. Current-run results are distinguished
from historical evidence. Planning completion is not implementation completion.
Successful planning gate checkpoint: 2026-11-07T04:19:26-03:00. Commands below
exited 0 unless the verifier correction is explicitly described afterward.

| Check | Required now? | Method / actor | Result and limitation |
| --- | --- | --- | --- |
| Branch and initial scope | Yes | `git status --short --branch`, primary | PASS: clean main, ahead 3 before planning writes. |
| Root/schema/inventory | Yes | `openspec context --json`, `list --json`, `list --specs --json`, `--version` | PASS: repository root; spec-driven; CLI 1.16.1; only prior MCP change and no main specs. |
| Planning artifact completeness | Yes | `openspec status --change docker-development-environment --json`, primary | PASS: all four artifacts done; this is file/planning completeness only, not executed tasks. |
| Structural validation | Yes | `openspec validate docker-development-environment --strict`, primary | PASS: `Change 'docker-development-environment' is valid`, CLI 1.16.1. |
| Tracked whitespace | Yes | `git diff --check`, primary | PASS: no whitespace errors; Git warned about future LF-to-CRLF conversion in README/STATE. |
| Staged whitespace | Yes | `git diff --cached --check`, primary | PASS: no staged changes or errors; not evidence about untracked content. |
| Untracked whitespace, links, STATE size and task state | Yes | Targeted read-only PowerShell checks, primary | PASS: 8 explicit planning/doc files, no trailing whitespace, 24 existing local-link targets, STATE 46 lines/5 actions, 22 unchecked tasks. |
| Scope preservation | Yes | `git diff --name-only`, `git diff --cached --name-only`, `git ls-files --others --exclude-standard`, explicit allowed-path comparison | PASS: only the 8 listed planning/doc paths changed; application, agent/Skill/config and existing MCP-change files untouched. |
| Independent review | No for this planning-only scope | Primary self-review, existing human design approval | NOT APPLICABLE to additive documentation planning; not a claim of independent review or a waiver for future risky changes. |
| Image registry verification, dependency resolution, real build | No in this request | Apply tasks | NOT APPLICABLE to planning execution; pending implementation evidence, not PASS. |
| Acceptance A and B, application tests/lint/type/build | No in this request | Apply tasks | NOT APPLICABLE to documentation-only verification; mandatory before implementation closure and not run here. |

## Problems, corrections, and remaining boundaries

No implementation cycles were attempted during this planning run. One auxiliary
link-verifier attempt failed with `Join-Path` receiving an empty parent for root
`README.md` (exit 1). The verifier, not repository behavior, was corrected to use
`Split-Path ([System.IO.Path]::GetFullPath($file)) -Parent`; its rerun passed with
the counts recorded above. A preceding multiline check returned no useful output
and was not counted as evidence. No test or requirement was weakened.

The successful read-only verifier inspected the eight changed files explicitly,
matched trailing whitespace, resolved non-HTTP Markdown links relative to each
absolute parent, counted STATE lines/actions, and asserted every task matches
`- [ ] X.Y`. It compared Git's tracked/staged/untracked path inventory against
that explicit allowed list. The same checks are rerun after evidence updates.

Earlier Plan-mode write restrictions ended before this authorized Build request.
Prior Docker version output is retained in design as prior evidence, not rerun.

No planning decision is blocked. Exact uv/library releases and image variants,
tags, platforms and digests require Apply-time verification; inability to obtain
an approved runtime must return to the user rather than cause a silent downgrade.
Test/lint framework approvals remain separate where needed. Teacher approval of
the topic/ten use cases remains undocumented and gates business implementation,
not this authorized environment preparation. Driver/ORM/migrations and assistant
implementation remain separate later changes. No commit, push, sync, archive or
Apply is authorized by this request.

## Apply checkpoint - 2026-11-07

The user separately authorized Apply of the technical environment, real Docker
startup and SQL persistence checks, with terminal-only proxy evidence explicitly
allowed to leave browser UI acceptance pending. No archive, commit or push is
authorized. Teacher approval remains a business-feature gate, not a blocker for
this explicitly approved technical scaffold.

Initial current-run evidence before editing: clean `main`, ahead 4; strict
OpenSpec validation PASS. Docker client/engine 29.1.3, Docker Desktop 4.55.0,
context `desktop-linux`, server `linux/amd64`; Compose v2.40.3-desktop.1.
Read installed `docker compose --help`, `docker compose up --help` and
`docker buildx imagetools inspect --help`. Task 1.1 completed from these actual
results, not the prior planning checkpoint.

Registry inspection at approximately 2026-11-07T04:25:34-03:00 used
`docker buildx imagetools inspect <reference>`. Official Docker Hub library images
and the upstream Astral GHCR image all supplied Linux/amd64 manifests:

| Reference | Immutable index digest | Linux/amd64 manifest digest |
| --- | --- | --- |
| `docker.io/library/python:3.13.18-slim-bookworm` | `sha256:a5a7017efc5969e00ae2b91c8eb0631049a569652aa4ffc4501769049ae45c72` | `sha256:f3dac913ab53b78c64f26d5518fcd7043d5a1a46522d6a493b598c3ed12f62a6` |
| `docker.io/library/node:24.22.2-bookworm-slim` | `sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9` | `sha256:c0a93797ee78814ae6d32fcca2561fdbbe423149c3f5389aad32d86e9fd85bd4` |
| `docker.io/library/postgres:18.6-bookworm` | `sha256:f1ea2a1a4fb7b68d4836be1fdcb8a6466a89b072158bf9d97663600538c294c5` | `sha256:02fb3245e038f33536cf13bc6c4e59f21d07b0cea3c1fe1c07c6e8aa8f083bcc` |
| `ghcr.io/astral-sh/uv:0.13.7` | `sha256:96f40d3904aad8d0bd010539001d36c8e2188b981e1334471a90c4a1d93bb490` | `sha256:c7db1d63057f268a8b6da8af9077850a60461f98d23db23c676a82089a050c91` |

The Node image was actually pulled by digest and `npm --version` returned
11.19.1. The pinned uv image was pulled and its CLI help inspected. No approved
runtime substitution was required. Compose targets Linux/amd64 explicitly and
pins the inspected immutable indexes; platform manifests are retained above as
provenance, not substituted with invented hashes.

Public npm/PyPI metadata was inspected for compatible initial exact package
versions: React/React DOM 19.3.1, TypeScript 7.0.2, Vite 8.3.6, React type packages
19.3.0, Node types 24.19.2, FastAPI 0.162.0, Uvicorn 0.54.0 and uv 0.13.7.
Vite requires Node ^20.19.0 or >=22.12.0; FastAPI/Uvicorn require Python >=3.10.
Actual locked installations/builds must still verify compatibility.

Primary loaded `openspec-apply-change`, `quality-gate`, and `fastapi-endpoint`.
Configured backend/frontend profiles were read and invoked for non-overlapping
source edits only; they cannot execute shell commands or install dependencies.
Primary owns shared Compose/scripts, lock generation, execution and evidence.
Context7 reads for Docker immutable manifest references, FastAPI response models
and Vite proxy configuration sent only public technical topics to the existing
Upstash remote MCP. No credential content was inspected or transferred.

No third-party test or lint runner has been approved or installed. Standard
runtime checks and approved TypeScript build checks do not constitute approval
of pytest, ESLint, Ruff, mypy, Vitest or browser automation dependencies. Missing
required lint/type or browser evidence will remain BLOCKED rather than PASS.

Backend checkpoint: official pinned Python/uv tooling stage built successfully;
`uv lock --python /usr/local/bin/python` generated the real lock (15 project/
dependency entries). Runtime image `uv sync --locked --no-dev` installed 14
dependencies. `docker run --rm energia-sur-backend:local python -m unittest
discover -s tests -v` passed all 4 actual ASGI/model/lifespan tests, including
configuration-free startup and exact HTTP response. Runtime version checks
returned Python 3.13.18, FastAPI 0.162.0 and Uvicorn 0.54.0.

One drift-verifier attempt failed before its intended assertion: the rootless
container could not initialize uv's default `/.cache/uv`. Set an explicit writable
`UV_CACHE_DIR=/tmp/uv-cache` in the backend image; rebuild and drift-verification
rerun are required before claiming that check passes. No dependency, assertion,
or security boundary was weakened.

### Runtime verification and corrections

The first rootless-cache correction alone was insufficient: a later default
`uv sync --locked --check` failed because the build had created root-owned cache
files at `/tmp/uv-cache`. Correction 2 kept the non-root user and added
`--no-cache` to the build-time locked sync. Rebuilt backend, then default rootless
`uv sync --locked --check` passed (14 packages, no changes) and all 4 tests passed
again. The drift script also isolates its cache/environment in `/tmp`. This
failure is resolved; neither root execution nor suppressed checks were used.

The npm negative drift fixture initially named unavailable TypeScript 7.0.1.
Its check correctly failed with ETARGET rather than accepting the wrong failure
as proof of lockfile drift. Verified the public registry's existing 5.9.3 release
and used it only in a disposable container manifest copy; the expected mismatch
assertion then passed with unchanged lock hash. Repository/runtime TypeScript
remains 7.0.2. No approved runtime was substituted.

All runtime commands below were executed by the primary from the repository root
using a synthetic, development-only `POSTGRES_PASSWORD` in the child PowerShell
process environment and with `OPENAI_API_KEY` unset for startup. No `.env` was
created/read for context, no real credential was used, no password was printed
from configuration, and no volume was deleted. The database contains only the
technical synthetic fixture; configure intended credentials explicitly before
future real use. The password environment value is not a committed default.

| Required check | Command / method | Result / actual evidence |
| --- | --- | --- |
| Official runtime/tool inputs | Four `docker buildx imagetools inspect` calls, pinned Node npm version and uv help | PASS: approved tags/platforms/digests above; npm 11.19.1; no substitution. |
| Backend lock and build | Tooling-stage build; containerized `uv lock --python /usr/local/bin/python`; backend build | PASS: real generated `backend/uv.lock`, exact Python 3.13.18, locked sync and image startup. |
| Frontend lock and build | Pinned Node container `npm install --package-lock-only --ignore-scripts --no-audit --no-fund`; frontend build | PASS: real generated `package-lock.json`; `npm ci` installed 25 packages with lifecycle install scripts disabled. |
| Backend tests | `docker compose exec -T backend python -m unittest discover -s tests -v` | PASS: 4 tests, rerun after final cache correction. Standard library only; no httpx/pytest. |
| Backend locked environment | `docker compose exec -T backend uv sync --locked --check` | PASS: would make no changes, works as non-root. |
| Frontend typecheck | `docker compose exec -T frontend npm run typecheck` | PASS: TypeScript 7.0.2, strict `tsc --noEmit`. |
| Frontend unit/state tests | `docker compose exec -T frontend npm test` | PASS: all 25 Node built-in tests; synthetic injected transport/state tests, not browser evidence. |
| Frontend production build | `docker compose exec -T frontend npm run build` | PASS: typecheck and Vite 8.3.6 build; no project diagnostics suppressed. |
| Manifest drift | `scripts/Test-Lockfiles.ps1` | PASS after fixture correction: uv and npm reject manifest drift; both copied lock hashes unchanged. Repository manifests are never mutated. |
| Missing password | `docker compose --env-file .env.example config --quiet` with empty password | PASS: expected interpolation rejection, not an insecure default or trust fallback. |
| Compose configuration | `docker compose config --quiet` | PASS with process-only synthetic config. Safe JSON field assertions confirmed only loopback ports, no DB host port, no application secrets/env or backend DB dependency. |
| Real startup and status | `docker compose up -d --build`; `docker compose up -d --wait --wait-timeout 90`; `docker compose ps` | PASS: frontend/backend/db healthy; host ports 5173/8000 on 127.0.0.1; db only 5432/tcp internally. |
| HTTP/proxy subset of Acceptance A | `scripts/Test-HealthProxy.ps1` | PASS: direct and proxied real HTTP 200/JSON, proxy fails with backend stopped, backend restored and proxy 200 again. |
| Full Acceptance A | React DOM and browser Network success/error/recovery | BLOCKED: this session has no browser automation tool; no package/browser installed to bypass the tooling decision. README has exact manual steps; tasks 5.1/5.2 remain unchecked. |
| Database-independent liveness | Stop only `db`, GET backend health, restore db in finally | PASS: HTTP liveness stayed `ok`; db restored healthy. |
| Acceptance B | `scripts/Test-DatabasePersistence.ps1` | PASS: SELECT 1; unique marker below committed/read before recreation; different container, same volume, exact marker read afterward without reinsertion. |
| Non-destructive normal lifecycle | `docker compose stop`; `docker compose up -d --wait --wait-timeout 90`; exact marker query | PASS: all services healthy again; original marker and `energia-sur_pgdata` preserved. |
| Lint and backend static typing | Additional runners remain unapproved | BLOCKED: no ESLint/Ruff/mypy or replacement runner installed. These decisions remain separate, not falsely passed or silently excluded. |
| Final OpenSpec/whitespace/links/scope | Strict change validation; `git diff --check`; `git diff --cached --check`; explicit tracked/untracked PowerShell checks | PASS at 2026-11-07T04:46:51-03:00: change valid, no whitespace errors, 33 scoped files, 23 local links, STATE 45 lines/5 actions, 16/22 evidenced tasks and 3 parsed PowerShell scripts. Git emits only LF-to-CRLF conversion warnings. |

Acceptance B redacted/synthetic evidence:
- Marker: `4811ca06-7c8a-403a-bf63-2f1cbf58d924`.
- Before container: `8796ab730e6dcb5f353256d34f47f4979dda35146105fbc73d12b92b0270f3df`.
- After container: `c0e90b6b19fe3eb60b8eb4d92a7cca7f5205cf515a88fb3059824b17aa9a17af`.
- Same named volume: `energia-sur_pgdata`; mount `/var/lib/postgresql`.
- The technical `environment_acceptance.persistence` table is test-only,
  autocommitted through `psql -X -v ON_ERROR_STOP=1`, not a business migration.

Backend/frontend delegated implementation reports were inspected, not treated as
execution evidence: their profiles cannot run shell. Primary performed all
build/test/service operations. A separate read-only reviewer was invoked for
static correctness/security review; outcome remains pending at this checkpoint.
The reviewer subsequently completed its read-only review with no confirmed
defects in the static code/contract scope. It independently inspected source,
tests, manifests, locks, Compose, Dockerfiles and acceptance scripts, including
the final backend `--no-cache` fix. Runtime results were primary-reported, not
independently rerun. Browser/lint/backend-type gaps remain BLOCKED; final evolving
documentation and Git inventory are primary checks, not reviewer certification.
Leave the change open for Verify: partial tasks and mandatory blocked gates must
not be marked complete, and no archive/commit/push occurred.

Task reconciliation: 16/22 tasks have complete implementation/evidence. Unchecked
1.4 and 2.4 retain the separate lint/backend-static-type decision and missing
checks; 5.1/5.2 retain real browser evidence; 7.1/7.2 retain the full final gate
until those mandatory checks are resolved. Passing structural/diff checks alone
does not complete these compound final-gate tasks.

The final file inventory contains 28 new technical files plus modifications to
README, STATE, this record, design and tasks (33 total). Existing `.gitkeep`,
AGENTS, permissions/Skills, main specs and prior MCP artifacts are untouched.
All three services are intentionally left running for manual Verify, with the
synthetic marker and named volume retained. No successful UI assertion is claimed.

Suggested future AGENTS navigation addition (proposal only, not applied; human
approval required before editing AGENTS): under "Setup and run", add
"For the approved local Docker environment and non-destructive checks, follow
README.md and openspec/changes/docker-development-environment/design.md."
This adds a durable setup pointer without replacing the existing conditional TBD
policy or hard-coding mutable runtime versions in instructions.

## Focused Verify - 2026-11-07

Requested by the user after Apply, without archive/commit/push authorization.
Initial Git status remained `main`, ahead 4, with the existing Apply diff and
untracked technical files preserved. Only documentation/task status is changed
by this Verify. Native `quality-gate` loaded; no subagent was needed for this
bounded evidence reconciliation and no tool/dependency was installed.

### Browser acceptance: human-reported PASS

The user explicitly confirmed in this conversation: the real React frontend
showed the correct state with FastAPI active, showed an error when `backend` was
stopped, and recovered after restarting it and clicking "Volver a comprobar".
Actor: human user; received in the current Verify request on 2026-11-07. This
supplies the missing real browser success/error/recovery evidence for 5.1/5.2,
combined with Apply's actual HTTP 200/JSON/proxy-failure evidence and unchanged
implementation. It is not an agent-run browser test or a newly captured Network
trace, screenshot or timing measurement; none of those artifacts were supplied.

Retained backend access logs were checked for the otherwise undocumented request
corroboration: `docker logs --tail 80 energia-sur-backend-1`, matched locally for
successful `GET /health` records, found 70 HTTP 200 responses. Only this count
is retained, not raw addresses or environment values; healthcheck traffic is
included and is not presented as a uniquely identified human browser session.
Together with the user's explicit manual acceptance and existing real proxy
checks, this completes tasks 5.1/5.2 without claiming fabricated browser details.

### Evidence reuse instead of repeated runtime tests

Source/manifests/locks/tests/configuration were inspected. Read-only, network-none,
pull-never ephemeral containers from the final Apply images computed SHA-256
hashes that were compared to current workspace files with `Get-FileHash`:
- Backend: all 5 application/test/manifest/lock files match Apply image
  `sha256:dc38099de766b430df519e5f50a72731666a9238c8a7dc7a665613aeaa3e9d24`.
- Frontend: all 13 source/test/config/manifest/lock files match Apply image
  `sha256:7ac452a24a3660be963b5bdbf5cde7d4d1988fed94558d9e454ea71fd9d499f2`.
- Dockerfiles, Compose, build exclusions and three acceptance scripts were read
  and match the final Apply versions. No application or infrastructure changes
  after the recorded checks were found.
- New aggregate technical baseline: 30 files, SHA-256
  `da5d4e19f309afb8b9abda16dd6c2b625263467ef444263017c6788bbe65e2f2`.
  Computed from sorted `git ls-files --cached --others --exclude-standard --
  frontend backend scripts compose.yaml .env.example` entries, each represented
  as `relative-path lowercase-SHA256`, joined with LF and hashed as UTF-8.

Accordingly, retain Apply PASS evidence for the 4 backend tests, 25 frontend
tests, TypeScript/build, locked builds/drift rejection, image provenance,
exposure/secret checks, startup and database-independent liveness, normal
lifecycle, SQL query and persistence, and independent read-only code review.
Do not relabel them as rerun in Verify. No build, dependency resolution, service
stop/recreation or SQL mutation was repeated: those inputs are unchanged and
adequate evidence already exists. No database volume was modified or removed.

### Current checks, task accounting and closure blockers

| Check / obligation | Result and evidence |
| --- | --- |
| Reuse identity and backend request corroboration | PASS: actual current-run hash comparisons and retained-log count above. |
| Acceptance A | PASS, human-reported with reused Apply HTTP/proxy evidence; tasks 5.1 and 5.2 complete. |
| Acceptance B | PASS, reused Apply SQL/marker/container/volume evidence; not rerun. |
| Structural validation and whitespace | PASS at 2026-11-07T04:55:27-03:00: `openspec validate docker-development-environment --strict`, `git diff --check`, and `git diff --cached --check` all exit 0; Git emits only LF-to-CRLF conversion warnings. |
| Documentation links, scope, STATE/task consistency | PASS: explicit tracked/untracked whitespace/scope checks, 33 scoped files, 23 local links, STATE 45 lines/5 actions, 18/22 complete with only 1.4/2.4/7.1/7.2 unchecked, and unchanged 30-file technical hash. |
| Lint Python/TypeScript and backend static typing | BLOCKED: no approved tooling, versions/configurations or executed results. Tasks 1.4 and 2.4 explicitly require these decisions/checks. |
| Full final gates 7.1 and 7.2 | BLOCKED by missing mandatory lint/backend static-type gates, even when structural/doc checks pass. |

Progress is now 18/22. Leave 1.4, 2.4, 7.1 and 7.2 unchecked; do not weaken task
requirements or treat missing tooling as NOT APPLICABLE to obtain closure.
Concrete pending decision: approve tools, exact versions, scope/rules and locked
development-dependency installation for Python lint, TypeScript/React lint and
Python static typing. Proposed package set, not installed or approved:
- Ruff for Python lint rather than adding separate Flake8-style checker stacks.
- ESLint with typescript-eslint for TypeScript/React lint rather than selecting
  Biome implicitly; confirm any React-specific plugins/rules before adding them.
- mypy for Python static typing rather than introducing a separate Node-based
  Pyright workflow; agree coverage of `backend/app` and its tests.
The existing standard-runtime tests and frontend `tsc` need no new external
test runner to retain their PASS evidence. Versions must be inspected and
approved before installing any proposed new tool. No such decision is inferred
from this Verify request; no new tooling/configuration/dependency edits occurred.

Verdict: BLOCKED, change remains open. No archive, spec sync, commit or push.

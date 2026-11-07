# Tasks

Apply was separately authorized on 2026-11-07. Mark tasks only with actual
evidence; leave partial or blocked verification unchecked. See
[spec](specs/development-environment/spec.md) for required behavior and
[design](design.md) for the approved approach and independent acceptance tests.

## 1. Verify approved build inputs

- [x] 1.1 Inspect permitted installed tool versions and CLI help, including Docker/Compose, and record current output in the AI Engineering record; verify Linux container support rather than reusing prior-session evidence.
- [x] 1.2 Verify registry tags, platform support, Debian variants, and immutable digests for Python 3.13.18, Node 24.22.2, PostgreSQL 18.6, and an exact uv release; record source/time/digests and stop for user review if any approved target is unavailable.
- [x] 1.3 Select and record exact compatible React/TypeScript/Vite/FastAPI/Uvicorn releases and uv version within the approved stack, confirm npm 11.19.1, and inspect metadata/CLI help before installation; verify the version matrix has no unresolved incompatibility or unapproved core dependency.
- [ ] 1.4 Agree the required test/lint/type commands and any new runner dependencies before installation; verify approval evidence and that the selected tools can exercise the technical contract without silently choosing an undecided framework.

## 2. Add the technical FastAPI scaffold

- [x] 2.1 Load `fastapi-endpoint`, add `backend/app/__init__.py` and `backend/app/main.py` with `GET /health`, and add focused contract tests; verify HTTP 200, JSON content type and exact body, and absence of database/provider initialization.
- [x] 2.2 Add `backend/pyproject.toml`, `.python-version`, and generate `backend/uv.lock` with the verified tool version; verify `uv sync --locked` succeeds and a controlled manifest/lock mismatch fails without changing the retained lockfile.
- [x] 2.3 Add `backend/Dockerfile` and `.dockerignore` using verified image/uv digests and locked installation; build the image, verify Python/Uvicorn versions and `app.main:app` startup, and inspect the build scope for secrets/host environments.
- [ ] 2.4 Document actual backend setup, contract-test, lint/type, and direct health-check commands in README; execute the documented checks and record results without claiming database readiness.

## 3. Add the technical React scaffold

- [x] 3.1 Add the React/TypeScript entry files, Vite and TypeScript configuration, and `package.json`/`.npmrc`; generate `package-lock.json`, verify the approved Node/npm versions and `npm ci`, and verify a controlled manifest/lock mismatch fails.
- [x] 3.2 Implement real `/api/health` fetch, response validation, loading/success/error states, bounded timeout, and explicit retry; verify failure modes with focused checks and ensure a failed retry removes previous success without mocks or cached success fallback.
- [x] 3.3 Configure Vite host/strict port and `/api` proxy rewrite to `http://backend:8000`, add `frontend/Dockerfile`/`.dockerignore` with immutable base and `npm ci`, and build the image; verify the production build/type checks and that no secret or host `node_modules` enters it.
- [x] 3.4 Document and execute the actual frontend install/build/type and approved test commands; verify README distinguishes isolated checks from the real browser acceptance required below.

## 4. Assemble and start the three-service environment

- [x] 4.1 Add root `compose.yaml` with `frontend`, `backend`, `db`, the approved loopback ports, default bridge network, PostgreSQL readiness check, and `pgdata:/var/lib/postgresql`; verify the rendered non-sensitive fields and no published database port or backend database dependency.
- [x] 4.2 Add secret-free `.env.example` and targeted variable wiring; verify missing database password is rejected, no `trust` fallback exists, backend/frontend receive no database secrets or provider keys, and ignored local credentials are not staged or logged.
- [x] 4.3 Run the real Compose build and initial startup without `OPENAI_API_KEY`; verify all three services start, direct and proxied health respond, and backend liveness still works when `db` is stopped; restore `db` and record actual evidence.
- [x] 4.4 Document and exercise PowerShell-compatible root setup/startup/status/shutdown commands and any source-only mounts; verify normal shutdown preserves `pgdata`, credentials-on-existing-volume behavior is explained, and no destructive cleanup is included.

## 5. Acceptance A - real frontend/API and backend failure

- [x] 5.1 Execute the independent browser acceptance against running services: record `/api/health` HTTP 200, expected JSON, backend request evidence, and the React success state; verify the result is real frontend-to-backend communication, not a direct-API-only or mocked substitute.
- [x] 5.2 Stop only backend and request another check in the same screen; verify an error within the bounded timeout clears previous success, then restore backend and confirm recovery; document exact steps and redacted evidence in the AI Engineering record.

## 6. Acceptance B - independent SQL query and persistence

- [x] 6.1 Add a narrow PowerShell/`psql` acceptance workflow with SQL fail-on-error and exit-code assertions; verify `SELECT 1`, commit a unique synthetic marker to an ordinary technical-only table, read it back, and record container/volume identities without credentials.
- [x] 6.2 Recreate only `db` without deleting the named volume or reinserting the marker; verify a new container identity, unchanged volume identity, readiness, and exact marker retrieval with `psql`; document actual results separately from Acceptance A and without adding a driver, business schema, or migrations.

## 7. Final cross-service verification

- [ ] 7.1 Run all applicable contract/state tests, lint/type checks, frontend build, the two real acceptance tests, and focused exposure/secret/regression checks against final files; record PASS/FAIL/BLOCKED with commands, actor, versions, and evidence, obtaining independent review if the implemented scope triggers it.
- [ ] 7.2 Rerun strict OpenSpec validation, tracked/staged/untracked whitespace and local-link checks, and reconcile README, STATE, tasks and the AI Engineering record; verify required gates pass and no unverified implementation task is marked complete.

## Workflow follow-up

- Apply and focused Verify evidence: [AI Engineering record](../../../docs/ai-engineering/docker-development-environment.md). 18/22 tasks evidenced, including human browser confirmation; leave partial checks unchecked.
- Verify blockers: 1.4/2.4 need separate lint/backend static-type decisions and checks; 7.1/7.2 await all mandatory gates even if OpenSpec/diff checks pass. Both runtime acceptances are satisfied.
- Apply is authorized; keep the change open for Verify without archive, commit or push.
- Do not add FastAPI/PostgreSQL integration, driver, ORM, migrations, business tables, or LangChain/OpenAI implementation to this change.
- Teacher approval of the topic and ten use cases must be documented before business-feature implementation; it does not block authorized environment preparation.
- Preserve the completed MCP checklist; do not repeat authentication or broaden permissions.
- Commit, push, deployment, data deletion, sync and archive require separate authorization and applicable successful gates.

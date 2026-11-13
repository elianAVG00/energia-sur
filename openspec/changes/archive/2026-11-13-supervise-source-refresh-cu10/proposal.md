# Proposal

## Why

CU01 and CU02 already acquire ENRE data automatically: each source has a FastAPI
lifespan scheduler, a PostgreSQL advisory lock, a fetch-run history and a
last-valid-snapshot rule (see `docs/use-cases/cu10.md`, CU10-R1, SR03 and SR05). What is
missing is the administrative layer approved under U24: an administrator cannot see
whether a source is failing, cannot request an immediate retry, and cannot tune the
refresh interval without editing Docker environment variables and restarting the
backend. This change adds only that layer and reuses the existing acquisition, locking
and persistence unchanged.

## Scope

- Add an `admin` role to the existing account model, promoted through a controlled
  backend CLI. No user/role management UI and no self-assignment.
- Add a persisted, per-source refresh interval (`5/10/15/30/60` minutes) with optimistic
  versioning, replacing the startup-only environment read with a per-cycle database read
  so changes apply without restarting the backend.
- Add three admin-only endpoints: read both source states, trigger a synchronous retry,
  and update one source interval.
- Reuse the existing acquisition, `pg_try_advisory_lock` keys, fetch-run history and
  snapshots. A retry that meets an active acquisition returns HTTP 409 and does not
  enqueue or record a new run.
- Add one admin view with two ENRE source cards showing real last-attempt,
  last-success, error and interval data, a retry button and an interval selector.

## Exclusions

- No new schedulers, connectors, parsers, queues, Redis/Celery or dependencies.
- No user/role management UI, no self-assignment and no request that accepts a role.
- No execution-history UI or dashboard; only the current per-source state.
- No change to CU01/CU02 public endpoints, response shapes, states or freshness
  thresholds. The only CU01/CU02 spec delta is the cadence clause.
- No backoff policy and no per-source enable/disable (Q22 residue); only the two
  existing ENRE sources are supervised.
- No new MCP integration. The academic two-server/one-external minimum is already met by
  the verified development integrations (GitHub and Context7, both external); U23's
  deferral of an external MCP to CU10 is read as satisfied by those integrations, as
  confirmed by the user in BUILD 2.

## Confirmed decisions (U24)

D1 promotion through a controlled CLI; D2 server-side ADMIN authorization with 401/403
and CSRF/Origin on mutations; D3 PostgreSQL persistence with dynamic application and no
restart; D4 the exact 5/10/15/30/60-minute set, independent per source; D5 HTTP 409 on a
concurrent retry with no queue and reuse of existing advisory locks; D6 atomic optimistic
configuration versioning with 409 on a stale version; D7 status derived from existing
run/snapshot records where a failure never erases the last success. Roles are lowercase
`user`/`admin`; 60 minutes is kept and its freshness interaction is documented without
changing the public thresholds; the manual retry is synchronous. See U24 in
`docs/use-cases/decisions.md` for the full record.

## Capabilities

### New Capabilities

- `source-refresh-administration`: admin-only inspection of per-source refresh status,
  synchronous manual retry with mutual exclusion, and persisted interval configuration
  with optimistic concurrency and dynamic application.

### Modified Capabilities

- `current-outages`: the periodic refresh clause changes from a fixed five-minute cadence
  to the CU10-configured interval, defaulting to five minutes; the advisory lock,
  `skipped_locked` behavior and public query contract are unchanged.
- `scheduled-works`: the same strictly necessary cadence change; public query behavior,
  provenance and freshness are unchanged.

## Impact

- **Backend:** additive migration `0008_cu10` adds `es_accounts.role` and
  `es_source_config`; a small `app/source_config.py`; `refresh_now()` in
  `outage_store.py` and `scheduled_store.py`; `app/admin_api.py`; a new `app/promote.py`
  CLI that leaves the existing `provision.py` invocation unchanged; dynamic interval
  reads in the existing lifespan scheduler loops.
- **Frontend:** `Session.account` gains an additive `role`; one admin view with two
  cards; a conditional "Administración" navigation entry.
- **Reuse, unchanged:** `_refresh_locked`, `refresh_once`, both advisory-lock keys,
  `es_outage_fetch_runs`/`es_scheduled_fetch_runs`, snapshots, the `current` and
  `mutation` auth dependencies, the CU04 optimistic-update pattern, the shared Axios
  client and UI primitives.
- **Docs:** `docs/use-cases/decisions.md` (U24), `docs/use-cases/cu10.md`,
  `docs/use-cases/shared-rules.md` (SR05), `docs/STATE.md` and a
  `docs/ai-engineering/supervise-source-refresh-cu10.md` record.

## Dependencies and approval gates

- U24 records the CU10 decisions; Q00 (ten approved CUs) remains satisfied and does not
  by itself authorize implementation.
- The BUILD 2 instruction confirmed the 25-second retry deadline, the no-new-MCP reading,
  the 60-minute interval and the synchronous retry; no open decision blocks Apply.
- Apply requires a subsequent explicit user request; this proposal stops at Review.
- No migration, user promotion, Docker, dependency, commit, push, Sync or Archive is
  authorized here.

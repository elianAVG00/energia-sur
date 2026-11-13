# Design

## Context

CU01 and CU02 are archived and already own the acquisition pipeline this change
supervises. Verified in the current code:

- `backend/app/main.py` runs one lifespan task per source (`_outage_scheduler`,
  `_scheduled_works_scheduler`). Each loop reads its interval **once at startup** from
  `OUTAGE_REFRESH_SECONDS` / `SCHEDULED_WORKS_REFRESH_SECONDS` (default `300`, floor
  `30`), calls `run_in_threadpool(<store>.refresh_once)` and then sleeps.
- `outage_store.py` (`LOCK_KEY = 0x43553031`) and `scheduled_store.py`
  (`LOCK_KEY = 0x43553032`) are parallel. `refresh_once()` takes `pg_try_advisory_lock`
  on a dedicated connection, records `skipped_locked` when it loses, otherwise runs
  `_refresh_locked` and releases the lock in `finally`.
- Real state is already persisted in `es_outage_fetch_runs` /
  `es_scheduled_fetch_runs` (`started_at`, `finished_at`, `outcome`, `http_status`,
  `detail_code`, `content_sha256`) and in the current snapshots (`fetched_at`,
  `last_checked_at`, `source_last_modified`).
- `es_accounts` has no `role`. `api.py` provides `current()` (authentication) and
  `mutation()` (trusted Origin + CSRF), `outages_api.py`/`scheduled_api.py` already use
  `no_cache`, and `management.py` implements the atomic optimistic-update pattern used
  for CU04. `enre_client._TIMEOUT_SECONDS = 20.0`; the shared frontend Axios client uses
  a fixed 10-second deadline.

See [proposal.md](proposal.md) — Why for motivation and scope.

## Goals / Non-Goals

**Goals:** admin-only status, synchronous retry, persisted per-source intervals with
optimistic concurrency; reuse existing acquisition, locks and run history; no restart
needed; CU01/CU02 public behavior unchanged.

**Non-Goals:** new schedulers, connectors, parsers or queues; Redis/Celery; a generic
user/role admin; execution-history UI; dashboards; backoff or source enable/disable; any
change to CU01/CU02 public endpoints, response shapes, states or freshness thresholds.

## Decisions

### D1 - A single `role` column and a separate promotion CLI

Add `es_accounts.role VARCHAR(16) NOT NULL DEFAULT 'user'` with
`CHECK (role IN ('user','admin'))` and a matching Python `default="user"`. Promote
through a **new** `app/promote.py` module (`python -m app.promote --username X`) that sets
`role='admin'` for an existing account. The existing `app/provision.py` invocation
documented in `README.md` and used by `scripts/Test-Cu09Acceptance.ps1` is left unchanged
so it cannot regress. The role is read from the stored account on every request, so a
promotion takes effect on the next request without invalidating sessions; the frontend
hides the nav from a stale cached role until it reloads `/session`, which is documented.

- **Alternative:** extending `provision.py` with subcommands. Rejected: a naive
  `add_subparsers` rewrite would break the documented `python -m app.provision --username`
  call, and a `--promote` flag risks reading a password or creating an account.
- **Alternative:** a roles/permissions table or UI. Rejected as over-architecture for one
  privileged role; the user excluded a role UI.
- **Follow-up, not in scope:** a `demote` command for incident response; CU10 ships only
  the promotion the decision requires.

### D2 - Authorization reuses the existing session dependencies

Add `require_admin` (built on `current`) and `admin_writer` (built on `mutation`) in the
admin router. They load the account fresh, check `role == 'admin'` and raise
`HTTPException(403)` otherwise; `current` already returns 401 for a missing/expired
session. The frontend only uses the role to show or hide navigation; the server never
trusts a client role. `SourceBusy` and `VersionConflict` live in `source_config.py` and
the stores, with exception handlers registered next to the existing ones in `main.py`
(reusing `management.VersionConflict` would leak a CU04 name).

- **Alternative:** encode the role in the session cookie/token. Rejected: it would go
  stale after promotion and duplicate the account as source of truth.

### D3 - Persist intervals in PostgreSQL and read them every cycle

Add `es_source_config` (`source_key` PK, `interval_seconds`, `version`) seeded with
`('outages', 300, 1)` and `('scheduled_works', 300, 1)`. Each scheduler loop reads the
interval from this table **before sleeping**, instead of once at startup.

- **Alternative:** keep environment variables and document a restart. Rejected: the
  approved decision requires applying changes without restarting, and the current loop
  only reads env once.
- **Alternative:** a dedicated config service or Redis. Rejected: PostgreSQL is already
  the shared store and the read is one row per cycle.
- **Failure handling:** `get_interval` catches every read failure, including **no row**,
  a **missing table** or an unexpected `None`, logs the failure class and returns the safe
  default `300`. Each scheduler cycle wraps the interval read in its own guard so any
  failure still reaches the sleep and never terminates the `while True` task.

### D4 - Allowed intervals validated at both boundaries

`ALLOWED_INTERVALS = {300, 600, 900, 1800, 3600}` enforced by the Pydantic input
(`interval_seconds`), the configuration helper and a database `CHECK`. The wire field is
seconds; the UI labels it in minutes. The seeded/default value is `300`, which preserves
the current five-minute cadence. The two sources are independent rows, so changing one
never affects the other.

### D5 - Manual retry reuses acquisition and the existing advisory lock

Add `refresh_now()` to each store. It attempts `pg_try_advisory_lock` with the store's
existing key; if it cannot acquire it, it raises `SourceBusy`, mapped to HTTP 409 with
`code: "SOURCE_BUSY"` **without recording a run and without enqueuing anything**. If it
acquires it, it calls the same `_refresh_locked` used by `refresh_once`, releases the lock
in `finally`, and returns the persisted outcome. The route resolves `{key}` with an
explicit lookup (unknown keys return 404, not a FastAPI 422), runs in
`run_in_threadpool`, and returns **HTTP 200 with the real outcome** for any completed
attempt (including failures); 5xx is reserved for transport/database failure.

- **Alternative:** an in-process lock. Rejected: it would not coordinate the scheduler
  task and a request worker, nor multiple processes/instances.
- **Alternative:** enqueue a background job. Rejected: the user excluded queues/workers
  and the advisory lock already provides mutual exclusion.
- **Why 409 and not `skipped_locked`:** a scheduler loser recording `skipped_locked` is
  correct for the automatic cadence, but a manual retry must tell the caller that an
  execution is active, so it returns 409 and writes no synthetic run.
- **Client deadline:** the synchronous retry can last up to the 20-second ENRE timeout,
  longer than the shared 10-second Axios deadline. The admin client therefore uses an
  explicit, documented 25-second deadline for the retry request only. This was confirmed by
  the user in BUILD 2; the shared client keeps its 10-second default. A client timeout is
  treated as an unconfirmed result followed by a real status read.

### D6 - Atomic optimistic concurrency for interval changes

`set_interval` performs a single
`UPDATE es_source_config SET interval_seconds=:s, version=version+1
WHERE source_key=:k AND version=:v RETURNING ...` and commits. If no row updates, it
raises `VersionConflict`, mapped to HTTP 409 `VERSION_CONFLICT`; the client reloads the
current version. This mirrors `management.correct_domicile` and keeps validation and
version increment in one statement.

- **Alternative:** read-check-write in Python. Rejected: it is racy under concurrent
  administrators; the single UPDATE is atomic in PostgreSQL.

### D7 - Status is derived from existing records

`GET /admin/sources` derives each source's state from existing data, adding no status
table:

- **Last attempt:** latest `es_*_fetch_runs` row excluding `skipped_locked` (a skipped
  run is not an attempt), ordered by `started_at` then `id`.
- **Outcome/error:** that run's `outcome` plus `detail_code`; the `http_status` is
  returned in the retry response, not in the status list.
- **Last successful check:** the current snapshot's `last_checked_at` (set on
  `ok`/`not_modified`, never on a failure), with `null` when no valid snapshot exists.
- **Last skipped-lock time:** the latest `skipped_locked` run's `started_at`, so lock
  contention is not hidden behind a stale success.
- **Interval/version and scheduler enabled:** the `es_source_config` row plus whether the
  corresponding `*_SCHEDULER_ENABLED` flag is on.

A failed attempt therefore never erases the last successful check and is never shown as a
recent success, satisfying SR03. The existing separate snapshot and run transactions leave
a small crash window where a success has no run; this is documented as a tolerated,
pre-existing inconsistency, not something CU10 fixes.

### D8 - Minimal admin endpoint surface

Three routes, all under the admin dependency set and the `no_cache` router:

- `GET /admin/sources` → two source status objects (no CSRF).
- `POST /admin/sources/{key}/refresh` → runs `refresh_now` in the threadpool; 200 with the
  real outcome; 409 `SOURCE_BUSY` when active.
- `PATCH /admin/sources/{key}/interval` → body `{ interval_seconds, version }`; 422 on an
  unsupported value; 409 `VERSION_CONFLICT` on a stale version.

`{key}` is resolved explicitly to `outages` or `scheduled_works`; anything else returns
404 after authorization. The router is registered in `main.py` next to the existing
routers.

### D9 - One admin view with two cards

Add an additive `role` to `Session.account` (frontend and backend deploy together) and an
`'admin'` shell view. The nav entry renders only when `role === 'admin'`. `AdminPanel`
renders one `Card` per source with real timestamps, outcome, error and interval, a retry
button and a selector limited to the five values. It reuses `http`, `sessionStore`,
`useRequestScope`, `Card`, `Button` and `Alert`; 401 already clears the session in the
interceptor, 403 uses a panel-specific "no autorizado" message (the shared copy wrongly
suggests re-login), `VERSION_CONFLICT` reloads the configuration, and `SOURCE_BUSY` reports
the active execution without reloading a success. Admin timestamps use the public `Z`
form. The UI never fakes a successful refresh.

- **Alternative:** a separate admin application. Rejected: the existing shell and the
  shared transport already cover it.

### D10 - Sixty minutes can reach `unavailable`, and that is documented

Freshness uses the source update time. With a sixty-minute cycle the publication age can
exceed sixty minutes late in a cycle, so CU01/CU02 will classify it `unavailable` for part
of the hour, not merely `stale`. This is correct: freshness describes the real age of the
publication. The public thresholds and contracts are not modified; only the acquisition
cadence becomes configurable, with a five-minute default.

### Concurrency analysis

1. **Two updates of the same source:** `pg_try_advisory_lock` admits one; the other
   returns 409 and writes nothing.
2. **Scheduler and manual retry:** both use the same per-source lock, so only one runs.
3. **Two admins changing intervals:** atomic `UPDATE ... WHERE version = :v`; the loser
   gets 409.
4. **Backend restart during a run:** the connection closes, releasing the advisory lock;
   the snapshot write is transactional (commit or rollback), and the last valid snapshot
   is preserved.
5. **Multiple processes/instances:** the lock and the config row live in PostgreSQL, so
   coordination is shared; no in-memory-only guard is used.

The scheduler and the interval update touch different tables (config vs. snapshot/runs),
and the scheduler reads the interval at the start of a cycle before sleeping, so a
concurrent interval change cannot produce a torn write or an inconsistent snapshot.

## Risks / Trade-offs

- [Interval changes apply at the next cycle, not instantly] → documented behavior; no
  extra wake-up mechanism, which would only work within one process.
- [Synchronous retry can exceed the shared 10-second client deadline] → the admin retry
  uses the confirmed 25-second deadline; a client timeout is reported as unconfirmed and
  followed by a real status read.
- [Sixty-minute interval can show `unavailable` on the public panels] → documented; it
  reflects real age and does not change the public contract.
- [Environment refresh variables become inert after the migration] → the seeded default
  preserves current behavior; optional cleanup of the compose variables is a follow-up.
- [Adding `role` to the session response touches the CU09 session contract] → additive
  field only; frontend and backend deploy together.
- [A crash between snapshot commit and run recording can make last success newer than last
  attempt] → tolerated and documented; not introduced by CU10.

## Migration Plan

Additive `0008_cu10`: add `es_accounts.role` with `DEFAULT 'user'` (existing accounts
become `user`), create `es_source_config`, and seed the two five-minute rows. No backfill
of CU01/CU02 data and no change to their tables. `provision.py` is untouched; promotion
uses the new `app/promote.py`. Downgrade drops the config table and the added column;
forward-only correction is preferred if data exists. The `*_REFRESH_SECONDS` variables
remain declared but inert after the migration.

## Open Questions

These are deferrable and do not change the specs, approach or task breakdown:

- Q22 backoff and per-source enable/disable remain out of scope; a future change would
  add them.
- Removal of the now-inert `*_REFRESH_SECONDS` variables is an optional cleanup.

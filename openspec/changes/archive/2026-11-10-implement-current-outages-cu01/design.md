# Design

## Context

CU01 is the first use case to ingest an external public source. The approved stack is FastAPI + SQLAlchemy/psycopg/Alembic + PostgreSQL in Docker, React/TypeScript/Vite + Axios + Zustand + Tailwind/shadcn, with `mypy --strict`, Ruff and Oxlint gates and `uv sync --locked` / npm lockfile drift rejection. The backend already has the `DB`/`Auth`/`Writer`/`no_cache` dependency pattern (`app/api.py`), a `run_in_threadpool` lifespan (`app/main.py`), `DateTime(timezone=True)` conventions and additive migrations (`0001`–`0004`). See `proposal.md` for motivation and scope.

**Verified ENRE feed contract** (read-only probe on 2026-11-10, from the host and from inside the backend container):

- `GET https://www.enre.gov.ar/paginacorte/js/data_EDS.js` → `200`, `Content-Type: application/x-javascript` (no `charset`), `Server: Lotus-Domino`, body ≈1.3 KB, UTF-8, CRLF, trailing whitespace.
- Body is `var data = { … }`: a data-only JavaScript object literal — unquoted keys, single-quoted strings, no functions/comments/`undefined`/backticks in the capture, so JSON5 can parse the literal after stripping the `var data =` wrapper.
- Root keys: `fuente`, `empresa`, `totalUsuariosSinSuministro`, `totalUsuariosConSuministro`, `ultimaActualizacion`, `totalUsuariosAyer`, `cortesPreventivos[]`, `cortesProgramados[]`, `cortesServicioMedia[]`, `cortesComunicados[]`, `cortesServicioBaja[]`.
- Observed row shapes: `cortesProgramados` → `partido, localidad, subestacion_alimentador, usuarios, normalizacion` (all `"Sin datos"` in the capture); `cortesServicioBaja` → `partido, localidad, usuarios`. The other three collections were empty; their populated shape is **not observed**.
- All values are strings, including numbers, with two conventions: `'7.202'` (thousands dot) and `'2742'`.
- `ultimaActualizacion` is Buenos Aires (UTC−3) `H:MM`, no date, no leading zero, and may be `'--:--'`; `Last-Modified` (GMT) is the only absolute source timestamp and advances with each publication. No `ETag`/`Cache-Control`.
- **TLS:** default OpenSSL settings fail with `SSLV3_ALERT_HANDSHAKE_FAILURE`; `SSLContext.set_ciphers("DEFAULT@SECLEVEL=1")` succeeds (TLS 1.2 / AES256-GCM-SHA384, RSA key exchange). Plain HTTP also returns 200 without redirect.
- Geographic precision: partido + localidad/barrio only (plus `subestacion_alimentador`); no coordinates, polygons, outage IDs or start/end timestamps.

**Verified GeoRef contract** (read-only probe on 2026-11-10):

- `/ubicacion?lat=…&lon=…` returns `departamento`, `municipio` and `provincia`; it returned **no** `localidad`.
- `/direcciones?direccion=…` returns `departamento`, `localidad_censal` and `provincia`; unscoped free text is **not** restricted to a province (an Av. Mitre address in Lomas de Zamora returned Chaco results first), so explicit province/departamento scoping is mandatory.
- ENRE emits uppercase `partido`/`localidad` and `CAPITAL` for CABA; GeoRef uses title-case `departamento`/`localidad_censal`. Name correspondence is **not** guaranteed and requires a verified mapping rule.

## Goals / Non-Goals

**Goals:**

- Backend acquisition that never executes remote code, isolates legacy TLS (D1), parses with JSON5 under a real-fixture gate (D7), and persists the last valid snapshot with provenance (D5/D8).
- A public read-only API served only from the snapshot, with a normative state machine and freshness (D11), and a frontend that filters only at the verified granularity.
- Correct category scoping (D3), distributor-wide totals (D10), zone-level-only matching (CU01-R2), and a conservative GeoRef/coverage contract (T1/T2).

**Non-Goals:**

- No CU02 programmed-works view, no CU10 source-administration UI, no map/heatmap, no outage-event reconstruction, no new authentication surface, no parser other than JSON5 without a new approval.

## Decisions

### D1 — Isolated legacy-TLS client

`app/enre_client.py` builds one `ssl.SSLContext` with `check_hostname=True`, `verify_mode=CERT_REQUIRED` and `set_ciphers("DEFAULT@SECLEVEL=1")`, and passes it to httpx as `verify=<context>` (not `verify=True`, which would discard the context and reproduce the handshake failure). The same `httpx.Client` sets a 20 s timeout, a 256 KB body cap, the research `User-Agent`, `Cache-Control: no-cache` and same-host redirects only. The context is used only for `www.enre.gov.ar`; certificate and hostname verification remain enabled. Plain HTTP was rejected for integrity; a TLS-terminating proxy was rejected as out of scope. The reduced OpenSSL security level is documented as a known, isolated trade-off.

### D7 — httpx + JSON5, gated on a real-fixture proof

Add pinned `httpx` and `json5`. The parser strips the `var data =` wrapper and trailing semicolon/whitespace, then `json5.loads` the object literal; remote JavaScript is never executed. A redacted real capture plus edge fixtures (empty arrays, `N/A`, `'-'`, `'--:--'`) become committed test fixtures, and the parse is proven before the dependency is accepted. **If the proof fails, work stops and the primary agent requests approval** for an in-house strict tokenizer; JSON5 is never silently replaced. Rationale: the captured literal uses unquoted keys and single quotes that `json` rejects, while JSON5 accepts both without executing code.

### D5/D6 — Snapshot persistence, retention and scheduler

Three additive tables (migration `0005_cu01`):

- `es_outage_snapshots`: `id`, `distributor`, `source_url`, `source_last_modified` (UTC), `source_reported_time` (nullable ART `H:MM` text), `fetched_at` (UTC), `last_checked_at` (UTC), `content_sha256`, `is_current` (boolean, default false), `total_users_without`, `total_users_with`, `users_affected_yesterday`, `row_counts` (JSON). The API derives the public `source_status` from the latest non-`skipped_locked` attempt (run outcome), so a degraded or failed attempt is representable; a partial unique index on `WHERE is_current` enforces exactly one current snapshot.
- `es_outage_reports`: `snapshot_id`, `category`, `partido`, `localidad`, `partido_key`, `localidad_key`, `subestacion_alimentador`, `affected_users`, `normalizacion_text`.
- `es_outage_fetch_runs`: `started_at`, `finished_at`, `outcome` (`ok|not_modified|http_error|tls_error|parse_error|schema_error|source_degraded|timeout|skipped_locked`), `http_status`, `detail_code`, `content_sha256`; raw bodies are never stored.

Refresh runs in the FastAPI `lifespan` every five minutes. Advisory locking is explicit: acquire `pg_try_advisory_lock(<constant>)` on a **dedicated connection**, hold it across the fetch, and release it with `pg_advisory_unlock` in `finally` before returning the connection to the pool. A holder that cannot acquire the lock records `skipped_locked` and writes no snapshot. A refresh whose `content_sha256` is unchanged records `not_modified` and updates the snapshot's `source_last_modified`, `fetched_at` and `last_checked_at` so a healthy feed never drifts to stale. A failure, timeout, unknown schema or `N/A` total leaves the current snapshot intact and records the matching run. **Retention:** keep the current snapshot plus a bounded history (default 24 snapshots) and prune older snapshots/reports; keep fetch runs for 30 days. A scheduler enable/disable flag keeps ASGI/PostgreSQL tests free of ENRE I/O.

### D8 + D11 — Freshness and normative state

`freshness` is `fresh` when `now − source_last_modified ≤ 15 min`, `stale` when `≤ 60 min`, `unavailable` when `> 60 min`, when no valid snapshot exists, or when the source timestamp cannot be determined (missing/malformed `Last-Modified` is never replaced by a fabricated time). The result exposes exactly one `state`, evaluated in precedence order: `geographic_error` → `out_of_coverage` → `unavailable` → `stale` → `reported` → `no_reports` → `coverage_unverified`. `reported` outranks `coverage_unverified` because a published row is direct evidence even when the catalog is incomplete; `no_reports` requires a `covered` area and a `fresh` snapshot with no rows. The response also carries `source_status` (`ok|degraded`) so a degraded run is representable. Every snapshot-based state returns **HTTP 200** with provenance and may carry rows for `stale`/`unavailable`; `outages: []` accompanies only `no_reports`. `503` is reserved for database unavailability. A feed with `totalUsuariosSinSuministro` of `N/A` or `'-'` is `source_degraded`: keep the snapshot, expose `source_status: degraded`, never emit `no_reports`.

### D3/D10 — Categories, totals and validator tolerance

Only `cortesServicioMedia`, `cortesServicioBaja` and `cortesPreventivos` map to the outward categories `medium_voltage`, `low_voltage` and `preventive`; `cortesProgramados` and `cortesComunicados` are not read by CU01 (programmed belongs to CU02; comunicados are left unassigned pending a CU02 review). The API returns `total_users_without`, `total_users_with` and `users_affected_yesterday` labelled `totals_scope: "edesur"`, plus each row's `affected_users`; it never sums by locality or deduplicates. The schema validator is **strict on required fields and value ranges, tolerant of additional unknown keys**: a new extra key must not discard a whole snapshot, while a missing required field or invalid range yields `schema_error`. Because media/preventivo shapes were not observed, the validator must accept rows that only carry the fields the category actually publishes. **0.1 accepted exception (U20):** no populated capture exists; the parser fails closed on invalid rows, missing or null known collections and preserves the last valid snapshot, and synthetic fixtures are used only for automated tests, never as production evidence.

### D2/D9/T1 — GeoRef adapter, ambiguity, degradation and privacy

A single backend adapter (`app/georef.py`) serves both forward and reverse lookups. Forward lookups send the address with an explicit province scope (Buenos Aires `06` or CABA) and map `departamento`→partido and `localidad_censal`/`localidad`→localidad **only when the catalog or the current ENRE snapshot uses that localidad**; otherwise the result degrades to partido. Multiple candidates are returned to the user for selection and are never guessed. Reverse geocoding maps `departamento`→partido, uses `localidad` only when present, and maps CABA to `CAPITAL`; because GeoRef returns a comuna (not an ENRE barrio), CABA addresses and positions always degrade to the `CAPITAL` partido and the catalog's CABA barrios are not address-resolvable. A GeoRef failure or timeout yields `geographic_error`, never an empty outage list. Coordinates and addresses are sent in a request body (not a query string), are used only for the lookup, and are **never persisted or logged**. Denied consent performs no query and does not repeat the permission request; the user keeps the partido/localidad/address modes (exact Q02 wording remains pending). Public resolve requests are rate-limited per client, returning 429 with `Retry-After`.

### D4/T2 — Versioned coverage catalog

A versioned data file (`backend/app/data/edesur_coverage.<version>.json`) lists the covered partidos/localidades with `source` and `retrieved_on`. It is loaded server-side, is independent of the reported outages, and classifies each zone as `covered`, `out_of_coverage` (only for explicit entries) or `coverage_unverified` (absence). `/outages/areas` returns the union of catalog entries and current snapshot rows, so a covered area with zero reports remains selectable. The catalog has no CU10 UI. **BUILD 2 seed:** the committed file is a partial, observation-based seed (each localidad appeared in a real ENRE Edesur payload on the retrieval date, in current-outage or programmed/comunicado collections of the same feed; recorded as provenance). Absence is always `coverage_unverified` and no `out_of_coverage` entry is asserted without explicit evidence. The definitive Edesur concession enumeration is still unavailable, so `out_of_coverage` remains unimplemented in practice and `no_reports` applies only to explicitly seeded localidades. **0.4 accepted (U20):** the nine-localidad catalog with documented provenance is approved; unverified zones remain `coverage_unverified`, no coverage is expanded without evidence and no negative result is invented.

### Public API contract (sketch)

- `GET /outages/areas` → `{ coverage_version, coverage_retrieved_on, areas: [{ partido, localidades: [{ localidad, coverage, reported }] }] }`.
- `GET /outages?partido=<required>&localidad=<optional>` → `{ state, source_status, freshness, granularity: "localidad"|"partido", source, source_url, fetched_at, source_updated_at, source_reported_time, coverage: { partido, localidad, status }, totals_scope: "edesur", total_users_without, total_users_with, users_affected_yesterday, outages: [{ category, partido, localidad, subestacion_alimentador, affected_users, normalizacion }] }`.
- `POST /outages/resolve` (address in the body) and `POST /outages/resolve-location` (coordinates in the body) → a resolved zone or candidate list, or `geographic_error`. Both are body-carrying so personal addresses and coordinates never enter a URL, access log or browser history.
- `partido`/`localidad` are at most 120 characters and an address at most 300; all reject control characters; invalid input returns 422 without touching the store or ENRE. `localidad` without `partido` returns 422. The public resolve endpoints are rate-limited per client to protect the free GeoRef API; a throttled request returns 429 with `Retry-After`, calls no GeoRef endpoint and surfaces a retry message. The `outages` array is present when it carries rows and omitted for `geographic_error`, `out_of_coverage` and `coverage_unverified`; `[]` is used only for `no_reports`. All responses use `Cache-Control: no-store` and require no session (SR01).

### Frontend

The current shell has no router: `frontend/src/App.tsx` renders a login form or the authenticated `Workspace`, and `AppLayout.tsx` hard-codes the diary title. CU01 adds a minimal, additive "Cortes"/"Mi cuenta" view switch in `App.tsx`; the account view remains the default so the existing CU09 login flow and E2E are unchanged, and the public "Cortes" view is reachable without a session. `frontend/src/features/outages/` holds the typed API client, state helpers and panel: dependent partido→localidad selector from `/outages/areas`, a normalized "Buscar zona" filter, GeoRef address search with candidate selection, consented geolocation, category table, distributor-wide totals, the provenance header and all normative states. The shared Axios client (`frontend/src/lib/http.ts`) forces a CSRF token on every unsafe path except `/api/login`; CU01 adds a narrow allowlist for the two public resolve POSTs (no CSRF) with tests, and exposes `Retry-After` on 429. The browser calls only `/api/outages/*` plus the shared `/api/session`/`/api/health` probes (never ENRE or GeoRef).

## Risks / Trade-offs

- [Legacy TLS at security level 1] → isolated to the ENRE client, verification retained, documented; revisit if the server modernizes.
- [JSON5 may not parse an unseen construct] → real-fixture gate; on failure stop and request approval (D7).
- [GeoRef/ENRE name mismatch and CABA "CAPITAL"] → explicit mapping rule; address/location modes stay behind verified tasks 0.3.
- [No verified coverage contents] → `coverage_unverified` for zones outside the approved nine-localidad catalog (U20); `out_of_coverage` remains unimplemented without explicit evidence.
- [Unobserved categories] → validator tolerant of extra keys and category-specific missing fields; 0.1 accepted exception (U20): no populated capture, fail-closed rows and last-snapshot retention.
- [No outage IDs] → snapshot state only; no cross-snapshot event tracking.
- [Advisory-lock leak] → dedicated connection with guaranteed `finally` release; `skipped_locked` is observable.
- [Domino caching / missing `Cache-Control`] → `no-cache`, trust `Last-Modified`, freshness thresholds.
- [Missing or malformed `Last-Modified`] → classify the snapshot `unavailable` and never fabricate a source timestamp.
- [Public resolve endpoints could exhaust the free GeoRef API] → per-client rate limit and no address/coordinate logging.
- [Shell edit for a public view] → additive view switch without a router, a narrow public-POST allowlist in `lib/http.ts`, and a CU09 shell regression.

## Migration Plan

Additive Alembic migration `0005_cu01` creating the three tables, their indexes and the `is_current` partial unique index; no data backfill and no destructive change. Rollback downgrades the migration and removes the router registration and frontend view. Retention pruning runs inside the refresh task in the same transaction boundary as the run record; the 24-snapshot history is bounded audit data for CU10 reuse, while D5's "last valid snapshot" is the single `is_current` row.

## Open Questions

- Exact Spanish UX wording for ambiguous-address selection and denied-location (Q02) — the behavior is constrained (no guessing, no repeated prompt) but the copy remains pending.
- Catalog expansion beyond the approved nine localidades (U20) requires new documented evidence; it is not an open blocker for CU01.

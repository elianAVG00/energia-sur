# Proposal

**Demo name:** *CU02 — Consultar trabajos programados informados por ENRE.*

## Why

CU02 is approved as a **reduced, demonstrable** use case. The 2026-11-10 investigation
verified that ENRE `data_EDS.js` publishes reported maintenance works
(`cortesProgramados`) with partido, localidad, alimentador, affected users and an
estimated restoration time, but **without** start date, end date, reason or
coordinates. `cortesComunicados` has never been observed populated, and the Edesur
`outage-report` agenda returns HTTP 500 or times out and has no archived payload.
Therefore the original CU02-R1 contract (filter by area and dates; show planned
start/end, reason and proximity) cannot be satisfied without inventing data. U21
records the approved reduction: show only what the operational source publishes,
mark every unpublished field as such, and keep the dated behavior as a future rule.

## What Changes

- Add a **public, read-only scheduled-works API** (`GET /scheduled-works...`) served
  from a PostgreSQL snapshot, never from ENRE at request time.
- Add an **independent server-to-server acquisition** for the same ENRE feed, reusing
  the existing TLS/`httpx` transport unchanged, with its own JSON5 parser, advisory
  lock, snapshot tables and fetch-run history. CU01 is not modified.
- Parse only `cortesProgramados` into normalized rows; count `cortesComunicados` and
  record whether it is present, but do not emit its rows because no populated shape
  has been observed.
- Return provenance, publication freshness, three-valued coverage and a normative
  state; keep the last valid snapshot across failures and never invent a negative.
- Expose `planned_start_at`, `planned_end_at` and `reason_text` as **null** with an
  explicit `limitations` list, and surface `normalizacion` verbatim as an estimated
  restoration time, never as a planned end.
- Add an independent public **"Trabajos"** view with partido/localidad selection,
  address assistance through the existing resolve endpoints, and no date inputs.

## Capabilities

### New Capabilities

- `scheduled-works`: public acquisition, caching and querying of ENRE-reported
  maintenance works by partido with an optional localidad, including provenance,
  publication freshness, three-valued coverage and explicit unpublished-field limits.

### Modified Capabilities

None. No existing spec-level requirement changes. `current-outages`,
`interruption-diary`, `frontend-shell` and the account capabilities keep their
requirements unchanged; the new public "Trabajos" view is owned by the new
`scheduled-works` capability. `App.tsx` gains an additive third view in the same way
CU01 added "Cortes", and CU01's GeoRef/coverage code is reused read-only.

## Impact

- **Backend:** new `app/scheduled_parser.py`, `app/scheduled_store.py`,
  `app/scheduled_api.py`; additive migration `0006_cu02` with
  `es_scheduled_snapshots`, `es_scheduled_works`, `es_scheduled_fetch_runs`; a second
  lifespan task with its own advisory-lock key.
- **Frontend:** new `frontend/src/features/scheduled-works/` and a "Trabajos" entry in
  the existing shell; no router and no new frontend dependency.
- **Reuse, unchanged:** `app/enre_client.py` (transport), `app/georef.py` (resolve
  endpoints), `app/coverage.py` (read-only catalog), the shared Axios client and UI
  primitives.
- **Excluded:** Edesur `outage-report`, date filtering, temporal classification,
  distance/coordinates, reasons not published by the source, coverage-catalog
  expansion, CU01 changes and CU10 UI.

## Documented limitations (accepted)

1. **Populated `cortesComunicados` shape unobserved.** It stays counted and not
   displayed; displaying it requires a new capture and an approved change. This is an
   accepted limitation for the demo, not a silent feature.
2. **No official future-dated source.** CU02-R1's dates, start/end and proximity are
   explicitly out of scope; Q05 remains TBD.
3. **Partial coverage catalog (inherited from CU01 U20).** Unverified zones stay
   `coverage_unverified` and no negative result is invented.

See [design](design.md) for the acquisition flow, contracts, states and limitations.
